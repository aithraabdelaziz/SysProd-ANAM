from django.utils.module_loading import import_string

from wagtail import blocks
from wagtail.blocks import StructValue
from wagtail.contrib.table_block.blocks import TableBlock
from wagtail.images.blocks import ImageChooserBlock
from forecast.models import Forecast,Zone,Variable
from observation.models import Observation,Station
from bulletins.models import Echeance
from datetime import date
from pprint import pprint

from bulletins.models import Localites,Echeances,Parametres
from chartmet.models import MapObsConfiguration,MapFcstConfiguration,MapModelConfiguration

from wagtail.snippets.blocks import SnippetChooserBlock
from django.utils.translation import gettext_lazy as _
from django.utils.functional import lazy

from django.core.validators import MinValueValidator, MaxValueValidator
from wagtail_color_panel.blocks import NativeColorBlock


from chartmet.models import MapSpatialConfiguration
from wagtail.blocks import IntegerBlock

# from chartmet.utils import get_parameters, get_functions, get_parameters_decade
# models_list = [('gfs_model','GFS 0.25')]
# parametres_list = [('1','1'),('2','2')] #[(p["grib_variable"], p["parameter_name"]) for p in get_parameters(schema='gfs_model').to_dict(orient='records')]
# functions_list = [('1','1'),('2','2')] #[(f["function"], f["name"]) for f in get_functions(schema='gfs_model').to_dict(orient='records')]
# parametres_decades = [('1','1'),('2','2')] #[(p['parameter'][0],p['parameter'][0]) for p in get_parameters_decade(schema='climat',table='parameters_decades').to_dict(orient='records')]

# from chartmet.utils import get_parameters, get_functions, get_parameters_decade
# models_list = [('gfs_model','GFS 0.25')]
# parametres_list = [(p["grib_variable"], p["parameter_name"]) for p in get_parameters(schema='gfs_model').to_dict(orient='records')]
# functions_list = [(f["function"], f["name"]) for f in get_functions(schema='gfs_model').to_dict(orient='records')]
# parametres_decades = [(p['parameter'][0],p['parameter'][0]) for p in get_parameters_decade(schema='climat',table='parameters_decades').to_dict(orient='records')]
from .choices import (
    get_model_choices,
    get_parametres_choices,
    get_functions_choices,
    get_parametres_decades_choices,
)

class LazyChoiceBlock(blocks.ChoiceBlock):
    def __init__(self, get_choices, **kwargs):
        self.get_choices = get_choices
        super().__init__(choices=[], **kwargs)

    def get_form_state(self, value):
        self.choices = self.get_choices()
        return super().get_form_state(value)

    def clean(self, value):
        self.choices = self.get_choices()
        return super().clean(value)

#############################################################
#################          Styles        ####################
#############################################################
class StyleTitleBlock(blocks.StructBlock):
    title_color = NativeColorBlock(
        default='#000000',
        label="Couleur du titre"
    )
    title_size = blocks.FloatBlock(
        default=14,
        help_text="taille de la police du titre(5 à 27)",
        label='Police du titre',
        validators=[MinValueValidator(5.0), MaxValueValidator(74.0)]
    )
    title_bold = blocks.BooleanBlock(required=False,default=True, help_text="Mettre le titre en gras")
    title_underline = blocks.BooleanBlock(required=False, help_text="Souligner le titre")
    class Meta:
        label = "Style des titres"
        icon = "paintbrush"
        collapsed = True
class StyleTableBlock(blocks.StructBlock):
    table_color = NativeColorBlock(
        default='#000000',
        label="Couleur du texte tableau"
    )
    table_size = blocks.FloatBlock(
        default=12,
        help_text="taille de la police du tableau(5 à 54)",
        label='Police',
        validators=[MinValueValidator(5.0), MaxValueValidator(54.0)]
    )
    table_bold = blocks.BooleanBlock(required=False, help_text="Mettre le texte du tableau en gras")

    class Meta:
        label = "Style des tables"
        icon = "paintbrush"
        collapsed = True
