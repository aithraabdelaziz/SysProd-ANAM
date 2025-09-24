from django.shortcuts import render

from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import BulletinDessimination, BulletinTransmissionLog
from datetime import datetime
from .forms import DiffusionForm, FiltreDateForm
import os

from django.http import JsonResponse, FileResponse, HttpResponse

from django.shortcuts import get_object_or_404
from bulletins.models import BulletinTemplate
from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils import timezone

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required, login_required

from django.utils.html import format_html, strip_tags

from .utils import embed_images_as_cid
from django.conf import settings
@xframe_options_exempt
def bulletin_pdf_view(request, pk):
    try:
        bulletin = BulletinTemplate.objects.get(pk=pk)
    except BulletinTemplate.DoesNotExist:
        return render(request, 'dissimination/bulletin-indispo.html')

    if bulletin.pdf_file and os.path.exists(bulletin.pdf_file.path):
        return FileResponse(open(bulletin.pdf_file.path, 'rb'), content_type='application/pdf')

    return render(request, 'dissimination/bulletin-indispo.html', {'bulletin': bulletin})
    
def send_bulletins_via_mail(bulletin, user):
    results = []
    distributions = BulletinDessimination.objects.filter(
        bulletin=bulletin,
        active=True,
        via_mail=True
    )

    for dist in distributions:
        try:
            subject = f"Bulletin {dist.bulletin.name} - {dist.distributed_at.strftime('%d/%m/%Y')}"
            if dist.message_body is not None :
                body = dist.message_body
            else : 
                body = (
                    f"Bonjour {dist.client.name},\n\n"
                    f"Veuillez trouver ci-joint le bulletin '{dist.bulletin.name}' du {dist.distributed_at.strftime('%d/%m/%Y')}.\n\n"
                    "Cordialement,\nANAM ©2025."
                )
            mails = [c.email for c in dist.clients.clients.all()]
            if dist.client.email :
                main_mail = dist.client.email
            else :
                main_mail = 'anam.meteo@gmail.com'
            # email = EmailMessage(subject, body, to=[dist.client.email])
            email = EmailMultiAlternatives(
                subject=subject,
                body = body,
                to=[main_mail],  
                bcc=mails  # destinataire en copie cachée
            )
            if dist.bulletin.pdf_file:
                email.attach_file(dist.bulletin.pdf_file.path)

            # if dist.html_content :
            #     html_content = ""
            #     if dist.html_content and dist.bulletin.html_file:
            #         with open(dist.bulletin.html_file.path, 'r', encoding='utf-8') as f:
            #             html_content = f.read()

            #     # Variante texte brut (fallback si le client mail ne supporte pas HTML)
            #     text_content = strip_tags(html_content) or "Veuillez consulter ce message en HTML."
            #     email.body = text_content
            #     email.attach_alternative(html_content, "text/html")
            if dist.html_content and dist.bulletin.html_file:
                with open(dist.bulletin.html_file.path, 'r', encoding='utf-8') as f:
                    raw_html = f.read()

                updated_html = embed_images_as_cid(raw_html, email, settings.MEDIA_ROOT)
                text_content = strip_tags(updated_html) or "Veuillez consulter ce message en HTML."

                email.body += text_content
                email.attach_alternative(updated_html, "text/html")

            email.send()

            BulletinTransmissionLog.objects.create(
                bulletin=dist.bulletin,
                client=dist.client,
                clients=dist.clients,
                emails=main_mail+','+', '.join(mails),
                sent_by=user,
                status="Envoyé"
            )

            results.append({'client': dist.clients.name+' : '+', '.join(mails), 'status': '✔️ Envoyé'})
        except Exception as e:
            BulletinTransmissionLog.objects.create(
                bulletin=dist.bulletin,
                client=dist.client,
                clients=dist.clients,
                emails=main_mail+','+', '.join(mails),
                sent_by=user,
                status=f"Échec : {str(e)}"
            )
            results.append({'client': dist.client.name, 'status': f'❌ Échec : {str(e)}'})
    return results
# def send_bulletins_via_mail(bulletin, user):
#     results = []
#     distributions = BulletinDessimination.objects.filter(
#         bulletin=bulletin,
#         active=True,
#         via_mail=True,
#         client__email__isnull=False
#     )

