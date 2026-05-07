This is for documentation purposes! This shows all available decision types along with their fields!

# decisions type CHARACTER - For affecting a single character's stats
{
    "decision_type" : "CHARACTER",
    "character_pk" : 1,
    "percentage_chance" : 10,
    "decision" : {
        "title" : "[NAME] - Task Assign",
        "body" : "hey, could I do [TASKS.5]?"
    },
    "repeatable" : true, # If not set, decision is only once per run
    "deadline" : 2,
    "related_name" : "decision_task_cool", # Used to identify a decision after its been made. Optional, but you'll need this if you want an option to unlock a decision
    "is_locked" : true, # Use this to make a decision locked until explicitly unlocked by an option using its related_name
    "requirements" : { # Requirements
        "task_available" : 5,
        "task_complete" : 2,
        "day_requirement" : 0,
        "is_working_task" : true,
        "isnt_working_task" : true,
        "stat_require" : [ # For if you need stat(s) to be a certain value
            { 
                "stat" : "happiness", # The stat in question
                "operator" : "<", # Available operators are <, >, ==, <=, >=
                "value" : 50, # The value in question
                "character_pk" : 1 # The character whose stats you're checking
            },
            { 
                "stat" : "happiness", # The stat in question
                "operator" : "==", # Available operators are <, >, ==, <=, >=
                "value" : 22, # The value in question
                "character_pk" : 3 # The character whose stats you're checking
            },
        ]
    },
    "options" : [
        {
            "text" : "Sure",
            "score_effect": 2, # The score is additive!
            "happiness_effect": 1.03, # These effects are multiplicative!
            "reliability_effect" : 1.05,
            "confidence_effect" : 0.8,
            "stress_effect" : 0.8,
            "irritability_effect" : 2.8,
            "skill_level_effect" : 0.1,
            "communication_skills_effect" : 0.01,
            "teachability_effect" : 0.11,
            "energy_effect" : 1.5,
            "task_assign_result" : 5, # Assigns them to this task
            "set_rest" : true,
            "unassign_task" : true,
            "unlocking_decision" : "some_other_decision", # Allows you to unlock a decision with this option, uses related_name to identify the decision
            "unlocking_day_delay" : 3, # Optional, sets minimum day requirement to X days after this option is clicked. if omitted, decision just uses its default day minimum
            "leave_team": 1, # Choosing this option makes any SaveCharacter with this Character pk leave! Use sparingly...
            "create_tasks" : [ # an option can create tasks
                { # All fields in here are mandatory!
                    "task_type" : 1, 
                    "name" : "Bugfix", # Don't include the "Task X -" it'll be added automatically
                    "time_to_complete": 3,
                    "unlocks_at_percent":0,
                    "number_of_people_required":3,
                    "energy_cost": 5,
                    "difficulty": 1
                }
            ]
        }, # You can have as many options as you like
        {
            "text" : "Sorry, no.",
            "score_effect": -1,
            "happiness_effect": 0.91,
            "reliability_effect" : 0.97
        }
    ]
}

