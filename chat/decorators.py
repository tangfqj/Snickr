from functools import wraps
from django.shortcuts import redirect


def login_required(view_func):
    """
    Redirect to login page if the user is not in the session.
    Usage: @login_required above any view function.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def workspace_member_required(view_func):
    """
    Redirect to workspace list if the user is not a member
    of the workspace specified in the URL kwargs.
    Usage: @workspace_member_required above any view that has
           workspace_id in its URL pattern.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from chat.queries import is_workspace_member
        if not request.session.get('user_id'):
            return redirect('login')
        workspace_id = kwargs.get('workspace_id')
        user_id = request.session['user_id']
        if not is_workspace_member(workspace_id, user_id):
            return redirect('workspace_list')
        return view_func(request, *args, **kwargs)
    return wrapper


def channel_member_required(view_func):
    """
    Redirect to workspace view if the user is not a member
    of the channel specified in the URL kwargs.
    Usage: @channel_member_required above any view that has
           channel_id in its URL pattern.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from chat.queries import is_channel_member
        if not request.session.get('user_id'):
            return redirect('login')
        channel_id = kwargs.get('channel_id')
        user_id = request.session['user_id']
        if not is_channel_member(channel_id, user_id):
            return redirect('workspace_list')
        return view_func(request, *args, **kwargs)
    return wrapper