from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from wagtail.admin.menu import MenuItem, SubmenuMenuItem
from wagtail import hooks
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from wagtail.admin.filters import DateRangePickerWidget

from .models import Variable, Zone, Forecast


#### Définition des ViewSets pour chaque snippet

class VariableViewSet(SnippetViewSet):
    model = Variable
    menu_label = _("Variables météo")
    icon = "cog"
    list_display = ['name', 'shortName', 'active', 'unit', 'category']
    list_filter = ['active', 'category']
    search_fields = ['name', 'shortName', 'category']  # Ajoutez 'category'
    ordering = ['name']  # Ajoutez un ordre par défaut
    add_to_admin_menu = False
    
    # Forcer l'utilisation de l'autocomplétion
    autocomplete_fields = ['name']

class ZoneViewSet(SnippetViewSet):
    model = Zone
    menu_label = _("Zones géographiques")
    icon = "site"
    list_display = ['name', 'category', 'active']
    list_filter = ('category', 'active')
    search_fields = ['name','category']
    ordering = ['name']
    add_to_admin_menu = False
    autocomplete_fields = ['name']



class ForecastViewSet(SnippetViewSet):
    model = Forecast
    menu_label = _("Prévisions")
    icon = "date"
    list_display = ['zone', 'date', 'echeance', 'parametre', 'prevision']
    list_filter = ['zone', 'parametre', 'echeance']
    search_fields = ['prevision', 'zone__name', 'parametre__name']
    add_to_admin_menu = False

    def formatted_date(self, obj):
        return obj.date.strftime('%d/%m/%Y')
    formatted_date.short_description = _("Date")
    formatted_date.admin_order_field = 'date'

    def prevision_preview(self, obj):
        return obj.prevision[:100] + "..." if len(obj.prevision) > 100 else obj.prevision
    prevision_preview.short_description = _("Aperçu prévision")

class FcsConfigGroup(SnippetViewSetGroup):
    items = (VariableViewSet, ZoneViewSet, ForecastViewSet)
    menu_icon = 'crosshairs'
    menu_label = "Previ-Conf"
    menu_name = "Previ-Conf"
    add_to_admin_menu = False

# register_snippet(FcsConfigGroup)
