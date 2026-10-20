"""Domain errors for sessions. The routers map these to status codes."""


class SessionNotFound(Exception):
    pass


class SessionHasNoLocation(Exception):
    pass


class SearchFailed(Exception):
    """The Places search errored out (network failure, bad key, quota)."""


class ResultsNotFound(Exception):
    """No cached results for the session: never searched, expired, or the server restarted."""


class PhotoNotFound(Exception):
    """The session's results, the place, or the place's photo is not available."""


class PhotoFetchFailed(Exception):
    """Fetching the image from Google failed (network, bad key, quota, expired name)."""
