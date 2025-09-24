# models.py
from forecast.models import Zone
from observation.models import Station  
import os
from django.db import models
from wagtail.search import index

from django.conf import settings
import warnings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from wagtail.models import ClusterableModel
from wagtail.admin.panels import (
    FieldPanel, MultiFieldPanel, ObjectList, TabbedInterface
)
from colorfield.fields import ColorField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, ObjectList, TabbedInterface
from django.core.files import File

from django.utils.safestring import mark_safe
from wagtail.snippets.models import register_snippet

from matplotlib.colors import ListedColormap, BoundaryNorm
from bulletins.models import Echeance
from forecast.models import Variable

from django import forms


from wagtail.models import Site
from administrate.models import OrganisationSetting
def default_descriptions():
    fr, to = -15, 45  
    colors_dict = {}
    for class_label in range(fr, to):
        gradient_factor = (class_label - fr) / (to - fr)
        r = int((1 - gradient_factor) * 71 + gradient_factor * 189)
        g = int((1 - gradient_factor) * 103 + gradient_factor * 39)
        b = int((1 - gradient_factor) * 183 + gradient_factor * 90)
        hex_color = "#{:02x}{:02x}{:02x}".format(r, g, b)
        colors_dict[str(class_label)] = {
            'description': f'Class {class_label}',
            'color': hex_color
        }
    return colors_dict
@register_snippet
class Legend(index.Indexed,models.Model):
    name = models.CharField(max_length=150, unique=True, null=False,help_text="Nom de la légende")
    title = models.CharField(max_length=150,blank=True, null=True,help_text="titre affiché sur la carte")
    active = models.BooleanField(default=True, help_text='Activate or disactivate the legend')
    descriptions = models.JSONField(
        default=default_descriptions,
        blank=True,
        help_text="Classes, descriptions et couleurs (dict JSON)"
    )
    search_fields = [
        index.SearchField('name', boost=2),
        index.SearchField('title'),
        index.AutocompleteField('name'),
        index.AutocompleteField('title')
    ]
    class Meta:
        permissions = [
            ("edit_legends", "Can edit legends"),
        ]
    def __str__(self):
        return self.name
    def get_cmap(self):
        desc = self.descriptions
        levels = []
        colors = []
        class_labels = []
        for l,v in sorted(desc.items(), key=lambda x: float(x[0])):
            levels.append(float(l))
            colors.append(v['color'])
            class_labels.append(v['description'][:20])
        cmap_custom = ListedColormap(colors)
        norm = BoundaryNorm(boundaries=levels, ncolors=len(colors))
         
        return levels,cmap_custom,norm, class_labels


def shapefile_upload_path(instance, filename):
    return os.path.join("shapefiles", filename)

class BaseMapConfiguration(index.Indexed,ClusterableModel):
    name = models.CharField(max_length=100, null=False, unique=True, default='Carte par defaut')
    # zip_file = models.FileField(
    #     null=True,
    #     blank=True,
    #     upload_to='shapefiles/',
    #     help_text="Fichier ZIP contenant le shapefile."
    # )
    zip_file = models.ForeignKey(
        'wagtaildocs.Document',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
        help_text="Shapefile associer à la carte (.zip)"
    )
    logo = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Logo ou icône à afficher sur la carte"
    )
    legende_1=models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Légende à afficher dans la carte (en haut à gauche)"
    )
    taille_legende_1 = models.FloatField(
        default=5,
        validators=[MinValueValidator(2), MaxValueValidator(20)],
        help_text="Taille de la légende de 2% à 20%"
    )

    legende_2=models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Légende à afficher dans la carte (en bas à droite)"
    )
    taille_legende_2 = models.FloatField(
        default=5,
        validators=[MinValueValidator(2), MaxValueValidator(20)],
        help_text="Taille de la légende de 2% à 20%"
    )

    legende_3=models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Légende à afficher dans la carte (en haut à droite)"
    )
    taille_legende_3 = models.FloatField(
        default=5,
        validators=[MinValueValidator(2), MaxValueValidator(20)],
        help_text="Taille de la légende de 2% à 20%"
    )


    # Style de carte
    facecolor = ColorField(default='#FFFFFF', help_text="Couleur de fond général de la carte.")
    color_shape = ColorField(default='#bef9ff', help_text="Couleur de remplissage des zones.")
    intern_edgecolor = ColorField(default='#808080', help_text="Couleur des lignes internes.")
    intern_linewidth = models.FloatField(
        default=0.3,
        validators=[MinValueValidator(0.1), MaxValueValidator(5.0)],
        help_text="Épaisseur des lignes internes (0.1 à 5.0)"
    )
    border_edgecolor = ColorField(default='#000000', help_text="Couleur du contour extérieur.")
    border_linewidth = models.FloatField(
        default=0.8,
        validators=[MinValueValidator(0.1), MaxValueValidator(10.0)],
        help_text="Épaisseur du contour extérieur (0.1 à 10.0)"
    )
    min_dist = models.FloatField(
        default=50,
        validators=[MinValueValidator(10.0), MaxValueValidator(300.0)],
        help_text="Distance minimale entre étiquettes (10 à 300km)."
    )

    # Titre
    titre_carte = models.CharField(max_length=255,null=True,blank=True)
    titre_date = models.BooleanField(default=False, help_text="Afficher la date sous le titre.")
    titre_fontsize = models.PositiveIntegerField(
        default=14,
        validators=[MinValueValidator(8), MaxValueValidator(48)],
        help_text="Taille de police du titre (8 à 48)."
    )
    titre_pad = models.PositiveIntegerField(
        default=20,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Marge verticale sous le titre (0 à 100 px)."
    )
    titre_backgroundcolor = ColorField(default='#FFFFFF', help_text="Couleur de fond du titre.")

    active = models.BooleanField(default=False, help_text="Activer cette configuration.")


    ##### paramètres à afficher dans la carte :
    temps_sensible = models.BooleanField(default=True, help_text="Afficher les picto du Temps Sensible")
    tmax = models.BooleanField(default=True, help_text="Afficher les Tmax")
    tmin = models.BooleanField(default=True, help_text="Afficher les Tmin")
    pluie = models.BooleanField(default=False, help_text="Afficher la Pluie")
    pression = models.BooleanField(default=False, help_text="Afficher la Pression")
    vent = models.BooleanField(default=False, help_text="Afficher le Vent")

    search_fields = [
        index.SearchField('name', boost=2),
        index.SearchField('titre_carte'),
        index.AutocompleteField('name'),
        index.AutocompleteField('titre_carte')
    ]
    class Meta:
        abstract = True

    def clean(self):
        if self.zip_file:
            ext = self.zip_file.file.name.lower().split('.')[-1]
            if ext not in ['zip']:
                raise ValidationError("Seuls les fichiers zip sont autorisés.")

    def save(self, *args, **kwargs):
        # if self.active:
        #     self.__class__.objects.exclude(id=self.id).update(active=False)
        if not self.zip_file:
            try:
                site = Site.objects.get(is_default_site=True)
                org_settings = OrganisationSetting.for_site(site)
                if org_settings and org_settings.shapefile_zip:
                    self.zip_file = org_settings.shapefile_zip
            except OrganisationSetting.DoesNotExist:
                default_path = os.path.join(settings.MEDIA_ROOT, 'shapefiles/provinces.zip')
                if os.path.exists(default_path):
                    with open(default_path, 'rb') as f:
                        wrapped_file = File(f)
                        new_doc = Document.objects.create(
                            title='Shapefile Provinces',
                            file=wrapped_file
                        )
                        self.zip_file = new_doc
        
        if not self.logo:
            try:
                site = Site.objects.get(is_default_site=True)
                org_settings = OrganisationSetting.for_site(site)
                if org_settings and org_settings.logo:
                    self.logo = org_settings.logo
            except OrganisationSetting.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
