from django.conf import settings
from django.urls import include, path
from django.contrib import admin

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

from django.contrib.auth import views as auth_views

from search import views as search_views
import home.views

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("search/", search_views.search, name="search"),
    path("", include('home.urls')),
    path("forecast/", include('forecast.urls')),
    path("obs/", include('observation.urls')),
    # path("users/", include('users_manager.urls')),
    path("bulletins/", include('bulletins.urls')), 
    path("chartmet/", include('chartmet.urls')), 

    path("vigilance/", include('vigilance.urls')), 

    path("dissiminate/", include('dissiminate.urls')), 


    path('api/', include('api.urls')),
]

urlpatterns += [
    path('select2/', include('django_select2.urls')),

]

from django.conf.urls import handler403
from django.shortcuts import render

def custom_permission_denied_view(request, exception):
    return render(request, '403.html', {'message': str(exception)}, status=403)

handler403 = custom_permission_denied_view

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns = urlpatterns + [
    # Authentification
    path('login/', auth_views.LoginView.as_view(
        template_name='account/login.html',
        redirect_authenticated_user=True  # Redirige si déjà connecté
    ), name='login'),
    
    path('logout/', auth_views.LogoutView.as_view(
        template_name='account/logout.html'  # Optionnel
    ), name='logout'),
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:
    path("", include(wagtail_urls)),
    # Alternatively, if you want Wagtail pages to be served from a subpath
    # of your site, rather than the site root:
    #    path("pages/", include(wagtail_urls)),
]
