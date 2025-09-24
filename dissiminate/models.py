from django.db import models
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from wagtail.admin.panels import FieldPanel, MultiFieldPanel, ObjectList, TabbedInterface
from wagtail.admin.panels import (
    FieldPanel, MultiFieldPanel, ObjectList, TabbedInterface
)
from bulletins.models import BulletinTemplate

from django.core.validators import RegexValidator
from django import forms
from wagtail.fields import RichTextField


phone_validator = RegexValidator(r'^\+?\d{6,15}$', "Entrez un numéro de téléphone valide (min. 6 chiffres).")
# @register_snippet
class Client(index.Indexed, models.Model):
    # Identité
    name = models.CharField(max_length=100, unique=True, help_text="Nom officiel ou organisation du client")
    active = models.BooleanField(default=True, verbose_name="Actif", help_text="Décocher pour désactiver ce client")

    # Coordonnées
    email = models.EmailField(help_text="Adresse e-mail principale du client")
    phone = models.CharField(max_length=15, blank=True, null=True, validators=[phone_validator], help_text="Numéro de téléphone fixe")
    fax = models.CharField(max_length=15, blank=True, null=True, validators=[phone_validator], help_text="Numéro de fax")
    sms_phone = models.CharField(max_length=15, blank=True, null=True, validators=[phone_validator], help_text="Numéro GSM pour l'envoi de SMS")

    # Modes de transmission
    transmit_mail = models.BooleanField(default=True, verbose_name="Par e-mail")
    transmit_fax = models.BooleanField(default=False, verbose_name="Par fax")
    transmit_sms = models.BooleanField(default=False, verbose_name="Par SMS")
    transmit_ftp = models.BooleanField(default=False, verbose_name="Via FTP")
    transmit_sftp = models.BooleanField(default=False, verbose_name="Via SFTP")

    # (Configuration des accès FTP/SFTP
    ftp_host = models.CharField(max_length=200, blank=True, null=True)
    ftp_login = models.CharField(max_length=100, blank=True, null=True)
    ftp_path = models.CharField(max_length=200, blank=True, null=True)
    ftp_password = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Mot de passe FTP/SFTP"
    )

    # Configuration de recherche pour Wagtail
    autocomplete_search_field = 'name'
    search_fields = [
        index.SearchField('name', boost=2),
        index.SearchField('email'),
        index.AutocompleteField('name'),
    ]

    def autocomplete_label(self):
        return f"{self.name} ({self.email})"

    def __str__(self):
        suffix = []
        if self.email:
            suffix.append(self.email)
        if self.sms_phone:
            suffix.append(f"SMS: {self.sms_phone}")
        return f"{self.name} ({' - '.join(suffix)})"

    class Meta:
        ordering = ['name']
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['active']),
        ]
        permissions = [
            ("edit_client", "Can edit Clients"),
        ]

    panels = [
    TabbedInterface([
            # Onglet 1 : Informations générales
            ObjectList([
                MultiFieldPanel([
                    FieldPanel('name'),
                    FieldPanel('active'),
                ], heading="Identité"),
                MultiFieldPanel([
                    FieldPanel('email'),
                    FieldPanel('phone'),
                    FieldPanel('fax'),
                    FieldPanel('sms_phone'),
                ], heading="Coordonnées"),
            ], heading="Informations générales"),

            # Onglet 2 : Modes de transmission
            ObjectList([
                MultiFieldPanel([
                    FieldPanel('transmit_mail'),
                    FieldPanel('transmit_fax'),
                    FieldPanel('transmit_sms'),
                    FieldPanel('transmit_ftp'),
                    FieldPanel('transmit_sftp'),
                ], heading="Canaux de diffusion"),
            ], heading="Transmission"),

            # Onglet 3 : Configuration FTP/SFTP
            ObjectList([
                MultiFieldPanel([
                    FieldPanel('ftp_host'),
                    FieldPanel('ftp_login'),
                    FieldPanel('ftp_password', widget=forms.PasswordInput(render_value=True)),
                    FieldPanel('ftp_path'),
                ], heading="Accès FTP/SFTP"),
            ], heading="Paramètres techniques"),
        ])
    ]

