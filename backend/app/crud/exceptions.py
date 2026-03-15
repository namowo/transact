from fastapi import HTTPException, status


class CRUDOperationError(HTTPException):
    """Base exception for CRUD operations."""

    def __init__(
        self,
        status_code: status,
        message: str = "An error occurred during the CRUD operation",
    ):
        self.status_code = status_code
        self.message = message
        super().__init__(self.status_code, self.message)


class NotFoundError(CRUDOperationError):
    """Raised when a resource or group of resources is not found."""

    def __init__(
        self,
        status_code: status = status.HTTP_204_NO_CONTENT,
        message: str = "Reource not found.",
    ):
        super().__init__(status_code=status_code, message=message)


class AuthorizationError(CRUDOperationError):
    """Raised when a user is not authorized to perform an action."""

    def __init__(
        self,
        status_code: status = status.HTTP_401_UNAUTHORIZED,
        message: str = "User is not authorized to perform this action.",
    ):
        super().__init__(status_code, message=message)


class DatabaseCommitError(CRUDOperationError):
    """Raised when a database commit fails."""

    def __init__(
        self,
        status_code: status = status.HTTP_500_INTERNAL_SERVER_ERROR,
        message: str = "Database commit failed.",
    ):
        super().__init__(status_code, message=message)
