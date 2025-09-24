import os
import zipfile
import requests
import datetime
from datetime import date

import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask
from rasterio.windows import from_bounds
from rasterio.plot import reshape_as_image, plotting_extent

from PIL import Image

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.patches import Patch
import matplotlib.patches as patches
from matplotlib.colors import ListedColormap
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

import geopandas as gpd

import cartopy.crs as ccrs
import cartopy.feature as cfeature

from pprint import pprint
def delete_files_by_extension(extensions, directory='.'):
    """
    Deletes all files in a given directory with the specified extensions.

    :param extensions: List of extensions to delete (e.g., ['.zip', '.tif', '.png'])
    :param directory: Directory to search for files (default is current directory '.')
    """
    for filename in os.listdir(directory):
        if any(filename.endswith(ext) for ext in extensions):
            file_path = os.path.join(directory, filename)
            try:
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
def get_previous_decade_code(date_now=None):
    if date_now is not None:
        today = date_now.date()
    else:
        today = date.today()

    day = today.day
    month = today.month
    year = today.year

    # Identifier la décade actuelle
    if day <= 10:
        current_decade = 1
    elif day <= 20:
        current_decade = 2
    else:
        current_decade = 3

    # Passer à la décade précédente
    if current_decade == 1:
        decade = 3
        if month == 1:
            month = 12
            year -= 1
        else:
            month -= 1
    else:
        decade = current_decade - 1

    return f"{decade:02d}{month:02d}{year}"
def get_last_complete_decade():
    today = datetime.date.today()
    year = today.year
    doy = today.timetuple().tm_yday
    last_complete_decade = (doy -1 ) // 10 + 1
    # Reculer de 1 pour prendre la decade précédente
    return (year, last_complete_decade - 1)

def get_decade_label(year, decade_number):
    months = [
        "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
        "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
    ]

    month_index = (decade_number - 1) // 3
    decade_in_month = (decade_number - 1) % 3 + 1

    # Formater le préfixe ordinal
    if decade_in_month == 1:
        prefix = "1ère"
    else:
        prefix = f"{decade_in_month}ème"

    month_name = months[month_index]

    return f"{prefix} décade {month_name} {year}"
def build_url_and_names(year,decade):
    base_url = "https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/africa/west/dekadal/evmodis/ndvi/differencepreviousyear/downloads/dekadal/"

    zip_name = f"wa{year:04d}{decade:02d}dif.zip"
    tif_name = f"wa{year:04d}{decade:02d}dif.tif"
    tif_namebis = f"wa{year:04d}{decade:02d}difm.tif"
    return base_url + zip_name, zip_name, tif_name, tif_namebis

