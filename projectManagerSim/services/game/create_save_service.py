import json
import random

from django.db import IntegrityError, transaction
from django.http import HttpResponse

from projectManagerSim.fixtures.character_descr import get_relationship_score
from projectManagerSim.models import (
    Character,
    Save,
    SaveCharacter,
    Task,
    TaskType,
)
from projectManagerSim.models.character_relationships import CharacterRelationship
from projectManagerSim.models.character_template_relationships import CharacterTemplateRelationship
from projectManagerSim.models.decisions.character_decision import CharacterDecision
from projectManagerSim.models.decisions.option import *
import json
import os
import re
import random
from itertools import product
import copy
from itertools import permutations
from pathlib import Path

from projectManagerSim.models.decisions.project_option import ProjectOption
from projectManagerSim.models.decisions.save_character_option import SaveCharacterOption
from projectManagerSim.models.decisions.save_character_relation_option import SaveCharacterRelationOption
TAG_PATTERN = r"\[([A-Z0-9._]+)\]"
def replace_tags(text, character_name="", character_name2=""):
    def mapper(match):
        tag = match.group(1) # The text inside the [], e.g., "TASKS.5"
        
        if tag == "NAME":
            return character_name
        if tag == "NAME2":
            return character_name2
        
        if tag.startswith("TASKS."):
            task_id = tag.split(".")[1]
            task =Task.objects.filter(internal_id=task_id).first()
            if task:
                return task.name_short()
            
        return f"[{tag}]" # Return original if no match found

    return re.sub(TAG_PATTERN, mapper, text)

def populate_character_relationships(save_characters):
    """Create save-specific relationships from global template relationships."""

    template_scores = {}
    character_ids = [save_char.character_id for save_char in save_characters]
    if character_ids:
        for template in CharacterTemplateRelationship.objects.filter(
            character_a_id__in=character_ids,
            character_b_id__in=character_ids,
        ):
            template_scores[(template.character_a_id, template.character_b_id)] = template.relationship_score

    for i, save_char_a in enumerate(save_characters):
        for save_char_b in save_characters[i + 1:]:
            key = tuple(sorted((save_char_a.character_id, save_char_b.character_id)))
            relationship_score = template_scores.get(
                key,
                get_relationship_score(save_char_a.character_id, save_char_b.character_id),
            )
            CharacterRelationship.objects.create(
                character_a=save_char_a,
                character_b=save_char_b,
                relationship_score=relationship_score,
            )

def populate_characters(save, characters):
    """Create SaveCharacter rows and per-save relationship rows."""

    save_characters = []
    for c in characters:
        save_characters.append(
            SaveCharacter.objects.create(
                game_save=save,
                character=c,
                current_energy=c.initial_energy,
                current_happiness=c.initial_happiness,
                current_confidence=c.initial_confidence,
                current_dedication=c.initial_dedication,
                current_stress=c.initial_stress,
                current_irritability=c.initial_irritability,
                current_skill_level=c.initial_skill_level,
                current_communication_skills=c.initial_communication_skills,
                current_reliability=c.initial_reliability,
                current_teachability=c.initial_teachability,
            )
        )

    populate_character_relationships(save_characters)

    return save_characters

def populate_tasks(save):
    """Function to initialise game save with tasks"""

    types = TaskType.objects.all()
    
    count=0
    for t in types:
        count += 1

        percent = 0
        if count % 3 == 0:
            percent = 33
        if count+1 % 3 == 0:
            percent = 66
        Task.objects.create(
            name=f"Task {count}: {t.task_type_name} Task",
            game_save=save,
            time_to_complete=random.randint(1, 3),
            task_type=t,
            unlocks_at_percent=percent,
            number_of_people_required=random.randint(1, 3),
            energy_cost=random.randint(5, 30),
            difficulty=random.randint(1, 10),
            internal_id=count
        )
    print(Task.objects.all())

#
# POPULATE DECISIONS METHODS - this stuff is really lengthy
#
def inject_pks(json_str, lookup):
    """Helper to swap placeholder strings for real integer IDs."""
    for placeholder, real_pk in lookup.items():
        json_str = json_str.replace(f'"{placeholder}"', str(real_pk))
    return json.loads(json_str)
def get_placeholders(json_str):
    """
    Gets the placeholders from a json_str (*a and ?a) and puts them in a tuple
    """
    found = re.findall(r'["\']([?*][a-z])["\']', json_str)
    placeholders = sorted(list(set(found)))
    return (
        [p for p in placeholders if p.startswith('?')],
        [p for p in placeholders if p.startswith('*')]
    )

def apply_lookup(json_str, lookup):
    for placeholder, real_pk in lookup.items():
        json_str = json_str.replace(f'"{placeholder}"', str(real_pk))
    return json.loads(json_str)

def generate_variants(json_str, random_map, multis, remaining_pks):
    """
    Generates multiple variants for when '*a' is used
    """
    if not multis:
        return [apply_lookup(json_str, random_map)]

    if len(multis) > len(remaining_pks):
        print("Warning: Skipping file. Not enough unique characters for '*' placeholders.")
        return []

    variants = []
    for combo in permutations(remaining_pks, len(multis)):
        lookup = {**random_map, **dict(zip(multis, combo))}
        variants.append(apply_lookup(json_str, lookup))
    return variants

