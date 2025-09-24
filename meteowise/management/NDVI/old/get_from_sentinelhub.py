from sentinelhub import SHConfig, SentinelHubRequest, DataCollection, MimeType, CRS, BBox, bbox_to_dimensions, SentinelHubDownloadClient, SentinelHubStatistical
import datetime

# Configuration
config = SHConfig()
config.sh_client_id = 'TON_CLIENT_ID'
config.sh_client_secret = 'TON_CLIENT_SECRET'

# Bounding box sur une zone du Burkina Faso
burkina_bbox = BBox(bbox=[-1.9, 11.5, -1.2, 12.2], crs=CRS.WGS84)  # Format: [lon_min, lat_min, lon_max, lat_max]
resolution = 10  # m

# Calcul des dimensions
size = bbox_to_dimensions(burkina_bbox, resolution=resolution)

# Script Evalscript pour NDVI
evalscript_ndvi = """
//VERSION=3
function setup() {
  return {
    input: ["B4", "B8"],
    output: { bands: 1, sampleType: "FLOAT32" }
  };
}

function evaluatePixel(sample) {
  let ndvi = (sample.B8 - sample.B4) / (sample.B8 + sample.B4);
  return [ndvi];
}
"""

# Création de la requête
request = SentinelHubRequest(
    evalscript=evalscript_ndvi,
    input_data=[
        SentinelHubRequest.input_data(
            data_collection=DataCollection.SENTINEL2_L2A,
            time_interval=("2024-07-01", "2024-07-10"),  # période d’intérêt
            mosaicking_order='mostRecent'
        )
    ],
    responses=[
        SentinelHubRequest.output_response("default", MimeType.TIFF)
    ],
    bbox=burkina_bbox,
    size=size,
    config=config
)

# Téléchargement
ndvi_data = request.get_data(save_data=True)
print("NDVI raster téléchargé.")