class StyleTexteBlock(blocks.StructBlock):
    bg_color = NativeColorBlock(
        default='#FFFFFF',
        label="couleur d'arrière plan"
    )
    # text_size = blocks.FloatBlock(
    #     default=14,
    #     help_text="Taille de la police du texte (5 à 54)",
    #     label="Taille du texte",
    #     validators=[MinValueValidator(5.0), MaxValueValidator(54.0)]
    # )
    text_align = blocks.ChoiceBlock(
        choices=[
            ('1', 'Gauche'),
            ('0', 'Centre'),
            ('2', 'Droite'),
        ],
        default='left',
        label="Position du texte"
    )
    width_percentage = blocks.IntegerBlock(
        default=100,
        help_text="Largeur occupée par le texte (%)",
        label="Largeur (%)",
        validators=[MinValueValidator(10), MaxValueValidator(100)]
    )
    # text_bold = blocks.BooleanBlock(required=False, label="Gras")
    # text_italic = blocks.BooleanBlock(required=False, label="Italique")
    # text_underline = blocks.BooleanBlock(required=False, label="Souligné")

    class Meta:
        label = "Style du texte"
        icon = "pilcrow"
        collapsed = True
class StyleImageBlock(blocks.StructBlock):
    image_width = blocks.IntegerBlock(
        default=100,
        help_text="Largeur de l’image en pourcentage (10 à 100)",
        label="Largeur (%)",
        validators=[MinValueValidator(10), MaxValueValidator(100)]
    )
    image_align = blocks.ChoiceBlock(
        choices=[
            ('1', 'Gauche'),
            ('0', 'Centre'),
            ('2', 'Droite'),
        ],
        default='center',
        label="Position de l'image"
    )

    class Meta:
        label = "Style de l’image"
        icon = "image"
        collapsed = True
#############################################################
##############         content block      ###################
#############################################################
class TitleTextBlock(blocks.StructBlock):
    title = blocks.CharBlock(max_length=100,required=False, help_text="Titre de la section" )
    type_block='Forecast'
    periode = blocks.BooleanBlock(required=False, help_text="Inclure la période dans le titre")
    zone = SnippetChooserBlock(Zone, required=False, label="Zone")
    echeance = SnippetChooserBlock(Echeance, required=False, label="Echéance")
    parametre = SnippetChooserBlock(Variable, required=False, label="Paramètre")
    texte = blocks.RichTextBlock(required=False, label="Texte")
    style_title = StyleTitleBlock()
    style_text = StyleTexteBlock()
    
    def get_data(self,date_bult,value):
        # Récupérez les données du modèle Forecast
        parametre=value.get('parametre')
        zone=value.get('zone')
        echeance=value.get('echeance').echeance
        try:
            prevision = Forecast.objects.get(
                date=date_bult,
                parametre=parametre,
                zone=zone,
                echeance=echeance
            ).prevision
            prevision_id = Forecast.objects.get(
                date=date_bult,
                parametre=parametre,
                zone=zone,
                echeance=echeance
            ).id
        except Forecast.DoesNotExist:
            prevision = ''  # ou une valeur par défaut
            prevision_id = 0
        return prevision,prevision_id,parametre,zone,echeance

    class Meta:
        icon = "placeholder"
        label = "Titre, Text"
        template = "streams/block-title-text.html"
        collapsed = True

class ObsImageBlock(blocks.StructBlock):
    echeance = SnippetChooserBlock(Echeance, required=False, label="Echéance")
    carte = SnippetChooserBlock(MapObsConfiguration, required=False, label="Carte temps sensible")
    url_img = blocks.URLBlock(required=False, help_text="External link to where the image can be found and downloaded, the images should be in folder yyyy/mm/dd/obs_map.png")
    titre_legende = blocks.CharBlock(max_length=100,required=False,help_text="Légende de la figure" )
    style_img= StyleImageBlock()
    class Meta:
        icon = "placeholder"
        label = "Carte Obs"
        template = "streams/block-image.html"
        collapsed = True
class ObsTitleTextImageBlock(ObsImageBlock,TitleTextBlock):
    class Meta:
        icon = "placeholder"
        label = "Titre, Text et Carte Obs"
        template = "streams/block-title-text-image.html"
        collapsed = True
class FcstImageBlock(blocks.StructBlock):
    echeance = SnippetChooserBlock(Echeance, required=False, label="Echéance")
    carte = SnippetChooserBlock(MapFcstConfiguration, required=False, label="Carte temps sensible")
    url_img = blocks.URLBlock(required=False, help_text="External link to where the image can be found and downloaded, the images should be in folder yyyy/mm/dd/obs_map.png")
    titre_legende = blocks.CharBlock(max_length=100,required=False,help_text="Légende de la figure" )
    style_img= StyleImageBlock()

    class Meta:
        icon = "placeholder"
        label = "Carte Prévi"
        template = "streams/block-image.html"
        collapsed = True
