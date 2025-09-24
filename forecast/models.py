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

# @register_snippet
class Variable(index.Indexed,models.Model):
	"""docstring for Parameter"""
	name = models.CharField(max_length=150, unique=True, null=False,help_text="Name of the meteorological variable")
	shortName = models.CharField(max_length=50, unique=True, null=False, help_text="Short_name used by the systems source")
	active = models.BooleanField(default=True, help_text='Activate or disactivate the variable')
	unit = models.CharField(max_length=50, null=True, default='', help_text="The unit of the variable")
	category =  models.CharField(
		max_length=5,default='class', help_text="The variable should be displayed in classes or in a continuous values",
		choices=[
			('class', 'Classes'),
			('value', 'Valeurs continues'),
			('text','Texte')
		])
	
	base_form_class=None

	panels = [
	
		FieldPanel('name'),
		FieldPanel('shortName'),
		FieldPanel('active'),
		FieldPanel('unit'),
		FieldPanel('category')

	]

	search_fields = [
	    index.SearchField('name', boost=2),  # Boost pour prioriser le nom
	    index.SearchField('shortName'),
	    index.SearchField('category'),
	    index.AutocompleteField('name'),  # Pour l'autocomplétion
	    index.AutocompleteField('category'),
	    index.AutocompleteField('shortName'),
	]
	
	class Meta:
		ordering = ['name']
		permissions = [
			("edit_variables", "Can edit variables"),
		]
	@classmethod
	def create_or_update(cls, name, shortName,active,unit,category, **kwargs):
		obj, created = cls.objects.update_or_create(
			name=name,
			shortName=shortName,
			active=active,
			unit=unit,
			category=category,
			defaults=kwargs
		)
		return obj, created
	
	def __str__(self):
		return f"{self.name}"


# @register_snippet
class Zone(index.Indexed,gismodels.Model):
	CATEGORY_CHOICES = [
		('polygon','Plolygone'),
		('commune', 'Commune'),
		('province', 'Province'),
		('region', 'Région'),
		('ville', 'Ville'),
		# ('axe', 'Axe'),
		# ('point', 'Point'),
		# ('divers', 'Divers')
	]
	name = gismodels.CharField(max_length=255, null=True)
	# geometrie = models.PolygonField(geography=True,null=True,blank=True)
	geom=gismodels.GeometryField(geography=True,null=True,blank=True)
	active = gismodels.BooleanField(default=True,null=False)
	category = gismodels.CharField(max_length=10, choices=CATEGORY_CHOICES, null=True, blank=True)
	rayon = gismodels.FloatField(default=0, null=True, blank=True,validators=[MinValueValidator(0.0)])
	#larg_bande = models.IntegerField(null=True, blank=True)

	def save(self, *args, **kwargs):
		# Contrôle de la valeur de rayon en fonction de la catégorie
		if self.category not in ['axe', 'ville', 'point']:
			self.rayon = 0  # Forcer à 0 pour les autres catégories
		elif self.rayon is None or self.rayon <= 0:
			raise ValidationError("Rayon doit être un nombre positif (en km) pour les catégories 'axe', 'ville' ou 'point'.")

		super().save(*args, **kwargs)

	panels = [
		FieldPanel('name'), #widget=OSMWidget(attrs={'map_height': 600,'map_width': 800})),
		FieldPanel('geom',widget=OSMWidget(attrs={'map_height':600,'map_width':800,'default_lat':29.26340520817928,'default_lon':-10.413367744774774,'default_zoom':5})),
		FieldPanel('active'),
		FieldPanel('category'),
		FieldPanel('rayon'),
	]

	search_fields = [
		index.SearchField('name', boost=2),
		index.SearchField('category'),
		index.FilterField('category'),  # Ajoutez ça aussi
	    index.AutocompleteField('name'),
	    index.AutocompleteField('category')
	]
	class Meta:

		ordering = ['name']
		permissions = [
			("edit_zone", "Can edit zones"),
		]

	def __str__(self):
		return f"{self.name}"

# @register_snippet
class Forecast(models.Model):
	"""
	model contenant les prévisions d'une zone donnée
	"""
	zone = models.ForeignKey(Zone, on_delete=models.CASCADE, blank=False, null=False)
	date = models.DateField(blank=False, null=False)
	echeance = models.CharField(blank=False, null=False)
	# echeance = models.ForeignKey("bulletins.Echeance", on_delete=models.CASCADE, blank=False, null=False)
	parametre = models.ForeignKey(Variable, on_delete=models.CASCADE, blank=False, null=False)
	prevision = RichTextField(blank=True, null=True)
	
	# base_form_class=None

	panels = [
		FieldPanel('zone'),
		FieldPanel('date'),
		FieldPanel('echeance'),
		FieldPanel('parametre'),
		FieldPanel('prevision'),
	]

	search_fields = [
		index.SearchField('date'),
		index.SearchField('prevision'),
		index.RelatedFields('zone', 'name'),  # Indexe le champ 'name' de la relation ManyToMany
		index.RelatedFields('zone', 'category'),
		# index.RelatedFields('echeance', 'name'),
		# index.RelatedFields('echeance', 'start'),
		# index.RelatedFields('echeance', 'end'),
		index.RelatedFields('parameters', 'name'),
	]

	class Meta:
		permissions = [
			("edit_forecast", "Can edit Forecast"),
		]
		constraints = [
			models.UniqueConstraint(fields=['zone', 'date','echeance','parametre'], name='unique_attributs_fcst')
		]
	@classmethod
	def create_or_update(cls, zone, date,echeance,parametre, **kwargs):
		obj, created = cls.objects.update_or_create(
			zone=zone, 
			date=date,
			echeance=echeance,
			parametre=parametre,
			defaults=kwargs
		)
		return obj, created
	@classmethod
	def get_admin_list_display(cls):
		return [
			'zone',
			'date',
			'echeance',
			'parametre',
			'prevision_preview',
		]

	@classmethod
	def get_admin_list_filter(cls):
		return [
			'zone',
			'parametre',
			{'field_name': 'date', 'widget': DateRangePickerWidget},
			'echeance',
		]

	@classmethod
	def get_admin_search_fields(cls):
		return {
			'zone__name': {'partial_match': True},
			'parametre__name': {'partial_match': True},
			'prevision': {'partial_match': True},
		}

	def prevision_preview(self):
		return self.prevision[:100] + "..." if len(self.prevision) > 100 else self.prevision
	prevision_preview.short_description = _("Aperçu prévision")
	def __str__(self):
		return f'Prevision de {self.parametre} pour {self.zone} le {str(self.date)}, echeance : {self.echeance}'