from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from django.utils.translation import gettext_lazy as _
from chartmet.models import MapObsConfiguration, MapFcstConfiguration, MapModelConfiguration, MapSpatialConfiguration


class MapObsConfigurationViewSet(SnippetViewSet):
    model = MapObsConfiguration
    menu_label = _("Carte-Observation")
    icon = "site"
    list_display = ['name','active']
    list_filter = ['name']
    add_to_admin_menu = False

class MapFcstConfigurationViewSet(SnippetViewSet):
    model = MapFcstConfiguration
    menu_label = _("Carte-Prévision")
    icon = "site"
    list_display = ['name','active']
    list_filter = ['name']
    add_to_admin_menu = False

class MapModelConfigurationViewSet(SnippetViewSet):
    model = MapModelConfiguration
    menu_label = _("Carte-Modèle")
    icon = "site"
    list_display = ['name','active']
    list_filter = ['name']
    add_to_admin_menu = False
    
class MapSpatialConfigurationViewSet(SnippetViewSet):
    model = MapSpatialConfiguration
    menu_label = _("Carte-Spatialisée")
    icon = "site"
    list_display = ['name','active']
    list_filter = ['name']
    add_to_admin_menu = False

class MapConfigGroup(SnippetViewSetGroup):
    items = (MapObsConfigurationViewSet, MapFcstConfigurationViewSet, MapModelConfigurationViewSet, MapSpatialConfigurationViewSet)
    menu_icon = 'view'
    menu_label = "Config-Maps"
    menu_name = "Config-Maps"
    add_to_admin_menu = False

# register_snippet(MapConfigGroup)