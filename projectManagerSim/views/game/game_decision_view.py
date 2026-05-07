from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from projectManagerSim.models import Decision, Save
from projectManagerSim.decorators import game_view
import random
import json
from projectManagerSim.models import Decision, Option, Save
from projectManagerSim.models.save_character import SaveCharacter


@require_GET
@game_view
def get_decision(request, engine):
    """"Returns a random decision from the Decision table in JSON Format (for displaying via modal)"""
    decision_id = request.GET.get('decision_id')
    decision_object = Decision.objects.filter(pk=decision_id).first()
    if not decision_object:
        return JsonResponse(
            {"error": "No decisions available"},
            status=404
        )
    
    # Get the options for this decision
    options = list(decision_object.options.all())
    
    if len(options) < 2:
        return JsonResponse(
            {"error": "Decision does not have enough options"},
            status=500
        )
    
    decision = {
        "title": decision_object.title,
        "body": decision_object.body,
        "option1": {
            "label": options[0].text,
            "action": "option1",
            "option_id": options[0].pk
        },
        "option2": {
            "label": options[1].text,
            "action": "option2",
            "option_id": options[1].pk
        },
        "decision_id": decision_object.pk
    }
    return JsonResponse(decision)


@require_POST
@game_view
def process_decision(request, engine):
    """"
    Takes in a request with a given action (between 2 options) and a decision ID (pk), 
    then calls the relevant choice_result method
    """
    data = json.loads(request.body)
    option_id = data.get("option_id")
    decision_id = data.get("decision_id")
    save = engine.fetch('save')
    for d in save.available_decisions:
        for o in d['options']:
            print(f"Option {o['id']} - {o['text']}")
    
    if not decision_id or not option_id:
        return JsonResponse({"error": "Invalid request"}, status=400)
    
    game_save = save

    decision = Decision.objects.filter(pk=decision_id).filter(game_save=game_save).first()
    option = Option.objects.filter(pk=option_id).first()
    
    if not decision or not option:
        return JsonResponse({"error": "Decision or option not found"}, status=404)
    
    game_save.available_decisions
    game_save.available_decisions = [
        d for d in game_save.available_decisions 
        if d['id'] != int(decision_id)
    ]
    game_save.save()
    
    option.apply()
    SaveCharacter.objects.filter(game_save=game_save).filter(leaving=True).delete()
    engine.save.refresh_from_db()

    return JsonResponse({"success": True})