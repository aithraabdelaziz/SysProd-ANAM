from .wagtail_hooks import api_router

urlpatterns = [
    # autres urls
    path('api/v2/', api_router.urls),
]