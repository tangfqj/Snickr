from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import IntegrityError

from chat import queries
from chat.forms import (
    LoginForm, RegisterForm, WorkspaceForm, ChannelForm,
    MessageForm, InviteUserForm, SearchForm
)
from chat.decorators import (
    login_required, workspace_member_required, channel_member_required
)


# =============================================================
# AUTH
# =============================================================

def login_view(request):
    if request.session.get('user_id'):
        return redirect('workspace_list')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = queries.get_user_by_username(form.cleaned_data['username'])
        if user and queries.check_password(user, form.cleaned_data['password']):
            request.session['user_id'] = user['user_id']
            request.session['username'] = user['username']
            return redirect('workspace_list')
        form.add_error(None, 'Invalid username or password.')
    return render(request, 'chat/login.html', {'form': form})


def logout_view(request):
    request.session.flush()
    return redirect('login')


def register_view(request):
    if request.session.get('user_id'):
        return redirect('workspace_list')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        try:
            user_id = queries.create_user(
                d['email'], d['username'], d['nickname'], d['password']
            )
            request.session['user_id'] = user_id
            request.session['username'] = d['username']
            return redirect('workspace_list')
        except IntegrityError:
            form.add_error(None, 'Email or username already taken.')
    return render(request, 'chat/register.html', {'form': form})


# =============================================================
# WORKSPACES
# =============================================================

@login_required
def workspace_list_view(request):
    user_id = request.session['user_id']
    workspaces = queries.get_workspaces_for_user(user_id)
    form = WorkspaceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        workspace_id = queries.create_workspace(d['name'], d['description'], user_id)
        return redirect('workspace', workspace_id=workspace_id)
    return render(request, 'chat/workspace_list.html', {
        'workspaces': workspaces,
        'form': form,
    })


@workspace_member_required
def workspace_view(request, workspace_id):
    user_id = request.session['user_id']
    workspace = queries.get_workspace(workspace_id)
    channels = queries.get_channels_for_user(workspace_id, user_id)
    public_channels = queries.get_public_channels_for_workspace(workspace_id)
    members = queries.get_workspace_members(workspace_id)
    is_admin = queries.is_workspace_admin(workspace_id, user_id)
    stale = queries.get_stale_pending_invites(workspace_id)

    # split channels by type for sidebar
    my_public   = [c for c in channels if c['type'] == 'public']
    my_private  = [c for c in channels if c['type'] == 'private']
    my_direct = queries.get_direct_channels_for_user(workspace_id, user_id)

    # public channels the user hasn't joined yet
    joined_ids = {c['channel_id'] for c in channels}
    joinable = [c for c in public_channels if c['channel_id'] not in joined_ids]

    channel_form = ChannelForm(request.POST or None)
    invite_form  = InviteUserForm()
    search_form  = SearchForm()

    if request.method == 'POST' and 'create_channel' in request.POST:
        if channel_form.is_valid():
            d = channel_form.cleaned_data
            try:
                channel_id = queries.create_channel(
                    workspace_id, d['name'], d['channel_type'], user_id
                )
                return redirect('channel', workspace_id=workspace_id, channel_id=channel_id)
            except IntegrityError:
                channel_form.add_error('name', 'A channel with that name already exists.')

    return render(request, 'chat/workspace.html', {
        'workspace':     workspace,
        'my_public':     my_public,
        'my_private':    my_private,
        'my_direct':     my_direct,
        'joinable':      joinable,
        'members':       members,
        'is_admin':      is_admin,
        'stale':         stale,
        'channel_form':  channel_form,
        'invite_form':   invite_form,
        'search_form':   search_form,
        'workspace_id':  workspace_id,
    })


@login_required
def join_channel_view(request, workspace_id, channel_id):
    user_id = request.session['user_id']
    if request.method == 'POST':
        queries.join_public_channel(channel_id, user_id)
    return redirect('channel', workspace_id=workspace_id, channel_id=channel_id)


@workspace_member_required
def create_direct_channel_view(request, workspace_id, target_user_id):
    if request.method == 'POST':
        user_id = request.session['user_id']
        if user_id == target_user_id:
            return redirect('workspace', workspace_id=workspace_id)
        channel_id = queries.create_direct_channel(
            workspace_id, user_id, target_user_id
        )
        return redirect('channel', workspace_id=workspace_id, channel_id=channel_id)
    return redirect('workspace', workspace_id=workspace_id)
# =============================================================
# WORKSPACE ADMIN ACTIONS
# =============================================================

