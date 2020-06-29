from ekklesia_common.app import EkklesiaBrowserApp
from ekklesia_common.identity_policy import NoIdentity


class WritePermission:
    pass


class CreatePermission(WritePermission):
    pass


class EditPermission(WritePermission):
    pass


class ViewPermission:
    pass


@EkklesiaBrowserApp.permission_rule(model=object, permission=WritePermission, identity=NoIdentity)
def has_write_permission_not_logged_in(identity, model, permission):
    """Protects all views with write actions from users that aren't logged in."""
    return False
