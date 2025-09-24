from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.api.v2.router import WagtailAPIRouter

api_router = WagtailAPIRouter('wagtailapi')
api_router.register_endpoint('pages', PagesAPIViewSet)

from wagtail import hooks
from wagtail.models import Site
from wagtail.contrib.settings.registry import registry
from django.templatetags.static import static
from administrate.models import OrganisationSetting


from django.contrib import messages
from django.apps import apps
from django.db.models import ForeignKey
from wagtail.documents import get_document_model

@hooks.register("before_delete_document")
def prevent_deletion_if_used_globally(request, document):
    Document = get_document_model()
    related_models = []

    # Parcourt tous les modèles de toutes les apps
    for model in apps.get_models():
        for field in model._meta.fields:
            if isinstance(field, ForeignKey) and field.remote_field.model == Document:
                kwargs = {field.name: document}
                if model.objects.filter(**kwargs).exists():
                    related_models.append((model._meta.verbose_name_plural, field.name))

    if related_models:
        message = f"Impossible de supprimer le document « {document.title} » : utilisé dans {len(related_models)} modèle(s)."
        messages.error(request, message)
        return False  # Empêche la suppression

from wagtail.admin.menu import MenuItem

@hooks.register('construct_main_menu')
def add_site_link_item(request, menu_items):
    menu_items.append(
        MenuItem(
            'Revenir au site',
            '/',
            classnames='icon icon-site',
            order=10000,
            attrs={'target': '_self'}
        )
    )


from wagtail.snippets.models import register_snippet
from .views import LogEntrySnippetViewSet  # ou l'endroit où vous l'avez définie

# register_snippet(LogEntrySnippetViewSet)

from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup


class PeriodicTaskSnippetViewSet(SnippetViewSet):
    model = PeriodicTask
    icon = "time"
    menu_label = "Tâches périodiques"
    add_to_admin_menu = False
    list_display = ("name", "task", "interval", "crontab", "last_run_at", "enabled")
    
    def get_queryset(self, request):
        return self.model.objects.filter(solar__isnull=True, clocked__isnull=True)

class IntervalScheduleSnippetViewSet(SnippetViewSet):
    model = IntervalSchedule
    icon = "date"
    menu_label = "Interval Schedules"
    add_to_admin_menu = False

class CrontabScheduleSnippetViewSet(SnippetViewSet):
    model = CrontabSchedule
    icon = "time"
    menu_label = "Crontab Schedules"
    add_to_admin_menu = False

class CeleryGroup(SnippetViewSetGroup):
    items = (PeriodicTaskSnippetViewSet, IntervalScheduleSnippetViewSet, CrontabScheduleSnippetViewSet, LogEntrySnippetViewSet)
    menu_icon = 'time'
    menu_label = "Execution des Tâches"
    menu_name = "Execution des Tâches"

register_snippet(CeleryGroup)
# @hooks.register('insert_global_admin_css')
# def custom_admin_logo_css():
#     site = Site.find_for_request(None) or Site.objects.first()
#     logo_url = static('images/default-logo.png')
#     favicon_url = static('images/favicon.ico')

#     try:
#         settings_model = OrganisationSetting.for_site(site)
#         org_settings = settings_model.for_site(site)
#         if org_settings.logo:
#             logo_url = org_settings.logo.file.url
#         if org_settings.favicon:
#             favicon_url = org_settings.favicon.file.url
#     except Exception as e :
#         print(e)
#         pass  # On garde les URLs par défaut
#     print(f"""
#     <style>
#     .wagtail-logo {{
#         background-image: url('{logo_url}') !important;
#         background-size: contain !important;
#         width: 200px !important;
#         height: 40px !important;
#     }}
#     </style>
#     <link rel="shortcut icon" href="{favicon_url}" />
#     """)
#     return f"""
#     <style>
#     .wagtail-logo {{
#         background-image: url('{logo_url}') !important;
#         background-size: contain !important;
#         width: 200px !important;
#         height: 40px !important;
#     }}
#     </style>
#     <link rel="shortcut icon" href="{favicon_url}" />
#     """


