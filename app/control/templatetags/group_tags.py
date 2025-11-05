from django import template

register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name):
    """Return True if the user belongs to the given group name.

    Safe to call with AnonymousUser.
    Usage in template: {% if user|has_group:"administracion" %}
    """
    try:
        if not user or not user.is_authenticated:
            return False
        return user.groups.filter(name=group_name).exists()
    except Exception:
        return False
