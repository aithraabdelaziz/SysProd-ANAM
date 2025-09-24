from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from django.conf import settings
from django.http import FileResponse, Http404
from urllib.parse import quote
import os

from drf_spectacular.utils import extend_schema, OpenApiParameter

class VigilanceViewSet(viewsets.ViewSet):
    """
    ViewSet pour lister ou télécharger les fichiers de la vigilance (vc ou vf).
    """

    @extend_schema(
        parameters=[
            OpenApiParameter(name='date', location=OpenApiParameter.QUERY, description='Date format YYYYmmdd', required=True, type=str),
            OpenApiParameter(name='param', location=OpenApiParameter.QUERY, description='Paramètre vc ou vf, * pour lister tous', required=True, type=str),
        ],
        responses={200: dict, 400: dict, 404: dict}
    )
    @action(detail=False, methods=['get'], url_path='list')
    def list_files(self, request):
        date = request.query_params.get('date')
        param = request.query_params.get('param')  # 'vc' ou 'vf'

        if not date or not param or param not in ['vc', 'vf','*']:
            return Response({"detail": "Paramètres requis : date=YYYYmmdd, param=vc|vf|*"}, status=400)

        folder_path = os.path.join(settings.MEDIA_ROOT, 'vigilance','images', date)
        base_url = request.build_absolute_uri(settings.MEDIA_URL)

        if not os.path.exists(folder_path):
            return Response({"detail": "Dossier introuvable"}, status=404)

        files = []
        for f in os.listdir(folder_path):
            if f.endswith(".png"):
                if param == "*":
                    if "-" in f:
                        file_url = f"{base_url}vigilance/images/{date}/{quote(f)}"
                        files.append({"filename": f, "url": file_url})
                else:
                    if f.startswith(f"{param}-"):
                        file_url = f"{base_url}vigilance/images/{date}/{quote(f)}"
                        files.append({"filename": f, "url": file_url})

        return Response({"files": files})

    @extend_schema(
        parameters=[
            OpenApiParameter(name='date', location=OpenApiParameter.QUERY, description='Date format YYYYmmdd', required=True, type=str),
            OpenApiParameter(name='filename', location=OpenApiParameter.QUERY, description='Nom de la viglance', required=True, type=str),
        ],
        responses={200: None}
    )
    @action(detail=False, methods=['get'], url_path='download')
    def download_file(self, request):
        date = request.query_params.get('date')
        filename = request.query_params.get('filename')

        if not date or not filename:
            return Response({"detail": "Paramètres requis : date, filename"}, status=400)

        file_path = os.path.join(settings.MEDIA_ROOT, 'vigilance','images', date, filename)
        if not os.path.exists(file_path):
            raise Http404("Fichier introuvable")

        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
