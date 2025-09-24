from django import forms
from .models import BulletinTemplate,Echeance
from forecast.models import Zone, Variable,Forecast
from observation.models import Observation

from wagtail.fields import StreamField
from wagtail.blocks import CharBlock, RichTextBlock
from . import blocks

# from wagtail.admin.widgets import StreamFieldPanel
from wagtail.blocks import StreamBlock

from wagtail.blocks.stream_block import StreamValue
from wagtail.admin.forms import WagtailAdminModelForm

from datetime import datetime, timedelta

from pprint import pprint
from django_select2.forms import ModelSelect2MultipleWidget,ModelSelect2Widget

from .models import Localites
from wagtail.admin.forms import WagtailAdminModelForm
from observation.models import Station
from forecast.models import Zone
class LocalitesForm(WagtailAdminModelForm):
    class Meta:
        model = Localites
        fields = '__all__'

    widgets = {
            'stations': ModelSelect2MultipleWidget(
                model=Station,
                search_fields=['name__icontains'],  # adapte ce champ
            ),
            'villes': ModelSelect2MultipleWidget(
                model=Zone,
                search_fields=['name__icontains'],  # adapte ce champ
            ),
            'zone': ModelSelect2Widget(
                model=Zone,
                search_fields=['name__icontains'],  # adapte ce champ
            ),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['stations'].queryset = Station.objects.order_by('name')



class BulletinChoiceForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(BulletinChoiceForm, self).__init__(*args, **kwargs)

        dates1 = Forecast.objects.all().values_list('date', flat=True).distinct().order_by('-date')
        dates2 = Observation.objects.all().values_list('date', flat=True).distinct().order_by('-date')
        dates = sorted(set(dates1) | set(dates2), reverse=True)
        # dates = [(datetime.today() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)]
        self.fields['date'] = forms.ChoiceField(choices=[(value, value) for value in dates], widget=forms.Select(attrs={'class': 'form-control'}))
        
    select_all = forms.BooleanField(required=False, label="Selectionner tous")
    
    def clean(self):
        cleaned_data = super().clean()
        select_all = cleaned_data.get('select_all')
        return cleaned_data
