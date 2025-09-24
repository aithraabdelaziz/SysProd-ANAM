from django.db import models
from forecast.models import Variable, Zone
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from wagtail.admin.panels import FieldPanel, MultiFieldPanel, ObjectList, TabbedInterface

from wagtail.images import get_image_model
from wagtail.images import get_image_model_string

from observation.models import Station
from django.core.exceptions import ValidationError
from colorfield.fields import ColorField
from datetime import datetime, time, timedelta, date



from .constantes import *
class BulletinStyleConfiguration(index.Indexed,models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Nom du style (ex: Style par défaut, Rapport interne...)")
    
    # Police
    font_family = models.CharField(max_length=50, choices=FONT_CHOICES, default="Arial")
    font_size = models.PositiveSmallIntegerField(default=11, help_text="Taille de base du texte (pt)")
    line_height = models.DecimalField(default=1.1, max_digits=3, decimal_places=1, help_text="Interligne")
    text_color = ColorField(default="#000000", help_text="Couleur du texte (hex)")
    background_color = ColorField(default="#FFFFFF", help_text="Couleur de fond (hex)")
    header_text_font_size = models.PositiveSmallIntegerField(default=10, help_text="Taille du texte dans l'en-tête (pt)")
    
    # Page
    orientation = models.CharField(max_length=10, choices=ORIENTATION_CHOICES, default="portrait")
    twoColumns = models.BooleanField(default=False,null=False,help_text="Affichage en deux colonnes")
    margin_top = models.DecimalField(default=1.5, max_digits=4, decimal_places=2, help_text="Marge haut (cm)")
    margin_bottom = models.DecimalField(default=1.5, max_digits=4, decimal_places=2, help_text="Marge bas (cm)")
    margin_left = models.DecimalField(default=1.5, max_digits=4, decimal_places=2, help_text="Marge gauche (cm)")
    margin_right = models.DecimalField(default=1.0, max_digits=4, decimal_places=2, help_text="Marge droite (cm)")
    margin_top_first_page = models.PositiveIntegerField(default=150, help_text="Marge haute de la première page (px)")
    margin_bottom_with_footer = models.PositiveIntegerField(default=100, help_text="Marge basse avec pied de page (px)")

    bordures = models.BooleanField(default=False,null=False,help_text="Bordures de la page")
    border_width = models.PositiveIntegerField(default=6, help_text="Épaisseur de la bordure (px)")
    border_style = models.CharField(max_length=10, choices=BORDER_STYLE_CHOICES, default="double", help_text="Style de bordure CSS")
    border_color = ColorField(default="#000000", help_text="Couleur de bordure")
    border_padding = models.PositiveIntegerField(default=5, help_text="Padding intérieur (px)")
    
    # Pied de page
    page_number_font_size = models.PositiveSmallIntegerField(default=9, help_text="Taille du numéro de page (pt)")
    page_number_color = ColorField(default="#555555", help_text="Couleur du numéro de page (hex)")

    footer_font_family = models.CharField(max_length=50, choices=FONT_CHOICES, default="Georgia")
    footer_font_size = models.PositiveSmallIntegerField(default=12, help_text="Taille de base du texte (pt)")
    footer_line_height = models.DecimalField(default=1.6, max_digits=3, decimal_places=1, help_text="Interligne")
    footer_text_color = ColorField(default="#000000", help_text="Couleur du texte (hex)")
    footer_background_color = ColorField(default="#FFFFFF", help_text="Couleur de fond (hex)")
    footer_text_align = models.CharField(max_length=50, choices=ALIGN_CHOICES, default="left")

    
    # Tableaux
    forecast_table_font_size = models.PositiveSmallIntegerField(default=10, help_text="Taille du texte dans les tableaux (pt)")
    caption_font_size = models.PositiveSmallIntegerField(default=12, help_text="Taille du titre des tableaux (pt)")
    table_border_color = ColorField(default="#555555", help_text="Couleur des bordures de tableau (hex)")
    table_header_background_color = ColorField(default="#f0f0f0", help_text="Fond des en-têtes de tableau")
    row_even_background_color = ColorField(default="#f9f9f9", help_text="Fond des lignes paires")
    row_hover_background_color = ColorField(default="#f1f1f1", help_text="Fond des lignes au survol")
    block_forecast_table_margin_top = models.DecimalField(default=2.0, max_digits=3, decimal_places=1, help_text="Marge haute des tableaux de prévision (em)")
    
    # Mise en page StreamField
    stream_block_margin_top = models.DecimalField(default=0.0, max_digits=3, decimal_places=1, help_text="Marge haute des blocs (em)")
    stream_block_margin_bottom = models.DecimalField(default=0.0, max_digits=3, decimal_places=1, help_text="Marge basse des blocs (em)")
    two_column_gap = models.CharField(default="1rem", max_length=10, help_text="Espacement entre colonnes en mode deux colonnes")

    # Caption Figure
    figcaption_size = models.PositiveSmallIntegerField(default=10, help_text="Taille de la légende des figures (pt)")
    figcaption_color = ColorField(default="#f0f0f0", help_text="Couleur de la légende des figures")
    figcaption_align = models.CharField(max_length=50, choices=ALIGN_CHOICES, default="left", help_text="Position de la légende des figures")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    edit_handler = TabbedInterface([
        ObjectList([
            MultiFieldPanel([
                FieldPanel('name'),
            ], heading="Configuration générale"),
        ], heading="Général"),
        ObjectList([
            MultiFieldPanel([
                FieldPanel('font_family'),
                FieldPanel('font_size'),
                FieldPanel('line_height'),
                FieldPanel('text_color'),
                FieldPanel('background_color'),
                FieldPanel('header_text_font_size'),
            ], heading="Police"),
        ], heading="Police"),
        ObjectList([
            MultiFieldPanel([
                FieldPanel('orientation'),
                FieldPanel('twoColumns'),
                FieldPanel('margin_top'),
                FieldPanel('margin_bottom'),
                FieldPanel('margin_left'),
                FieldPanel('margin_right'),
                FieldPanel('margin_top_first_page'),
                FieldPanel('margin_bottom_with_footer'),
            ], heading="Page"),
            MultiFieldPanel([
                FieldPanel('bordures'),
                FieldPanel('border_width'),
                FieldPanel('border_style'),
                FieldPanel('border_color'),
                FieldPanel('border_padding'),
            ], heading="Bordures"),


        ], heading="Page"),
        ObjectList([
            MultiFieldPanel([
                FieldPanel('page_number_font_size'),
                FieldPanel('page_number_color'),
            ], heading="Numérotation"),
            MultiFieldPanel([
                FieldPanel('footer_font_family'),
                FieldPanel('footer_font_size'),
                FieldPanel('footer_line_height'),
                FieldPanel('footer_text_color'),
                FieldPanel('footer_background_color'),
                FieldPanel('footer_text_align'),
            ], heading="Style text"),
        ], heading="Pied de page"),
        ObjectList([
            MultiFieldPanel([
                FieldPanel('forecast_table_font_size'),
                FieldPanel('caption_font_size'),
                FieldPanel('table_border_color'),
                FieldPanel('table_header_background_color'),
                FieldPanel('row_even_background_color'),
                FieldPanel('row_hover_background_color'),
                FieldPanel('block_forecast_table_margin_top'),
            ], heading="Tableaux"),
        ], heading="Tableaux"),
        ObjectList([
            MultiFieldPanel([
                FieldPanel('stream_block_margin_top'),
                FieldPanel('stream_block_margin_bottom'),
                FieldPanel('two_column_gap'),
            ], heading="Disposition StreamField"),
        ], heading="Blocs"),
        ObjectList([
            MultiFieldPanel([
                FieldPanel('figcaption_size'),
                FieldPanel('figcaption_color'),
                FieldPanel('figcaption_align'),
            ], heading="Légende des figures"),
        ], heading="Figures"),
    
    ])

    def generate_style_tag(self):

        pageBorder =""
        if self.bordures :
            pageBorder =f"""
            .page-frame {{
                border: {self.border_width}px {self.border_style} {self.border_color};
                padding: {self.border_padding}px;
                height: 100%;
                box-sizing: border-box;
                position: relative;
                z-index: 1;
                page-break-after: always;
            }}
            """
        return f"""
        <style>
            @page {{
                size: A4 {self.orientation};
                margin: {self.margin_top}cm {self.margin_right}cm {self.margin_bottom}cm {self.margin_left}cm;
            }}

            @page:first {{
                margin-top: {self.margin_top_first_page}px;
                @top-center {{
                    content: element(header);
                }}
            }}

            @page {{
                margin-bottom: {self.margin_bottom_with_footer}px;
                @bottom-center {{
                    content: element(footer);
                }}
                @bottom-right {{
                    content: "Page " counter(page) " / " counter(pages);
                    font-size: {self.page_number_font_size}pt;
                    color: {self.page_number_color};
                }}
            }}

            .footer-text{{
                font-family: "{self.footer_font_family}", sans-serif;
                font-size: {self.footer_font_size}pt;
                line-height: {self.footer_line_height};
                color: {self.footer_text_color};
                background-color: {self.footer_background_color};
                text-align: {self.footer_text_align};
            }}

            body {{
                font-family: "{self.font_family}", sans-serif;
                font-size: {self.font_size}pt;
                line-height: {self.line_height};
                color: {self.text_color};
                background-color: {self.background_color};
                margin: 0;
                padding: 0;
            }}

            .center-text {{
                text-align: center;
                margin-bottom: 15px;
            }}

            .page-number {{
                position: running(pageFooter);
                font-size: {self.page_number_font_size}pt;
                color: {self.page_number_color};
                text-align: right;
            }}

            .header, .footer {{
                width: 100%;
                text-align: center;
                z-index: 0;
            }}

            .header img, .footer img {{
                max-width: 100%;
                margin-bottom: 0;
                z-index: 0;
            }}

            .header-text {{
                margin: 2px 0 5px 0;
                font-size: {self.header_text_font_size}pt;
            }}

            #header {{
                position: running(header);
                padding: 0 20px;
                box-sizing: border-box;
                z-index: 0;
            }}

            #footer {{
                position: running(footer);
            }}

            .streamfield-content {{
                display: block;
            }}

            .streamfield-content.two-columns {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: {self.two_column_gap};
            }}

            .stream-block {{
                display: block;
                width: 100%;
                clear: both;
                margin-top: {self.stream_block_margin_top};
                margin-bottom: {self.stream_block_margin_bottom};
            }}

            .stream-block::after {{
                content: "";
                display: table;
                clear: both;
            }}

            .tmax {{ color: red; }}
            .tmin {{ color: blue; }}

            .forecast-container {{
                display: flex;
                justify-content: center;
            }}

            .forecast-table {{
                border-collapse: collapse;
                width: auto;
                margin: 0 auto;
                font-family: {self.font_family}, sans-serif;
                font-size: {self.forecast_table_font_size}pt;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }}

            .forecast-table caption {{
                font-weight: bold;
                font-size: {self.caption_font_size}pt;
                margin-bottom: 10px;
                text-align: center;
            }}

            .forecast-table th,
            .forecast-table td,
            th, td {{
                padding: 8px 12px;
                border: 1px solid {self.table_border_color};
                text-align: center;
                white-space: nowrap;
                vertical-align: middle;
            }}

            .forecast-table th {{
                background-color: {self.table_header_background_color};
                font-weight: bold;
            }}

            .forecast-table tr:nth-child(even) {{
                background-color: {self.row_even_background_color};
            }}

            .forecast-table tr:hover {{
                background-color: {self.row_hover_background_color};
            }}

            .block-forecast-table table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: {self.block_forecast_table_margin_top}em;
            }}

            .block-forecast-table th {{
                background-color: {self.table_header_background_color};
                font-weight: bold;
            }}

            .parameter-col {{
                text-align: left;
                background-color: {self.row_even_background_color};
            }}

            .echeance-col {{
                min-width: 90px;
            }}

            .weather_icon {{
                width: 20%;
            }}

            figcaption {{
                font-size: {self.figcaption_size}px;
                color: {self.figcaption_color};
                text-align: {self.figcaption_align}; 
                font-style: italic;
            }}

            {pageBorder}
        </style>
        """.strip()

    search_fields = [
        index.SearchField('name', boost=2),  # Boost pour prioriser le nom
        index.AutocompleteField('name'),  # Pour l'autocomplétion
    ]
    class Meta:
        permissions = [
            ("edit_style_bulletin", "Can edit style bulletin"),
        ]

    def __str__(self):
        return self.name

# @register_snippet
class Echeance(index.Indexed,models.Model):
    name = models.CharField(max_length=100)
    echeance = models.CharField(unique=True)
    start = models.IntegerField(default=12,verbose_name='Début',help_text='exprimé en nombre d heures')
    end = models.IntegerField(default=36,verbose_name='Fin',help_text='exprimé en nombre d heure')
    active = models.BooleanField(default=True, null=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['start', 'end'], name='unique_start_end')
        ]
        permissions = [
            ("edit_echeance", "Can edit Echeance"),
        ]

    search_fields = [
        index.SearchField('name', boost=2),
        index.SearchField('echeance'),
        index.FilterField('start'), 
        index.FilterField('end'), 
        index.AutocompleteField('name'),
        index.AutocompleteField('echeance')
    ]

    def __str__(self):
        return f'{self.name} ({self.echeance})' or "Nom non défini"