from django_select2.forms import ModelSelect2MultipleWidget, Select2MultipleWidget

class MapObsConfiguration(BaseMapConfiguration):
    stations = models.ManyToManyField(
        Station, blank=True, related_name='map_configurations',
        help_text="Stations utilisées pour les cartes d'observation."
    )

    edit_handler = TabbedInterface([
        ObjectList([
            MultiFieldPanel([
                FieldPanel('name'),
                FieldPanel('active'),
                FieldPanel('logo'),
                FieldPanel('zip_file'),
                # FieldPanel('shapefile'),
            ], heading="Général"),
        ], heading="Configuration générale"),

        ObjectList([
            MultiFieldPanel([
                FieldPanel('facecolor'),
                FieldPanel('color_shape'),
                FieldPanel('intern_edgecolor'),
                FieldPanel('intern_linewidth'),
                FieldPanel('border_edgecolor'),
                FieldPanel('border_linewidth'),
                FieldPanel('min_dist'),
            ], heading="Style de la carte"),
        ], heading="Style"),

        ObjectList([
            MultiFieldPanel([
                FieldPanel('titre_carte'),
                FieldPanel('titre_date'),
                FieldPanel('titre_fontsize'),
                FieldPanel('titre_pad'),
                FieldPanel('titre_backgroundcolor'),
            ], heading="Titre de la carte"),
        ], heading="Titre"),
        
        ObjectList([
            MultiFieldPanel([
                FieldPanel('legende_1'),
                FieldPanel('taille_legende_1'),
            ], heading="Légende 1"),
            MultiFieldPanel([
                FieldPanel('legende_2'),
                FieldPanel('taille_legende_2'),
            ], heading="Légende 2"),
            MultiFieldPanel([
                FieldPanel('legende_3'),
                FieldPanel('taille_legende_3'),
            ], heading="Légende 3"),
        ], heading="Légendes"),

        ObjectList([
            MultiFieldPanel([
                # FieldPanel('stations', widget=forms.CheckboxSelectMultiple),
                # FieldPanel('stations')#, widget=ModelSelect2MultipleWidget(model=Station, search_fields=['name__icontains','wigos_id__icontains']))
                # FieldPanel('stations', widget=Select2MultipleWidget(attrs={
                #     'data-placeholder': 'Sélectionnez des stations...',
                #     'data-tags': 'true',
                #     'data-minimum-input-length': 2
                # }))
                FieldPanel('stations')
            ], heading="Localités liées"),
        ], heading="Localités"),

        ObjectList([
            MultiFieldPanel([
                FieldPanel('temps_sensible'),
                FieldPanel('tmax'),
                FieldPanel('tmin'),
                FieldPanel('pluie'),
                FieldPanel('pression'),
                FieldPanel('vent'),
            ], heading="Paramètres"),
        ], heading="Paramètres"),

    ])
    class Meta:
        permissions = [
            ("edit_mapobs", "Can edit Map Observation"),
        ]

