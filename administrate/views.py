from django.shortcuts import render
from wagtail.snippets.views.snippets import SnippetViewSet
from auditlog.models import LogEntry
from django.utils.translation import gettext_lazy as _

class LogEntrySnippetViewSet(SnippetViewSet):
    model = LogEntry
    menu_label = _("Journal des actions")
    icon = "doc-full"
    list_display = ['timestamp', 'actor', 'action', 'object_repr', 'content_type']
    list_filter = ['action', 'timestamp', 'content_type']
    search_fields = ['object_repr', 'changes']
    add_to_admin_menu = True
    inspect_view_enabled = True
    add_view_enabled = False
    edit_view_enabled = False
    delete_view_enabled = False
