from django.urls import path
from . import views
from django.shortcuts import redirect

urlpatterns = [
    path('health', views.health_check, name='health'),
    path('app', views.dashboard_index, name='dashboard'),
    path('app/guild/<str:guild_id>', views.guild_detail, name='guild_detail'),
    path('app/guild/<str:guild_id>/toggle/<str:module_name>', views.toggle_module, name='toggle_module'),
    
    # Specific Module/Page routes
    path('app/guild/<str:guild_id>/overview', views.module_config, {'module_name': 'overview'}, name='guild_overview'),
    path('app/guild/<str:guild_id>/audit', views.module_config, {'module_name': 'audit'}, name='guild_audit'),
    path('app/guild/<str:guild_id>/test-configuration', views.module_config, {'module_name': 'test-configuration'}, name='guild_test_config'),
    
    # Generic Module route
    path('app/guild/<str:guild_id>/<str:module_name>', views.module_config, name='module_config'),
    
    path('', lambda r: redirect('dashboard'), name='root'),
]