@workspace_member_required
def invite_to_workspace_view(request, workspace_id):
    user_id = request.session['user_id']
    if not queries.is_workspace_admin(workspace_id, user_id):
        return redirect('workspace', workspace_id=workspace_id)
    if request.method == 'POST':
        form = InviteUserForm(request.POST)
        if form.is_valid():
            target = queries.find_user_by_username(form.cleaned_data['username'])
            if target:
                queries.invite_to_workspace(workspace_id, target['user_id'], user_id)
            else:
                messages.error(request, 'User not found.')
    return redirect('workspace', workspace_id=workspace_id)


@workspace_member_required
def promote_admin_view(request, workspace_id, target_user_id):
    user_id = request.session['user_id']
    if request.method == 'POST' and queries.is_workspace_admin(workspace_id, user_id):
        queries.promote_to_admin(workspace_id, target_user_id)
    return redirect('workspace', workspace_id=workspace_id)


# =============================================================
# CHANNEL / MESSAGES
# =============================================================

@channel_member_required
def channel_view(request, workspace_id, channel_id):
    user_id  = request.session['user_id']
    workspace = queries.get_workspace(workspace_id)
    channel   = queries.get_channel(channel_id)
    msgs      = queries.get_messages(channel_id)
    channels  = queries.get_channels_for_user(workspace_id, user_id)
    is_admin  = queries.is_workspace_admin(workspace_id, user_id)

    my_public  = [c for c in channels if c['type'] == 'public']
    my_private = [c for c in channels if c['type'] == 'private']
    my_direct = queries.get_direct_channels_for_user(workspace_id, user_id)

    msg_form    = MessageForm(request.POST or None)
    invite_form = InviteUserForm()
    search_form = SearchForm()

    if request.method == 'POST' and 'send_message' in request.POST:
        if msg_form.is_valid() and msg_form.cleaned_data['body'].strip():
            queries.post_message(channel_id, user_id, msg_form.cleaned_data['body'].strip())
            return redirect('channel', workspace_id=workspace_id, channel_id=channel_id)

    return render(request, 'chat/channel.html', {
        'workspace':    workspace,
        'channel':      channel,
        'chat_messages':     msgs,
        'my_public':    my_public,
        'my_private':   my_private,
        'my_direct':    my_direct,
        'is_admin':     is_admin,
        'msg_form':     msg_form,
        'invite_form':  invite_form,
        'search_form':  search_form,
        'workspace_id': workspace_id,
        'channel_id':   channel_id,
    })


@workspace_member_required
def invite_to_channel_view(request, workspace_id, channel_id):
    user_id = request.session['user_id']
    if request.method == 'POST':
        form = InviteUserForm(request.POST)
        if form.is_valid():
            target = queries.find_user_by_username(form.cleaned_data['username'])
            if target:
                queries.invite_to_channel(channel_id, target['user_id'], user_id)
            else:
                messages.error(request, 'User not found.')
    return redirect('channel', workspace_id=workspace_id, channel_id=channel_id)


# =============================================================
# INVITATIONS INBOX
# =============================================================

@login_required
def invitations_view(request):
    user_id = request.session['user_id']
    workspace_invites = queries.get_pending_workspace_invites(user_id)
    channel_invites   = queries.get_pending_channel_invites(user_id)
    return render(request, 'chat/invitations.html', {
        'workspace_invites': workspace_invites,
        'channel_invites':   channel_invites,
    })


@login_required
def accept_workspace_invite_view(request, workspace_id):
    if request.method == 'POST':
        queries.accept_workspace_invite(workspace_id, request.session['user_id'])
    return redirect('invitations')


@login_required
def accept_channel_invite_view(request, channel_id):
    if request.method == 'POST':
        queries.accept_channel_invite(channel_id, request.session['user_id'])
    return redirect('invitations')


# =============================================================
# SEARCH
# =============================================================

@login_required
def search_view(request):
    user_id = request.session['user_id']
    keyword = request.GET.get('keyword', '').strip()
    results = queries.search_messages(user_id, keyword) if keyword else []
    search_form = SearchForm(initial={'keyword': keyword})

    # need workspaces for the sidebar back-link
    workspaces = queries.get_workspaces_for_user(user_id)
    return render(request, 'chat/search_results.html', {
        'keyword':     keyword,
        'results':     results,
        'search_form': search_form,
        'workspaces':  workspaces,
    })


# =============================================================
# PROFILE
# =============================================================

@login_required
def profile_view(request):
    user_id = request.session['user_id']
    user = queries.get_user_by_id(user_id)
    my_messages = queries.get_messages_by_user(user_id)
    return render(request, 'chat/profile.html', {
        'user':        user,
        'my_messages': my_messages,
    })