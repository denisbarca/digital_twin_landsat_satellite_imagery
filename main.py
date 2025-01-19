import ee
from datetime import datetime
from config.config import Config
from src import vector_mask
from src.ee_utils import EEUtils, get_landsat_image_processed, initialize_ee
from src.lst_calculator import compute_toa, compute_toa_manual
from src.vector_mask import get_vector_mask_coords
from src.visualization import set_new_map

def main():
    # Initialize Earth Engine
    initialize_ee()
    
    # Get Landsat collection
    image_config = EEUtils(
        Config.IMAGE_COLLECTION, 
        ee.Geometry.Polygon(get_vector_mask_coords()), 
        "2024-08-01", 
        "2024-08-31", 
        Config.CLOUD_COVER_THRESHOLD, 
        Config.TARGET_CRS, 
        Config.EXPORT_SCALE
    )
    image = get_landsat_image_processed(image_config)
    # radiance_mult_band_10 = image.getInfo()['properties']['RADIANCE_MULT_BAND_10']
    # print('RADIANCE', radiance_mult_band_10)
    map = set_new_map(
        image=image, 
        viz_params_type='natural', 
        name='Landsat 9 Ciampino Natural Color', 
        file_path='data/output/landsat_natural_image_map.html'
    )
    image = compute_toa_manual(image)
    map = set_new_map(
        map=map,
        image=image, 
        viz_params_type='toa', 
        name='Landsat 9 Ciampino TOA Color', 
        file_path='data/output/landsat_TOA.html'
    )
    
if __name__ == "__main__":
    main()