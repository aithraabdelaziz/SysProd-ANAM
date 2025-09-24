from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
import pandas as pd
from datetime import datetime, timedelta
import csv

from django.db import models
from django.core.validators import FileExtensionValidator
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.models import Page
from wagtail.admin import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
import csv
import io
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

from observation.models import CSVImportForm, ClimatDecades

def index(request): 
    
    return render(request, 'climat/index.html')


def get_current_decade():
    """Calcule la décade actuelle"""
    today = datetime.now()
    day = today.day
    
    if day <= 10:
        return 1
    elif day <= 20:
        return 2
    else:
        return 3

from pprint import pprint
@staff_member_required
@csrf_protect
def csv_import_view(request):
    """Vue pour l'import de CSV"""
    
    if request.method == 'POST':
        form_data = {
            'decade': request.POST.get('decade', get_current_decade()),
            'month': request.POST.get('month', datetime.now().month),
            'year': request.POST.get('year', datetime.now().year),
            'source': request.POST.get('source', ''),
        }
        
        if 'csv_file' not in request.FILES:
            messages.error(request, "Veuillez sélectionner un fichier CSV")
            return render(request, 'climat/csv_import.html', {'form_data': form_data})
        
        csv_file = request.FILES['csv_file']
        
        # Validation du fichier
        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Le fichier doit être au format CSV")
            return render(request, 'climat/csv_import.html', {'form_data': form_data})
        
        # Créer l'enregistrement d'import
        import_record = CSVImportForm.objects.create(
            decade=int(form_data['decade']),
            month=int(form_data['month']),
            year=int(form_data['year']),
            source=form_data['source'],
            csv_file=csv_file
        )
        # Traiter le fichier CSV
        success = process_csv_file(import_record, csv_file, form_data)
        
        if success:
            messages.success(
                request, 
                f"Import réussi! {import_record.success_count} lignes importées"
            )
        else:
            messages.error(
                request, 
                f"Erreurs lors de l'import: {import_record.error_count} erreurs. "
                f"{import_record.success_count} lignes importées avec succès."
            )
        
        return redirect('observation:csv_import')
    
    # GET request - afficher le formulaire
    form_data = {
        'decade': get_current_decade(),
        'month': datetime.now().month,
        'year': datetime.now().year,
        'source': '',
    }
    
    recent_imports = CSVImportForm.objects.order_by('-created_at')[:10]
    
    return render(request, 'climat/csv_import.html', {
        'form_data': form_data,
        'recent_imports': recent_imports
    })


def process_csv_file(import_record, csv_file, form_data):
    success_count = 0
    error_count = 0
    errors = []

    try:
        csv_file.seek(0)
        csv_content = csv_file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content), delimiter=';')

        required_columns = ['lat', 'lon', 'value', 'parameter']
        if not all(col in csv_reader.fieldnames for col in required_columns):
            missing = [col for col in required_columns if col not in csv_reader.fieldnames]
            import_record.error_log = f"Colonnes manquantes: {', '.join(missing)}"
            import_record.processed = True
            import_record.save()
            return False

        # Blocs d'insertion transactionnelle
        
        for row_num, row in enumerate(csv_reader, start=1):
            try:
                lat = float(row['lat'])
                lon = float(row['lon'])
                value = float(row['value']) if row['value'] else None
                parameter = row['parameter'].strip().lower()
                source = row.get('source', '').strip().lower() or form_data['source'].lower()
                station = row.get('station', '').strip() or None
                with transaction.atomic():
                    ClimatDecades.objects.update_or_create(
                        station=station,
                        lon=lon,
                        lat=lat,
                        decade=int(form_data['decade']),
                        month=int(form_data['month']),
                        year=int(form_data['year']),
                        parameter=parameter,
                        value=value,
                        source=source
                    )
        #             _, created = ClimatDecades.objects.update_or_create(
        #     lat=lat,
        #     lon=lon,
        #     decade=int(form_data['decade']),
        #     month=int(form_data['month']),
        #     year=int(form_data['year']),
        #     parameter=parameter,
        #     source=source,
        #     defaults={
        #         'value': value,
        #         'station': station,
        #     }
        # )
                success_count += 1

            except (ValueError, TypeError) as e:
                print(f"Ligne {row_num}: {str(e)}")
                error_count += 1
                errors.append(f"Ligne {row_num}: {str(e)}")
            except IntegrityError:
                continue
            except Exception as e:
                print(f"Ligne {row_num}: {str(e)}")
                error_count += 1
                errors.append(f"Ligne {row_num}: {str(e)}")

    except Exception as e:
        # Cas d'erreur en dehors de la transaction
        print(f"Erreur lors de la lecture ou du traitement : {str(e)}")
        error_count += 1
        errors.append(f"Erreur lors de la lecture ou du traitement : {str(e)}")

    import_record.success_count = success_count
    import_record.error_count = error_count
    import_record.error_log = '\n'.join(errors[:50])
    import_record.processed = True
    import_record.save()

    return error_count == 0

