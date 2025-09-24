from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views.forecast import ForecastViewSet, ForecastFiltersViewSet
from api.views.observation import ObservationViewSet, ObservationFiltersViewSet
from api.views.bulletins import BulletinTemplateViewSet, BulletinFiltersViewSet,BulletinTemplateMetadataViewSet
from api.views.cap import CAPViewSet
from api.views.vigilance import VigilanceViewSet
from rest_framework.authtoken.views import obtain_auth_token
app_name = 'api'
router = DefaultRouter()

router.register(r'forecasts', ForecastFiltersViewSet, basename='forecast_filter')
router.register(r'forecasts', ForecastViewSet, basename='forecast_data')

router.register(r'observations', ObservationFiltersViewSet, basename='observation_filter')
router.register(r'observations', ObservationViewSet, basename='observation_data')

router.register(r'bulletins', BulletinTemplateViewSet, basename='bulletin_filter')
router.register(r'bulletins', BulletinFiltersViewSet, basename='bulletin')
#router.register(r'bulletin-template/metadata', BulletinTemplateMetadataViewSet, basename='bulletintemplate-metadata')

router.register(r'cap', CAPViewSet, basename='cap')
router.register(r'vigilance', VigilanceViewSet, basename='vigilance')


urlpatterns = [
    path('token/', obtain_auth_token),  # POST avec username/password → token
    path('', include(router.urls)),
]


from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    # Schéma brut (OpenAPI JSON)
    path("schema/", SpectacularAPIView.as_view(), name="schema"),

    # Interface Swagger
    path("docs/", SpectacularSwaggerView.as_view(url_name="api:schema"), name="swagger-ui"),
]
