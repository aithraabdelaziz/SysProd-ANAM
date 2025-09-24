from django.db import models
from django.contrib.gis.db import models as gismodels
from wagtail.snippets.models import register_snippet
from wagtail.search import index
from wagtail.admin.panels import (FieldPanel)
from wagtail.fields import RichTextField
from django.utils.translation import gettext_lazy as _

from django.contrib.gis.forms.widgets import OSMWidget
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

from leaflet.forms.widgets import LeafletWidget
from forecast.models import Variable
from django.contrib.gis.geos import Point
# @register_snippet
class Station(gismodels.Model):
    name = gismodels.CharField(max_length=255, null=False)
    wigos_id = models.CharField("Wigos ID", max_length=50,null=False)
    geom=gismodels.PointField(geography=True,null=True,blank=True)
    elevation=gismodels.FloatField(null=True,blank=True)
    active = gismodels.BooleanField(default=True,null=False)
    latitude = models.FloatField(null=True,blank=True)
    longitude = models.FloatField(null=True,blank=True)
    
    panels = [
        FieldPanel('name'),
        FieldPanel('wigos_id'),
        FieldPanel('latitude'),
        FieldPanel('longitude'),
        FieldPanel('geom',widget=OSMWidget(attrs={'map_height':600,'map_width':800,'default_lat':12.72,'default_lon':-1.57,'default_zoom':5})),
        FieldPanel('elevation'),
        FieldPanel('active')
    ]
    search_fields = [
        index.SearchField('name', boost=2),  # Boost pour prioriser le nom
        index.SearchField('wigos_id'),
        index.AutocompleteField('name'),  # Pour l'autocomplétion
        index.AutocompleteField('wigos_id')
    ]

    class Meta:
        constraints = [
            gismodels.UniqueConstraint(
                fields=['name', 'wigos_id'],
                name='unique_name_wigos_id'
            )
        ]
        permissions = [
            ("edit_station", "Can edit stations"),
        ]
        ordering = ['name']
    def save(self, *args, **kwargs):
        if hasattr(self, 'latitude') and hasattr(self, 'longitude'):
            if self.latitude is not None and self.longitude is not None:
                self.geom = Point(self.longitude, self.latitude)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

# @register_snippet
class Observation(gismodels.Model):
    """
    Classe héritée de Forecast mais avec des modifications spécifiques pour l'observation.
    """
    station = models.ForeignKey(Station, on_delete=models.CASCADE, blank=False, null=False)
    date = models.DateField(blank=False, null=False)
    heure = models.CharField(blank=False, null=False)
    parametre = models.ForeignKey(Variable, on_delete=models.CASCADE, blank=False, null=False)
    observation = RichTextField(blank=True, null=True)

    
    panels = [
        FieldPanel('station'),
        FieldPanel('parametre'),
        FieldPanel('date'),
        FieldPanel('heure'),
        FieldPanel('observation'),
    ]

    search_fields = [
        index.SearchField('date'),
        index.SearchField('heure'),
        index.SearchField('heure'),
        index.RelatedFields('station', 'name'),
        index.RelatedFields('station', 'wigos_id'),
        index.RelatedFields('parameters', 'name'),
    ]


    class Meta:
        permissions = [
            ("edit_observation", "Can edit Observation"),
        ]
        constraints = [
            models.UniqueConstraint(fields=['station', 'date','heure','parametre'], name='unique_attributs_obs')
        ]

    @classmethod
    def create_or_update(cls, station, date, heure, parametre, **kwargs):
        """
        Méthode de création ou mise à jour spécifique à l'Observation
        """
        obj, created = cls.objects.update_or_create(
            station=station, 
            date=date,
            heure=heure,
            parametre=parametre,
            defaults=kwargs
        )
        return obj, created

    def __str__(self):
        return f'Observation de {self.parametre} pour {self.station} le {str(self.date)}, heure : {self.heure}'



from django.core.validators import FileExtensionValidator
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.models import Page
from wagtail.admin import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
import csv
import io
import logging

