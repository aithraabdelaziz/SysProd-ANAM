from django.urls import path
from .views import zones,forecasts

from .views.variables import *
app_name = 'forecast'
urlpatterns = [
    path('manage_variables/', manage_variables, name='manage_variables'),
    path('add_variable/', add_variable, name='add_variable'),
    path('activate_variable/<int:variable_id>/', activate_variable, name='activate_variable'),
    path('deactivate_variable/<int:variable_id>/', deactivate_variable, name='deactivate_variable'),
    path('delete_variable/<int:variable_id>/', delete_variable, name='delete_variable'),
    path('edit_variable/<int:variable_id>/', edit_variable, name='edit_variable'),

    path('georaphic_area/', zones.ZoneListView.as_view(), name='georaphic_area_list'),
    path('georaphic_area/create/', zones.ZoneCreateView.as_view(), name='georaphic_area_create'),
    path('georaphic_area/<int:pk>/update/', zones.ZoneUpdateView.as_view(), name='georaphic_area_update'),
    path('georaphic_area/<int:pk>/delete/', zones.ZoneDeleteView.as_view(), name='georaphic_area_delete'),
    path('georaphic_area/<int:pk>/deactivate/', zones.ZoneDeactivateView.as_view(), name='georaphic_area_deactivate'),
    #path('upload_shapefile/', UploadShapefileView.as_view(), name='upload_shapefile'),
    #path('uploadShapefile/', uploadShapefile, name='uploadShapefile'),
    #path('config_shapefile/',TemplateView.as_view(template_name='config_shapefile.html')),
    path('shapefile/', zones.shapefile_view, name='shapefile_view'),
    path('save_geographic_area/', zones.save_geographic_area, name='save_geographic_area'),
    path('select_geographic_area/', zones.SelectZonesView.as_view(), name='select_geographic_area'),
    path('merge_geographic_areas/', zones.MergeZonesView.as_view(), name='merge_geographic_areas'),
    path('save_merged_georaphic_area/', zones.SaveMergedZoneView.as_view(), name='save_merged_georaphic_area'),

]

urlpatterns += [
    path('', forecasts.ForecastListView.as_view(), name='forecast_list'),
    path('ajouter/', forecasts.ForecastCreateView.as_view(), name='forecast_create'),
    path('<int:pk>/modifier/', forecasts.ForecastUpdateView.as_view(), name='forecast_update'),
    path('<int:pk>/supprimer/', forecasts.ForecastDeleteView.as_view(), name='forecast_delete'),
]

from django.urls import path
from .views import editions

urlpatterns += [
    path('edition/', editions.index, name='edition_index'),
    path('edition/select/', editions.select_localites, name='select_localites'),
    path('edition/<int:localite_id>/zones/', editions.select_zone, name='select_zone'),
    path('edition/<int:localite_id>/zone/<int:zone_id>/date/', editions.select_date, name='select_date'),
    # path('edition/<int:bulletin_id>/zone/<int:zone_id>/date/<str:date_str>/', editions.edit_forecasts, name='edit_forecasts'),
    path('edition/zone/', editions.edit_forecasts, name='edit_forecasts'),


    path('edition/bul/select/', editions.select_bulletins, name='select_bulletins'),
    path('edition/bul/<int:bulletin_id>/zones/', editions.select_zonebulletin, name='select_zonebulletin'),


]