from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db import transaction, IntegrityError
from datetime import datetime
import csv, io
from observation.models import ClimatMois,CSVImportMois

@staff_member_required
@csrf_protect
def csv_import_climatmois_view(request):
    if request.method == 'POST':
        form_data = {
            'month': request.POST.get('month', datetime.now().month),
            'year': request.POST.get('year', datetime.now().year),
            'source': request.POST.get('source', '').strip(),
        }

        if 'csv_file' not in request.FILES:
            messages.error(request, "Veuillez sélectionner un fichier CSV")
            return render(request, 'climat/csv_import.html', {'form_data': form_data})

        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Le fichier doit être au format CSV")
            return render(request, 'climat/csv_import.html', {'form_data': form_data})

        # Création de l’enregistrement d’import
        import_record = CSVImportMois.objects.create(
            month=int(form_data['month']),
            year=int(form_data['year']),
            source=form_data['source'],
            csv_file=csv_file
        )

        success = process_csv_file_climatmois(import_record, csv_file, form_data)

        if success:
            messages.success(request, f"Import réussi ! {import_record.success_count} lignes importées.")
        else:
            messages.error(request,
                f"Import avec erreurs : {import_record.error_count} erreurs, "
                f"{import_record.success_count} lignes importées.")

        return redirect('climat:csv_import_climatmois')

    # GET - affichage formulaire initial
    form_data = {
        'month': datetime.now().month,
        'year': datetime.now().year,
        'source': '',
    }
    recent_imports = CSVImportMois.objects.order_by('-created_at')[:10]

    return render(request, 'climat/csv_import_monthData.html', {
        'form_data': form_data,
        'recent_imports': recent_imports
    })

def process_csv_file_climatmois(import_record, csv_file, form_data):
    success_count = 0
    error_count = 0
    errors = []

    try:
        csv_file.seek(0)
        content = csv_file.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(content), delimiter=';')

        required_cols = ['lat', 'lon', 'value', 'parameter', 'name']
        if not all(col in reader.fieldnames for col in required_cols):
            missing = [c for c in required_cols if c not in reader.fieldnames]
            import_record.error_log = f"Colonnes manquantes dans le CSV : {', '.join(missing)}"
            import_record.processed = True
            import_record.save()
            return False

        for i, row in enumerate(reader, start=1):
            try:
                lat = float(row['lat'])
                lon = float(row['lon'])
                value = float(row['value']) if row['value'] else None
                parameter = row['parameter'].strip().lower()
                name = row['name'].strip()
                source = row.get('source', '').strip().lower() or form_data['source'].lower()
                station = row.get('station', '').strip() or ''

                with transaction.atomic():
                    ClimatMois.objects.update_or_create(
                        lon=lon,
                        lat=lat,
                        month=int(form_data['month']),
                        year=int(form_data['year']),
                        parameter=parameter,
                        source=source,
                        defaults={
                            'value': value,
                            'station': station,
                            'name': name,
                        }
                    )
                success_count += 1
            except (ValueError, TypeError) as e:
                error_count += 1
                errors.append(f"Ligne {i} : {str(e)}")
            except IntegrityError:
                continue
            except Exception as e:
                error_count += 1
                errors.append(f"Ligne {i} : {str(e)}")

    except Exception as e:
        error_count += 1
        errors.append(f"Erreur lecture/traitement du fichier : {str(e)}")

    import_record.success_count = success_count
    import_record.error_count = error_count
    import_record.error_log = '\n'.join(errors[:50])
    import_record.processed = True
    import_record.save()

    return error_count == 0


import os
import tempfile
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.contrib.admin.views.decorators import staff_member_required

from observation.forms import GribImportForm, NetcdfImportForm
from meteowise.utils import extract_grib_info,import_grib1_to_climatmois, extract_netcdf_info, import_netcdf_to_climatmois

import shutil