logger = logging.getLogger(__name__)
# @register_snippet
class ClimatDecades(models.Model):
    """Modèle pour la table climat.decades"""
    station = models.CharField(max_length=255, null=True, blank=True)
    lon = models.FloatField()
    lat = models.FloatField()
    decade = models.IntegerField()
    month = models.IntegerField()
    year = models.IntegerField()
    parameter = models.CharField(max_length=255)
    value = models.FloatField(null=True, blank=True)
    source = models.CharField(max_length=255, null=True, blank=True)
    
    search_fields = [
        index.SearchField('station', boost=2),  # Boost pour prioriser le nom
        index.SearchField('decade'),
        index.SearchField('month'),
        index.SearchField('year'),
        index.SearchField('parameter'),
        index.SearchField('source'),
        index.AutocompleteField('station'),  # Pour l'autocomplétion
        index.AutocompleteField('parameter'),
        index.AutocompleteField('source')
    ]
    class Meta:
        permissions = [
            ("edit_climdata", "Can edit Clim Data"),
        ]
        # db_table = 'climat.decades'
        unique_together = ('lon', 'lat', 'decade', 'month', 'year', 'parameter', 'source')
        
    def __str__(self):
        return f"{self.parameter} - {self.lat},{self.lon} - {self.year}/{self.month}/{self.decade}"

# @register_snippet
from django.db import models
from django.core.validators import FileExtensionValidator

class BaseCSVImport(models.Model):
    """Classe abstraite pour l'import CSV commun"""
    month = models.IntegerField(help_text="Mois (1-12)")
    year = models.IntegerField(help_text="Année")
    source = models.CharField(max_length=255, help_text="Source des données")
    csv_file = models.FileField(
        upload_to='csv_imports/',
        validators=[FileExtensionValidator(allowed_extensions=['csv'])],
        help_text="Fichier CSV contenant les données"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    error_log = models.TextField(blank=True, null=True)
    success_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)

    class Meta:
        abstract = True

    def __str__(self):
        return f"Import {self.source} - {self.year}/{self.month}"


class CSVImportForm(BaseCSVImport):
    """Import CSV spécifique pour ClimatDecades"""
    decade = models.IntegerField(help_text="Décade (1-3 pour les 10 premiers, 11-20, 21-31 jours du mois)")

    class Meta:
        verbose_name = "Import CSV Climat Décades"
        verbose_name_plural = "Imports CSV Climat Décades"

    def __str__(self):
        return f"Import {self.source} - {self.year}/{self.month} - Décade {self.decade}"


class CSVImportMois(BaseCSVImport):
    """Import CSV spécifique pour ClimatMois"""

    class Meta:
        verbose_name = "Import CSV Climat Mensuel"
        verbose_name_plural = "Imports CSV Climat Mensuel"


# @register_snippet
class ClimatMois(models.Model):
    """Modèle pour les données climatiques mensuelles"""
    station = models.CharField(max_length=255, null=True, blank=True)
    lon = models.FloatField()
    lat = models.FloatField()
    month = models.IntegerField()
    year = models.IntegerField()
    parameter = models.CharField(max_length=255)
    name = models.CharField(max_length=255,default='')
    value = models.FloatField(null=True, blank=True)
    source = models.CharField(max_length=255, null=True, blank=True)

    search_fields = [
        index.SearchField('station', boost=2),
        index.SearchField('month'),
        index.SearchField('year'),
        index.SearchField('parameter'),
        index.SearchField('name'),
        index.SearchField('source'),
        index.AutocompleteField('station'),
        index.AutocompleteField('parameter'),
        index.AutocompleteField('source'),
    ]

    class Meta:
        permissions = [
            ("edit_climdata", "Can edit Clim Data"),
        ]
        # db_table = 'climat.mois'
        unique_together = ('lon', 'lat', 'month', 'year', 'parameter', 'source')

    def __str__(self):
        return f"{self.parameter} - {self.lat},{self.lon} - {self.year}/{self.month}"