# @register_snippet
class Localites(models.Model):
    name = models.CharField(max_length=150, blank=False, null=False, help_text="Nom du regrouppement de localités")
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE,limit_choices_to={'category__in': ['polygon', 'region','province']},related_name='localites_zones')
    stations = models.ManyToManyField(Station,blank=True, )
    villes = models.ManyToManyField(Zone,blank=True,limit_choices_to={'category': 'ville'})

    panels = [
        FieldPanel('name'),
        FieldPanel('zone'),
        FieldPanel('stations'),
        FieldPanel('villes'),
    ]
    class Meta:
        permissions = [
            ("edit_localites", "Can edit Localites"),
        ]


    def __str__(self):
        return f"{self.name}"


from modelcluster.fields import ParentalManyToManyField

@register_snippet
class Parametres(models.Model):
    name = models.CharField(max_length=150, blank=False, null=False, help_text="Nom du regrouppement des paramètres")
    parametres = models.ManyToManyField(Variable)
    class Meta:
        permissions = [
            ("edit_groupParameters", "Can edit group of parameters"),
        ]
    def __str__(self):
        return f"{self.name}"

@register_snippet
class Echeances(models.Model):
    name = models.CharField(max_length=150, blank=False, null=False, help_text="Nom du regrouppement des echéances")
    echeances = models.ManyToManyField(Echeance)
    def __str__(self):
        return f"{self.name}"
    class Meta:
        permissions = [
            ("edit_groupEcheance", "Can edit Observation"),
        ]
