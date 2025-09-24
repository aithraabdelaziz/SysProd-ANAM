import logging
from django.shortcuts import render
from django.core.exceptions import PermissionDenied
logger = logging.getLogger(__name__)

class HandleViewErrorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, PermissionDenied):
            return None
        logger.error(f"Exception capturée dans la vue : {exception}", exc_info=True)
        return render(request, 'error.html', {'message': str(exception)}, status=500)
