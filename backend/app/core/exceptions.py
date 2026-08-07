class ApplicationError(Exception):
    status_code = 400
    code = "application_error"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class AuthenticationError(ApplicationError):
    status_code = 401
    code = "authentication_failed"


class AuthorizationError(ApplicationError):
    status_code = 403
    code = "authorization_failed"


class ConflictError(ApplicationError):
    status_code = 409
    code = "resource_conflict"


class NotFoundError(ApplicationError):
    status_code = 404
    code = "resource_not_found"