def resolve_placeholders(data):
    """
    Analyzes the JSON for placeholders and returns a list of data objects 
    with real PKs injected.
    """
    char_pks = list(Character.objects.all().values_list('pk', flat=True))
    json_str = json.dumps(data)
    
    randoms, multis = get_placeholders(json_str)
    
    if not randoms and not multis:
        return [data]

    if len(randoms) > len(char_pks):
        raise ValueError(f"Not enough characters ({len(char_pks)}) for {len(randoms)} '?' placeholders.")
    
    random_values = random.sample(char_pks, len(randoms))
    random_map = dict(zip(randoms, random_values))
    remaining_pks = [pk for pk in char_pks if pk not in random_map.values()]
    
    return generate_variants(json_str, random_map, multis, remaining_pks)


def get_task_by_index(task_list, index_val):
    """Get's a task from task_list by it's index, implements bounds checking"""
    if 0 < index_val <= len(task_list):
        return task_list[index_val - 1]
    return None

def get_unlocking_decision(opt_json, save):
    """Gets the decision unlocked by the option"""
    related_name = opt_json.get("unlocking_decision")
    return Decision.objects.filter(game_save=save).filter(related_name=related_name).first() if related_name else None

def get_effects(opt_json, suffix="", remove_task_assign_result=False):
    """Extracts the effect fields from the JSON"""
    fields = [
        "happiness", "confidence", "dedication", "stress", "irritability", 
        "skill_level", "communication_skills", "reliability", "teachability", "energy"
    ]
    effects = {f"{field}_effect{suffix}": opt_json.get(f"{field}_effect{suffix}", 1.0) for field in fields}
    extra_effects = {
        f"set_rest{suffix}": opt_json.get(f"set_rest{suffix}", False),
        f"unassign_task{suffix}": opt_json.get(f"unassign_task{suffix}", False)
    }
    if not remove_task_assign_result:
        extra_effects[f"task_assign_result{suffix}"] = opt_json.get(f"task_assign_result{suffix}", -1)
    effects.update(extra_effects)
    return effects

def make_character_decision_object(save, data, title, body) -> CharacterDecision:
    """Creates a CharacterDecision object"""
    reqs = data.get('requirements', {})
    
    d = CharacterDecision.objects.create(
        title=title, body=body, game_save=save,
        deadline=data.get("deadline", 3),
        percentage_chance=data.get("percentage_chance", 100),
        day_requirement=reqs.get("day_requirement", 0),
        related_name=data.get('related_name'),
        is_locked=data.get("is_locked", False),
        stat_requirement=data.get('requirements', {}).get('stat_require', []),
        repeatable=data.get("repeatable", False)
    )
    return d

def handle_character_option(opt, char, task_list, decision, save):
    """Creates a CharacterOption object"""
    task_res = get_task_by_index(task_list, opt.get("task_assign_result", -1))
    for sc in SaveCharacter.objects.filter(character=char, game_save=save):
        SaveCharacterOption.objects.create(
            decision=decision, save_character=sc, text=opt.get("text", ""),
            score_effect=opt.get("score_effect", 0),
            unlocking_decision=get_unlocking_decision(opt, save),
            unlocking_day_delay=opt.get("unlocking_day_delay", 0),
            leave_team=opt.get('leave_team'),
            create_tasks=opt.get('create_tasks'),
            **{**get_effects(opt), "task_assign_result": task_res.id if task_res else -1}
        )

def handle_character_decision(save, data, task_list):
    """Handles the creation of a character decision given JSON"""
    char = Character.objects.filter(pk=data['character_pk']).first()
    if not char: return
    
    title = replace_tags(data['decision']['title'], char.get_full_name())
    body = replace_tags(data['decision']['body'], char.first_name)
    
    reqs = data.get('requirements', {})
    sc_query = SaveCharacter.objects.filter(game_save=save, character=char).first()
    d = make_character_decision_object(save, data, title, body)
    CharacterDecision.objects.filter(id=d.id).update(
        task_available = get_task_by_index(task_list, reqs.get("task_available", 0)),
        task_complete = get_task_by_index(task_list, reqs.get("task_complete", 0)),
        task_working = sc_query if reqs.get("is_working_task") else None,
        task_not_working = sc_query if reqs.get("isnt_working_task") else None
    )
    d.required_characters_in_save.add(char)
    d.save()

    for opt in data['options']:
        handle_character_option(opt, char, task_list, d, save)

