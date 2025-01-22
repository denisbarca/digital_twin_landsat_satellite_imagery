from datetime import datetime
import ee
from config.config import Config
import folium
from src.vector_mask import get_vector_mask, get_vector_mask_centroid, get_vector_mask_coords

class EEUtils:
    def __init__(self, image_collection_code: str, roi: ee.Geometry, start_date: str, end_date: str, cloud_cover: float, target_crs: str, target_scale: int):
        self.image_collection_code = image_collection_code
        self.roi = roi
        self.start_date = start_date
        self.end_date = end_date
        self.cloud_cover = cloud_cover
        self.target_crs = target_crs
        self.target_scale = target_scale
    
def initialize_ee():
    """Initialize Earth Engine."""
    try:
        ee.Initialize()
        print("Google Earth Engine has been initialized successfully")
    except Exception as e:
            ee.Authenticate()
            ee.Initialize()
        
# Processing image
def get_landsat_image_processed(self: EEUtils) -> ee.Image:
    """Get a processed Landsat image."""
    collection = get_landsat_collection(self)
    image = get_landsat_image(collection)
    image = clip_image_to_roi(self, image)
    # display_image_on_map(image, self.roi, map_center)
    repro_image = resample_reproject_image(image, self)
    print(get_image_info(repro_image))
    return repro_image
    
def get_landsat_collection(self: EEUtils) -> ee.ImageCollection:
    """Get Landsat 8/9 collection filtered by parameters."""
    return ee.ImageCollection(self.image_collection_code) \
        .filterBounds(self.roi) \
        .filterDate(self.start_date, self.end_date) \
        .filter(ee.Filter.lt('CLOUD_COVER', self.cloud_cover)) \
        .map(mask_clouds)
        # .map(scale_factors) \
        
def get_landsat_image(collection: ee.ImageCollection) -> ee.Image:
    """Get the first image from a Landsat collection."""
    if len(collection.getInfo()['features']) == 0:
        raise ValueError("No images found in the collection")
    else:
        return ee.Image(collection.sort('system:time_start', False).first())

def resample_reproject_image(image: ee.Image, self: EEUtils) -> ee.Image:
    """Resample and reproject an image."""
    return image.reproject(crs=self.target_crs, scale=self.target_scale)

def clip_image_to_roi(self, image: ee.Image) -> ee.Image:
    """Clip the image to the region of interest (ROI)."""
    return image.clip(self.roi)
        
# Enhnacing image visualization
def scale_factors(image):
    """Apply scaling factors to Landsat bands."""
    optical_bands = image.select(['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B9']).multiply(0.0000275).add(-0.2)
    thermal_bands = image.select(['B10', 'B11']).multiply(0.00341802).add(149.0)
    return image.addBands(optical_bands, None, True).addBands(thermal_bands, None, True)   

def mask_clouds(image):
    """Mask clouds and cloud shadows."""
    qa = image.select('QA_PIXEL')
    cloud = qa.bitwiseAnd(1 << 3).eq(0)  # Clear pixels
    shadow = qa.bitwiseAnd(1 << 4).eq(0)  # No cloud shadow
    return image.updateMask(cloud).updateMask(shadow) 
        
# Utils image info
def get_image_info(image: ee.Image) -> dict:
    """Get the info of an image.
    Es. LANDSAT/LC09/C02/T1_TOA/LC09_190031_20240811"""
    
    image_id = image.get('system:id').getInfo()
    acquisition_time = datetime.utcfromtimestamp(
        image.get("system:time_start").getInfo() / 1000
    )
    return {
        'code_satellite': image_id.split('/')[0],
        'type_satellite': image_id.split('/')[1],
        'type_collection': image_id.split('/')[2],
        'tier_quality': image_id.split('/')[3].split('_')[0],
        'type_image': image_id.split('/')[3].split('_')[1],
        'date_time_acquisition': acquisition_time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
