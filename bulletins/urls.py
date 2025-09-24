from django.urls import path
from django.views.generic import TemplateView

from .views import * #bulletin_list ,BulletinListView , BulletinDetailView
from .editions_views import *
app_name = 'bulletins'


urlpatterns = [
path('generate/<int:pk>/', generate_bulletin, name='generate_bulletin'),   
path("mgnt/", BulletinListView.as_view(), name="gestion_bulletins"),
path("list/", bulletin_list, name="bulletin_list"),
# path("display/<int:pk>/", display_bulletin, name="display_bulletin"),
path("display", display_bulletin, name="display_bulletin"),
path("detail/<int:pk>/", BulletinDetailView.as_view(), name="bulletin_detail"),
path("add", add_bulletin, name="add_bulletin"),
path("desactivate/<int:pk>/", bulletin_deactivate, name="bulletin_deactivate"),
path("delete/<int:pk>/", bulletin_delete, name="bulletin_delete"),
path("update/<int:pk>/", bulletin_update, name="bulletin_update"),
] 


urlpatterns += [
    path('edition/select/', select_bulletins, name='select_bulletins'),
    path('edition/<int:pk>/zones/<str:date_bult>/', editBulletin, name='editBulletin'),
    path('edition/<int:pk>/obs/<str:date_bult>/', save_observation, name='save_observation'),
    path('edition/<int:pk>/obsT/<str:date_bult>/', save_obsTable, name='save_obsTable'),
    path('edition/<int:pk>/fcst/<str:date_bult>/', save_forecast, name='save_forecast'),
    path('edition/<int:pk>/fcstT/<str:date_bult>/', save_fcstTable, name='save_fcstTable'),
]

