class LaudoError(Exception):
    """User-facing error: the message is meant to be shown without a traceback."""


class ImageNotFoundError(LaudoError, LookupError):
    pass


class TemplateNotFoundError(LaudoError, FileNotFoundError):
    pass
