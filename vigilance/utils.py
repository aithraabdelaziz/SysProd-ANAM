# vigilance/utils.py
import folium
import geopandas as gpd
from .models import VigimetProvince

def create_map_html(df, param, forecast_date):
    shapefile_path = "./gadm_bfa/gadm41_BFA_2.shp"
    provinces = gpd.read_file(shapefile_path).to_crs("EPSG:4326")

    merged = provinces.merge(df, left_on='NAME_2', right_on='province_name', how='left')
    merged['forecast_date'] = merged['forecast_date'].astype(str)

    colors = {0: '#00FF00', 1: '#FFFF00', 2: '#FFA500', 3: '#FF0000', None: '#808080'}

    def style_function(feature):
        vigilance = feature['properties'].get('vigilance_level')
        return {
            'fillColor': colors.get(vigilance, '#808080'),
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.7,
        }

    # Ici on peut aussi générer le popup html (idem que ton code original)

    center_lat, center_lon = 12, -1
    m = folium.Map(location=[center_lat, center_lon], zoom_start=7, tiles='cartodbpositron')

    folium.GeoJson(merged, style_function=style_function, name=f"Vigilance {param.upper()}").add_to(m)
    bounds = merged.total_bounds
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    # CSS et JS statiques
    m.get_root().header.add_child(folium.Element('<link rel="stylesheet" href="/static/css/popup.css">'))
    m.get_root().header.add_child(folium.Element('<script src="/static/js/popup_behavior.js"></script>'))

    return m._repr_html_()
