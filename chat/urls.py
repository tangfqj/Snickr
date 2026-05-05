from django.urls import path
from chat import views

urlpatterns = [
    # ----------------------------------------------------------
    # AUTH
    # ----------------------------------------------------------
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # ----------------------------------------------------------
    # PROFILE
    # ----------------------------------------------------------
    path('profile/', views.profile_view, name='profile'),

    # ----------------------------------------------------------
    # INVITATIONS INBOX
    # ----------------------------------------------------------
    path('invitations/', views.invitations_view, name='invitations'),
    path('invitations/workspace/<int:workspace_id>/accept/',
         views.accept_workspace_invite_view, name='accept_workspace_invite'),
    path('invitations/channel/<int:channel_id>/accept/',
         views.accept_channel_invite_view, name='accept_channel_invite'),

    # ----------------------------------------------------------
    # WORKSPACES
    # ----------------------------------------------------------
    path('workspaces/', views.workspace_list_view, name='workspace_list'),
    path('workspaces/<int:workspace_id>/',
         views.workspace_view, name='workspace'),
    path('workspaces/<int:workspace_id>/invite/',
         views.invite_to_workspace_view, name='invite_to_workspace'),
    path('workspaces/<int:workspace_id>/promote/<int:target_user_id>/',
         views.promote_admin_view, name='promote_admin'),
    path('workspaces/<int:workspace_id>/direct/<int:target_user_id>/',
         views.create_direct_channel_view, name='create_direct'),
    # ----------------------------------------------------------
    # CHANNELS
    # ----------------------------------------------------------
    path('workspaces/<int:workspace_id>/channels/<int:channel_id>/',
         views.channel_view, name='channel'),
    path('workspaces/<int:workspace_id>/channels/<int:channel_id>/join/',
         views.join_channel_view, name='join_channel'),
    path('workspaces/<int:workspace_id>/channels/<int:channel_id>/invite/',
         views.invite_to_channel_view, name='invite_to_channel'),

    # ----------------------------------------------------------
    # SEARCH
    # ----------------------------------------------------------
    path('search/', views.search_view, name='search'),
]