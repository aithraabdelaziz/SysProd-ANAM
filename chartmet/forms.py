from django import forms
from .models import Legend
from wagtail.admin.forms import WagtailAdminModelForm

class LegendForm(forms.ModelForm):
    class Meta:
        model = Legend
        fields = ['name', 'active', 'descriptions']
