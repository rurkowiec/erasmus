from .models import Settings, User


def global_settings(request):
    """
    Context processor to add global settings and user info to all templates.
    """
    context = {}
    
    # Add global cost limit
    try:
        settings = Settings.get_settings()
        context['cost_limit'] = settings.global_cost_limit
    except Exception:
        context['cost_limit'] = 100.0  # Fallback default
    
    # Add user object if logged in
    user_id = request.session.get('user_id')
    if user_id:
        try:
            context['user'] = User.objects.get(id=user_id)
        except User.DoesNotExist:
            context['user'] = None
    else:
        context['user'] = None
    
    return context
