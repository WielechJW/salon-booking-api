class DomainError(Exception):
    """Base error raised by the domain layer."""


class DomainNotFoundError(DomainError):
    """A required domain entity does not exist."""


class DomainConflictError(DomainError):
    """A business rule prevents the requested operation."""


class DomainValidationError(DomainError):
    """Input passed directly to a domain service is invalid."""
