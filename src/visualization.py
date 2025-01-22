
import ee
import folium
from config.config import Config
from src.vector_mask import get_vector_mask_centroid

def set_new_map(map: folium.Map = None, image: ee.Image = None, viz_params_type: str = None, name: str = None, file_path: str = None) -> folium.Map: 
    """Initialize a folium map."""
    if map is None:
        print("Setting initial map")
        map = set_initial_map()
    if image:
        map = add_ee_layer(map, image, viz_params_type, name)
        map = save_map_output(map, file_path)
    return map

# Setting map characteristics
def set_initial_map(map_zoom = Config.MAP_ZOOM_START):
    """Set the map configuration."""
    centroid = get_vector_mask_centroid()
    map_center = [centroid.y.mean(), centroid.x.mean()] 
    map = folium.Map(location=map_center, zoom_start=map_zoom)
    return map

def add_ee_layer(map: folium.Map, ee_image_object: ee.Image, vis_params_type: str, name: str):
    """Add a Google Earth Engine layer to a folium map."""
    # Setting image visualization parameters
    vis_params = VIZ_PARAMS[vis_params_type]
    if not vis_params:
        raise ValueError(f"Invalid visualization parameter type: {vis_params_type}")
    map_id_dict = ee_image_object.getMapId(vis_params)
    folium.TileLayer(
        tiles=map_id_dict['tile_fetcher'].url_format,
        attr='Google Earth Engine',
        name=name,
        overlay=True,
        control=True
    ).add_to(map)
    
     # Add layer control to the map
    folium.LayerControl().add_to(map)
    return map

# Saving map output
def save_map_output(map, file_path):
    """Save the map to an HTML file."""
    map.save(file_path)
    print(f"Map has been saved to {file_path}")
    return map

# Visualization parameters
VIZ_PARAMS = {
    'natural': {
        'bands': ['B4', 'B3', 'B2'],
        'min': 0,
        'max': 0.3,
        'gamma': 1.4,
        'scale': 10,
        'format': 'png',     # Better quality format
        'quantization': 0
    },
    'ndvi': {
        'bands': ['NDVI'],
        'min': -1,
        'max': 1,
        'palette': ['blue', 'white', 'green']
    },
    'lst': {
        'bands': ['LST'],
        'min': 20,
        'max': 40,
        'palette': ['blue', 'yellow', 'red']
    },
    'toa': {
        'bands': ['B4', 'B3', 'B2'], 
        'max': 0.2, 
        'scale': 10,
        'format': 'png',     # Better quality format
        'quantization': 0
    }
}