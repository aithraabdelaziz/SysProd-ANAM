from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from wagtail.admin.menu import MenuItem, SubmenuMenuItem
from wagtail import hooks
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from wagtail.admin.filters import DateRangePickerWidget

from .models import Client, GroupClient, BulletinDessimination, BulletinTransmissionLog
from .forms import ClientForm

class ClientViewSet(SnippetViewSet):
    model = Client
    form_class = ClientForm
    menu_label = _("Clients")
    icon = "group"
    list_display = ['name', 'email', 'active']
    list_filter = ['active', 'transmit_mail', 'transmit_fax', 'transmit_sms']
    search_fields = ['name', 'email']
    add_to_admin_menu = False 
    ordering = ['name']

class GroupClientViewSet(SnippetViewSet):
    model = GroupClient
    menu_label = _("Groupe des Clients")
    icon = "group"
    list_display = ['name']
    search_fields = ['name','clients__name', 'clients__email']
    add_to_admin_menu = False 
    ordering = ['name']

class BulletinDessiminationViewSet(SnippetViewSet):
    model = BulletinDessimination
    menu_label = "Diffusions"
    menu_icon = "resubmit"  # ou 'megaphone', 'upload' si supporté
    menu_order = 300
    add_to_settings_menu = False
    list_display = ('bulletin', 'client', 'distributed_at')
    search_fields = ('bulletin__name', 'clients__name')

class BulletinTransmissionLogViewSet(SnippetViewSet):
    model = BulletinTransmissionLog
    menu_label = "Historique"
    menu_icon = "history"  # ou 'megaphone', 'upload' si supporté
    menu_order = 300
    add_to_settings_menu = False
    list_display = ('bulletin', 'client', 'sent_at','sent_by','status')
    search_fields = ('bulletin__name', 'client__name','client__mail')
    def can_create(self, request):
        return False  # interdit la création

    def can_edit(self, request, instance=None):
        return False  # interdit la modification

    def can_delete(self, request, instance=None):
        return False  # interdit la suppression
class DiffusionConfigGroup(SnippetViewSetGroup):
    items = (ClientViewSet, GroupClientViewSet, BulletinDessiminationViewSet, BulletinTransmissionLogViewSet)
    menu_icon = 'mail'
    menu_label = "Diffusion"
    menu_name = "Diffusion"
    add_to_admin_menu = False



# register_snippet(DiffusionConfigGroup)