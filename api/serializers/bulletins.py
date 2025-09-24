from rest_framework import serializers
from bulletins.models import BulletinTemplate

class BulletinTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BulletinTemplate
        fields = ['id', 'name', 'pdf_file']



class BulletinTemplateMetadataSerializer(serializers.ModelSerializer):
    name = serializers.CharField(help_text="Unique technical name of the bulletin template.")
    bulletin_title = serializers.CharField(help_text="Visible title on the bulletin.")
    subtitle = serializers.CharField(help_text="Optional subtitle of the bulletin.", required=False, allow_null=True)
    active = serializers.BooleanField(help_text="Indicates whether this template is active.")
    header_text = serializers.CharField(help_text="Header text of the bulletin (rich text format).", required=False)
    footer_text = serializers.CharField(help_text="Footer text of the bulletin (rich text format).", required=False)
    created_at = serializers.DateTimeField(help_text="Creation date of the template.")

    class Meta:
        model = BulletinTemplate
        fields = [
            'id', 'name', 'bulletin_title', 'subtitle', 'active',
            'header_text', 'footer_text',
            'created_at'
        ]