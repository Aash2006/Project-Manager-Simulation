from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class AdminSettingsTemplateTests(TestCase):

    def setUp(self):
        self.staff = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="pass12345",
            is_staff=True,
            is_superuser=True,
        )
        self.client.login(username="adminuser", password="pass12345")

    # ---- Nav bar links present on all admin pages ----

    def _nav_links_present(self, url_name):
        resp = self.client.get(reverse(url_name))
        self.assertContains(resp, reverse("admin_settings"))
        self.assertContains(resp, reverse("log_out"))
        self.assertContains(resp, "/admin/")

    def test_dashboard_nav_has_settings_and_logout(self):
        self._nav_links_present("admin_dashboard")

    def test_statistics_nav_has_settings_and_logout(self):
        self._nav_links_present("admin_statistics")

    def test_save_list_nav_has_settings_and_logout(self):
        self._nav_links_present("admin_save_list")

    # ---- Settings page content ----

    def test_settings_page_has_back_link_to_admin_dashboard(self):
        resp = self.client.get(reverse("admin_settings"))
        self.assertContains(resp, reverse("admin_dashboard"))

    def test_settings_page_has_password_form(self):
        resp = self.client.get(reverse("admin_settings"))
        self.assertContains(resp, "Change Password")
        self.assertContains(resp, "change_password")

    def test_settings_page_has_email_form(self):
        resp = self.client.get(reverse("admin_settings"))
        self.assertContains(resp, "Change Email")
        self.assertContains(resp, "change_email")

    def test_settings_page_does_not_show_welcome_header(self):
        resp = self.client.get(reverse("admin_settings"))
        self.assertNotContains(resp, "Staff-only dashboard")
        self.assertNotContains(resp, "Hello,")
