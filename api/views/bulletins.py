
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import FileResponse, Http404
from bulletins.models import BulletinTemplate
from api.serializers.bulletins import BulletinTemplateSerializer, BulletinTemplateMetadataSerializer
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

class BulletinTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A read-only ViewSet for accessing bulletin templates with PDF files.

    Provides list and detail views of bulletin templates that have associated PDF files.
    Access is restricted based on user groups - users can only see templates
    associated with their groups, while superusers can see all templates.

    Attributes:
        queryset (QuerySet): Base queryset filtering templates with PDF files
        serializer_class (Serializer): Serializer for bulletin templates
        permission_classes (list): Requires authenticated access

    Methods:
        get_queryset: Applies additional group-based filtering

    Example Usage:
        GET /api/bulletin-templates/ - List all accessible templates
        GET /api/bulletin-templates/1/ - Retrieve specific template details
    """
    queryset = BulletinTemplate.objects.filter(pdf_file__isnull=False)
    serializer_class = BulletinTemplateSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        """
        Apply group-based filtering to the queryset.

        Returns:
            QuerySet: Filtered queryset containing only templates accessible to:
                - All templates for superusers
                - Templates matching the user's groups for regular users
        """
        if self.request.user.is_superuser:
            return self.queryset
        user_groups = self.request.user.groups.all()
        return self.queryset.filter(role__in=user_groups).distinct()


class BulletinFiltersViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A read-only ViewSet for filtering bulletin templates.

    Provides list and detail views of bulletin templates with filtering capabilities.
    Access control follows the same rules as BulletinTemplateViewSet.

    Attributes:
        queryset (QuerySet): All bulletin templates
        serializer_class (Serializer): Serializer for bulletin templates
        permission_classes (list): Requires authenticated access
        filter_backends (list): DjangoFilterBackend for field filtering
        filterset_fields (list): Available fields for filtering (id, name)

    Methods:
        get_queryset: Applies group-based filtering before any other filters

    Example Usage:
        GET /api/bulletin-filters/?name=weather - Filter templates by name
        GET /api/bulletin-filters/?id=1 - Get specific template by ID
    """
    queryset = BulletinTemplate.objects.all()
    serializer_class = BulletinTemplateSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        """
        Apply group-based filtering to the base queryset.

        Returns:
            QuerySet: Filtered queryset containing only templates accessible to:
                - All templates for superusers
                - Templates matching the user's groups for regular users
        """
        if self.request.user.is_superuser:
            return self.queryset
        user_groups = self.request.user.groups.all()
        return self.queryset.filter(role__in=user_groups).distinct()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id', 'name']



class BulletinTemplateMetadataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BulletinTemplate.objects.all()
    serializer_class = BulletinTemplateMetadataSerializer