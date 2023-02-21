class Permission:
    pass


class WritePermission(Permission):
    pass


class CreatePermission(WritePermission):
    pass


class EditPermission(WritePermission):
    pass


class DeletePermission(WritePermission):
    pass


class ViewPermission(Permission):
    pass
