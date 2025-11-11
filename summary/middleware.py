"""Custom middleware for summary service."""

import logging
import time
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware to log API requests and response times."""

    def process_request(self, request):
        """Log incoming request."""
        request.start_time = time.time()
        logger.info(
            f"Request: {request.method} {request.path}",
            extra={
                'method': request.method,
                'path': request.path,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
        )

    def process_response(self, request, response):
        """Log outgoing response with timing."""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            logger.info(
                f"Response: {request.method} {request.path} - "
                f"{response.status_code} ({duration:.2f}s)",
                extra={
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration': duration,
                }
            )
        return response


class ErrorHandlingMiddleware(MiddlewareMixin):
    """Middleware for consistent error handling."""

    def process_exception(self, request, exception):
        """Handle exceptions consistently."""
        logger.error(
            f"Exception in {request.method} {request.path}: {str(exception)}",
            exc_info=True,
            extra={
                'method': request.method,
                'path': request.path,
                'exception_type': type(exception).__name__,
            }
        )
        # Let Django's default exception handling continue
        return None
