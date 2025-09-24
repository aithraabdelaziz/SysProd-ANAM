from django.contrib.gis.db import models


from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail.admin.panels import (
    MultiFieldPanel,
    FieldPanel,
    TabbedInterface,
    ObjectList,
    FieldRowPanel
)
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.contrib.settings.registry import register_setting
from wagtail.fields import RichTextField, StreamField

@register_setting
class OrganisationSetting(BaseSiteSetting):
    # country = models.CharField(max_length=100, blank=True, null=True, choices=COUNTRY_CHOICES,
    #                            verbose_name=_("Country"))
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Organisation Name"))
    name_site = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("System Name"))
    
    phone = models.CharField(max_length=255, blank=True, null=True, help_text=_("Phone Number"),
                             verbose_name=_("Phone number"))
    email = models.EmailField(blank=True, null=True, max_length=254, help_text=_("Email address"),
                              verbose_name=_("Email address"))
    address = RichTextField(max_length=250, blank=True, null=True, help_text=_("Postal Address"),
                            verbose_name=_("Postal address"))
    
    # social_media_accounts = StreamField([
    #     ('social_media_account', SocialMediaBlock()),
    # ], blank=True, null=True, use_json_field=True)
    
    # logo
    logo = models.ForeignKey("wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
                             verbose_name=_("Organisation Logo"))
    country_flag = models.ForeignKey("wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL,
                                     related_name="+",
                                     verbose_name=_("Country Flag"))
    
    favicon = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text=_("Does not need to be any larger than 200x200 pixels. A 1:1 (square) image ratio is best here "
                  "- If the image is not square, it will be scaled to a square.")
    )

    footer_text_site = models.CharField(max_length=455, blank=True, null=True, verbose_name=_("Footer site"))
    
    footer_logo = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Footer Logo"),
        help_text=_("Logo that appears on the footer"),
    )
    header_image_bulletin = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Footer Logo"),
        help_text=_("Logo that appears on the footer of bulletins"),
    )

    footer_image_bulletin = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Footer Logo"),
        help_text=_("Logo that appears on the footer of bulletins"),
    )
    
    site_logo = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Logo Site"),
        help_text=_("Logo that appears on the Site. Should be a whit transparent logo preferably"),
    )
    
    page_not_found_error_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Page not Found Image"),
        help_text=_("Image shown on error 404 page"),
    )
    
    server_error_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Server Error Image"),
        help_text=_("Image shown on error 500 error page"),
    )
    
    # shapefile_zip = models.FileField(
    #     upload_to="shapefiles/",
    #     blank=True,
    #     null=True,
    #     verbose_name=_("Shapefile (ZIP)"),
    #     help_text=_("Upload a ZIP file containing .shp, .shx, .dbf, .prj files")
    # )

    shapefile_zip = models.ForeignKey(
        'wagtaildocs.Document',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Shapefile associer à la carte (.zip)"
    )

    edit_handler = TabbedInterface([
        ObjectList([
            FieldPanel("name"),
            FieldPanel("name_site"),
            FieldPanel("footer_text_site"),
            # FieldPanel('country'),
            MultiFieldPanel(
                [
                    FieldPanel("logo"),
                    #FieldPanel("country_flag"),
                    FieldPanel("favicon"),
                    FieldPanel("footer_logo"),
                    FieldPanel("site_logo"),
                ],
                heading=_("Logo")
            ),
        ], heading="Général"),

        ObjectList([
            FieldPanel("page_not_found_error_image"),
            FieldPanel("server_error_image"),
        ], heading="Pages Erreurs"),
        ObjectList([
            MultiFieldPanel([
            FieldPanel("address"),
            ], heading=_("Address Settings")),
            MultiFieldPanel([
                FieldPanel("email"),
                FieldPanel("phone"),
            ], heading=_("Contact Settings")),
        ], heading="Contacts"),
        ObjectList([
                FieldPanel("header_image_bulletin"),
                FieldPanel("footer_image_bulletin"),
        ], heading="Bulletins"),

        ObjectList([
            FieldPanel("shapefile_zip"),
        ], heading="Cartographie"),
    ])
    
    class Meta:
        verbose_name = _("Paramètres du site")
        permissions = [
            ("edit_setting", "Can edit settings site"),
        ]
    
    # @cached_property
    # def country_info(self):
    #     if self.country:
    #         return get_country_info(self.country)