class MapFcstConfiguration(BaseMapConfiguration):
    zones = models.ManyToManyField(
        Zone, blank=True, related_name='map_configurations',
        limit_choices_to={'category': 'ville'},
        help_text="Zones utilisées pour les cartes de type prévision."
    )

    edit_handler = TabbedInterface([
        ObjectList([
            MultiFieldPanel([
                FieldPanel('name'),
                FieldPanel('active'),
                FieldPanel('logo'),
                FieldPanel('zip_file'),
            ], heading="Général"),
        ], heading="Configuration générale"),

        ObjectList([
            MultiFieldPanel([
                FieldPanel('facecolor'),
                FieldPanel('color_shape'),
                FieldPanel('intern_edgecolor'),
                FieldPanel('intern_linewidth'),
                FieldPanel('border_edgecolor'),
                FieldPanel('border_linewidth'),
                FieldPanel('min_dist'),
            ], heading="Style de la carte"),
        ], heading="Style"),

        ObjectList([
            MultiFieldPanel([
                FieldPanel('titre_carte'),
                FieldPanel('titre_date'),
                FieldPanel('titre_fontsize'),
                FieldPanel('titre_pad'),
                FieldPanel('titre_backgroundcolor'),
            ], heading="Titre de la carte"),
        ], heading="Titre"),

         ObjectList([
            MultiFieldPanel([
                FieldPanel('legende_1'),
                FieldPanel('taille_legende_1'),
            ], heading="Légende 1"),
            MultiFieldPanel([
                FieldPanel('legende_2'),
                FieldPanel('taille_legende_2'),
            ], heading="Légende 2"),
            MultiFieldPanel([
                FieldPanel('legende_3'),
                FieldPanel('taille_legende_3'),
            ], heading="Légende 3"),
        ], heading="Légendes"),

        ObjectList([
            MultiFieldPanel([
                FieldPanel('zones'),
            ], heading="Localités liées"),
        ], heading="Localités"),

        ObjectList([
            MultiFieldPanel([
                FieldPanel('temps_sensible'),
                FieldPanel('tmax'),
                FieldPanel('tmin'),
                FieldPanel('pluie'),
                FieldPanel('pression'),
                FieldPanel('vent'),
            ], heading="Paramètres"),
        ], heading="Paramètres"),
    ])

    class Meta:
        permissions = [
            ("edit_mapfcst", "Can edit Map Forecast"),
        ]


from django.core.exceptions import ValidationError
from .constantes import *

