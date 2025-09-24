from django.urls import path
from django.views.generic import TemplateView

from .views import * 
from .legend import * 
app_name = 'chartmet'

urlpatterns = [
    path('fcst', index, name='index'),
	path('fcst/map', generate_map, name='generate_map'), 
    path('fcst/sensitive_map/', sensitive_map_form, name='sensitive_map'),
    path('fcst/sensitive_map/show/', sensitive_map_show, name='sensitive_map_show'), 
    path('obs', obs_index, name='obs_index'),
	path('obs/map', generate_obsmap, name='generate_obsmap'),  
	path('obs/sensitive_map/', sensitive_obsmap_form, name='sensitive_obsmap'),
    path('obs/sensitive_map/show/', sensitive_obsmap_show, name='sensitive_obsmap_show'), 

    path('model/map', generate_modelmap, name='generate_modelmap'),  
	path('model/model_map/', model_map_form, name='model_map'),
    # path('model/model_map/show/', sensitive_obsmap_show, name='sensitive_obsmap_show'), 

    path('points/form/',extrapolated_map_form,name='extrapolated_map_form'),
    path('points/points_map/', points_map, name='points_map'),

    path('model/model_map2/', extrapolated_mapPreconfigured_form, name='extrapolated_mapPreconfigured_form'),
    path('points/points_map2/',points_map_preconfigured,name='points_map_preconfigured'),

    path('manage_legends/', manage_legends, name='manage_legends'),
    path('add_legend/', add_legend, name='add_legend'),
    path('activate_legend/<int:legend_id>/', activate_legend, name='activate_legend'),
    path('deactivate_legend/<int:legend_id>/', deactivate_legend, name='deactivate_legend'),
    path('delete_legend/<int:legend_id>/', delete_legend, name='delete_legend'),
    path('edit_legend/<int:legend_id>/', edit_legend, name='edit_legend'),

] 

from .climat_view import *
urlpatterns += [
    path('clim/', index_climat, name='index_climat'),
    path('clim/import', imports, name='imports'),
    path('clim/maps', list_cartes, name='list_cartes'),
    path('clim/month', month_map_form, name='month_map_form'),
    path('clim/month/map', generate_monthly_clim_map, name='generate_monthly_clim_map'),
    path('clim/decade', decade_map_form, name='decade_map_form'),
    path('clim/decade/map', generate_decade_clim_map, name='generate_decade_clim_map'),
    
]