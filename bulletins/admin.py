# from .models import Client, BulletinTemplate, Echeance, BulletinParameter, BulletinZone
# # from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

# from .forms import BulletinTemplateForm
# from wagtail.snippets.models import register_snippet
# from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
# class BulletinViewSet(SnippetViewSet):
#     model = BulletinTemplate
#     form = BulletinTemplateForm
#     menu_label = 'Bulletins'
#     menu_icon = 'doc-full-inverse'
#     menu_order = 200
#     add_to_settings_menu = False
#     exclude_from_explorer = False
#     list_display = ('name','bulletin_title')
#     search_fields = ('name','bulletin_title', 'subtitle','geographic_areas')
#     # Définir les filtres pour les champs ManyToMany
#     list_filter = ('geographic_areas', 'parameters', 'clients')
#     # Ajouter des champs ManyToMany dans l'édition en masse
#     list_editable = ('parameters', 'clients', 'geographic_areas')
#     # Configuration des champs de recherche ManyToMany
#     search_fields = ('name','bulletin_title', 'geographic_areas__name', 'parameters__name', 'clients__name')
#     edit_form_class = BulletinTemplateForm
#     list_filter = ('geographic_areas','clients','parameters')

# # register_snippet(BulletinViewSet)

# class ClientViewSet(SnippetViewSet):
#     model=Client
#     menu_label = 'Clients'
#     menu_icon = 'user'
#     list_display = ('name', 'email','active', 'phone')
#     search_fields = ('name', 'email','active', 'phone')

# # register_snippet(ClientViewSet)

# class EchanceViewSet(SnippetViewSet):
#     model=Echeance
#     menu_label = 'Echeances'
#     menu_icon = 'time'
#     list_display = ('name', 'echeance', 'active')
#     search_fields = ('name', 'echeance', 'active')

# # register_snippet(EchanceViewSet)

# class BulletinParameterViewSet(SnippetViewSet):
#     model=BulletinParameter
#     menu_label = 'Order paramètres'
#     menu_icon = 'time'
#     list_display = ('bulletin', 'parameter', 'order')
#     search_fields = ('bulletin', 'parameter')

# class BulletinZoneViewSet(SnippetViewSet):
#     model=BulletinZone
#     menu_label = 'Order zones'
#     menu_icon = 'time'
#     list_display = ('bulletin', 'zone', 'order')
#     search_fields = ('bulletin', 'zone')