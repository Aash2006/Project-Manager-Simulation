from django.test import TransactionTestCase
from django.core.management import call_command
from django.contrib.auth.models import User
from projectManagerSim.models import Save, SaveCharacter, Character, Task, TaskType, CharacterRelationship
from io import StringIO


class UnseedImportTest(TransactionTestCase):
    """Tests that unseed command is importable and well-formed"""

    def test_unseed_can_be_imported(self):
        try:
            from projectManagerSim.management.commands.unseed import Command  # noqa
        except ImportError as e:
            self.fail(f"Cannot import unseed command: {e}")

    def test_unseed_has_help_text(self):
        from projectManagerSim.management.commands.unseed import Command
        self.assertTrue(hasattr(Command, 'help'))
        self.assertIsInstance(Command.help, str)
        self.assertIn('Clears all test data', Command.help)

    def test_unseed_has_keep_superusers_argument(self):
        from projectManagerSim.management.commands.unseed import Command
        import argparse
        parser = argparse.ArgumentParser()
        cmd = Command()
        cmd.add_arguments(parser)
        # Should not raise
        args = parser.parse_args(['--keep-superusers'])
        self.assertTrue(args.keep_superusers)


class UnseedBasicTest(TransactionTestCase):
    """Tests that unseed clears all data correctly"""

    def setUp(self):
        call_command('seed', verbosity=0)

    def test_unseed_clears_save_characters(self):
        self.assertGreater(SaveCharacter.objects.count(), 0)
        call_command('unseed', verbosity=0)
        self.assertEqual(SaveCharacter.objects.count(), 0)

    def test_unseed_clears_saves(self):
        self.assertGreater(Save.objects.count(), 0)
        call_command('unseed', verbosity=0)
        self.assertEqual(Save.objects.count(), 0)

    def test_unseed_clears_tasks(self):
        self.assertGreater(Task.objects.count(), 0)
        call_command('unseed', verbosity=0)
        self.assertEqual(Task.objects.count(), 0)

    def test_unseed_clears_task_types(self):
        self.assertGreater(TaskType.objects.count(), 0)
        call_command('unseed', verbosity=0)
        self.assertEqual(TaskType.objects.count(), 0)

    def test_unseed_clears_characters(self):
        self.assertGreater(Character.objects.count(), 0)
        call_command('unseed', verbosity=0)
        self.assertEqual(Character.objects.count(), 0)

    def test_unseed_clears_users(self):
        self.assertGreater(User.objects.count(), 0)
        call_command('unseed', verbosity=0)
        self.assertEqual(User.objects.count(), 0)

    def test_unseed_clears_everything_at_once(self):
        call_command('unseed', verbosity=0)
        self.assertEqual(SaveCharacter.objects.count(), 0)
        self.assertEqual(Save.objects.count(), 0)
        self.assertEqual(Task.objects.count(), 0)
        self.assertEqual(TaskType.objects.count(), 0)
        self.assertEqual(Character.objects.count(), 0)
        self.assertEqual(User.objects.count(), 0)


class UnseedKeepSuperusersTest(TransactionTestCase):
    """Tests for --keep-superusers flag"""

    def setUp(self):
        # Create a superuser and a regular user manually
        User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
        User.objects.create_user('regular', password='pass123')

        # Create some data using correct fields
        TaskType.objects.create(task_type_name='Test Type', required_role='backend')
        Character.objects.create(
            first_name='John',
            last_name='Doe',
            primary_role='backend',
            description='Test character'
        )

    def test_keep_superusers_keeps_superuser(self):
        call_command('unseed', keep_superusers=True, verbosity=0)
        self.assertTrue(User.objects.filter(username='admin', is_superuser=True).exists())

    def test_keep_superusers_deletes_regular_users(self):
        call_command('unseed', keep_superusers=True, verbosity=0)
        self.assertFalse(User.objects.filter(username='regular').exists())

    def test_keep_superusers_correct_user_count(self):
        call_command('unseed', keep_superusers=True, verbosity=0)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.filter(is_superuser=True).count(), 1)

    def test_keep_superusers_still_clears_other_tables(self):
        call_command('unseed', keep_superusers=True, verbosity=0)
        self.assertEqual(SaveCharacter.objects.count(), 0)
        self.assertEqual(Save.objects.count(), 0)
        self.assertEqual(Task.objects.count(), 0)
        self.assertEqual(TaskType.objects.count(), 0)
        self.assertEqual(Character.objects.count(), 0)

    def test_without_flag_deletes_superusers_too(self):
        call_command('unseed', verbosity=0)
        self.assertEqual(User.objects.count(), 0)
        self.assertFalse(User.objects.filter(username='admin').exists())


class UnseedIdempotencyTest(TransactionTestCase):
    """Tests that unseed can be run multiple times safely"""

    def test_unseed_on_empty_database(self):
        # Should not raise any errors on empty db
        call_command('unseed', verbosity=0)
        call_command('unseed', verbosity=0)
        self.assertEqual(User.objects.count(), 0)

    def test_unseed_multiple_times_after_seed(self):
        call_command('seed', verbosity=0)
        call_command('unseed', verbosity=0)
        call_command('unseed', verbosity=0)
        call_command('unseed', verbosity=0)

        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(TaskType.objects.count(), 0)
        self.assertEqual(Task.objects.count(), 0)
        self.assertEqual(Character.objects.count(), 0)
        self.assertEqual(Save.objects.count(), 0)
        self.assertEqual(SaveCharacter.objects.count(), 0)

    def test_seed_unseed_seed_cycle(self):
        # Full cycle should work cleanly
        call_command('seed', verbosity=0)
        call_command('unseed', verbosity=0)
        call_command('seed', verbosity=0)

        # After re-seeding, data should exist again
        self.assertGreater(User.objects.count(), 0)
        self.assertGreater(Character.objects.count(), 0)
        self.assertGreater(TaskType.objects.count(), 0)


class UnseedOrderTest(TransactionTestCase):
    """Tests that unseed deletes in the correct order (no FK violations)"""

    def setUp(self):
        call_command('seed', verbosity=0)

    def test_save_characters_deleted_before_saves(self):
        # If order is wrong this would raise IntegrityError
        try:
            call_command('unseed', verbosity=0)
        except Exception as e:
            self.fail(f"Unseed raised an exception due to deletion order: {e}")

    def test_tasks_deleted_before_saves(self):
        try:
            call_command('unseed', verbosity=0)
        except Exception as e:
            self.fail(f"Unseed raised an exception due to deletion order: {e}")
