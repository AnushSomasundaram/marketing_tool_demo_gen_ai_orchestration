"""Typed exceptions for external-provider and storage failures.

Routers translate these into safe HTTP responses (see `to_http_exception`)
that never leak API keys, tokens, raw provider payloads, or stack traces.
"""

from fastapi import HTTPException


class ProviderError(Exception):
    def __init__(self, message: str, *, provider: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.provider = provider


class ProviderNotConfiguredError(ProviderError):
    """Raised when a real provider is selected but required credentials are missing."""


class ProviderAuthenticationError(ProviderError):
    """Raised when a provider rejects our credentials."""


class ProviderRateLimitError(ProviderError):
    """Raised when a provider throttles us."""


class ProviderSafetyError(ProviderError):
    """Raised when a provider refuses a request on content-safety grounds."""


class ProviderTimeoutError(ProviderError):
    """Raised when a provider call exceeds its configured timeout."""


class ProviderTaskFailedError(ProviderError):
    """Raised when an asynchronous provider task (e.g. Runway) reports failure."""


class StorageError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class StaleVersionError(Exception):
    """Raised when an action targets a caption/asset version that has already
    been superseded — spawning a new version from a stale one would create two
    sibling versions both claiming to be current."""

    def __init__(self, message: str = "This version is no longer current. Refresh and try again.") -> None:
        super().__init__(message)
        self.message = message


class PublishError(Exception):
    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def to_http_exception(exc: Exception) -> HTTPException:
    """Map an internal exception to a safe HTTPException for API responses."""
    match exc:
        case ProviderNotConfiguredError():
            return HTTPException(status_code=503, detail=f"{exc.provider or 'Provider'} is not configured.")
        case ProviderAuthenticationError():
            return HTTPException(status_code=502, detail="Upstream provider rejected our credentials.")
        case ProviderRateLimitError():
            return HTTPException(status_code=502, detail="Upstream provider rate limit exceeded.")
        case ProviderSafetyError():
            return HTTPException(
                status_code=502, detail="Upstream provider declined the request on safety grounds."
            )
        case ProviderTimeoutError():
            return HTTPException(status_code=502, detail="Upstream provider request timed out.")
        case ProviderTaskFailedError():
            return HTTPException(status_code=502, detail=f"Generation task failed: {exc.message}")
        case StorageError():
            return HTTPException(status_code=502, detail="Storage operation failed.")
        case PublishError():
            return HTTPException(status_code=502, detail=exc.message)
        case StaleVersionError():
            return HTTPException(status_code=409, detail=exc.message)
        case _:
            return HTTPException(status_code=500, detail="Internal server error.")
