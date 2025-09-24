from rest_framework import serializers
from forecast.models import Forecast
import html2text

class ForecastSerializer(serializers.ModelSerializer):
    zone = serializers.StringRelatedField()
    parametre = serializers.StringRelatedField()
    prevision_formatee = serializers.SerializerMethodField()  # Nouveau champ formaté
    
    class Meta:
        model = Forecast
        fields = ['id', 'zone', 'date', 'echeance', 'parametre', 'prevision', 'prevision_formatee']

    def get_prevision_formatee(self, obj):
        h = html2text.HTML2Text()
        h.ignore_links = True  # Ignore les liens
        h.ignore_images = True # ignore les images
        h.body_width = 0       # Désactive le retour à la ligne forcé
        return h.handle(obj.prevision).strip()  # Convertit HTML → Markdown/text

class DateFilterSerializer(serializers.Serializer):
    date = serializers.DateField(required=True, help_text="Date au format YYYY-MM-DD")