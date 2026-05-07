
from django.contrib import admin
from django.urls import path

from projectManagerSim import views
from projectManagerSim.views import AdminDashboardView, AdminSaveListView, AdminSettingsView, complete_tour

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('sign_up/', views.SignUpView.as_view(), name='sign_up'),
    path('log_in/', views.LogInView.as_view(), name='log_in'),
    path('log_out/', views.log_out, name='log_out'),

    ###### ADMIN URLS ######
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin/statistics/', views.AdminStatisticsView.as_view(), name='admin_statistics'),
    path('admin/saves/', AdminSaveListView.as_view(), name='admin_save_list'),
    path('admin/settings/', AdminSettingsView.as_view(), name='admin_settings'),
    path('admin/game_content/characters', views.CharacterListView.as_view(), name='character_list'),
    path('admin/game_content/task_types', views.TaskTypeListView.as_view(), name='task_type_list'),
    path('admin/', admin.site.urls),

    ###### USER URLS ######
    path('dashboard/', views.UserDashboardView.as_view(), name='user_dashboard'),
    path('settings/', views.UserSettingsView.as_view(), name='user_settings'),

    ###### GAME URLS ######
    path('game/start/', views.game_start, name='game_start'), 
    path('game/character-selection/', views.character_selection_view, name='game_start_new'),
    path('game/dashboard/', views.GameDashboardView.as_view(), name='game_dashboard'),
    path('game/tasks/', views.GameTaskListView.as_view(), name='game_tasks'),
    path('game/teammates/', views.GameCharacterListView.as_view(), name='game_characters'),
    path('game/statistics/', views.GameStatisticsView.as_view(), name='game_statistics'),
    path('game/results', views.GameEndView.as_view(), name='game_end'),
    
    
    path('decisions/get_decision/', views.get_decision, name='get_decision'),
    path('decisions/process_decision/', views.process_decision, name='process_decision'),

    path('assign_task/', views.AssignTaskView.as_view(), name='assign_task'),
    path('get_task/', views.GetLatestTaskView.as_view(), name='get_task'),
    path('remove_task/', views.RemoveTaskView.as_view(), name='remove_task'),
    path('toggle_resting/', views.ToggleRestingView.as_view(), name='toggle_resting'),
    path('start_day/', views.StartDayView.as_view(), name='start_day'),
    path('save_precheck/<int:save_id>/', views.SavePrecheckView.as_view(), name='save_precheck'),

    path('character-selection/', views.character_selection_view, name='character_selection'),
    path('game/relationships/<int:save_id>/', views.relationships_view, name='relationships'),

    path('api/preview-chemistry/', views.preview_team_chemistry, name='preview_chemistry'),

    path('game/statistics/', views.GameStatisticsView.as_view(), name='game_statistics'),
    path('tour/complete/', complete_tour, name='complete_tour'),

    path('game/previous-saves/', views.PreviousSavesView.as_view(), name='previous_saves'),

]
