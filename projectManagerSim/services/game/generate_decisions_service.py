from random import randint, sample
from projectManagerSim.models import Decision
from django.db.models import Case, When, Value, IntegerField


def generate_decisions(game_save, count=2):
    decisions = (
        Decision.objects.select_for_update()
        .filter(game_save=game_save, is_made=False)
        .annotate(
            priority=Case(
                When(characterdecision__isnull=False, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        )
        .order_by('priority', 'id')
    )

    decisions_chosen = []
    
    for decision in decisions:
        is_available = decision.is_available()
        if is_available and not decision.is_served:
            if decision.percentage_chance > 0 and decision.percentage_chance < 100:
                if randint(0, 100) > decision.percentage_chance:
                    continue
            decisions_chosen.append(decision)
            count -= 1
            if not decision.repeatable:
                decision.is_served = True
                decision.save(update_fields=['is_served'])
        if count < 1:
            break

    
    return decisions_chosen