from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
import json

from projectManagerSim.models import Character, CharacterRelationship, CharacterTemplateRelationship, Save, SaveCharacter
from projectManagerSim.services import game


@login_required
@require_http_methods(["GET", "POST"])
def character_selection_view(request):
    """
    Character selection screen - player chooses 4 characters from 12
    """
    
    if request.method == "GET":
        # Check if user has existing save
        existing_save = game.get_save_or_none(request.user)
        
        # Get all available characters
        characters = Character.objects.all().order_by('first_name')
        
        # Build character data with relationships
        character_data = []
        
        
        
        for char in characters:

            relationship_list = []
            relationships = CharacterTemplateRelationship.objects.filter(
                Q(character_a=char) | Q(character_b=char)
            ).select_related("character_a", "character_b")
            for rel in relationships:
                other_char = rel.character_b if rel.character_a == char else rel.character_a

                if other_char is None:
                    continue
                
                relationship_list.append({
                    'character_name': other_char.get_full_name(),
                    'character_id': other_char.id,
                    'type': rel.relationship_type,
                    'type_display': rel.relationship_type_display,
                    'icon': rel.get_icon(),
                    'score': rel.relationship_score,
                    'badge_class': rel.get_badge_class(),
                })
            relationship_list.sort(key=lambda rel: (rel['score'], rel['character_name']), reverse=True)
            character_data.append({
                'id': char.id,
                'first_name': char.first_name,
                'last_name': char.last_name,
                'full_name': char.get_full_name(),
                'description': char.description,
                'primary_role': char.get_primary_role_display(),
                'secondary_role': char.get_secondary_role_display() if char.secondary_role else None,
                'role_display': char.get_role_display_full(),
                'personality_type': char.get_personality_type_display(),
                'personality_icon': char.get_personality_type_icon(),
                'traits': char.get_traits_list(),
                'traits_display': char.get_traits_display(),
                'work_life_balance': char.work_life_balance,
                'relationships': relationship_list,
            })
        
        context = {
            'characters': character_data,
            'min_team_size': 4,
            'max_team_size': 4,
            'existing_save': existing_save,
        }
        
        return render(request, 'game/game_character_selection.html', context)
    
    elif request.method == "POST":
        # Handle team selection and save creation
        try:
            print("Starting POST")
            data = json.loads(request.body)
            selected_ids = data.get('selected_characters', [])
            print("Validate Selection")
            # Validate selection
            if len(selected_ids) != 4:
                return JsonResponse({
                    'success': False,
                    'error': 'You must select exactly 4 characters'
                }, status=400)
            print("Verify all characters exist")
            # Verify all characters exist
            if not Character.objects.exists():
                raise ValueError(
                    "Game data not loaded to database - run 'python3 manage.py loaddata characters task_types' to populate!"
                )
            print("Getting Characters")
            characters = Character.objects.filter(id__in=selected_ids)
            if characters.count() != 4:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid character selection'
                }, status=400)
            
            # Calculate team chemistry
            chemistry_analysis = analyze_team_chemistry(characters)
            
            # Deactivate old save if exists
            existing_save = game.get_save_or_none(request.user)
            if existing_save:
                existing_save.deactivate()

            print('about to make new save')
            # Create new save
            new_save = game.create_save(request.user, characters)
            print("made new save")
            
            # Start tour for every new game
            request.session['tour_step'] = 'prompt'
            request.session['tour_complete'] = False
            
            return JsonResponse({
                'success': True,
                'save_id': new_save.id,
                'team_chemistry': chemistry_analysis,
                'redirect_url': '/game/dashboard/?new_game=true'
            })
            

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            print(e)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
        
        


def analyze_team_chemistry(characters):
    """
    Analyze the chemistry of the selected team
    
    Args:
        characters: QuerySet or list of Character objects
    
    Returns:
        dict: Chemistry analysis with warnings and bonuses
    """
    char_list = [c for c in characters if c is not None]
    
    relationships = {
        'best_friends': [],
        'friends': [],
        'tensions': [],
        'rivalries': [],
    }
    
    # Check all pairs
    for i, char_a in enumerate(char_list):
        for char_b in char_list[i+1:]:
            rel = CharacterTemplateRelationship.get_relationship_between(char_a, char_b)
            if rel:
                pair = f"{char_a.get_full_name()} & {char_b.get_full_name()}"
                
                if rel.relationship_type == 'best_friends':
                    relationships['best_friends'].append(pair)
                elif rel.relationship_type == 'friends':
                    relationships['friends'].append(pair)
                elif rel.relationship_type == 'tension':
                    relationships['tensions'].append(pair)
                elif rel.relationship_type == 'rivalry':
                    relationships['rivalries'].append(pair)
    
    # Calculate overall chemistry score
    chemistry_score = (
        len(relationships['best_friends']) * 2 +
        len(relationships['friends']) * 1 -
        len(relationships['tensions']) * 1 -
        len(relationships['rivalries']) * 3
    )
    
    # Determine chemistry level
    if chemistry_score >= 4:
        chemistry_level = 'excellent'
        chemistry_message = '✓ Excellent team chemistry! This team works very well together.'
    elif chemistry_score >= 1:
        chemistry_level = 'good'
        chemistry_message = '✓ Good team chemistry. Some strong partnerships here.'
    elif chemistry_score >= -2:
        chemistry_level = 'mixed'
        chemistry_message = '⚠ Mixed chemistry. Some friction, but manageable.'
    elif chemistry_score >= -5:
        chemistry_level = 'poor'
        chemistry_message = '⚠ Poor chemistry. Expect conflicts and higher energy costs.'
    else:
        chemistry_level = 'toxic'
        chemistry_message = '⚠ Toxic team! Major conflicts will drain energy significantly.'
    
    return {
        'score': chemistry_score,
        'level': chemistry_level,
        'message': chemistry_message,
        'best_friends': relationships['best_friends'],
        'friends': relationships['friends'],
        'tensions': relationships['tensions'],
        'rivalries': relationships['rivalries'],
    }


@login_required
@require_http_methods(["POST"])
def preview_team_chemistry(request):
    """
    Preview team chemistry without creating a save.
    Called when user selects 4th character to show chemistry immediately.
    """
    try:
        data = json.loads(request.body)
        selected_ids = data.get('selected_characters', [])
        
        # Validate exactly 4 characters
        if len(selected_ids) != 4:
            return JsonResponse({
                'success': False,
                'error': 'Must select exactly 4 characters'
            }, status=400)
        
        # Get selected characters
        characters = Character.objects.filter(id__in=selected_ids)
        if characters.count() != 4:
            return JsonResponse({
                'success': False,
                'error': 'Invalid character selection'
            }, status=400)
        
        # Calculate chemistry using existing function
        chemistry_analysis = analyze_team_chemistry(characters)
        
        return JsonResponse({
            'success': True,
            'team_chemistry': chemistry_analysis
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        print(f"Preview chemistry error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to analyze chemistry'
        }, status=500)
