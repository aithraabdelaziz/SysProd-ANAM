from django.shortcuts import render, redirect, get_object_or_404
from forecast.models import *
from collections import defaultdict  
from django.views.generic import ListView, DetailView
from .models import *
from .forms import *
from datetime import datetime, date, timedelta
import locale

from.blocks import *
from weasyprint import HTML, CSS
import os
from django.conf import settings
from django.http import HttpResponse

from collections import OrderedDict
from chartmet.utils import generate_observation_map, generate_forecast_map, generate_model_map

from pprint import pprint
import pprint as ppt

from .utils import display_blocks, embed_images_as_base64 #,display_blocks_old
from django.urls import reverse

# Définir la locale en français (France)
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

from administrate.utils import handle_view_errors
from django.contrib.auth.decorators import permission_required, login_required, permission_required
from django.core.exceptions import PermissionDenied

@permission_required('bulletins.edit_bulletin', raise_exception=True)
def bulletin_deactivate(request, pk):
    bulletin = get_object_or_404(BulletinTemplate, id=pk)
    if bulletin.active==False : bulletin.active = True
    else : bulletin.active = False
    bulletin.save()
    return redirect('bulletins:gestion_bulletins') 
@permission_required('bulletins.edit_bulletin', raise_exception=True)
def add_bulletin(request):
    clients = Client.objects.all()
    zones = Zone.objects.all()
    form = BulletinTemplateForm()
    return render(request, "manage_bulletin/add_bulletin.html", {'form': form,"clients": clients,'zones':zones})
@permission_required('bulletins.edit_bulletin', raise_exception=True)
def bulletin_update(request, pk):
    bulletin = get_object_or_404(BulletinTemplate, id=pk)
    clients = Client.objects.all()
    zones = Zone.objects.all()
    if request.method == 'POST':
        form = BulletinTemplateForm(request.POST, request.FILES, instance=bulletin)#, category_filter=category_filter)
        if form.is_valid():
            bulletin = form.save()
            return redirect('bulletins:manage_bulletins')
    else:
        form = BulletinTemplateForm(instance=bulletin)
    return render(request, "manage_bulletin/add_bulletin.html", {'form': form, 'bulletin':bulletin,"clients": clients,'zones':zones})

@permission_required('bulletins.edit_bulletin', raise_exception=True)
def bulletin_delete(request,pk):
    bulletin = get_object_or_404(BulletinTemplate, id=pk)
    bulletin.delete()
    return redirect('bulletins:gestion_bulletins') 

class BulletinListView(ListView):
    model = BulletinTemplate
    template_name = "manage_bulletin/manage_bulletins.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bulletins = BulletinTemplate.objects.all()
        context['bulletins'] = bulletins
        return context

class BulletinDetailView(DetailView):
    model = BulletinTemplate
    template_name = "production/bulletin_detail.html"


from django.db.models import Q
from django.contrib.auth.models import Group
@permission_required('bulletins.edit_bulletin', raise_exception=True)
def bulletin_list(request):
    user_groups = request.user.groups.all()

    if request.user.is_superuser:
        bulletins = BulletinTemplate.objects.filter(active=True).order_by('name') .distinct()
    else :
        # Filtrer les bulletins liés à au moins un des services de l'utilisateur
        bulletins = BulletinTemplate.objects.filter(
            Q(role__in=user_groups) | Q(role__isnull=True),
            active=True
        ).order_by('name').distinct()

    return render(request, 'production/list_bulletins.html', {'bulletins':bulletins,'today': date.today().strftime("%Y-%m-%d")}) #})

from django.core.files.base import ContentFile


from django.core.files.storage import default_storage
# @handle_view_errors
@permission_required('bulletins.edit_bulletin', raise_exception=True)
def display_bulletin(request):
    
    if request.method == "POST":
        bulletin_id = None
        action = None

        if 'select' in request.POST:
            bulletin_id = request.POST.get('select')
            action = 'select'
        elif 'edit' in request.POST:
            bulletin_id = request.POST.get('edit')
            action = 'edit'
        elif 'generate' in request.POST:
            bulletin_id = request.POST.get('generate')
            action = 'generate'

        bulletin = BulletinTemplate.objects.get(id=bulletin_id)
        date_str = request.POST.get('date')
        date_bult=datetime.strptime(date_str, "%Y-%m-%d")
        initialize = request.POST.get('initialize')
    else :
        url = reverse('bulletins:bulletin_list')
        return redirect(url)

    bulletin.established_date=date_bult

    if request.method == 'POST':
        if action == 'edit' :
            url = f"/bulletins/edition/{bulletin_id}/zones/{date_str}/"
            return redirect(url)

    context={}
    error_msg=[]

    context = display_blocks(bulletin,date_bult,initialize=initialize)
    if action == 'generate' :
        pdf_name=bulletin.name+'_'+bulletin.established_date.strftime("%Y-%m-%d")+'.pdf'
        html_name = bulletin.name + '_' + bulletin.established_date.strftime("%Y-%m-%d") + '.html'
        html_content_ini = render(request, 'production/table_forecast.html', context).content.decode('utf-8')
        html_content = embed_images_as_base64(html_content_ini, settings.MEDIA_ROOT)

        # print(html_content_ini)
        # print('----------------------------------')
        # print(html_content)

        base_url = request.build_absolute_uri(settings.STATIC_URL)
        pdf = HTML(string=html_content, base_url=base_url).write_pdf()

        # Supprimer l'ancien fichier s'il existe
        if bulletin.pdf_file:
            if default_storage.exists(bulletin.pdf_file.name):
                default_storage.delete(bulletin.pdf_file.name)
            bulletin.pdf_file.delete(save=False)

        if bulletin.html_file:
            if default_storage.exists(bulletin.html_file.name):
                default_storage.delete(bulletin.html_file.name)
            bulletin.html_file.delete(save=False)

        # Enregistrer le PDF
        pdf_django_file = ContentFile(pdf, name=pdf_name)
        bulletin.pdf_file.save(pdf_name, pdf_django_file, save=False)

        # Enregistrer le HTML (encoder la chaîne en bytes)
        html_django_file = ContentFile(html_content.encode('utf-8'), name=html_name)
        bulletin.html_file.save(html_name, html_django_file, save=False)

        bulletin.save()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="'+pdf_name+'"'
        return response
    return render(request, "production/bulletin_detail.html",context)


