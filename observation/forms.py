from django import forms
from django.contrib.gis import forms as gis_forms
from .models import Station, Observation
from wagtail.admin.forms import WagtailAdminModelForm
from django.core.exceptions import ValidationError


class StationForm(forms.ModelForm):
    class Meta:
        model = Station
        fields = ['name', 'geom','wigos_id']

    geom = gis_forms.GeometryField(widget=gis_forms.OSMWidget(
        attrs={'map_height': 600, 'map_width': 800, 'default_lat':12.72,'default_lon':-1.57, 'default_zoom': 5}
    ))
           
class ObservationForm(forms.ModelForm):
    class Meta:
        model = Observation
        fields = ['station', 'date', 'heure', 'parametre', 'observation']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'prevision': forms.Textarea(attrs={'rows': 6,'cols':150}), 
        }

class ShapefileUploadForm(forms.Form):
    shapefile = forms.FileField(label='un fichier (.zip)', required=False)


class GribImportForm(forms.Form):
    grib_file = forms.FileField(
        label="Fichier GRIB",
        help_text="Sélectionnez un fichier .grib à importer.",
    )

    def clean_grib_file(self):
        file = self.cleaned_data.get('grib_file')
        if not file.name.lower().endswith('.grib'):
            raise ValidationError("Seuls les fichiers avec l’extension .grib sont autorisés.")
        return file
        
class NetcdfImportForm(forms.Form):
    netcdf_file = forms.FileField(
        label="Fichier NetCDF",
        help_text="Sélectionnez un fichier .nc à importer.",
    )

    def clean_netcdf_file(self):
        file = self.cleaned_data.get('netcdf_file')
        if not file.name.lower().endswith('.nc'):
            raise ValidationError("Seuls les fichiers avec l’extension .nc sont autorisés.")
        return file