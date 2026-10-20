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
