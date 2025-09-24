from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from forecast.models import Forecast
from api.serializers.forecast import ForecastSerializer, DateFilterSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from collections import defaultdict
from django.utils.dateparse import parse_date
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample


class ForecastViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A ViewSet for retrieving weather forecasts in read-only mode.

    Provides list and detail actions to access Forecast objects filtered by
    zone, date, forecast range (echeance), and parameter (parametre).
    Requires authentication for all operations.

    Attributes:
        queryset (QuerySet): The default queryset containing all Forecast objects.
        serializer_class (Serializer): The serializer class for Forecast objects.
        permission_classes (list): Authentication requirements (IsAuthenticated).
        filter_backends (list): Filtering backend (DjangoFilterBackend).
        filterset_fields (list): Fields available for filtering.

    Example requests:
        - GET /api/forecasts/?zone=Ouagadougou&date=2025-05-28
        - GET /api/forecasts/?parametre=temperature&echeance=24

    Note:
        This ViewSet does not support create, update, or delete operations
        (inherits from ReadOnlyModelViewSet).
    """
    queryset = Forecast.objects.all()
    serializer_class = ForecastSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['zone', 'date', 'echeance', 'parametre']





class ForecastFiltersViewSet(viewsets.ViewSet):
    """
    ViewSet to expose available filters (zones, parameters, forecast lead times) for weather forecasts on a given date.

    This ViewSet provides a custom endpoint to retrieve:
    - The list of available zones
    - Available weather parameters
    - Available lead times
    For a specific date within the forecasts.

    Note:
        Requires a valid date as a query parameter.
    """
    @extend_schema(
        parameters=[DateFilterSerializer],
        responses={
            200: OpenApiResponse(
                description="Returns the structure of available filters",
                examples={
                    "application/json": [
                        {
                            "zone_id": 1,
                            "zone_name": "Ouagadougou",
                            "parametres": [
                                {
                                    "parametre_id": 1,
                                    "parametre_name": "temperature",
                                    "echeances": [24, 48, 72]
                                },
                                {
                                    "parametre_id": 2,
                                    "parametre_name": "tmax",
                                    "echeances": [24, 48]
                                }
                            ]
                        }
                    ]
                }
            ),
            400: OpenApiResponse(description="Invalid or missing date")
        },
        description="""Retrieves the available filters (zones, parameters, lead times) for a given date.

        Example:
            /api/forecast-filters/filters/?date=2025-05-28
        """
    )
    @action(detail=False, methods=['get'], url_path='filters')
    def get_filters(self, request):
        """
        Retrieves available filters for a specific date.

        Args:
            request (Request): The HTTP request containing:
                - date (str): Date in YYYY-MM-DD format (required)

        Returns:
            Response: A JSON array containing for each zone:
                - zone_id: Zone identifier
                - zone_name: Zone name
                - parametres: List of available parameters with:
                    - parametre_id: Parameter ID
                    - parametre_name: Parameter name
                    - echeances: Sorted list of available lead times

        Raises:
            ValidationError: If the date is invalid or missing
        """
        serializer = DateFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        date = serializer.validated_data['date']

        forecasts = Forecast.objects.filter(date=date).select_related('zone', 'parametre').values(
            'zone_id', 'zone__name', 'parametre_id', 'parametre__name', 'echeance'
        ).distinct()

        data = defaultdict(lambda: defaultdict(lambda: {'parametre_name': '', 'echeances': set()}))
        zone_names = {}

        for fcst in forecasts:
            zone_id = fcst['zone_id']
            param_id = fcst['parametre_id']
            zone_names[zone_id] = fcst['zone__name']
            data[zone_id][param_id]['parametre_name'] = fcst['parametre__name']
            data[zone_id][param_id]['echeances'].add(fcst['echeance'])


        result = []
        for zone_id, params in data.items():
            result.append({
                'zone_id': zone_id,
                'zone_name': zone_names[zone_id],
                'parametres': [
                    {
                        'parametre_id': param_id,
                        'parametre_name': param_data['parametre_name'],
                        'echeances': sorted(list(param_data['echeances']))
                    }
                    for param_id, param_data in params.items()
                ]
            })

        return Response(result)