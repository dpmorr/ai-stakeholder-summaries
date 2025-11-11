"""Custom exceptions for summary service."""


class SummaryServiceException(Exception):
    """Base exception for summary service."""
    pass


class DocumentNotFoundException(SummaryServiceException):
    """Raised when a document is not found."""
    pass


class SummaryGenerationException(SummaryServiceException):
    """Raised when summary generation fails."""
    pass


class InvalidDocumentException(SummaryServiceException):
    """Raised when document data is invalid."""
    pass


class TokenLimitExceededException(SummaryServiceException):
    """Raised when token limit is exceeded."""
    pass


class InvalidStakeholderRoleException(SummaryServiceException):
    """Raised when stakeholder role is invalid."""
    pass


class ModelUnavailableException(SummaryServiceException):
    """Raised when LLM model is unavailable."""
    pass


class InsufficientDataException(SummaryServiceException):
    """Raised when there's insufficient data to generate summary."""
    pass
