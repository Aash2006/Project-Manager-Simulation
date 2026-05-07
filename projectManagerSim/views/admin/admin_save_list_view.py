from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Prefetch, Q
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from projectManagerSim.models import Save, SaveCharacter


@method_decorator(staff_member_required, name="dispatch")
class AdminSaveListView(ListView):
    model = Save
    template_name = "admin_save_list.html"
    context_object_name = "saves"
    paginate_by = 50

    def _get_query(self) -> str:
        return (self.request.GET.get("q") or "").strip()

    def get_queryset(self):
        q = self._get_query()

        qs = (
            Save.objects
            .select_related("user")
            .prefetch_related(
                Prefetch(
                    "characters",
                    queryset=SaveCharacter.objects.select_related("character", "task_assigned"),
                )
            )
            .order_by("-last_used")
        )

        if q:
            qs = qs.filter(Q(user__username__icontains=q) | Q(save_name__icontains=q))

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self._get_query()
        return ctx
