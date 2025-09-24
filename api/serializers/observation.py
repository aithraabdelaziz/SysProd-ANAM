from rest_framework import serializers
from observation.models import Observation
import html2text

class ObservationSerializer(serializers.ModelSerializer):
    station = serializers.StringRelatedField()
    parametre = serializers.StringRelatedField()
    observation_formatee = serializers.SerializerMethodField()  # Nouveau champ formaté
    
    class Meta:
        model = Observation
        fields = ['id', 'station', 'date', 'heure', 'parametre', 'observation', 'observation_formatee']

    def get_observation_formatee(self, obj):
        h = html2text.HTML2Text()
        h.ignore_links = True  # Ignore les liens
        h.ignore_images = True # ignore les images
        h.body_width = 0       # Désactive le retour à la ligne forcé
        return h.handle(obj.observation).strip()  # Convertit HTML → Markdown/text

class DateFilterSerializer(serializers.Serializer):
    date = serializers.DateField(required=True, help_text="Date au format YYYY-MM-DD")