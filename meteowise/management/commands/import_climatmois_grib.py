import os
import glob
from django.core.management.base import BaseCommand
from meteowise.utils import download_netcdf_era, download_grib_era, import_grib1_to_climatmois

from pprint import pprint

class Command(BaseCommand):
    help = "Importer un fichier GRIB1 dans ClimatMois"

    def add_arguments(self, parser):
        parser.add_argument(
            '--grib_file',
            type=str,
            help='Chemin vers le fichier GRIB à importer (optionnel si --variables est fourni)'
        )
        parser.add_argument(
            '--variables',
            nargs='+',
            type=str,
            help="Nom(s) de la ou des variables à télécharger depuis ERA5, ex: --variable 2m_temperature evaporation"
        )
        parser.add_argument(
            '--year',
            nargs='+',
            type=str,
            help='Année(s) au format YYYY, ex: --year 2023 2024'
        )
        parser.add_argument(
            '--month',
            nargs='+',
            type=str,
            help='Mois au format MM, ex: --month 05 06 07'
        )

    def handle(self, *args, **options):
        grib_file = options.get('grib_file')
        variables = options.get('variables')
        year = options['year'] if options.get('year') else None
        month = options['month'] if options.get('month') else None

        if grib_file:
            try :
                self.stdout.write(f"Import du fichier : {grib_file}")
                import_grib1_to_climatmois(grib_file)
            except Exception as e:
                print(e)
        else:
            gribs = download_grib_era(varias=variables, year=year, month=month)
            for grib_file in gribs:
                self.stdout.write(f"Import du fichier : {grib_file}")
                import_grib1_to_climatmois(grib_file)
                # Suppression du fichier GRIB
                try:
                    os.remove(grib_file)
                    # self.stderr.write(f"Info {grib_file} Supprimé")
                except Exception as e:
                    self.stderr.write(f"Erreur suppression {grib_file} : {e}")

                # Suppression des fichiers .grib.*.idx correspondants
                idx_pattern = f"{grib_file}.*.idx"
                idx_files = glob.glob(idx_pattern)
                for idx_file in idx_files:
                    try:
                        os.remove(idx_file)
                        # self.stderr.write(f"Info {idx_file} Supprimé")
                    except Exception as e:
                        self.stderr.write(f"Erreur suppression {idx_file} : {e}")