class MapModelConfiguration(ClusterableModel):
    name = models.CharField(
        max_length=100,
        null=False,
        unique=True,
        default='Carte par défaut',
        verbose_name="Nom de la configuration"
    )

    # zip_file = models.FileField(
    #     null=True,
    #     blank=True,
    #     upload_to=shapefile_upload_path,
    #     help_text="Fichier ZIP contenant le shapefile.",
    #     verbose_name="Fichier Shapefile (ZIP)"
    # )
    zip_file = models.ForeignKey(
        'wagtaildocs.Document',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
        help_text="Shapefile associer à la carte (.zip)"
    )
    logo = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Logo ou icône à afficher sur la carte"
    )

    # Apparence générale
    facecolor = ColorField(default='#FFFFFF', help_text="Couleur de fond général de la carte.", verbose_name="Couleur de fond")
    intern_edgecolor = ColorField(default='#808080', help_text="Couleur des lignes internes.", verbose_name="Couleur des lignes internes")
    intern_linewidth = models.FloatField(
        default=0.3,
        validators=[MinValueValidator(0.1), MaxValueValidator(5.0)],
        help_text="Épaisseur des lignes internes (0.1 à 5.0)",
        verbose_name="Épaisseur des lignes internes"
    )
    border_edgecolor = ColorField(default='#000000', help_text="Couleur du contour extérieur.", verbose_name="Couleur du contour extérieur")
    border_linewidth = models.FloatField(
        default=0.8,
        validators=[MinValueValidator(0.1), MaxValueValidator(10.0)],
        help_text="Épaisseur du contour extérieur (0.1 à 10.0)",
        verbose_name="Épaisseur du contour extérieur"
    )
    min_dist = models.FloatField(
        default=50,
        validators=[MinValueValidator(10.0), MaxValueValidator(300.0)],
        help_text="Distance minimale entre étiquettes (10 à 300 km).",
        verbose_name="Distance minimale entre étiquettes"
    )

    largeur = models.FloatField(
        default=6.4,
        validators=[MinValueValidator(5.0), MaxValueValidator(20.0)],
        help_text="Largeur de la carte (5.1 à 20.0 pouces)",
        verbose_name="Largeur de la carte"
    )

    hauteur = models.FloatField(
        default=6.4,
        validators=[MinValueValidator(5.0), MaxValueValidator(20.0)],
        help_text="Hauteur de la carte (5.1 à 20.0 pouces)",
        verbose_name="Hauteur de la carte"
    )

    
    cmap = models.CharField(
        choices=PALETTES,
        default='viridis',
        help_text=mark_safe(
            'Palette de couleur. '
            'Consultez la <a href="https://matplotlib.org/stable/gallery/color/colormap_reference.html" '
            'target="_blank" rel="noopener noreferrer">référence des palettes matplotlib</a>.'
        ),
        verbose_name="Palette de couleurs"
    )
    legend = models.ForeignKey(Legend, on_delete=models.CASCADE, null=True, blank=True, related_name='legendMap',verbose_name='Légende Personnalisée')

    orientation_palette = models.CharField(
        choices=[('horizontal', 'Horizontale'), ('vertical', 'Verticale')],
        default='horizontal',
        help_text="Orientation de la palette de couleur",
        verbose_name="Orientation de la palette"
    )
    
    interpolate = models.BooleanField(default=True,verbose_name="Interpolation",help_text="Activer l'interpolation",)
    interpolation_method = models.CharField(
        choices=INERTPOLATIONS,
        default='linear',
        verbose_name="Méthode d'interpolation"
    )
    
    extrapolate = models.BooleanField(default=False,verbose_name="Extrapolation",help_text="Activer l'extrapolatiin (Attention: il faut que l'interpolation soit désactivée",)
    extrapolation_method = models.CharField(
        choices=EXTRAPOLATIONS,
        default='linear',
        verbose_name="Méthode d'extrapolation"
    )
    variogram_model = models.CharField(
        choices=VARIOGRAMS,
        default='spherical',
        help_text="Choisir le variogramme Model seulement pour la méthode krigging",
        verbose_name="Variogram model utilisé"
    )
    vario_nugget = models.FloatField(
        null=True,
        blank=True,
        help_text="Nugget : effet de pépite, valeur proche de 0",
        verbose_name="Nugget"
    )
    vario_range = models.FloatField(
        null=True,
        blank=True,
        help_text="Range : portée du variogramme (distance maximale de corrélation)",
        verbose_name="Range"
    )
    vario_sill = models.FloatField(
        null=True,
        blank=True,
        help_text="Sill : palier du variogramme (valeur maximale de la variance)",
        verbose_name="Sill"
    )

    show_color_fill = models.BooleanField(
        default=True,
        help_text="Afficher le remplissage coloré (contourf)",
        verbose_name="Afficher le remplissage coloré"
    )
    show_contour_lines = models.BooleanField(
        default=False,
        help_text="Afficher les isolignes de contour (contour)",
        verbose_name="Afficher les isolignes de contour"
    )
    contour_edgecolor = ColorField(default='#000000', help_text="Couleur des isolignes.", verbose_name="Couleur des isolignes")
    contour_linewidths = models.FloatField(
        default=0.8,
        validators=[MinValueValidator(0.1), MaxValueValidator(3.0)],
        help_text="Épaisseur des isolignes (0.1 à 3.0)",
        verbose_name="Épaisseur des isolignes"
    )
    contour_labelsize = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(3), MaxValueValidator(20)],
        help_text="Taille de police des étiquettes (3 à 20).",
        verbose_name="Taille de la police des étiquettes"
    )
    # Titre
    titre_carte = models.CharField(max_length=255,null=True,blank=True, verbose_name="Titre de la carte")
    titre_date = models.BooleanField(default=False, help_text="Afficher la date sous le titre.", verbose_name="Afficher la date")
    titre_fontsize = models.PositiveIntegerField(
        default=14,
        validators=[MinValueValidator(8), MaxValueValidator(48)],
        help_text="Taille de police du titre (8 à 48).",
        verbose_name="Taille de la police du titre"
    )
    titre_pad = models.PositiveIntegerField(
        default=20,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Marge verticale sous le titre (0 à 100 px).",
        verbose_name="Marge sous le titre"
    )
    titre_backgroundcolor = ColorField(default='#FFFFFF', help_text="Couleur de fond du titre.", verbose_name="Couleur de fond du titre")

    # Localités et statut
    active = models.BooleanField(default=False, help_text="Activer cette configuration.", verbose_name="Activer")
    localites = models.ManyToManyField(
        Zone,
        blank=True,
        related_name='villes_map_configurations',
        limit_choices_to={'category': 'ville'},
        help_text="Zones à afficher comme villes sur la carte",
        verbose_name="Villes affichées"
    )
    MARKERS = [('o','o'), ('.','.'), (',',','), ('x','x'), ('+','+'), ('v','v'), ('^','^'), ('<','<'), ('>','>'), ('s','s'), ('p','p'), ('*','*'), ('h','h'), ('H','H'), ('D','D'), ('d','d'), ('|','|'), ('_','_')]
    symbole = models.CharField(
        choices=MARKERS,
        default='o',
        help_text=mark_safe(
            'symbole utilisé pour représenter les localités'
        ),
        verbose_name="Symboles"
    )
    couleur_symbole = ColorField(default='#000000', help_text="Couleur des symboles.", verbose_name="Couleur des symboles")
    symbole_size = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text="Taille des symboles (1 à 20).",
        verbose_name="Taille des symboles"
    )

    couleur_text = ColorField(default='#000000', help_text="Couleur des étiquettes.", verbose_name="Couleur des étiquettes")

    text_labelsize = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(3), MaxValueValidator(20)],
        help_text="Taille de police des étiquettes (3 à 20).",
        verbose_name="Taille de la police des étiquettes"
    )


    stations = models.ManyToManyField(
        Station,
        blank=True,
        related_name='stations_map_configurations',
        limit_choices_to={'active': True},
        help_text="Stations à afficher sur la carte",
        verbose_name="Stations affichées"
    )
    MARKERS = [('o','o'), ('.','.'), (',',','), ('x','x'), ('+','+'), ('v','v'), ('^','^'), ('<','<'), ('>','>'), ('s','s'), ('p','p'), ('*','*'), ('h','h'), ('H','H'), ('D','D'), ('d','d'), ('|','|'), ('_','_')]
    symbole_station = models.CharField(
        choices=MARKERS,
        default='o',
        help_text=mark_safe(
            'symbole utilisé pour représenter les stations'
        ),
        verbose_name="Symboles stations"
    )
    couleur_symbole_station = ColorField(default='#000000', help_text="Couleur des symboles.", verbose_name="Couleur des symboles")
    symbole_size_station = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text="Taille des symboles (1 à 20).",
        verbose_name="Taille des symboles"
    )

    couleur_text_station = ColorField(default='#000000', help_text="Couleur des étiquettes.", verbose_name="Couleur des étiquettes")

    text_labelsize_station = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(3), MaxValueValidator(20)],
        help_text="Taille de police des étiquettes (3 à 20).",
        verbose_name="Taille de la police des étiquettes"
    )

    class Meta:
        permissions = [
            ("edit_mapmodel", "Can edit Map Model"),
        ]

    def __str__(self):
        return f"{self.name}"

    def clean(self):
        super().clean()
        if not self.show_color_fill and not self.show_contour_lines:
            raise ValidationError("Au moins une des options 'remplissage coloré' ou 'lignes de contour' doit être activée.")
        if self.interpolate and self.extrapolate:
            raise ValidationError("Vous ne pouvez pas activer à la fois l'interpolation et l'extrapolation.")
        # if not self.interpolate and not self.extrapolate:
        #     raise ValidationError("Au moins l'une des methodes Interpolation ou Extrapolation doit être activée.")
        params = [self.vario_nugget, self.vario_range, self.vario_sill]
        all_none = all(v is None for v in params)
        all_filled = all(v is not None for v in params)
        if not (all_none or all_filled):
            raise ValidationError("Tous les paramètres de variogramme (nugget, range, sill) doivent être renseignés ou laissés vides ensemble pour être calculés automatiquement à l'aide d'un schéma de minimisation de norme L1 « soft ».")

        # Si variogramme est 'power' ou 'linear', on ignore les paramètres manuels
        if self.variogram_model in ('power', 'linear'):
            # Réinitialisation
            self.vario_nugget = None
            self.vario_range = None
            self.vario_sill = None

            # Ajout d'un avertissement visible dans l'admin Django
            print(f"Le modèle '{self.variogram_model}' utilise des paramètres par défaut. "
                    "Les champs nugget, range et sill ne doivent pas être renseignés.")
        if self.zip_file:
            ext = self.zip_file.file.name.lower().split('.')[-1]
            if ext not in ['zip']:
                raise ValidationError("Seuls les fichiers zip sont autorisés.")
    def save(self, *args, **kwargs):
        # if self.active:
        #     self.__class__.objects.exclude(id=self.id).update(active=False)
        if not self.zip_file:
            try:
                site = Site.objects.get(is_default_site=True)
                org_settings = OrganisationSetting.for_site(site)
                if org_settings and org_settings.shapefile_zip:
                    self.zip_file = org_settings.shapefile_zip
            except OrganisationSetting.DoesNotExist:
                default_path = os.path.join(settings.MEDIA_ROOT, 'shapefiles/provinces.zip')
                if os.path.exists(default_path):
                    with open(default_path, 'rb') as f:
                        wrapped_file = File(f)
                        new_doc = Document.objects.create(
                            title='Shapefile Provinces',
                            file=wrapped_file
                        )
                        self.zip_file = new_doc
        
        if not self.logo:
            try:
                site = Site.objects.get(is_default_site=True)
                org_settings = OrganisationSetting.for_site(site)
                if org_settings and org_settings.logo:
                    self.logo = org_settings.logo
            except OrganisationSetting.DoesNotExist:
                pass
        super().save(*args, **kwargs)


    edit_handler = TabbedInterface([
        ObjectList([
            MultiFieldPanel([
                FieldPanel('name'),
                FieldPanel('active'),
                FieldPanel('logo'),
                FieldPanel('zip_file'),
            ], heading="Configuration générale"),
        ], heading="Général"),

        ObjectList([
            MultiFieldPanel([
                FieldPanel('largeur'),
                FieldPanel('hauteur'),
                FieldPanel('facecolor'),
                FieldPanel('intern_edgecolor'),
                FieldPanel('intern_linewidth'),
                FieldPanel('border_edgecolor'),
                FieldPanel('border_linewidth'),
                FieldPanel('min_dist'),
            ], heading="Style de la carte"),
        ], heading="Style"),

        ObjectList([
            MultiFieldPanel([
                FieldPanel('cmap'),
                FieldPanel('legend'),
                FieldPanel('orientation_palette'),
                FieldPanel('show_color_fill'),
                FieldPanel('show_contour_lines'),
                FieldPanel('contour_edgecolor'),
                FieldPanel('contour_linewidths'),
                FieldPanel('contour_labelsize'),
            ], heading="Représentation des données"),
        ], heading="Données"),

        ObjectList([
            MultiFieldPanel([
                FieldPanel('interpolate'),
                FieldPanel('interpolation_method'),
            ], heading="Interpolation"),
            MultiFieldPanel([
                FieldPanel('extrapolate'),
                FieldPanel('extrapolation_method'),
            ], heading="Extrapolation"),
            MultiFieldPanel([
                FieldPanel('variogram_model'),
            ], heading="Variaogramme"),
            MultiFieldPanel([
                FieldPanel('vario_nugget'),
                FieldPanel('vario_range'),
                FieldPanel('vario_sill'),
            ], heading="variogram_parameters"),
        ], heading="Extra/Interpolation"),

        ObjectList([
            MultiFieldPanel([
                FieldPanel('titre_carte'),
                FieldPanel('titre_date'),
                FieldPanel('titre_fontsize'),
                FieldPanel('titre_pad'),
                FieldPanel('titre_backgroundcolor'),
            ], heading="Titre de la carte"),
        ], heading="Titre"),

        ObjectList([
            MultiFieldPanel([
                FieldPanel('localites'),
                FieldPanel('symbole'),
                FieldPanel('couleur_symbole'),
                FieldPanel('symbole_size'),
                FieldPanel('couleur_text'),
                FieldPanel('text_labelsize'),
            ], heading="Localités à afficher"),
        ], heading="Localités"),

        ObjectList([
            MultiFieldPanel([
                FieldPanel('stations'),
                FieldPanel('symbole_station'),
                FieldPanel('couleur_symbole_station'),
                FieldPanel('symbole_size_station'),
                FieldPanel('couleur_text_station'),
                FieldPanel('text_labelsize_station'),
            ], heading="Stations à afficher"),
        ], heading="Stations"),

    ])