def grib_import_view(request):
    if request.method == 'POST':
        if 'confirm_import' in request.POST:
            # Étape 2 : confirmation import
            tmp_path = request.session.get('tmp_grib_path')
            if not tmp_path or not os.path.exists(tmp_path):
                messages.error(request, "Fichier temporaire introuvable. Veuillez recommencer.")
                return redirect('observation:grib_import_view')

            try:
                # Copier dans un dossier temporaire à droits garantis pour cfgrib (.idx)
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp_copy_path = os.path.join(tmpdir, os.path.basename(tmp_path))
                    shutil.copy(tmp_path, tmp_copy_path)

                    # Appel de la fonction d'import sur le fichier copié
                    import_grib1_to_climatmois(tmp_copy_path)

                messages.success(request, "Import GRIB réussi.")
            except Exception as e:
                messages.error(request, f"Erreur lors de l'import : {e}")
            finally:
                # Nettoyage : supprimer fichier ET dossier temporaire créé à l'upload
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                        tmp_dir = os.path.dirname(tmp_path)
                        if os.path.isdir(tmp_dir):
                            os.rmdir(tmp_dir)
                    except Exception:
                        pass

                request.session.pop('tmp_grib_path', None)
                request.session.pop('grib_info', None)

            return redirect('observation:grib_import_view')

        else:
            # Étape 1 : upload et extraction infos
            form = GribImportForm(request.POST, request.FILES)
            if form.is_valid():
                grib_file = form.cleaned_data['grib_file']

                # Créer un dossier temporaire stable
                tmp_dir = tempfile.mkdtemp(prefix="grib_upload_")
                tmp_path = os.path.join(tmp_dir, grib_file.name)

                # Écrire le fichier uploadé dans ce dossier
                with open(tmp_path, 'wb+') as f:
                    for chunk in grib_file.chunks():
                        f.write(chunk)

                try:
                    info = extract_grib_info(tmp_path)
                except Exception as e:
                    messages.error(request, f"Erreur lecture fichier GRIB : {e}")
                    # Nettoyage si erreur
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                    if os.path.isdir(tmp_dir):
                        os.rmdir(tmp_dir)
                    return redirect('observation:grib_import_view')

                # Stocker chemin et infos en session
                request.session['tmp_grib_path'] = tmp_path
                request.session['grib_info'] = info

                return render(request, 'climat/grib_import_confirm.html', {'info': info})

    else:
        form = GribImportForm()
        # Nettoyer session à l'ouverture de la page
        tmp_path = request.session.get('tmp_grib_path')
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                tmp_dir = os.path.dirname(tmp_path)
                if os.path.isdir(tmp_dir):
                    os.rmdir(tmp_dir)
            except Exception:
                pass
        request.session.pop('tmp_grib_path', None)
        request.session.pop('grib_info', None)

    return render(request, 'climat/grib_import.html', {'form': form})

import os
import shutil
import tempfile
from django.shortcuts import render, redirect
from django.contrib import messages
# from .utils import import_netcdf_to_climatmois, extract_netcdf_info  # à adapter selon l'implémentation

def netcdf_import_view(request):
    if request.method == 'POST':
        if 'confirm_import' in request.POST:
            # Étape 2 : confirmation import
            tmp_path = request.session.get('tmp_netcdf_path')
            if not tmp_path or not os.path.exists(tmp_path):
                messages.error(request, "Fichier temporaire introuvable. Veuillez recommencer.")
                return redirect('observation:netcdf_import_view')

            try:
                # Copier dans un dossier temporaire à droits garantis
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp_copy_path = os.path.join(tmpdir, os.path.basename(tmp_path))
                    shutil.copy(tmp_path, tmp_copy_path)
                    import_netcdf_to_climatmois(tmp_copy_path)
                messages.success(request, "Import NetCDF réussi.")
            except Exception as e:
                messages.error(request, f"Erreur lors de l'import : {e}")
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                        tmp_dir = os.path.dirname(tmp_path)
                        if os.path.isdir(tmp_dir):
                            os.rmdir(tmp_dir)
                    except Exception:
                        pass
                request.session.pop('tmp_netcdf_path', None)
                request.session.pop('netcdf_info', None)

            return redirect('observation:netcdf_import_view')

        else:
            # Étape 1 : upload et extraction infos
            form = NetcdfImportForm(request.POST, request.FILES)
            if form.is_valid():
                nc_file = form.cleaned_data['netcdf_file']

                tmp_dir = tempfile.mkdtemp(prefix="netcdf_upload_")
                tmp_path = os.path.join(tmp_dir, nc_file.name)

                with open(tmp_path, 'wb+') as f:
                    for chunk in nc_file.chunks():
                        f.write(chunk)

                try:
                    info = extract_netcdf_info(tmp_path)
                except Exception as e:
                    messages.error(request, f"Erreur lecture fichier NetCDF : {e}")
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                    if os.path.isdir(tmp_dir):
                        os.rmdir(tmp_dir)
                    return redirect('observation:netcdf_import_view')

                request.session['tmp_netcdf_path'] = tmp_path
                request.session['netcdf_info'] = info

                return render(request, 'climat/netcdf_import_confirm.html', {'info': info})

    else:
        form = NetcdfImportForm()
        tmp_path = request.session.get('tmp_netcdf_path')
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                tmp_dir = os.path.dirname(tmp_path)
                if os.path.isdir(tmp_dir):
                    os.rmdir(tmp_dir)
            except Exception:
                pass
        request.session.pop('tmp_netcdf_path', None)
        request.session.pop('netcdf_info', None)

    return render(request, 'climat/netcdf_import.html', {'form': form})



