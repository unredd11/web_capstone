from .models import AuditLog


def record_audit_event(
    request,
    action_type,
    target_entity,
    target_id=None,
    user=None,
):
    actor = user
    if actor is None and request.user.is_authenticated:
        actor = request.user

    return AuditLog.objects.create(
        user=actor,
        action_type=action_type,
        target_entity=target_entity,
        target_id=target_id,
        ip_address=request.META.get('REMOTE_ADDR'),
        device_info=request.META.get(
            'HTTP_USER_AGENT',
            '',
        )[:255],
    )