class GroupClient(index.Indexed, models.Model):
    name = models.CharField(max_length=150, blank=False, null=False,verbose_name="Nom du groupe", help_text="Nom du groupe des clients")
    clients = models.ManyToManyField(Client, help_text="Nom du groupe des clients")

    panels = [
        FieldPanel('name'),
        FieldPanel('clients'),
    ]
    class Meta:
        permissions = [
            ("edit_gclient", "Can edit Group Clients"),
        ]


    def __str__(self):
        return f"{self.name}"
        
class BulletinDessimination(models.Model):
    bulletin = models.ForeignKey(BulletinTemplate, on_delete=models.CASCADE, related_name='distributions')
    client = models.ForeignKey(Client,blank=True,null=True, on_delete=models.CASCADE, related_name='distributions', verbose_name="Client principal",
        help_text="Client dans le mail principal.")
    clients = models.ForeignKey(GroupClient,blank=True,null=True, on_delete=models.CASCADE, related_name='distributions', verbose_name="Groupe de Clients",
        help_text="Groupe de clients en CCi (mail).")
    distributed_at = models.DateTimeField(auto_now_add=True)
    via_mail = models.BooleanField(default=True)
    via_fax = models.BooleanField(default=False)
    via_sms = models.BooleanField(default=False)
    via_ftp = models.BooleanField(default=False)
    via_sftp = models.BooleanField(default=False)
    active = models.BooleanField(default=True, verbose_name="Diffusion active",
        help_text="Décochez pour suspendre temporairement l'envoi de ce bulletin à ce client.")
     # Contenu du message
    message_body=RichTextField(blank=True,null=True, verbose_name="Contenu du message")
    pdf_content = models.BooleanField(default=True, verbose_name="Contenu Pdf", help_text="Envoyer le bulletin en format pdf en pièce jointe")
    html_content = models.BooleanField(default=False, verbose_name="Contenu Html", help_text="Envoyer le bulletin en format html dans le mail")


    class Meta:
        unique_together = ('bulletin', 'clients')
        verbose_name = "Diffusion du bulletin"
        verbose_name_plural = "Diffusions de bulletins"
        permissions = [
            ("edit_dessiminate", "Can edit Diffusion mail"),
        ]

    panels = [
	    TabbedInterface([
	            ObjectList([
	                    FieldPanel('bulletin'),
                        FieldPanel('client'),
	                    FieldPanel('clients'),
	                    FieldPanel('active'),
	            ], heading="Définition"),
	            ObjectList([
	                MultiFieldPanel([
	                    FieldPanel('via_mail'),
	                    FieldPanel('via_fax'),
	                    FieldPanel('via_sms'),
	                    FieldPanel('via_ftp'),
	                    FieldPanel('via_sftp'),
	                ]),
	            ], heading="Canaux de diffusion"),
                ObjectList([
                        FieldPanel('message_body'),
                        FieldPanel('pdf_content'),
                        FieldPanel('html_content'),
                ], heading="Contenu mail"),
	    ])
	]

    def __str__(self):
        return f"{self.bulletin.name} → {self.clients}"

from django.contrib.auth import get_user_model

User = get_user_model()

class BulletinTransmissionLog(models.Model):
    bulletin = models.ForeignKey(BulletinTemplate, on_delete=models.CASCADE)
    client = models.ForeignKey('Client', null=True, blank=True, on_delete=models.CASCADE)
    clients = models.ForeignKey('GroupClient', null=True, blank=True, on_delete=models.CASCADE)
    emails = models.EmailField()
    sent_at = models.DateTimeField(auto_now_add=True)
    sent_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=255)

    class Meta:
        ordering = ['-sent_at']
        permissions = [
            ("edit_logTrans", "Can edit Log Transmission"),
        ]

    def __str__(self):
        return f"{self.bulletin.name} → {self.client.name} ({self.sent_at.strftime('%Y-%m-%d %H:%M')})"