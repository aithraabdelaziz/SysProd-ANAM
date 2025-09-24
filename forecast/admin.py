# from django.contrib import admin

# from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from .models import Variable
from .forms import VariableForm
# class VariableAdmin(ModelAdmin):
class VariableViewSet(SnippetViewSet):
    model = Variable
    form =  VariableForm
    menu_label = "Variables Météo"  # ditch this to use verbose_name_plural from model
    icon = "list-ol"  # change as required
    menu_order = 200  # (000 being 1st, 100 2nd)
    add_to_admin_menu = False  # or True to add your model to the Settings sub-menu
    # exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('name', 'shortName', 'active', 'category')
    list_filter = ('category')
    search_fields = ('name', 'shortName')
    edit_form_class =  VariableForm
# modeladmin_register(VariableAdmin)
# register_snippet(VariableViewSet)

