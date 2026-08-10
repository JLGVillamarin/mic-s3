class ActaParserError(Exception):
    def __init__(self, message: str, details: list[str] | None = None):
        super().__init__(message)
        self.details = details or []


class ActaFormatError(ActaParserError):
    """Raised when the PDF structure is unrecognizable."""
    pass


class ActaExtractionError(ActaParserError):
    """Raised when specific fields cannot be extracted."""
    pass
