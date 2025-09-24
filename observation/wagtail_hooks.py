from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from wagtail.admin.menu import MenuItem, SubmenuMenuItem
from wagtail import hooks
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from wagtail.admin.filters import DateRangePickerWidget

from .models import Station, Observation, ClimatDecades, CSVImportForm, ClimatMois
from forecast.models import Variable
from django import forms
from wagtail.admin.forms.models import WagtailAdminModelForm

class StationAdminForm(WagtailAdminModelForm):
    latitude = forms.FloatField(required=False)
    longitude = forms.FloatField(required=False)

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        initial = kwargs.setdefault('initial', {})
        if instance and instance.geom:
            initial['latitude'] = instance.geom.y
            initial['longitude'] = instance.geom.x
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        lat = self.cleaned_data.get('latitude')
        lon = self.cleaned_data.get('longitude')
        if lat is not None and lon is not None:
            instance.geom = Point(lon, lat)
        if commit:
            instance.save()
        return instance

class StationViewSet(SnippetViewSet):
    model = Station
    form_class = StationAdminForm
    menu_label = _("Stations météo")
    icon = "placeholder"
    list_display = ['name', 'wigos_id', 'active']
    list_filter = ['active']
    search_fields = ['name', 'wigos_id']
    add_to_admin_menu = False

class ObservationViewSet(SnippetViewSet):
    model = Observation
    menu_label = _("Observations")
    icon = "view"
    list_display = ['station', 'date', 'heure', 'parametre', 'observation']
    list_filter = ['station__name','station__wigos_id', 'parametre', 'heure']
    search_fields = ['observations', 'station__name','station__wigos_id', 'parametre__name']
    add_to_admin_menu = False

    def formatted_date(self, obj):
        return obj.date.strftime('%d/%m/%Y')
    formatted_date.short_description = _("Date")
    formatted_date.admin_order_field = 'date'

    def observations_preview(self, obj):
        return obj.observations[:100] + "..." if len(obj.observations) > 100 else obj.observations
    observations_preview.short_description = _("Aperçu observation")


class ClimatDecadesViewSet(SnippetViewSet):
    model = ClimatDecades
    icon = "date"  # Choisis une icône Wagtail
    add_to_admin_menu = False
    menu_label = "Décades climat"
    menu_order = 200
    list_display = ["parameter", "lat", "lon", "year", "month", "decade", "source"]
    search_fields = ["parameter", "source", "station"]
    list_filter = ['station', 'source','parameter', 'decade', 'month','year']

class ClimatMoisViewSet(SnippetViewSet):
    model = ClimatMois
    icon = "date"  # Choisis une icône Wagtail
    add_to_admin_menu = False
    menu_label = "Mois climat"
    menu_order = 200
    list_display = ["parameter", "name", "lat", "lon", "year", "month", "source"]
    search_fields = ["parameter","name", "source", "station"]
    list_filter = ['station',"name", 'source','parameter', 'month','year']


class CSVImportFormViewSet(SnippetViewSet):
    model = CSVImportForm
    icon = "doc-full"
    add_to_admin_menu = False
    menu_label = "Imports CSV Climat"
    menu_order = 201
    list_display = ["source", "year", "month", "decade", "processed", "success_count", "error_count"]
    search_fields = ["source"]

class ObsConfigGroup(SnippetViewSetGroup):
    items = (StationViewSet, ObservationViewSet, ClimatDecadesViewSet, CSVImportFormViewSet, ClimatMoisViewSet)
    menu_icon = 'view'
    menu_label = "Obs-Conf"
    menu_name = "Obs-Conf"
    add_to_admin_menu = False


###############################################################
# from wagtail import hooks
# from wagtail.admin import menu
# from django.urls import reverse
# from django.utils.html import format_html

# @hooks.register('register_admin_menu_item')
# def register_csv_import_menu_item():
#     return menu.MenuItem(
#         'Import CSV Climat', 
#         reverse('csv_import'), 
#         icon_name='upload',
#         order=1000
#     )


# @hooks.register('insert_global_admin_css')
# def global_admin_css():
#     return format_html(
#         '<style>'
#         '.csv-import-form {{ max-width: 800px; margin: 20px auto; }}'
#         '.csv-import-field {{ margin-bottom: 15px; }}'
#         '.csv-import-help {{ font-size: 0.9em; color: #666; margin-top: 5px; }}'
#         '.recent-imports {{ margin-top: 30px; }}'
#         '.import-status.success {{ color: green; }}'
#         '.import-status.error {{ color: red; }}'
#         '</style>'
#     )