from django.apps import AppConfig


class ForecastConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'forecast'

    def ready(self):
        from . import signals
        # Importer les modèles et les formulaires après le chargement des applications
        from .models import Variable
        from .forms import VariableForm

        # Associer le formulaire personnalisé après que tout soit prêt
        Variable.base_form_class = VariableForm
    