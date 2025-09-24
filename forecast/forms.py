from django import forms
from django.contrib.gis import forms as gis_forms
from .models import Variable, Zone, Forecast
from wagtail.admin.forms import WagtailAdminModelForm


class VariableForm(WagtailAdminModelForm):
    class Meta:
        model = Variable
        fields = ['name', 'shortName', 'unit', 'active', 'category']
    name = forms.CharField(widget=forms.TextInput(attrs={'size': 60}), required=True)
    shortName = forms.CharField(widget=forms.TextInput(attrs={'size': 60}), required=True)
    unit = forms.CharField(widget=forms.TextInput(attrs={'size': 10}), required=False)
    active = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),required=False)
    category = forms.ChoiceField(
                choices=[
                    ('class', 'Classes'),
                    ('value', 'Valeures continues'),
                    ('text','Texte')
                ],
                widget=forms.Select(attrs={'class': 'form-control'}),
                required=True,  # Le champ est obligatoire par défaut
                help_text="The variable should be displayed in classes or in a continuous values"
            )

class ZoneForm(forms.ModelForm):
    class Meta:
        model = Zone
        fields = ['name', 'geom','rayon']

    geom = gis_forms.GeometryField(widget=gis_forms.OSMWidget(
        attrs={'map_height': 600, 'map_width': 800, 'default_lat':12.72,'default_lon':-1.57, 'default_zoom': 5}
    ))
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        category = self.initial.get('category', None)
        
        # Désactiver rayon si la catégorie n'est pas 'axe', 'ville' ou 'point'
        if category not in ['axe', 'ville', 'point']:
            self.fields['rayon'].widget.attrs['disabled'] = 'disabled'          



class ShapefileUploadForm(forms.Form):
    shapefile = forms.FileField(label='un fichier (.zip)', required=False)

class MergeZonesForm(forms.Form):
    name = forms.CharField(label='Nom de la nouvelle zone fusionnée')
    category_choices = [
        ('Commune', 'Commune'),
        ('Province', 'Province'),
        ('Axe', 'Axe'),
        ('Point', 'Point'),
        ('Divers', 'Divers'),
    ]
    category = forms.ChoiceField(choices=category_choices, label='Catégorie')


class ForecastChoiceForm(forms.Form):
    def __init__(self, category, expertise,*args, **kwargs):
        super(ForecastChoiceForm, self).__init__(*args, **kwargs)

        dates = Forecast.objects.filter(zone__category=category).values_list('date', flat=True).distinct().order_by('-date')
        self.fields['date'] = forms.ChoiceField(choices=[(value, value) for value in dates], widget=forms.Select(attrs={'class': 'form-control'}))
        if expertise == 'yes' :
            parametres = Forecast.objects.filter(zone__category=category,parametre__shortName__icontains='expertise').values_list('parametre', flat=True).distinct()
        else :
            parametres = Forecast.objects.filter(zone__category=category).exclude(parametre__shortName__icontains='expertise').values_list('parametre', flat=True).distinct()
        
        self.fields['parametre'] = forms.ChoiceField(choices=[(value, Variable.objects.get(id=value)) for value in parametres], widget=forms.Select(attrs={'class': 'form-control'}))
        
        zones = Forecast.objects.filter(zone__category=category).values_list('zone', flat=True).distinct()
        self.fields['zones'] = forms.MultipleChoiceField(choices=[(value, Zone.objects.get(id=value)) for value in zones], widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}))

    select_all = forms.BooleanField(required=False, label="Selectionner tous")
    
    def clean(self):
        cleaned_data = super().clean()
        select_all = cleaned_data.get('select_all')
        zones = cleaned_data.get('zones')
         # Si select_all n'est pas coché, zones doit être rempli
        if not select_all and not zones:
            raise forms.ValidationError('Vous devez choisir une zone ou sélectionner "Tout".')
        
        return cleaned_data


from django.utils import timezone
class ForecastForm(forms.ModelForm):
    class Meta:
        model = Forecast
        fields = ['zone', 'date', 'echeance', 'parametre', 'prevision']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'prevision': forms.Textarea(attrs={'rows': 6,'cols':150}), 
        }


class ForecastFilterForm(forms.Form):
    zone = forms.ModelChoiceField(
        queryset=Zone.objects.all(),
        required=False,
        label="Zone"
    )
    parametre = forms.ModelChoiceField(
        queryset=Variable.objects.all(),
        required=False,
        label="Paramètre"
    )
    date_debut = forms.DateField(
        required=False,
        label="Date de début",
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_fin = forms.DateField(
        required=False,
        label="Date de fin", 
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    echeance = forms.IntegerField(
        required=False,
        label="Échéance"
    )