from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from wagtail.admin.menu import MenuItem, SubmenuMenuItem
from wagtail import hooks
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from wagtail.admin.filters import DateRangePickerWidget

from .models import Echeance,BulletinTemplate,Localites,BulletinStyleConfiguration, SendingSchedule

#### Définition des ViewSets pour chaque snippet

class EcheanceViewSet(SnippetViewSet):
    model = Echeance
    menu_label = _("Echéances")
    icon = "date"
    list_display = ['name', 'echeance','start','end', 'active']
    list_filter = ['echeance','active']
    search_fields = ['name', 'echeance', 'active']
    add_to_admin_menu = False
    def form_valid(self, form):
        if form.instance.start > form.instance.end:
            messages.warning(self.request, "Attention : début est supérieur à fin. en prendra la période précédante")
        return super().form_valid(form)

class BulletinTemplateViewSet(SnippetViewSet):
    model = BulletinTemplate
    menu_label = _("Bulletin")
    icon = "doc-full"
    list_display = ['name', 'active']
    list_filter = ['name','active']
    search_fields = ['name','bulletin_title','subtitle','content']
    add_to_admin_menu = False

class SendingScheduleViewSet(SnippetViewSet):
    model = SendingSchedule
    menu_label = _("ProgrammeEnvoi")
    icon = "time"
    list_display = ['frequency_type', 'send_time', 'weekday','day_of_month']
    list_filter = ['frequency_type','send_time']
    add_to_admin_menu = False
    
from .forms import LocalitesForm
class LocalitesViewSet(SnippetViewSet):
    model = Localites
    form_class = LocalitesForm
    menu_label = "Localités"
    menu_icon = "site"
    list_display = ("name",)
    search_fields = ("name",)


from django.db.models import ProtectedError
from rest_framework.response import Response
from rest_framework import status

class BulletinStyleConfigurationViewSet(SnippetViewSet):
    model = BulletinStyleConfiguration
    menu_label = "Style bulletins"
    list_display = ("name",)
    search_fields = ("name",)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "Suppression impossible : ce style est utilisé par des bulletins."},
                status=status.HTTP_400_BAD_REQUEST
            )

from forecast.wagtail_hooks import FcsConfigGroup
from observation.wagtail_hooks import ObsConfigGroup
from dissiminate.wagtail_hooks import DiffusionConfigGroup
from chartmet.wagtail_hooks import MapConfigGroup 

class BulletinConfigGroup(SnippetViewSetGroup):
    items = (EcheanceViewSet, BulletinTemplateViewSet, SendingScheduleViewSet,
        # MapObsConfigurationViewSet,MapFcstConfigurationViewSet,MapModelConfigurationViewSet,MapSpatialConfigurationViewSet,
        LocalitesViewSet ,
        BulletinStyleConfigurationViewSet,
        FcsConfigGroup,ObsConfigGroup,MapConfigGroup,DiffusionConfigGroup)
    menu_icon = 'doc-full'
    menu_label = "Bulletin-Conf"
    menu_name = "Bulletin-Conf"

register_snippet(BulletinConfigGroup)