def format_periode(display_periode,ech,date_bult):
    date_bult = datetime.combine(date_bult, datetime.min.time())
    if not display_periode :
        return ""
    emax = max([ h.start for h in ech]+[ h.end for h in ech])
    emin = min([ h.start for h in ech]+[ h.end for h in ech])
    d1 = date_bult + timedelta(hours=emin)
    d2 = date_bult + timedelta(hours=emax)
    periode = ""
    if (d2-d1) >= timedelta(days=2):
        if d1.strftime("%B") == d2.strftime("%B") :
            periode = d1.strftime("%A %d") + " au "+d2.strftime("%A %d %B %Y")
        else :
            periode = d1.strftime("%A %d %B") + " au "+d2.strftime("%A %d %B %Y")
    else :
        if d1.strftime("%B") == d2.strftime("%B") :
            periode = "du "+d1.strftime("%A %d à %Hh") + " au "+d2.strftime("%A %d %B %Y à %Hh")
        else :
            periode = "du "+d1.strftime("%A %d %B à %Hh") + " au "+d2.strftime("%A %d %B %Y à %Hh")
    return periode


@permission_required('bulletins.generate_bulletin', raise_exception=True)
def generate_bulletin(request, pk):
    bulletin = BulletinTemplate.objects.get(id=pk)
    if request.method == 'POST':
        date_str = request.POST.get('date')
        date_obj=datetime.strptime(date_str, "%Y-%m-%d")
        date_bult = date_obj.date()
    else :
        date_bult=date.today()
    zones = bulletin.zone.all()
    echeances = bulletin.echeances.all()
    echeances = [ech.echeance for ech in echeances]
    parameters = bulletin.parameters.all()
    
    for b in bulletin.content:
        if b.block_type == 'forecast_table' :
            forecast_data, sorted_echeances = b.block.get_forecast_data(date_bult,parameters,zones,echeances)
            jours =generate_echeances_dict(date_bult, sorted_echeances)
            context = {
                'forecast_data': forecast_data,
                'sorted_echeances': sorted_echeances,
                'jours': jours,
            }
    bulletin.established_date=date_bult
    context['object'] = bulletin

    html_content = render(request, 'production/table_forecast.html', context).content.decode('utf-8')
    output_path = os.path.join(settings.BASE_DIR, 'bulletins', 'output.pdf')

   # Assurez-vous que le répertoire existe, sinon créez-le
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(output_path)

    # Générer le PDF et l'enregistrer localement
    pdfkit.from_string(html_content, output_path)

    # Retourner une réponse HTTP indiquant que le PDF a été généré
    # return HttpResponse(f"Le PDF a été généré et sauvegardé à {output_path}")
    response['Content-Disposition'] = 'inline; filename="output.pdf"'
    
    return response
############# functions ###################
def generate_echeances_dict(date_bult, echeances):
   
    # Dictionnaire pour stocker les résultats
    date_echeances_dict = {}

    # Variable pour suivre le jour d'ajout
    current_date = date_bult

    # Boucle pour remplir le dictionnaire
    for ech in echeances :
        # if isinstance(ech.echeance,int) : 
        #     current_date = date_bult + timedelta(hours=(ech.echeance-1))
        # if current_date not in date_echeances_dict:
        #     date_echeances_dict[current_date]={}
        try :
            echint = int(ech.echeance)
            current_date = date_bult + timedelta(hours=(echint-1))
        except :
            pass
        if current_date not in date_echeances_dict:
            date_echeances_dict[current_date]={}
        date_echeances_dict[current_date][ech.echeance]=ech.name

    return date_echeances_dict
