"""Shared helpers for turning upstream Places failures into client-safe messages."""

import httpx

# Everything a Places call can raise: transport/HTTP errors, plus a payload we can't parse.
PLACES_ERRORS = (httpx.HTTPError, KeyError, ValueError)


def describe_error(exc: Exception) -> str:
    """One-line description of what went wrong, safe to show the client."""
    if isinstance(exc, httpx.HTTPStatusError):
        return f"Places returned HTTP {exc.response.status_code}"
    if isinstance(exc, httpx.TimeoutException):
        return "Places request timed out"
    if isinstance(exc, httpx.HTTPError):
        return f"Could not reach Places ({type(exc).__name__})"
    if isinstance(exc, KeyError):
        return f"Places response was missing field {exc}"
    return f"Places response was malformed ({type(exc).__name__}: {exc})"
