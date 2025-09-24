from functools import wraps
from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)

def handle_view_errors(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Erreur dans la vue {view_func.__name__} : {e}")
            return render(request, 'error.html', {'message': str(e)}, status=500)
    return _wrapped_view