# decisions type CHARACTER_RELATION - For affecting the relationship and stats between 2 characters
{
    "decision_type" : "CHARACTER_RELATION",
    "character_pk" : ?a, # You can do this to get random characters to have this happen. ?a, ?b, ?c, etc. etc. 
    "character_pk_2" : *b, # You can also do this to have it be with every possible combo. It shares letters with the ? one so don't do ?a and *a
    "relationship_score": "best friends", # You have to write them in this form
    "decision" : {
        "title" : "[NAME] & [NAME2] - Fight",
        "body" : "[NAME2]: [NAME] is being ridiculous!\n[NAME]: yeah shut up bro"
    },
    "related_name" : "decision_task_cool", # Used to identify a decision after its been made. Optional, but you'll need this if you want an option to unlock a decision
    "deadline" : 2,
    "requirements" : {
        "task_available" : 5,
        "day_requirement" : 0,
        "stat_require" : [{ # For if you need stat(s) to be a certain value
            "stat" : "happiness", # The stat in question
            "operator" : "<", # Available operators are <, >, ==, <=, >=
            "value" : 50, # The value in question
            "character_pk" : ?a # The character whose stats you're checking
        }]
    },
    "options" : [
        {
            "text" : "Sure",

            "score_effect": 2,
            "happiness_effect" : 1.8,
            "confidence_effect" : 0.8,
            "stress_effect" : 0.8,
            "irritability_effect" : 2.8,
            "skill_level_effect" : 0.1,
            "communication_skills_effect" : 0.01,
            "reliability_effect" : 1.5,
            "teachability_effect" : 0.11,
            "energy_effect" : 1.5,
            "task_assign_result" : 5,
            "set_rest" : true,
            "unassign_task" : true,

            "happiness_effect_2": 1.03,
            "confidence_effect_2" : 0.8,
            "stress_effect_2" : 0.8,
            "irritability_effect_2" : 2.8,
            "skill_level_effect_2" : 0.1,
            "communication_skills_effect_2" : 0.01,
            "reliability_effect_2" : 1.5,
            "teachability_effect_2" : 0.11,
            "energy_effect_2" : 1.5,
            "task_assign_result_2" : 5,
            "set_rest_2" : true,
            "unassign_task_2" : true,
            "leave_team": 1,
            "relation_change" : -10, # Relationship change between the 2 characters
            "unlocking_decision" : "some_other_decision",
            "unlocking_day_delay" : 3,
            "create_tasks" : [ # an option can create tasks
                { # All fields in here are mandatory!
                    "task_type" : 1, 
                    "name" : "Bugfix", # Don't include the "Task X -" it'll be added automatically
                    "time_to_complete": 3,
                    "unlocks_at_percent":0,
                    "number_of_people_required":3,
                    "energy_cost": 5,
                    "difficulty": 1
                }
            ]
        }, # You can have as many options as you like
        {
            "text" : "Sorry, no.",
            "score_effect": -1,
            "happiness_effect": 0.91,
            "reliability_effect" : 0.97,

            "relation_change" : 10
        }
    ]
}

# decisions type PROJECT - For affecting all characters' tasks
{
    "decision_type" : "PROJECT",
    "decision" : {
        "title" : "BIG PROJECT ISSUE!!!",
        "body" : "My Goodness."
    },
    "deadline" : 2,
    "related_name" : "decision_task_cool", # Used to identify a decision after its been made. Optional, but you'll need this if you want an option to unlock a decision
    "is_locked" : true, # Use this to make a decision locked until explicitly unlocked by an option using its related_name
    "requirements" : { # Requirements
        "task_available" : 5,
        "task_complete" : 2,
        "day_requirement" : 0
    },
    "options" : [
        {
            "text" : "Sure",
            "score_effect": 2, # The score is additive!
            "happiness_effect": 1.03, # These effects are multiplicative!
            "reliability_effect" : 1.05,
            "confidence_effect" : 0.8,
            "stress_effect" : 0.8,
            "irritability_effect" : 2.8,
            "skill_level_effect" : 0.1,
            "communication_skills_effect" : 0.01,
            "teachability_effect" : 0.11,
            "energy_effect" : 1.5,
            "set_rest" : true,
            "unassign_task" : true,
            "unlocking_decision" : "some_other_decision", # Allows you to unlock a decision with this option, uses related_name to identify the decision
            "unlocking_day_delay" : 3, # Optional, sets minimum day requirement to X days after this option is clicked. if omitted, decision just uses its default day minimum
            "leave_team": 1, # Choosing this option makes any SaveCharacter with this Character pk leave! Use sparingly...
            "create_tasks" : [ # an option can create tasks
                { # All fields in here are mandatory!
                    "task_type" : 1, 
                    "name" : "Bugfix", # Don't include the "Task X -" it'll be added automatically
                    "time_to_complete": 3,
                    "unlocks_at_percent":0,
                    "number_of_people_required":3,
                    "energy_cost": 5,
                    "difficulty": 1
                }
            ]
        }, # You can have as many options as you like
        {
            "text" : "Sorry, no.",
            "score_effect": -1,
            "happiness_effect": 0.91,
            "reliability_effect" : 0.97
        }
    ]
}