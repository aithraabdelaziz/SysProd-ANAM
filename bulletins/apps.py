from django.apps import AppConfig


# class BulletinconfigConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'bulletins'
    
#     def ready(self):
#         # Importer les modèles et les formulaires après le chargement des applications
#         from .models import BulletinTemplate
#         from .forms import BulletinTemplateForm

#         # Associer le formulaire personnalisé après que tout soit prêt
#         BulletinTemplate.base_form_class = BulletinTemplateForm

