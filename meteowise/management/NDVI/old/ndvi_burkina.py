import geopandas as gpd
from rasterio.mask import mask
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

import datetime
import requests
import zipfile
import os
import rasterio
from rasterio.windows import from_bounds
import pandas as pd
import numpy as np
from datetime import date
from pprint import pprint
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
    base_url = "https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/africa/west/dekadal/evmodis/ndvi/meananomaly/downloads/dekadal/"

    zip_name = f"wa{year:04d}{decade:02d}ltmean.zip"
    tif_name = f"wa{year:04d}{decade:02d}ltmean.tif"
    tif_namebis = f"wa{year:04d}{decade:02d}ltmeanm.tif"
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

def plot_tiff_on_shape(tif_path, shapefile_path, output_image="ndvi_map.png"):
    # Charger shapefile
    shape = gpd.read_file(shapefile_path)
    shape = shape.to_crs('EPSG:4326')

    # Charger le raster
    with rasterio.open(tif_path) as src:
        out_image, out_transform = mask(src, shape.geometry, crop=True)
        data = out_image[0]
        # data[data == src.nodata] = np.nan

    # Déterminer l'étendue
    extent = [
        out_transform[2],
        out_transform[2] + out_transform[0] * data.shape[1],
        out_transform[5] + out_transform[4] * data.shape[0],
        out_transform[5]
    ]

    # Affichage
    plt.figure(figsize=(10, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    im = ax.imshow(data, origin='upper', extent=extent, transform=ccrs.PlateCarree(),
                   cmap='YlGn', interpolation='none')
    ax.add_feature(cfeature.BORDERS)
    ax.add_feature(cfeature.COASTLINE)
    ax.set_title("NDVI Mean Anomaly (Décade)", fontsize=14)
    plt.colorbar(im, ax=ax, orientation='vertical', label='NDVI Anomaly')
    plt.tight_layout()

    # Enregistrement de l'image
    plt.savefig(output_image, dpi=300)
    print(f"✅ Carte enregistrée sous : {output_image}")

def plot_tiff_with_original_colormap(tif_path, shapefile_path, output_image="ndvi_colormap_map.png"):
    import matplotlib.pyplot as plt
    import geopandas as gpd
    from rasterio.plot import reshape_as_image
    import rasterio
    from rasterio.mask import mask
    import numpy as np
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

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
        from matplotlib.colors import ListedColormap
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

import rasterio
from rasterio.mask import mask
import geopandas as gpd
import numpy as np
from PIL import Image

def crop_tiff_and_export_png_gris(tif_path, shapefile_path, output_png_path="ndvi_original_tif.png"):
    # Lire le shapefile (Burkina)
    shapes = gpd.read_file(shapefile_path)
    shapes = shapes.to_crs("EPSG:4326")

    with rasterio.open(tif_path) as src:
        # Découper le raster avec le shapefile
        out_image, out_transform = mask(src, shapes.geometry, crop=True)
        out_meta = src.meta.copy()
        out_image = out_image[0]  # Supposer une seule bande

        # Gérer les valeurs NoData
        if src.nodata is not None:
            out_image = np.where(out_image == src.nodata, 0, out_image)

        # Vérifier la colormap
        if 'colormap' in src.tags(1):
            colormap = src.colormap(1)
            # Convertir le colormap en format Pillow
            palette = []
            for i in range(256):
                rgb = colormap.get(i, (0, 0, 0))
                palette.extend(rgb)
            # S'assurer que la palette fait 768 valeurs (256*3)
            palette += [0, 0, 0] * (256 - len(colormap))

            # Créer une image PIL en mode 'P' (palette)
            img = Image.fromarray(out_image.astype(np.uint8), mode='P')
            img.putpalette(palette)
        else:
            # Pas de colormap => grayscale
            img = Image.fromarray(out_image.astype(np.uint8), mode='L')

        img.save(output_png_path)
        print(f"✅ PNG enregistré : {output_png_path}")

def crop_tiff_and_export_png(tif_path, shapefile_path, output_png_path):
    shapes = gpd.read_file(shapefile_path)
    shapes = shapes.to_crs("EPSG:4326")

    with rasterio.open(tif_path) as src:
        out_image, out_transform = mask(src, shapes.geometry, crop=True)
        out_meta = src.meta.copy()
        band = out_image[0]

        nodata = src.nodata
        if nodata is not None:
            band = np.where(band == nodata, 0, band)

        # Normaliser les données en indices 0-255 si nécessaire
        min_val = band.min()
        max_val = band.max()
        if max_val > 255 or min_val < 0 or not np.issubdtype(band.dtype, np.uint8):
            band_norm = ((band - min_val) / (max_val - min_val) * 255).astype(np.uint8)
        else:
            band_norm = band.astype(np.uint8)

        # Gestion palette
        try:
            colormap = src.colormap(1)
            pprint(colormap)
        except Exception:
            colormap = None

        if colormap:
            palette = []
            for i in range(256):
                rgb = colormap.get(i, (0, 0, 0))
                palette.extend(rgb)
            palette = palette[:768]
            palette += [0] * (768 - len(palette))
            img = Image.fromarray(band_norm, mode='P')
            img.putpalette(palette)
        else:
            img = Image.fromarray(band_norm, mode='L')

        img.save(output_png_path)
        print(f"✅ PNG sauvegardé : {output_png_path}")
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
def tiff_to_colored_png(tif_path, png_path):
    with rasterio.open(tif_path) as src:
        band = src.read(1)
        cmap = src.colormap(1)
        nodata_val = src.nodata if src.nodata is not None else 0

        # Initialiser RGB avec du blanc partout
        rgb = np.full((band.shape[0], band.shape[1], 3), 255, dtype=np.uint8)

        # Appliquer la colormap uniquement aux valeurs valides ≠ nodata
        for val, color in cmap.items():
            if val == nodata_val:
                continue
            mask = (band == val)
            rgb[mask] = color[:3]  # ignore alpha

        # Enregistrer en PNG
        img = Image.fromarray(rgb)
        img.save(png_path)
        print(f"✅ PNG avec fond blanc créée : {png_path}")

def crop_tif_keep_colormap(input_tif, shapefile, output_tif):
    shapes = gpd.read_file(shapefile)
    shapes = shapes.to_crs("EPSG:4326")  # adapter si besoin

    # Définition de la colormap NDVI basée sur l'image
    ndvi_colormap = {
        0: (255, 0, 0),       # Rouge pour < -0.3
        1: (255, 85, 0),      # Orange-rouge pour -0.2
        2: (255, 170, 0),     # Orange pour -0.1
        3: (255, 255, 0),    # Jaune pour -0.05
        4: (255, 255, 255),  # Blanc pour 0.05 (no difference)
        5: (170, 255, 0),    # Vert clair pour 0.1
        6: (85, 255, 0),     # Vert moyen pour 0.2
        7: (0, 255, 0)       # Vert foncé pour >0.3
    }
    
    with rasterio.open(input_tif) as src:
        out_image, out_transform = mask(src, shapes.geometry, crop=True)
        out_meta = src.meta.copy()

        out_meta.update({
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform
        })

        with rasterio.open(output_tif, "w", **out_meta) as dest:
            dest.write(out_image)

            # Appliquer la colormap NDVI personnalisée
            # if src.count == 1:  # Si image à une seule bande
            dest.write_colormap(1, ndvi_colormap)

    print(f"Découpage terminé, sauvegardé avec colormap NDVI dans {output_tif}")

import rasterio
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import geopandas as gpd
import matplotlib.image as mpimg
import matplotlib.patches as patches
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

def tiff_to_png_with_annotations(tif_path, png_path, shapefile=None, logo_path=None, title="", legend_dict=None):
    import rasterio
    import numpy as np
    from PIL import Image
    import matplotlib.pyplot as plt
    import geopandas as gpd
    from rasterio.plot import plotting_extent
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
        from matplotlib.patches import Patch
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
            (0, 0),                             # coin inférieur gauche
            fig.bbox.width,                    # largeur du cadre
            fig.bbox.height,                   # hauteur du cadre
            linewidth=4,                       # épaisseur du cadre
            edgecolor='black',                 # couleur du cadre
            facecolor='none',                  # pas de remplissage
            transform=fig.transFigure,         # coordonnée en unité figure
            zorder=1000                        # au-dessus de tout
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
    decadal = get_last_complete_decade()
    bbox = (-5.5, 9.0, 2.5, 15.0)  # Burkina Faso approx
    url, zip_name, tif_name, tif_namebis = build_url_and_names(decadal[0], decadal[1])
    go = False
    if os.path.exists(zip_name):
        go =True
    else :
        go = download_zip(url, zip_name)
    if go :
        tif_path = extract_tif(zip_name, tif_name, tif_namebis)
        if tif_path:
            shapefile_path = "data/regions.shp"
            logo_path = "data/anam.png"
            # plot_tiff_on_shape(tif_path, shapefile_path, output_image="ndvi_burkina.png")
            # plot_tiff_with_original_colormap(tif_path, shapefile_path, output_image="ndvi_colormap_map.png")
            # crop_tiff_and_export_png(tif_path, shapefile_path, output_png_path="ndvi_original_tif.png")
            crop_tif_keep_meta(tif_path, shapefile_path, output_tif="ndvi_original_tif.tif")
            tiff_to_colored_png("ndvi_original_tif.tif","ndvi_original_tif.png")
            # crop_tif_keep_colormap(tif_path, shapefile_path, output_tif="ndvi_originalcolormap.tif")

            legend = {
                1: {"label": "Plan d'eau/couverture nuageuse", "color": (250, 250, 250, 255)},
                2: {"label": "Végétation en baisse", "color": (126, 72, 0, 255)},
                3: {"label": "Végétation similaire", "color": (214, 220, 213, 255)},
                4: {"label": "Végétation en légère hausse", "color": (137, 180, 133, 255)},
                5: {"label": "Végétation en hausse", "color": (75, 131, 68, 255)},
            }

            titre = "Anomalie de NDVI/FEWSET/ANAM-BF/"+get_decade_label(decadal[0], decadal[1])
            png_name = 'NDVIanomalie_'+''.join([str(i) for i in decadal])+'.png'
            tiff_to_png_with_annotations(
                tif_path="ndvi_original_tif.tif",
                png_path=png_name,
                shapefile=shapefile_path,
                logo_path=logo_path,
                title=titre,
                legend_dict=legend
            )
    else:
        print("❌ Échec : données manquantes pour au moins une des deux pentades.")