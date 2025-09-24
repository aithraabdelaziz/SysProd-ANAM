# vigilance/models.py
from django.db import models
from django.db.models import JSONField
from django.contrib.gis.db import models as gis_models
from wagtail.snippets.models import register_snippet

class AbstractVigimetProvince(models.Model):
    province_id = models.CharField(max_length=100)
    province_name = models.CharField(max_length=255)
    forecast_date = models.DateField()
    param = models.CharField(max_length=50)
    details = JSONField()
    geom = gis_models.GeometryField(null=True, blank=True)
    status = models.IntegerField(null=True, blank=True)

    class Meta:
        abstract = True
        unique_together = ('province_id', 'forecast_date', 'param')
        permissions = [
            ("edit_vigilance", "Can edit vigilance"),
            ("view_vigilance", "Can display vigilance"),
        ]

    def get_vigilance_level(self):
        return self.details.get('level')

    def get_value(self):
        return self.details.get('value')

    def get_smin(self):
        return self.details.get('smin')

    def get_smax(self):
        return self.details.get('smax')

    def get_comment(self):
        return self.details.get('comment')

@register_snippet
class VigimetProvinceAuto(AbstractVigimetProvince):
    class Meta(AbstractVigimetProvince.Meta):
        db_table = '"gfs_model"."vigimet_provinces_auto"'

@register_snippet
class VigimetProvinceProd(AbstractVigimetProvince):
    class Meta(AbstractVigimetProvince.Meta):
        db_table = '"gfs_model"."vigimet_provinces_prod"'