# @register_snippet
class MapSpatialConfiguration(ClusterableModel):
    name = models.CharField(
        max_length=100,
        null=False,
        unique=True,
        default='Carte par défaut',
        verbose_name="Nom de la configuration"
    )

    # zip_file = models.FileField(
    #     null=True,
    #     blank=True,
    #     upload_to=shapefile_upload_path,
    #     help_text="Fichier ZIP contenant le shapefile.",
    #     verbose_name="Fichier Shapefile (ZIP)"
    # )
    zip_file = models.ForeignKey(
        'wagtaildocs.Document',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
        help_text="Shapefile associer à la carte (.zip)"
    )
    logo = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Logo ou icône à afficher sur la carte"
    )

    # Apparence générale
    facecolor = ColorField(default='#FFFFFF', help_text="Couleur de fond général de la carte.", verbose_name="Couleur de fond")
    intern_edgecolor = ColorField(default='#808080', help_text="Couleur des lignes internes.", verbose_name="Couleur des lignes internes")
    intern_linewidth = models.FloatField(
        default=0.3,
        validators=[MinValueValidator(0.1), MaxValueValidator(5.0)],
        help_text="Épaisseur des lignes internes (0.1 à 5.0)",
        verbose_name="Épaisseur des lignes internes"
    )
    border_edgecolor = ColorField(default='#000000', help_text="Couleur du contour extérieur.", verbose_name="Couleur du contour extérieur")
    border_linewidth = models.FloatField(
        default=0.8,
        validators=[MinValueValidator(0.1), MaxValueValidator(10.0)],
        help_text="Épaisseur du contour extérieur (0.1 à 10.0)",
        verbose_name="Épaisseur du contour extérieur"
    )
    min_dist = models.FloatField(
        default=50,
        validators=[MinValueValidator(10.0), MaxValueValidator(300.0)],
        help_text="Distance minimale entre étiquettes (10 à 300 km).",
        verbose_name="Distance minimale entre étiquettes"
    )

    largeur = models.FloatField(
        default=6.4,
        validators=[MinValueValidator(5.0), MaxValueValidator(20.0)],
        help_text="Largeur de la carte (5.1 à 20.0 pouces)",
        verbose_name="Largeur de la carte"
    )

    hauteur = models.FloatField(
        default=6.4,
        validators=[MinValueValidator(5.0), MaxValueValidator(20.0)],
        help_text="Hauteur de la carte (5.1 à 20.0 pouces)",
        verbose_name="Hauteur de la carte"
    )

    
    cmap = models.CharField(
        choices=PALETTES,
        default='viridis',
        help_text=mark_safe(
            'Palette de couleur. '
            'Consultez la <a href="https://matplotlib.org/stable/gallery/color/colormap_reference.html" '
            'target="_blank" rel="noopener noreferrer">référence des palettes matplotlib</a>.'
        ),
        verbose_name="Palette de couleurs"
    )
    legend = models.ForeignKey(Legend, on_delete=models.CASCADE, null=True, blank=True, related_name='legendMapSpatial',verbose_name='Légende Personnalisée')

    orientation_palette = models.CharField(
        choices=[('horizontal', 'Horizontale'), ('vertical', 'Verticale')],
        default='horizontal',
        help_text="Orientation de la palette de couleur",
        verbose_name="Orientation de la palette"
    )

    interpolate = models.BooleanField(default=False,verbose_name="Interpolation",help_text="Activer l'interpolation",)
    interpolation_method = models.CharField(
        choices=INERTPOLATIONS,
        default='linear',
        verbose_name="Méthode d'interpolation"
    )
    extrapolate = models.BooleanField(default=True,verbose_name="Extrapolation",help_text="Activer l'extrapolatiin (Attention: il faut que l'interpolation soit désactivée",)
    extrapolation_method = models.CharField(
        choices=EXTRAPOLATIONS,
        default='linear',
        verbose_name="Méthode d'extrapolation"
    )

    variogram_model = models.CharField(
        choices=VARIOGRAMS,
        default='spherical',
        help_text="Choisir le variogramme Model seulement pour la méthode krigging",
        verbose_name="Variogram model utilisé"
    )

    vario_nugget = models.FloatField(
        null=True,
        blank=True,
        help_text="Nugget : effet de pépite, valeur proche de 0",
        verbose_name="Nugget"
    )
    vario_range = models.FloatField(
        null=True,
        blank=True,
        help_text="Range : portée du variogramme (distance maximale de corrélation)",
        verbose_name="Range"
    )
    vario_sill = models.FloatField(
        null=True,
        blank=True,
        help_text="Sill : palier du variogramme (valeur maximale de la variance)",
        verbose_name="Sill"
    )

    show_color_fill = models.BooleanField(
        default=True,
        help_text="Afficher le remplissage coloré (contourf)",
        verbose_name="Afficher le remplissage coloré"
    )
    show_contour_lines = models.BooleanField(
        default=False,
        help_text="Afficher les isolignes de contour (contour)",
        verbose_name="Afficher les isolignes de contour"
    )
    contour_edgecolor = ColorField(default='#000000', help_text="Couleur des isolignes.", verbose_name="Couleur des isolignes")
    contour_linewidths = models.FloatField(
        default=0.8,
        validators=[MinValueValidator(0.1), MaxValueValidator(3.0)],
        help_text="Épaisseur des isolignes (0.1 à 3.0)",
        verbose_name="Épaisseur des isolignes"
    )
    contour_labelsize = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(3), MaxValueValidator(20)],
        help_text="Taille de police des étiquettes (3 à 20).",
        verbose_name="Taille de la police des étiquettes"
    )
    # Titre
    titre_carte = models.CharField(max_length=255,null=True,blank=True, verbose_name="Titre de la carte")
    titre_date = models.BooleanField(default=False, help_text="Afficher la date sous le titre.", verbose_name="Afficher la date")
    titre_fontsize = models.PositiveIntegerField(
        default=14,
        validators=[MinValueValidator(8), MaxValueValidator(48)],
        help_text="Taille de police du titre (8 à 48).",
        verbose_name="Taille de la police du titre"
    )
    titre_pad = models.PositiveIntegerField(
        default=20,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Marge verticale sous le titre (0 à 100 px).",
        verbose_name="Marge sous le titre"
    )
    titre_backgroundcolor = ColorField(default='#FFFFFF', help_text="Couleur de fond du titre.", verbose_name="Couleur de fond du titre")

    # Localités et statut
    active = models.BooleanField(default=False, help_text="Activer cette configuration.", verbose_name="Activer")
    localites = models.ManyToManyField(
        Zone,
        blank=True,
        related_name='villes_map_spatial_configurations',
        limit_choices_to={'category': 'ville'},
        help_text="Zones à afficher comme villes sur la carte",
        verbose_name="Villes affichées"
    )
    MARKERS = [('o','o'), ('.','.'), (',',','), ('x','x'), ('+','+'), ('v','v'), ('^','^'), ('<','<'), ('>','>'), ('s','s'), ('p','p'), ('*','*'), ('h','h'), ('H','H'), ('D','D'), ('d','d'), ('|','|'), ('_','_')]
    symbole = models.CharField(
        choices=MARKERS,
        default='o',
        help_text=mark_safe(
            'symbole utilisé pour représenter les localités'
        ),
        verbose_name="Symboles"
    )
    couleur_symbole = ColorField(default='#000000', help_text="Couleur des symboles.", verbose_name="Couleur des symboles")
    symbole_size = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text="Taille des symboles (1 à 20).",
        verbose_name="Taille des symboles"
    )

    couleur_text = ColorField(default='#000000', help_text="Couleur des étiquettes.", verbose_name="Couleur des étiquettes")

    text_labelsize = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(3), MaxValueValidator(20)],
        help_text="Taille de police des étiquettes (3 à 20).",
        verbose_name="Taille de la police des étiquettes"
    )


    stations = models.ManyToManyField(
        Station,
        blank=True,
        related_name='stations_map_spatial_configurations',
        limit_choices_to={'active': True},
        help_text="Stations à afficher sur la carte",
        verbose_name="Stations affichées"
    )
    MARKERS = [('o','o'), ('.','.'), (',',','), ('x','x'), ('+','+'), ('v','v'), ('^','^'), ('<','<'), ('>','>'), ('s','s'), ('p','p'), ('*','*'), ('h','h'), ('H','H'), ('D','D'), ('d','d'), ('|','|'), ('_','_')]
    symbole_station = models.CharField(
        choices=MARKERS,
        default='o',
        help_text=mark_safe(
            'symbole utilisé pour représenter les stations'
        ),
        verbose_name="Symboles stations"
    )
    couleur_symbole_station = ColorField(default='#000000', help_text="Couleur des symboles.", verbose_name="Couleur des symboles")
    symbole_size_station = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text="Taille des symboles (1 à 20).",
        verbose_name="Taille des symboles"
    )

    couleur_text_station = ColorField(default='#000000', help_text="Couleur des étiquettes.", verbose_name="Couleur des étiquettes")

    text_labelsize_station = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(3), MaxValueValidator(20)],
        help_text="Taille de police des étiquettes (3 à 20).",
        verbose_name="Taille de la police des étiquettes"
    )


    source = models.CharField(
        choices=[('observation','Observation')],
        default='observation',
        help_text="Source d'observation",
        verbose_name="Source de données"
    )

    echeance= models.ForeignKey(Echeance, on_delete=models.CASCADE, null=True, related_name='EchMapSpa',verbose_name='Echéance')
    parametre = models.ForeignKey(Variable, on_delete=models.CASCADE, null=True, related_name='ParamMapSpa',verbose_name='Paramètre')

    def __str__(self):
        return f"{self.name}"

    class Meta:
        permissions = [
            ("edit_mapspatial", "Can edit Map Spacialised"),
        ]

    def clean(self):
        super().clean()
        if not self.show_color_fill and not self.show_contour_lines:
            raise ValidationError("Au moins une des options 'remplissage coloré' ou 'lignes de contour' doit être activée.")
        if self.interpolate and self.extrapolate:
            raise ValidationError("Vous ne pouvez pas activer à la fois l'interpolation et l'extrapolation.")
        # if not self.interpolate and not self.extrapolate:
        #     raise ValidationError("Au moins l'une des methodes Interpolation ou Extrapolation doit être activée.")
        params = [self.vario_nugget, self.vario_range, self.vario_sill]
        all_none = all(v is None for v in params)
        all_filled = all(v is not None for v in params)
        if not (all_none or all_filled):
            raise ValidationError("Tous les paramètres de variogramme (nugget, range, sill) doivent être renseignés ou laissés vides ensemble pour être calculés automatiquement à l'aide d'un schéma de minimisation de norme L1 « soft ».")
        # Si variogramme est 'power' ou 'linear', on ignore les paramètres manuels
        if self.variogram_model in ('power', 'linear'):
            # Réinitialisation
            self.vario_nugget = None
            self.vario_range = None
            self.vario_sill = None

            # Ajout d'un avertissement visible dans l'admin Django
            print(f"Le modèle '{self.variogram_model}' utilise des paramètres par défaut. "
                    "Les champs nugget, range et sill ne doivent pas être renseignés.")
        if self.zip_file:
            ext = self.zip_file.file.name.lower().split('.')[-1]
            if ext not in ['zip']:
                raise ValidationError("Seuls les fichiers zip sont autorisés.")
    def save(self, *args, **kwargs):
        # if self.active:
        #     self.__class__.objects.exclude(id=self.id).update(active=False)
        if not self.zip_file:
            try:
                site = Site.objects.get(is_default_site=True)
                org_settings = OrganisationSetting.for_site(site)
                if org_settings and org_settings.shapefile_zip:
                    self.zip_file = org_settings.shapefile_zip
            except OrganisationSetting.DoesNotExist:
                default_path = os.path.join(settings.MEDIA_ROOT, 'shapefiles/provinces.zip')
                if os.path.exists(default_path):
                    with open(default_path, 'rb') as f:
                        wrapped_file = File(f)
                        new_doc = Document.objects.create(
                            title='Shapefile Provinces',
                            file=wrapped_file
                        )
                        self.zip_file = new_doc
        
        if not self.logo:
            try:
                site = Site.objects.get(is_default_site=True)
                org_settings = OrganisationSetting.for_site(site)
                if org_settings and org_settings.logo:
                    self.logo = org_settings.logo
            except OrganisationSetting.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    edit_handler = TabbedInterface([
        ObjectList([
            MultiFieldPanel([
                FieldPanel('source'),
                FieldPanel('echeance'),
                FieldPanel('parametre'),
            ], heading="Data"),
        ], heading="Data"),
        ObjectList([
            MultiFieldPanel([
                FieldPanel('name'),
                FieldPanel('active'),
                FieldPanel('logo'),
                FieldPanel('zip_file'),
            ], heading="Configuration générale"),
        ], heading="Général"),

        ObjectList([
            MultiFieldPanel([
                FieldPanel('largeur'),
                FieldPanel('hauteur'),
                FieldPanel('facecolor'),
                FieldPanel('intern_edgecolor'),
                FieldPanel('intern_linewidth'),
                FieldPanel('border_edgecolor'),
                FieldPanel('border_linewidth'),
                FieldPanel('min_dist'),
            ], heading="Style de la carte"),
        ], heading="Style"),

        ObjectList([
            MultiFieldPanel([
                FieldPanel('cmap'),
                FieldPanel('legend'),
                FieldPanel('orientation_palette'),
                FieldPanel('show_color_fill'),
                FieldPanel('show_contour_lines'),
                FieldPanel('contour_edgecolor'),
                FieldPanel('contour_linewidths'),
                FieldPanel('contour_labelsize'),
            ], heading="Représentation des données"),
        ], heading="Données"),

        ObjectList([
            MultiFieldPanel([
                FieldPanel('interpolate'),
                FieldPanel('interpolation_method'),
            ], heading="Interpolation"),
            MultiFieldPanel([
                FieldPanel('extrapolate'),
                FieldPanel('extrapolation_method'),
            ], heading="Extrapolation"),
            MultiFieldPanel([
                FieldPanel('variogram_model'),
            ], heading="Variaogramme"),
            MultiFieldPanel([
                FieldPanel('vario_nugget'),
                FieldPanel('vario_range'),
                FieldPanel('vario_sill'),
            ], heading="variogram_parameters"),
        ], heading="Extra/Interpolation"),

        ObjectList([
            MultiFieldPanel([
                FieldPanel('titre_carte'),
                FieldPanel('titre_date'),
                FieldPanel('titre_fontsize'),
                FieldPanel('titre_pad'),
                FieldPanel('titre_backgroundcolor'),
            ], heading="Titre de la carte"),
        ], heading="Titre"),

        ObjectList([
            MultiFieldPanel([
                FieldPanel('localites'),
                FieldPanel('symbole'),
                FieldPanel('couleur_symbole'),
                FieldPanel('symbole_size'),
                FieldPanel('couleur_text'),
                FieldPanel('text_labelsize'),
            ], heading="Localités à afficher"),
        ], heading="Localités"),

        ObjectList([
            MultiFieldPanel([
                FieldPanel('stations'),
                FieldPanel('symbole_station'),
                FieldPanel('couleur_symbole_station'),
                FieldPanel('symbole_size_station'),
                FieldPanel('couleur_text_station'),
                FieldPanel('text_labelsize_station'),
            ], heading="Stations à afficher"),
        ], heading="Stations"),

    ])
        
    def __str__(self):
        return self.name