class FcstTitleTextImageBlock(FcstImageBlock,TitleTextBlock):
    carte = SnippetChooserBlock(MapFcstConfiguration, required=False, label="Carte temps sensible")
    url_img = blocks.URLBlock(required=False, help_text="External link to where the image can be found and downloaded, the images should be in folder yyyy/mm/dd/obs_map.png")
    titre_legende = blocks.CharBlock(max_length=100,required=False,help_text="Légende de la figure" )
    style_img= StyleImageBlock()

    class Meta:
        icon = "placeholder"
        label = "Titre, Text et Carte Prévi"
        template = "streams/block-title-text-image.html"
        collapsed = True

class ModelImageBlock(blocks.StructBlock):
    
    modelmap = SnippetChooserBlock(MapModelConfiguration, required=False, label="Carte modèle")
    url_img = blocks.URLBlock(required=False, help_text="External link to where the image can be found and downloaded, the images should be in folder yyyy/mm/dd/obs_map.png")
    titre_legende = blocks.CharBlock(max_length=100,required=False,help_text="Légende de la figure" )
    modele = blocks.ChoiceBlock(choices=get_model_choices(), help_text="Modèle numérique du temps", label="MNT")
    model_parametre = blocks.ChoiceBlock(choices=get_parametres_choices(), help_text="Paramètre à projeter sur la carte", label="Paramètre du modèle")
    fonction = blocks.ChoiceBlock(choices=get_functions_choices(), help_text="Fonction à appliquer sur le paramètre", label="Fonction")
    # modele = LazyChoiceBlock(get_choices=get_model_choices, help_text="Modèle numérique du temps", label="MNT")
    # model_parametre = LazyChoiceBlock(get_choices=get_parametres_choices, help_text="Paramètre à projeter", label="Paramètre du modèle")
    # fonction = LazyChoiceBlock(get_choices=get_functions_choices, help_text="Fonction à appliquer", label="Fonction")
    
    fentre_calcul = SnippetChooserBlock(Echeance, required=False, label="Fenêtre de calcul")

    style_img= StyleImageBlock()

    class Meta:
        icon = "placeholder"
        label = "Carte modèle"
        template = "streams/block-image.html"
        collapsed = True
class ModelTitleTextImageBlock(ModelImageBlock,TitleTextBlock):
    class Meta:
        icon = "placeholder"
        label = "Titre, Text et Carte modèle"
        template = "streams/block-title-text-image.html"
        collapsed = True
class TwoCarteModelBlock(blocks.StructBlock):
    carte_1 = ModelImageBlock(label="Première carte")
    carte_2 = ModelImageBlock(label="Deuxième carte")

    class Meta:
        icon = "placeholder"
        label = "Deux Cartes Modèle"
        template = "streams/block-two-images.html"
        collapsed = True

def get_parametres_decades():
    from observation.models import ClimatDecades 
    queryset = ClimatDecades.objects.values_list('source', 'parameter').distinct()
    return [(f"{s};{p}", f"{s} : {p}") for s, p in queryset]
class CarteDecadeBlock(blocks.StructBlock): 
    map_obs = SnippetChooserBlock(MapModelConfiguration, required=False, label="Carte")
    url_img = blocks.URLBlock(required=False, help_text="External link to where the image can be found and downloaded, the images should be in folder yyyy/mm/dd/obs_map.png")    
    
    titre_legende = blocks.CharBlock(max_length=100,required=False,help_text="Légende de la figure" )
    parametre_decade = blocks.ChoiceBlock(choices=get_parametres_decades_choices(), help_text="Paramètre à projeter sur la carte", label="Paramètre")
    # parametre_decade = LazyChoiceBlock(get_choices=get_parametres_decades_choices, help_text="Paramètre à projeter", label="Paramètre du modèle")
    fonction = blocks.ChoiceBlock(choices=[('diff','Ecart'),('sum','Cumul'),('mean','Moyenne'),('max','Max'),('min','Min')], default='diff',help_text="Fonction à appliquer sur le paramètre entre decade1 et decade2", label="Fonction")
    decade1 = IntegerBlock(min_value=-2, default=0,max_value=1, label="Décade", help_text="-1 : decade précédente, 0: décade courante, 1 decade à venir")    
    decade2 = IntegerBlock(min_value=-2, default=-1,max_value=1, label="Décade", help_text="-1 : decade précédente, 0: décade courante, 1 decade à venir")    

    style_img= StyleImageBlock()

    class Meta:
        icon = "placeholder"
        label = "Carte Décadaire"
        template = "streams/block-image.html"
        collapsed = True
    # def get_parametres_decades(self):
    #     from observation.models import ClimatDecades
    #     try:
    #         qs = ClimatDecades.objects.values_list('source', 'parameter').distinct()
    #         return [(f"{s};{p}", f"{s}:{p}") for s, p in qs]
    #     except Exception:
    #         return []
