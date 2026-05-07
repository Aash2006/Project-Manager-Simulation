from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from ...models import Character, TaskType


@method_decorator(staff_member_required, name="dispatch")
class CharacterListView(ListView):
    model = Character
    template_name = "admin_character_list.html"
    context_object_name = "object_list"


@method_decorator(staff_member_required, name="dispatch")
class TaskTypeListView(ListView):
    model = TaskType
    template_name = "admin_task_type_list.html"
    context_object_name = "object_list"
