from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from observation.models import Observation
from api.serializers.observation import ObservationSerializer, DateFilterSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from collections import defaultdict
from django.utils.dateparse import parse_date
from drf_spectacular.utils import extend_schema

class ObservationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Observation.objects.all()
    serializer_class = ObservationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['station', 'station__wigos_id', 'date', 'heure', 'parametre']





class ObservationFiltersViewSet(viewsets.ViewSet):
    """
    Expose les filtres disponibles (zones, paramètres, échéances) pour une date donnée.
    """

    @extend_schema(
        parameters=[DateFilterSerializer],
        responses={200: None}
    )
    @action(detail=False, methods=['get'], url_path='filters')
    def get_filters(self, request):
        serializer = DateFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        date = serializer.validated_data['date']

        observations = Observation.objects.filter(date=date).select_related('station', 'parametre').values(
            'station_id','station__wigos_id', 'station__name', 'parametre_id', 'parametre__name', 'heure'
        ).distinct()

        data = defaultdict(lambda: defaultdict(lambda: {'parametre_name': '', 'heures': set()}))
        zone_names = {}
        zone_wigos = {}

        for obs in observations:
            zone_id = obs['station_id']
            zone_wigos[zone_id] = obs['station__wigos_id']
            param_id = obs['parametre_id']
            zone_names[zone_id] = obs['station__name']
            zone_names[zone_id] = obs['station__name']

            data[zone_id][param_id]['parametre_name'] = obs['parametre__name']
            data[zone_id][param_id]['heures'].add(obs['heure'])


        result = []
        for zone_id, params in data.items():
            result.append({
                'station_id': zone_id,
                'station_name': zone_names[zone_id],
                'station_wigos': zone_wigos[zone_id],
                'parametres': [
                    {
                        'parametre_id': param_id,
                        'parametre_name': param_data['parametre_name'],
                        'heures': sorted(list(param_data['heures']))
                    }
                    for param_id, param_data in params.items()
                ]
            })

        return Response(result)