import os
import glob
from django.core.management.base import BaseCommand
from meteowise.utils import download_netcdf_era, import_netcdf_to_climatmois

from pprint import pprint
class Command(BaseCommand):
    help = "Importer un fichier NetCDF dans ClimatMois"

    def add_arguments(self, parser):
        parser.add_argument('--netcdf_file', type=str, help='Chemin vers le fichier NetCDF')
        parser.add_argument('--variables', nargs='+', type=str, help="Variables à télécharger depuis ERA5")
        parser.add_argument('--year', nargs='+', type=str)
        parser.add_argument('--month', nargs='+', type=str)

    def handle(self, *args, **options):
        netcdf_file = options.get('netcdf_file')
        variables = options.get('variables')
        year = options.get('year')
        month = options.get('month')

        if netcdf_file:
            self.stdout.write(f"Import du fichier : {netcdf_file}")
            import_netcdf_to_climatmois(netcdf_file)
        else:
            netcdfs = download_netcdf_era(varias=variables, year=year, month=month)
            for nc in netcdfs:
                self.stdout.write(f"Import du fichier : {nc}")
                import_netcdf_to_climatmois(nc)
                try:
                    os.remove(nc)
                except Exception as e:
                    self.stderr.write(f"Erreur suppression {nc} : {e}")