def handle_relation_option(opt, char1, char2, task_list, decision, save):
    """Creates a CharacterRelationOption object"""
    t1 = get_task_by_index(task_list, opt.get("task_assign_result", -1))
    t2 = get_task_by_index(task_list, opt.get("task_assign_result_2", -1))
    
    sc1_qs = SaveCharacter.objects.filter(character=char1, game_save=save)
    sc2_qs = SaveCharacter.objects.filter(character=char2, game_save=save)

    for sc1, sc2 in zip(sc1_qs, sc2_qs):
        SaveCharacterRelationOption.objects.create(
            decision=decision, text=opt.get("text", ""),
            score_effect=opt.get("score_effect", 0),
            relation_change=opt.get("relation_change", 0),
            unlocking_decision=get_unlocking_decision(opt, save),
            unlocking_day_delay=opt.get("unlocking_day_delay", 0),
            leave_team=opt.get('leave_team'),
            create_tasks=opt.get('create_tasks'),
            save_character=sc1,
            save_character_2=sc2,
            **{**get_effects(opt), "task_assign_result": t1.id if t1 else -1},
            **{**get_effects(opt, "_2"), "task_assign_result_2": t2.id if t2 else -1}
        )

def handle_relation_decision(save, data, task_list):
    """Handles the creation of a character relation decision given JSON"""
    char1 = Character.objects.filter(pk=data['character_pk']).first()
    char2 = Character.objects.filter(pk=data['character_pk_2']).first()
    if not char1 or not char2: return

    sc1 = SaveCharacter.objects.filter(game_save=save, character=char1).first()
    sc2 = SaveCharacter.objects.filter(game_save=save, character=char2).first()

    title = replace_tags(data['decision']['title'], char1.get_full_name(), char2.get_full_name())
    body = replace_tags(data['decision']['body'], char1.first_name, char2.first_name)
    reqs = data.get('requirements', {})
    d = make_character_decision_object(save, data, title, body)
    CharacterDecision.objects.filter(id=d.id).update(
        task_available = get_task_by_index(task_list, reqs.get("task_available", 0)),
        task_complete = get_task_by_index(task_list, reqs.get("task_complete", 0)),
        relationship=CharacterRelationship.get_relationship_between(sc1, sc2),
        relationship_score=data.get('relationship_score')
    )
    d.required_characters_in_save.add(char1, char2)
    d.save()

    for opt in data['options']:
        handle_relation_option(opt, char1, char2, task_list, d, save)


def handle_project_decision(save, data, task_list):
    """Handles the creation of a project decision given JSON"""
    title = data['decision']['title']
    body = data['decision']['body']
    
    reqs = data.get('requirements', {})
    
    d = Decision.objects.create(
        title=title, body=body, game_save=save,
        deadline=data.get("deadline", 3),
        percentage_chance=data.get("percentage_chance", 100),
        day_requirement=reqs.get("day_requirement", 0),
        related_name=data.get('related_name'),
        is_locked=data.get("is_locked", False),
        repeatable=data.get("repeatable", False)
    )

    for opt in data['options']:
        ProjectOption.objects.create(
            decision=d, text=opt.get("text", ""),
            score_effect=opt.get("score_effect", 0),
            unlocking_decision=get_unlocking_decision(opt, save),
            unlocking_day_delay=opt.get("unlocking_day_delay", 0),
            create_tasks=opt.get('create_tasks'),
            **{**get_effects(opt, remove_task_assign_result=True)}
        )

DECISION_HANDLERS = {
    "CHARACTER": handle_character_decision,
    "CHARACTER_RELATION": handle_relation_decision,
    "PROJECT" : handle_project_decision
}            

def populate_decisions(save):
    """
    Initialise all the decisions. Checks for the category of decision and then runs the related handler!
    """
    decisions_folder = Path(__file__).resolve().parents[2] / "decisions"
    task_list = list(Task.objects.filter(game_save=save).order_by('internal_id'))

    for root, _, files in os.walk(decisions_folder):
        for file in files:
            if not file.endswith('.json'): continue
            
            try:
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                resolved_variants = resolve_placeholders(template_data)
                
                for data in resolved_variants:
                    handler = DECISION_HANDLERS.get(data.get('decision_type'))
                    if handler:
                        handler(save, data, task_list)
                    else:
                        print(f"Unknown decision type: {data.get('decision_type')} in {file}")

            except (Exception) as e:
                print(f'Error reading {file}: {e}')
    print(f"The Decisions...\n{Decision.objects.filter(game_save=save)}")


@transaction.atomic
def create_save(auth_user, characters):
    """
    initialise an active save instance
    
    this will raise the exception ValueError if there is already an 
    active save, and all possible other db exceptions if the
    atomic transaction fails
    """
    print('in create_save')
    try: save = Save.objects.create(user=auth_user, active=True)
    except IntegrityError: 
        print('got IntegrityError')
        raise IntegrityError(
            f'Error in create_save(): active save for {auth_user} initiated but one already exists'
        )
    print("populating characters...")
    populate_characters(save, characters)
    print("populating tasks...")
    populate_tasks(save)
    print("populating decisions...")
    populate_decisions(save)
    
    print(f'all done: {save}')
    return save



def get_save_or_none(user):
    """
    try and get an active save for the user
    return none if not found
    """
    try: 
        return Save.objects.get(
                user = user,
                active = True
            )

    except Save.DoesNotExist: 
        return None