# class CarteDecade2Block(blocks.StructBlock):
    
#     map_obs = SnippetChooserBlock(MapModelConfiguration, required=False, label="Carte")
#     url_img = blocks.URLBlock(required=False, help_text="External link to where the image can be found and downloaded, the images should be in folder yyyy/mm/dd/obs_map.png")    
    
#     titre_legende = blocks.CharBlock(max_length=100,required=False,help_text="Légende de la figure" )
#     source = blocks.ChoiceBlock(choices=[('climat','Climatologie'),('gfs_model','GFS0.25')],default='climat', help_text="Climatologie ou données modèle", label="Source")
#     parametre_decade = blocks.ChoiceBlock(choices=get_parametres_decades_choices(), help_text="Paramètre à projeter sur la carte", label="Paramètre")
#     fonction = blocks.ChoiceBlock(choices=[('diff','Ecart'),('sum','Cumul'),('mean','Moyenne'),('max','Max'),('min','Min')], default='diff',help_text="Fonction à appliquer sur le paramètre entre decade1 et decade2", label="Fonction")
#     decade1 = IntegerBlock(min_value=-2, default=0,max_value=1, label="Décade", help_text="-1 : decade précédente, 0: décade courante, 1 decade à venir")    
#     decade2 = IntegerBlock(min_value=-2, default=-1,max_value=1, label="Décade", help_text="-1 : decade précédente, 0: décade courante, 1 decade à venir")    

#     style_img= StyleImageBlock()

#     class Meta:
#         icon = "placeholder"
#         label = "Carte Décadaire"
#         template = "streams/block-image.html"
#         collapsed = True
class TwoCarteDecadelock(blocks.StructBlock):
    carte_1 = CarteDecadeBlock(label="Première carte")
    carte_2 = CarteDecadeBlock(label="Deuxième carte")

    class Meta:
        icon = "placeholder"
        label = "Deux Cartes Décadaires"
        template = "streams/block-two-images.html"
        collapsed = True
class ObsTitleTextCarteDecadeBlock(CarteDecadeBlock,TitleTextBlock):
    class Meta:
        icon = "placeholder"
        label = "Titre, Text et Carte Decadaire"
        template = "streams/block-title-text-image.html"
        collapsed = True

class CarteSpatialBlock(blocks.StructBlock):
    
    map_obs = SnippetChooserBlock(MapSpatialConfiguration, required=False, label="Carte spatialisée preconfigurée")
    url_img = blocks.URLBlock(required=False, help_text="External link to where the image can be found and downloaded, the images should be in folder yyyy/mm/dd/obs_map.png")
    titre_legende = blocks.CharBlock(max_length=100,required=False,help_text="Légende de la figure" )
    stations = SnippetChooserBlock(Localites, required=False, label="Stations de la carte")
    
    style_img= StyleImageBlock()

    class Meta:
        icon = "placeholder"
        label = "Carte Spatialisée"
        template = "streams/block-image.html"
        collapsed = True
class TwoCarteSpatialBlock(blocks.StructBlock):
    carte_1 = CarteSpatialBlock(label="Première carte")
    carte_2 = CarteSpatialBlock(label="Deuxième carte")

    class Meta:
        icon = "placeholder"
        label = "Deux Cartes Spatialisées"
        template = "streams/block-two-images.html"
        collapsed = True
class ObsTitleTextCarteSpatialBlock(CarteSpatialBlock,TitleTextBlock):
    
    class Meta:
        icon = "placeholder"
        label = "Titre, Text et Carte Spatialisée"
        template = "streams/block-title-text-image.html"
        collapsed = True

class BesoinsEauBlock(blocks.StructBlock):
    title = blocks.CharBlock(max_length=100,required=False,help_text="Titre de la section" ) 
    format_contenu = blocks.ChoiceBlock(choices=[('html','HTML'),('png','PNG')],default='html', help_text="format des tableaux de besoins en eau", label="Fromat")
    url_img= blocks.URLBlock(required=False, help_text="lien externe pour integrer les besoins en eau (intègre tous les fichier (.html ou .png) selon le format choisi")
    texte = blocks.RichTextBlock(required=False, label="Texte")
    style_img= StyleImageBlock()
    style_title = StyleTitleBlock()
    style_text = StyleTexteBlock()
    class Meta:
        icon = "placeholder"
        label = "Besoins en eau"
        template = "streams/block-contenu-html.html"
        collapsed = True