#     for dist in distributions:
#         try:
#             subject = f"Bulletin {dist.bulletin.name} - {dist.distributed_at.strftime('%d/%m/%Y')}"
#             body = (
#                 f"Bonjour {dist.client.name},\n\n"
#                 f"Veuillez trouver ci-joint le bulletin '{dist.bulletin.name}' du {dist.distributed_at.strftime('%d/%m/%Y')}.\n\n"
#                 "Cordialement,\nANAM ©2025."
#             )
#             email = EmailMessage(subject, body, to=[dist.client.email])
#             if dist.bulletin.pdf_file:
#                 email.attach_file(dist.bulletin.pdf_file.path)
#             email.send()

#             BulletinTransmissionLog.objects.create(
#                 bulletin=dist.bulletin,
#                 client=dist.client,
#                 email=dist.client.email,
#                 sent_by=user,
#                 status="Envoyé"
#             )

#             results.append({'client': dist.client.name, 'status': '✔️ Envoyé'})
#         except Exception as e:
#             BulletinTransmissionLog.objects.create(
#                 bulletin=dist.bulletin,
#                 client=dist.client,
#                 email=dist.client.email,
#                 sent_by=user,
#                 status=f"Échec : {str(e)}"
#             )
#             results.append({'client': dist.client.name, 'status': f'❌ Échec : {str(e)}'})
#     return results
from ftplib import FTP
from django.core.exceptions import ImproperlyConfigured
import os

def send_bulletins_via_ftp(bulletin, user):
    results = []
    distributions = BulletinDessimination.objects.filter(
        bulletin=bulletin,
        active=True,
        via_ftp=True,
        client__ftp_host__isnull=False,
        client__ftp_login__isnull=False,
        client__ftp_password__isnull=False,
        client__ftp_path__isnull=False
    )

    for dist in distributions:
        client = dist.client
        try:
            if not bulletin.pdf_file:
                raise ImproperlyConfigured("Aucun fichier PDF à envoyer.")

            pdf_path = bulletin.pdf_file.path
            pdf_name = os.path.basename(pdf_path)

            ftp = FTP()
            ftp.connect(client.ftp_host, 21, timeout=30)
            ftp.login(client.ftp_login, client.ftp_password)
            ftp.cwd(client.ftp_path)

            with open(pdf_path, 'rb') as f:
                ftp.storbinary(f'STOR {pdf_name}', f)

            ftp.quit()

            BulletinTransmissionLog.objects.create(
                bulletin=dist.bulletin,
                client=client,
                email=client.email or '',
                sent_by=user,
                status="Envoyé via FTP"
            )
            results.append({'client': client.name, 'status': '✔️ Envoyé via FTP'})
        except Exception as e:
            BulletinTransmissionLog.objects.create(
                bulletin=dist.bulletin,
                client=client,
                email=client.email or '',
                sent_by=user,
                status=f"Échec FTP : {str(e)}"
            )
            results.append({'client': client.name, 'status': f'❌ Échec FTP : {str(e)}'})
    return results
from pprint import pprint

@permission_required('dissiminate.edit_dessiminate', raise_exception=True)
def diffusion_view(request):
    if request.method == 'POST':
        form = DiffusionForm(request.POST, request.FILES)
        if form.is_valid():
            bulletin = form.cleaned_data['bulletin']
            uploaded_file = form.cleaned_data.get('pdf_file')  # Le fichier PDF optionnel

            if uploaded_file:
                extension = os.path.splitext(uploaded_file.name)[1]
                bulletin.pdf_file.save(bulletin.name+datetime.today().strftime("_%Y-%m-%d")+f'{extension}', uploaded_file, save=True)
                return render(request, 'dissimination/diffusion_form.html', {'form': form,'msg':f'{uploaded_file.name} enregistré en tant que bulletin {bulletin.name}' })
            results=[]
            results += send_bulletins_via_mail(bulletin, request.user)
            results += send_bulletins_via_ftp(bulletin, request.user)
            
            return render(request, 'dissimination/resultats.html', {
                'results': results,
                'bulletin': bulletin,
                'date_bulletin': timezone.now().date()
            })
    else:
        form = DiffusionForm()

    return render(request, 'dissimination/diffusion_form.html', {'form': form})



@permission_required('dissiminate.edit_logTrans', raise_exception=True)
# @staff_member_required
def historique_transmissions(request):
    form = FiltreDateForm(request.GET or None)
    logs = BulletinTransmissionLog.objects.select_related('bulletin', 'client', 'sent_by')
    if form.is_valid() and form.cleaned_data.get('date'):
        selected_date = form.cleaned_data['date']
        logs = logs.filter(sent_at__date=selected_date)

    logs = logs.order_by('-sent_at')[:100]
    return render(request, 'dissimination/historique.html', {'logs': logs, 'form': form})