# @register_snippet
class SendingSchedule(models.Model):
    FREQUENCY_TYPE_CHOICES = [
        ('daily', 'Quotidien'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel'),
        ('dekadal', 'Décadaire'),
    ]

    frequency_type = models.CharField(
        max_length=10,
        choices=FREQUENCY_TYPE_CHOICES,
        default='daily'
    )

    # Pour weekly
    weekday = models.PositiveSmallIntegerField(
        null=True, blank=True,
        choices=[(i, day) for i, day in enumerate(
            ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        )]
    )

    # Pour monthly
    day_of_month = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text="Jour du mois (1 à 28)"
    )

    # Pour dekadal : pas besoin de champ spécifique (on code les jours 3, 13, 23 en dur)
    send_time = models.TimeField(default='08:00')
    def clean(self):
        if self.frequency_type == 'weekly' and self.weekday is None:
            raise ValidationError("Le champ 'weekday' est requis pour une fréquence hebdomadaire.")
        if self.frequency_type == 'monthly' and self.day_of_month is None:
            raise ValidationError("Le champ 'day_of_month' est requis pour une fréquence mensuelle.")
    def __str__(self):
        if self.frequency_type == 'daily':
            return f"Chaque jour à {self.send_time.strftime('%Hh:%M')}"
        elif self.frequency_type == 'weekly' and self.weekday is not None:
            return f"Chaque {self.get_weekday_display()} à {self.send_time.strftime('%Hh:%M')}"
        elif self.frequency_type == 'monthly' and self.day_of_month:
            return f"Chaque {self.day_of_month} du mois à {self.send_time.strftime('%Hh:%M')}"
        elif self.frequency_type == 'dekadal':
            return f"Chaque décade le 3, 13 et 23 du mois à {self.send_time.strftime('%Hh:%M')}"
        return "Fréquence personnalisée"