class NDVIBlock(blocks.StructBlock):
    type_carte = blocks.ChoiceBlock(choices=[('anomaly','Anomalie'),('diff','Ecart')],default='anomaly', help_text="choisir entre les cartes NDVI disponibles", label="Type carte")
    url_img= blocks.URLBlock(required=False, help_text="lien externe pour integrer les carte NDVI (.png)")
    titre_legende = blocks.CharBlock(max_length=100,required=False,help_text="Légende de la figure" )
    style_img= StyleImageBlock()
    class Meta:
        icon = "placeholder"
        label = "Carte NDVI"
        template = "streams/block-image.html"
        collapsed = True
class ObsTitleTextCarteNDVIBlock(NDVIBlock,TitleTextBlock):
    class Meta:
        icon = "placeholder"
        label = "Titre, Text et Carte NDVI"
        template = "streams/block-title-text-image.html"
        collapsed = True

class ObsTableBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=False)
    type_block='Observation'
    periode = blocks.BooleanBlock(required=False, help_text="Inclure la période dans le titre")
    stations = blocks.ListBlock(
        SnippetChooserBlock(Station),
        label="Stations"
    )
    heures = blocks.ListBlock(
        SnippetChooserBlock(Echeance),
        label="Echeances"
    )
    parametres = blocks.ListBlock(
        SnippetChooserBlock(Variable),
        label="Parametres"
    )
    texte = blocks.RichTextBlock(required=False, label="Texte")
    style_title = StyleTitleBlock()
    style_table = StyleTableBlock()

    def get_obs_data(self,date_bult,parametres, zones,echeances):
        observations = Observation.objects.filter(date=date_bult,parametre__in=parametres,station__in=zones,heure__in=echeances).values_list(
        'id','date', 'station', 'parametre', 'heure', 'observation'
        )#.order_by('date', 'zone__name', 'parametre__name', 'echeance')
        ### Organisez les données par zone et par paramètre
        data = {}
        echeances_obj = Echeance.objects.filter(echeance__in=echeances)
        for z in zones :
            data[z.id] = {}
            for p in parametres :
                data[z.id][p.id]={}
                for e in echeances_obj :
                    data[z.id][p.id][e.id]=(0,'None')

        for id_obs, date, zone, parametre, echeance, observation in observations:
            echeance = Echeance.objects.get(echeance=echeance)
            if zone not in data:
                data[zone] = {}
            if parametre not in data[zone]:
                data[zone][parametre] = {}

            data[zone][parametre][echeance.id] = (id_obs,observation)
        return data
    class Meta:
        icon = "table"
        label = "Obs Table/station/paramètre"
        template = "streams/block-observation-table.html"
        collapsed = True
class FcstTableBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=False)
    type_block='Forecast'
    periode = blocks.BooleanBlock(required=False, help_text="Inclure la période dans le titre")
    zones = blocks.ListBlock(
        SnippetChooserBlock(Zone),
        label="Localités"
    )
    echeances = blocks.ListBlock(
        SnippetChooserBlock(Echeance),
        label="Echeances"
    )
    parametres = blocks.ListBlock(
        SnippetChooserBlock(Variable),
        label="Parametres"
    )
    texte = blocks.RichTextBlock(required=False, label="Texte")
    style_title = StyleTitleBlock()
    style_table = StyleTableBlock()

    def get_forecast_data(self,date_bult,parametres, zones,echeances):
        forecasts = Forecast.objects.filter(date=date_bult,parametre__in=parametres,zone__in=zones,echeance__in=echeances).values_list(
            'id','date', 'zone', 'parametre', 'echeance', 'prevision'
        )

        data = {}
        echeances_obj = Echeance.objects.filter(echeance__in=echeances)
        for z in zones :
            data[z.id] = {}
            for p in parametres :
                data[z.id][p.id]={}
                for e in echeances_obj :
                    data[z.id][p.id][e.id]=(0,'None')

        for id_fcst, date, zone, parametre, echeance, prevision in forecasts:
            echeance = Echeance.objects.get(echeance=echeance)
            if zone not in data:
                data[zone] = {}
            if parametre not in data[zone]:
                data[zone][parametre] = {}

            data[zone][parametre][echeance.id] = (id_fcst,prevision)
        return data
        
    class Meta:
        icon = "table"
        label = "Prev Table/localité/paramètre"
        template = "streams/block-forecast-table.html"
        collapsed = True
