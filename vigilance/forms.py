from django import forms
import datetime

class VigilanceForm(forms.Form):
    PARAM_CHOICES = [
        ('vc', 'Vague de Chaleur'),
        ('vf', 'Vague de Froid'),
        ('rr', 'Fortes précipitations'),
        ('wind', 'Vents forts'),
    ]

    SOURCE_CHOICES = [
        ('expert', 'Expertisé'),
        ('gfs', 'Modèle GFS'),
    ]

    param = forms.ChoiceField(
        choices=PARAM_CHOICES,
        label="Phénomène météo",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    source = forms.ChoiceField(
        choices=SOURCE_CHOICES,
        label="Source de la donnée",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label="Date de prévision",
        initial=datetime.date.today
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Forcer le format ISO dans l'affichage initial
        if self.initial.get('date') and isinstance(self.initial['date'], datetime.date):
            self.initial['date'] = self.initial['date'].strftime('%Y-%m-%d')
