from django import forms
from bulletins.models import BulletinTemplate
from dal import autocomplete
from django.db.models import Q
from .models import Client
class DiffusionForm(forms.Form):
    bulletin = forms.ModelChoiceField(
        queryset=BulletinTemplate.objects.filter(
            Q(active=True) &
            Q(distributions__active=True) &
            (Q(distributions__via_mail=True) | Q(distributions__via_ftp=True))
        ).distinct(),
        label="Bulletin"
    )
    pdf_file = forms.FileField(required=False, label="Joindre un PDF personnalisé")

class FiltreDateForm(forms.Form):
    date = forms.DateField(
        required=False,
        label="Date",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = '__all__'
        widgets = {
            'ftp_password': forms.PasswordInput(render_value=True),
        }