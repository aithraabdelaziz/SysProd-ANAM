from django.urls import path

from .views import stations
app_name = 'observation'


urlpatterns = [
    path('station/', stations.StationListView.as_view(), name='station_list'),
    path('station/create/', stations.StationCreateView.as_view(), name='station_create'),
    path('station/<int:pk>/update/', stations.StationUpdateView.as_view(), name='station_update'),
    path('station/<int:pk>/delete/', stations.StationDeleteView.as_view(), name='station_delete'),
    path('station/<int:pk>/deactivate/', stations.StationDeactivateView.as_view(), name='station_deactivate'),
    path('stat_shapefile/', stations.shapefile_station_view, name='shapefile_station_view'),
    path('save_station/', stations.save_station, name='save_station'),
    path('select_station/', stations.SelectStationsView.as_view(), name='select_stations'),

]

from .views import editions
urlpatterns += [
    path('edition/', editions.index, name='edition_index'),
    path('edition/select/', editions.select_localite, name='select_localite'),
    path('edition/<int:localite_id>/stations/', editions.select_station, name='select_station'),
    path('edition/<int:localite_id>/stations/<int:zone_id>/date/', editions.select_date, name='select_date'),
    path('edition/stations/', editions.edit_observation, name='edit_observations'),

]

###############################################################
from .views import climat
urlpatterns += [
    path('climat/decade/csv-import/', climat.csv_import_view, name='csv_import'),
    path('climat/month/csv-import/', climat.csv_import_climatmois_view, name='csv_import_climatmois_view'),
    path('climat/month/grib-import/', climat.grib_import_view, name='grib_import_view'),
    path('climat/month/nc-import/', climat.netcdf_import_view, name='netcdf_import_view'),
]