from wagtail.admin.panels import (FieldPanel)
from wagtail.models import Page
from wagtail.snippets.models import register_snippet
from wagtail.fields import StreamField
from . import blocks

from wagtail.blocks import RichTextBlock, StructBlock, CharBlock, TextBlock
from forecast.models import Zone
from observation.models import Station
from chartmet.models import MapObsConfiguration,MapFcstConfiguration

from wagtail.fields import RichTextField

from django.contrib.auth.models import Group
from django.utils import timezone
# @register_snippet
class BulletinTemplate(index.Indexed,models.Model):
    name = models.CharField(max_length=100, unique=True,default='bulletin',null=False, verbose_name='Nom du bulletin')
    bulletin_title = models.CharField(max_length=250)
    active = models.BooleanField(default=True,null=False)
    style_bulletin = models.ForeignKey(BulletinStyleConfiguration, on_delete=models.SET_NULL, blank=True, null=True)
    role = models.ManyToManyField(Group, blank=True,verbose_name="Groupes autorisés",
        help_text="Groupes d'utilisateurs autorisés à accéder et gérer ce modèle de bulletin.")
    subtitle = models.CharField(max_length=100, blank=True, null=True)
    header_text = RichTextField(blank=True, null=True,features=[
            'bold', 'italic', 'link', 'ul', 'ol',
            'h2', 'h3', 'hr', 'blockquote',
            'document-link', 'image', 'embed',
            'superscript', 'subscript', 'code'
        ])
    header_image = models.ImageField(upload_to='bulletin_headers/', blank=True, null=True)

    footer_text = RichTextField(blank=True, null=True,features=[
            'bold', 'italic', 'link', 'ul', 'ol',
            'h2', 'h3', 'hr', 'blockquote',
            'document-link', 'image', 'embed',
            'superscript', 'subscript', 'code'
        ])
    footer_image = models.ImageField(upload_to='bulletin_footers/', blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    pdf_file = models.FileField(upload_to='bulletins/pdf/', blank=True)
    html_file = models.FileField(upload_to='bulletins/html/', blank=True)

    frequence_envoi = models.ForeignKey(
        SendingSchedule,
        blank=True, null=True,
        on_delete=models.CASCADE,
        related_name='newsletters'
    )
    # Champ StreamField pour les blocs flexibles
    content = StreamField([
            ('heading', CharBlock(form_classname="full title")),
            ('paragraph', RichTextBlock(editor="full")),
            # ("ObsTitleTextBlock", blocks.ObsTitleTextBlock()),
            ("TitleTextBlock", blocks.TitleTextBlock(collapsed=True)),
            
            ("ObsTableBlock", blocks.ObsTableBlock(collapsed=True)),
            ("FcstTableBlock", blocks.FcstTableBlock(collapsed=True)), 

            ("ObsImageBlock", blocks.ObsImageBlock(collapsed=True)),
            ("ObsTitleTextImageBlock", blocks.ObsTitleTextImageBlock(collapsed=True)),

            ("FcstImageBlock", blocks.FcstImageBlock(collapsed=True)),
            ("FcstTitleTextImageBlock", blocks.FcstTitleTextImageBlock(collapsed=True)),
            # ("FcstTitleTextBlock", blocks.FcstTitleTextBlock()),
            ("ModelTitleTextImageBlock", blocks.ModelTitleTextImageBlock(collapsed=True)),
            ("ModelImageBlock", blocks.ModelImageBlock(collapsed=True)),
            ("TwoCarteModelBlock", blocks.TwoCarteModelBlock(collapsed=True)),
            

            ("ObsTitleTextCarteSpatialBlock", blocks.ObsTitleTextCarteSpatialBlock(collapsed=True)),
            
            ("CarteSpatialBlock", blocks.CarteSpatialBlock(collapsed=True)),
            ("TwoCarteSpatialBlock", blocks.TwoCarteSpatialBlock(collapsed=True)),
            
            ("CarteDecadeBlock", blocks.CarteDecadeBlock(collapsed=True)),
            ("TwoCarteDecadelock", blocks.TwoCarteDecadelock(collapsed=True)),
            ("ObsTitleTextCarteDecadeBlock", blocks.ObsTitleTextCarteDecadeBlock(collapsed=True)),
            ("BesoinsEauBlock", blocks.BesoinsEauBlock(collapsed=True)),

            ("NDVIBlock", blocks.NDVIBlock(collapsed=True)),
            ("ObsTitleTextCarteNDVIBlock", blocks.ObsTitleTextCarteNDVIBlock(collapsed=True)),
                      
        ], use_json_field=True,
        help_text="Ajouter les blocks constituant le bulletin",
        verbose_name="Contenu du bulletin",
        )

    body = StreamField([
        ('Titre', CharBlock(form_classname="full title")),
        ('paragraphe', RichTextBlock(editor="full")),
        # ('text_block', blocks.TitleTextBlock()),
        # ("textImage", blocks.TitleTextImageBlock()), 
        ],
        blank=True,  # Rend le champ optionnel
        use_json_field=True,
        verbose_name="Contenu optionnel pour ajouter du texte au dessous")
   
    edit_handler = TabbedInterface([
        ObjectList([
            MultiFieldPanel([
                FieldPanel('name'),
                FieldPanel('active'),
                FieldPanel('bulletin_title'),
                FieldPanel('subtitle'),
                FieldPanel('header_text'),
                FieldPanel('header_image'),
                FieldPanel('footer_text'),
                FieldPanel('footer_image'),
            ], heading="Informations générales"),
        ], heading="Général"),


        ObjectList([
            FieldPanel('role'),
        ], heading="Permissions"),
        ObjectList([
            FieldPanel('frequence_envoi'),
        ], heading="Transmission"),
        ObjectList([
            FieldPanel('style_bulletin'),
            FieldPanel('content'),
            FieldPanel('body'),
        ], heading="Contenu"),
    ])
    search_fields = [
        index.SearchField('name', boost=2),  # Boost pour prioriser le nom
        index.AutocompleteField('name'),  # Pour l'autocomplétion
    ]

    @property
    def recipients(self):
        return [dist.client for dist in self.distributions.all()]
    
    def __str__(self):
        return self.name or "Nom non défini"
    class Meta:
        verbose_name = "Template de Bulletin"
        verbose_name_plural = "Templates de Bulletin"
        permissions = [
            ("edit_bulletin", "Can edit Bulletins"),
        ]

    def get_next_sending_delta(self):
        schedule = self.frequence_envoi
        if schedule is None:
            return False
        now = datetime.now()
        today = now.date()
        target_time = datetime.combine(today, schedule.send_time)

        if schedule.frequency_type == 'daily':
            if now < target_time:
                return target_time - now
            else:
                return target_time + timedelta(days=1) - now

        elif schedule.frequency_type == 'weekly' and schedule.weekday is not None:
            days_ahead = (schedule.weekday - today.weekday()) % 7
            if days_ahead == 0 and now >= target_time:
                days_ahead = 7
            next_date = today + timedelta(days=days_ahead)
            return datetime.combine(next_date, schedule.send_time) - now

        elif schedule.frequency_type == 'monthly' and schedule.day_of_month:
            current_month = today.month
            current_year = today.year
            day = min(schedule.day_of_month, 28)

            try:
                candidate = date(current_year, current_month, day)
            except ValueError:
                candidate = date(current_year, current_month, 28)

            if candidate < today or (candidate == today and now >= target_time):
                if current_month == 12:
                    candidate = date(current_year + 1, 1, day)
                else:
                    candidate = date(current_year, current_month + 1, day)
            return datetime.combine(candidate, schedule.send_time) - now

        elif schedule.frequency_type == 'dekadal':
            candidate_days = [3, 13, 23]
            future_dates = []
            for day in candidate_days:
                try:
                    d = date(today.year, today.month, day)
                    if d > today or (d == today and now < target_time):
                        future_dates.append(d)
                except ValueError:
                    continue
            if not future_dates:
                next_month = today.month + 1 if today.month < 12 else 1
                year = today.year if today.month < 12 else today.year + 1
                for day in candidate_days:
                    try:
                        d = date(year, next_month, day)
                        future_dates.append(d)
                    except ValueError:
                        continue
            if future_dates:
                d = min(future_dates)
                return datetime.combine(d, schedule.send_time) - now

        return timedelta(0)

    def format_timedelta_with_color(self):
        delta = self.get_next_sending_delta()
        if not delta:
            return {'time_str': '-', 'color': '#e0f7ff'}

        total_seconds = max(delta.total_seconds(), 0)

        minutes = int((total_seconds // 60) % 60)
        hours = int((total_seconds // 3600) % 24)
        days = int((total_seconds // 86400) % 30)
        months = int(total_seconds // (86400 * 30))  # approx. 30 jours/mois

        parts = []
        if months > 0:
            parts.append(f"{months}mois")
        if days > 0:
            parts.append(f"{days}j")
        if hours > 0:
            parts.append(f"{hours}h")
        parts.append(f"{minutes}min")

        time_str = " ".join(parts)

        # Choix de la couleur selon la durée (sur les secondes totales)
        if total_seconds < 5 * 60:  # moins de 5 minutes
            color = '#ff7c7c'
        elif 5 * 60 <= total_seconds < 3600:  # entre 5 min et 1 heure
            color = '#ffc566'
        elif 3600 <= total_seconds < 6 * 3600:  # entre 1h et 6h
            color = '#fef672'
        else:
            color = '#e0f7ff'  # au-delà de 6h (ou cas imprévu)

        return {'time_str': time_str, 'color': color}
