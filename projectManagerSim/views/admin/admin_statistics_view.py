from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Avg, Count
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...models import Character, Save, SaveCharacter, TaskType


@method_decorator(staff_member_required, name="dispatch")
class AdminStatisticsView(TemplateView):
    """Overview page with general save statistics and buttons for navigation."""
    template_name = "admin_statistics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        aggregates = Save.objects.aggregate(
            avg_progress=Avg("progress_percent"),
            avg_current_day=Avg("current_day"),
            avg_project_score=Avg("score"),
        )
        avg_team_size = SaveCharacter.objects.values("game_save").annotate(
            team_size=Count("id")
        ).aggregate(avg=Avg("team_size"))["avg"]

        context["total_saves_count"] = Save.objects.count()
        context["ongoing_saves_count"] = Save.objects.filter(status=Save.Status.ONGOING).count()
        context["completed_saves_count"] = Save.objects.filter(status=Save.Status.COMPLETED).count()
        context["avg_progress"] = round(aggregates["avg_progress"] or 0)
        context["avg_current_day"] = round(aggregates["avg_current_day"] or 0)
        context["avg_project_score"] = round(aggregates["avg_project_score"] or 0, 1)
        context["avg_team_size"] = round(avg_team_size or 0, 1)
        context["characters_count"] = Character.objects.count()
        context["tasks_count"] = TaskType.objects.count()
        context["top_saves"] = Save.objects.select_related("user").order_by("-progress_percent")[:10]

        return context
