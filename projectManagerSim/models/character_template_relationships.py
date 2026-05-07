from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from projectManagerSim.models.character import Character


class CharacterTemplateRelationship(models.Model):
    """Baseline relationship template between two global Character records.

    These rows are seeded once and describe the default chemistry between
    characters before a specific Save is created. When a new game starts,
    these template rows are copied into save-specific CharacterRelationship
    rows for the selected team.
    """

    character_a = models.ForeignKey(
        Character,
        on_delete=models.CASCADE,
        related_name="template_relationships_from",
        help_text="First character in the template relationship",
    )
    character_b = models.ForeignKey(
        Character,
        on_delete=models.CASCADE,
        related_name="template_relationships_to",
        help_text="Second character in the template relationship",
    )
    relationship_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(-50), MaxValueValidator(50)],
        help_text="Baseline relationship strength: -50 (rivalry) to +50 (best friends)",
    )

    class Meta:
        unique_together = ["character_a", "character_b"]
        ordering = ["character_a__first_name", "character_b__first_name"]
        verbose_name = "Character Template Relationship"
        verbose_name_plural = "Character Template Relationships"

    def __str__(self):
        return (
            f"{self.character_a.get_full_name()} ↔ {self.character_b.get_full_name()} "
            f"({self.relationship_type_display})"
        )

    @property
    def relationship_type(self):
        if self.relationship_score >= 40:
            return "best_friends"
        if self.relationship_score >= 15:
            return "friends"
        if self.relationship_score >= -14:
            return "neutral"
        if self.relationship_score >= -39:
            return "tension"
        return "rivalry"

    @property
    def relationship_type_display(self):
        return {
            "best_friends": "Best Friends",
            "friends": "Friends",
            "neutral": "Neutral",
            "tension": "Tension",
            "rivalry": "Rivalry",
        }.get(self.relationship_type, "Unknown")

    @property
    def energy_modifier(self):
        return {
            "best_friends": 0.85,
            "friends": 0.90,
            "neutral": 1.00,
            "tension": 1.10,
            "rivalry": 1.25,
        }.get(self.relationship_type, 1.00)

    @property
    def energy_modifier_percent(self):
        modifier = self.energy_modifier
        if modifier < 1.0:
            percent = round((1.0 - modifier) * 100)
            return f"-{percent}%"
        elif modifier > 1.0:
            percent = round((modifier - 1.0) * 100)
            return f"+{percent}%"
        else:
            return "0%"

    def get_icon(self):
        return {
            "best_friends": "❤️",
            "friends": "😊",
            "neutral": "😐",
            "tension": "😬",
            "rivalry": "⚡",
        }.get(self.relationship_type, "❓")

    def get_badge_class(self):
        return {
            "best_friends": "badge-success",
            "friends": "badge-primary",
            "neutral": "badge-secondary",
            "tension": "badge-warning",
            "rivalry": "badge-danger",
        }.get(self.relationship_type, "badge-secondary")

    @staticmethod
    def get_relationship_between(char_a, char_b):
        try:
            return CharacterTemplateRelationship.objects.get(
                character_a=char_a,
                character_b=char_b,
            )
        except CharacterTemplateRelationship.DoesNotExist:
            try:
                return CharacterTemplateRelationship.objects.get(
                    character_a=char_b,
                    character_b=char_a,
                )
            except CharacterTemplateRelationship.DoesNotExist:
                return None

    def save(self, *args, **kwargs):
        if self.character_a_id == self.character_b_id:
            raise ValueError("A character cannot have a relationship with themselves")

        if self.character_a_id and self.character_b_id and self.character_a_id > self.character_b_id:
            self.character_a_id, self.character_b_id = self.character_b_id, self.character_a_id

        super().save(*args, **kwargs)
