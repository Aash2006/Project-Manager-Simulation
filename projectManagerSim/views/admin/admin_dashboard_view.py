from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db.models import Avg, Count
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from projectManagerSim.models import Save, SaveCharacter


@method_decorator(staff_member_required, name="dispatch")
class AdminDashboardView(TemplateView):
    template_name = "admin_dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["total_users"] = User.objects.filter(is_superuser=False).count()
        ctx["total_saves"] = Save.objects.count()
        ctx["completed_saves"] = Save.objects.filter(status=Save.Status.COMPLETED).count()
        ctx["avg_progress"] = round(Save.objects.aggregate(a=Avg("progress_percent"))["a"] or 0)

        team_avg = (
            SaveCharacter.objects.values("game_save_id")
            .annotate(team_size=Count("id"))
            .aggregate(a=Avg("team_size"))["a"]
        )
        ctx["avg_team_size"] = round(team_avg or 0, 1)

        ctx["recent_saves"] = Save.objects.select_related("user").order_by("-last_used")[:5]
        return ctx