def download_zip(url, zip_name):

    print(f"Téléchargement de {zip_name} depuis {url}...")
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(zip_name, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        print("✅ Téléchargement terminé.")
        return True
    else:
        print(f"❌ Échec du téléchargement : {r.status_code}")
        return False

def extract_tif(zip_name, tif_name, tif_namebis, output_dir="."):
    with zipfile.ZipFile(zip_name, 'r') as zip_ref:
        for name in [tif_name, tif_namebis]:
            if name in zip_ref.namelist():
                zip_ref.extract(name, path=output_dir)
                print(f"✅ Fichier extrait : {name}")
                return os.path.join(output_dir, name)
        print(f"❌ Aucun fichier tif attendu trouvé dans {zip_name}")
        return None

def plot_tiff_with_original_colormap(tif_path, shapefile_path, output_image="ndvi_colormap_map.png"):
    # Charger shapefile
    shape = gpd.read_file(shapefile_path)
    shape = shape.to_crs('EPSG:4326')

    # Charger raster
    with rasterio.open(tif_path) as src:
        # Appliquer le masque du shapefile
        image, transform = mask(src, shape.geometry, crop=True)
        data = image[0]
        data = data.astype(np.float32)  # conversion en float pour accepter les NaN
        data[data == src.nodata] = np.nan

        # Tenter de récupérer la palette de couleurs
        cmap_dict = src.colormap(1)
        cmap_array = np.array([cmap_dict.get(i, (0, 0, 0)) for i in range(256)], dtype=np.uint8)
        cmap_array = cmap_array / 255.0  # Normalisation pour matplotlib
        cmap = ListedColormap(cmap_array)

    # Déterminer l’étendue géographique
    extent = [
        transform[2],
        transform[2] + transform[0] * data.shape[1],
        transform[5] + transform[4] * data.shape[0],
        transform[5]
    ]

    # Affichage
    plt.figure(figsize=(10, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent(extent, crs=ccrs.PlateCarree())

    im = ax.imshow(data, origin='upper', extent=extent, transform=ccrs.PlateCarree(),
                   cmap=cmap, interpolation='none')

    ax.add_feature(cfeature.BORDERS)
    ax.add_feature(cfeature.COASTLINE)
    ax.set_title("NDVI Mean Anomaly (Palette originale)", fontsize=14)
    cbar = plt.colorbar(im, ax=ax, orientation='vertical', label='Valeur NDVI')
    plt.tight_layout()

    plt.savefig(output_image, dpi=300)
    print(f"✅ Carte enregistrée avec la palette TIFF : {output_image}")


def crop_tif_keep_meta(input_tif, shapefile, output_tif):
    shapes = gpd.read_file(shapefile).to_crs("EPSG:4326")

    with rasterio.open(input_tif) as src:
        out_image, out_transform = mask(src, shapes.geometry, crop=True)

        out_meta = src.meta.copy()

        # Tenter de récupérer la colormap
        colormap = None
        if src.count == 1:
            try:
                colormap = src.colormap(1)
            except Exception:
                pass

        # Mettre à jour les métadonnées de sortie
        out_meta.update({
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
            "count": 1,
            "dtype": 'uint8'  # s'assurer que le type est bien uint8
        })

        with rasterio.open(output_tif, "w", **out_meta) as dest:
            dest.write(out_image)
            if colormap:
                dest.write_colormap(1, colormap)

    print(f"✅ Découpage terminé : {output_tif}")
# def tiff_to_colored_png(tif_path, png_path):
#     with rasterio.open(tif_path) as src:
#         band = src.read(1)
#         cmap = src.colormap(1)
#         nodata_val = src.nodata if src.nodata is not None else 0

#         # Initialiser RGB avec du blanc partout
#         rgb = np.full((band.shape[0], band.shape[1], 3), 255, dtype=np.uint8)

#         # Appliquer la colormap uniquement aux valeurs valides ≠ nodata
#         for val, color in cmap.items():
#             if val == nodata_val:
#                 continue
#             mask = (band == val)
#             rgb[mask] = color[:3]  # ignore alpha

#         # Enregistrer en PNG
#         img = Image.fromarray(rgb)
#         img.save(png_path)
#         print(f"✅ PNG avec fond blanc créée : {png_path}")

def tiff_to_png_with_annotations(tif_path, png_path, shapefile=None, logo_path=None, title="", legend_dict=None):
    with rasterio.open(tif_path) as src:
        band = src.read(1)
        cmap = src.colormap(1)
        nodata_val = src.nodata if src.nodata is not None else 0

        # Création image RGB blanche
        rgb = np.full((band.shape[0], band.shape[1], 3), 255, dtype=np.uint8)

        for val, color in cmap.items():
            if val == nodata_val:
                continue
            mask = (band == val)
            rgb[mask] = color[:3]

        # Dimensions géographiques
        extent = plotting_extent(src)

    # Affichage avec matplotlib
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(rgb, extent=extent)
    # ax.set_title(title, fontsize=16)
    
    
    # Ajout des contours shapefile
    if shapefile:
        gdf = gpd.read_file(shapefile).to_crs("EPSG:4326")
        gdf.boundary.plot(ax=ax, edgecolor='black', linewidth=1)
        
        # Optionnel : ajouter du texte (nom des entités)
        for idx, row in gdf.iterrows():
            if row.geometry.centroid.is_valid:
                x, y = row.geometry.centroid.x, row.geometry.centroid.y
                ax.text(x, y, str(row.get("ADM1_FR", f"{idx}")), fontsize=8, ha='center', fontweight='bold')

    # Ajout de légende manuelle
    if legend_dict:
        # legend_elements = [
        #     Patch(facecolor=np.array(color)/255, label=label)
        #     for val, color in cmap.items()
        #     if (label := legend_dict.get(val))
        # ]
        legend_elements = [
            Patch(facecolor=tuple(c / 255 for c in legend[val]["color"][:3]),
                  label=legend[val]["label"])
            for val in legend
        ]
        ax.legend(handles=legend_elements, loc='upper left', title='Légende')
    # Ajout du logo 
    # Chargement du logo
    if logo_path :
        # logo = mpimg.imread(logo_path)  # remplace par le vrai chemin

        # # Ajout du logo en bas à droite
        # fig.figimage(
        #     logo,
        #     xo=int(fig.bbox.xmax - logo.shape[1] - 10),  # 10 px depuis le bord droit
        #     yo=int(fig.bbox.ymin + 10),                 # 10 px depuis le bas
        #     origin='upper',
        #     zorder=10
        # )

        logo = mpimg.imread(logo_path)
        fig_width, fig_height = fig.get_size_inches() * fig.dpi
        max_logo_size = min(fig_width, fig_height) * 0.05  # 5 % de la dimension minimale

        zoom = max_logo_size / max(logo.shape[:2])  # adapte le zoom à la taille du logo

        # Création de l'image et de l'annotation
        imagebox = OffsetImage(logo, zoom=zoom)
        ab = AnnotationBbox(
            imagebox,
            xy=(0.99, 0.01),             # position en bas à droite
            xycoords='axes fraction',
            box_alignment=(1, 0),        # coin bas droit
            frameon=False,
            zorder=10
        )
        ax.add_artist(ab)


    # Ajouter un cadre autour de toute la figure
    fig.patches.extend([
        patches.Rectangle(
            (0, 0),         # coin inférieur gauche en coordonnées normalisées
            1,              # largeur = 100% de la figure
            1,              # hauteur = 100% de la figure
            linewidth=2,
            edgecolor='gray',
            facecolor='none',
            transform=fig.transFigure,
            zorder=1000
        )
    ])

    fig.suptitle(title, fontsize=12, fontweight='bold', y=0.1, ha='center')
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(png_path, dpi=300)
    plt.close()
    print(f"✅ PNG annotée enregistrée : {png_path}")
# --- Script principal ---
if __name__ == "__main__":
    now = datetime.datetime.now()
    print(now.strftime("[%Y-%m-%d %H:%M:%S]"))
    decadal = get_last_complete_decade()
    bbox = (-5.5, 9.0, 2.5, 15.0)  # Burkina Faso approx
    url, zip_name, tif_name, tif_namebis = build_url_and_names(decadal[0], decadal[1])
    go = True
    current_decade = get_previous_decade_code()
    pathdata = os.path.dirname(os.path.abspath(__file__))
    results_dir = f"{pathdata}/../../../media/agromet/ndvi/{current_decade}"
    os.makedirs(results_dir, exist_ok=True)
    png_name = f'{results_dir}/NDVI_diff.png'
    if os.path.exists(png_name):
        go = False
        print("✅ Données existantes")
        exit()
    else :
        go = download_zip(url, zip_name)
    if go :
        tif_path = extract_tif(zip_name, tif_name, tif_namebis)
        if tif_path:
            pathdata = os.path.dirname(os.path.abspath(__file__))
            shapefile_path = os.path.join(pathdata,"data/regions.shp")
            logo_path = os.path.join(pathdata,"data/anam.png")
            # shapefile_path = "data/regions.shp"
            # logo_path = "data/anam.png"
            crop_tif_keep_meta(tif_path, shapefile_path, output_tif="Diffndvi_original_tif.tif")
            # tiff_to_colored_png("ndvi_original_tif.tif","ndvi_original_tif.png")

            legend = {
                1: {"label": "Plan d'eau/couverture nuageuse", "color": (250, 250, 250, 255)},
                2: {"label": "Végétation en baisse", "color": (126, 72, 0, 255)},
                3: {"label": "Végétation similaire", "color": (214, 220, 213, 255)},
                4: {"label": "Végétation en légère hausse", "color": (137, 180, 133, 255)},
                5: {"label": "Végétation en hausse", "color": (75, 131, 68, 255)},
            }

            titre = "Ecart de NDVI par rapport à l'année précédente/FEWSET/ANAM-BF/"+get_decade_label(decadal[0], decadal[1])
            tiff_to_png_with_annotations(
                tif_path="Diffndvi_original_tif.tif",
                png_path=png_name,
                shapefile=shapefile_path,
                logo_path=logo_path,
                title=titre,
                legend_dict=legend
            )
        delete_files_by_extension(['.zip', '.tif', '.png'],'.')
    else:
        print("❌ Échec : données manquantes!")