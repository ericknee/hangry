"""Domain errors for group sessions. The routers map these to status codes."""


class NotAGroupSession(Exception):
    """The session exists but was created as a solo session."""


class NotInLobby(Exception):
    """The host already started, so members can no longer join or edit."""


class GroupFull(Exception):
    pass


class NotAMember(Exception):
    """No member with that id in this session."""


class AlreadySubmitted(Exception):
    pass


class NotSwiping(Exception):
    """Votes and ending only make sense while the group is swiping."""


class NotHost(Exception):
    pass


class InvalidVotes(Exception):
    """The submitted votes don't match the deck (missing, extra or duplicate places)."""


class StartInProgress(Exception):
    """The host's search is already running, so a second start, join or edit must wait."""
