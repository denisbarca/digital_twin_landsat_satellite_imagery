import ee
import geemap
from datetime import datetime
from config.config import Config
from src import vector_mask
from src.ee_utils import EEUtils, get_landsat_image_processed, initialize_ee
from src.lst_calculator import compute_lst, compute_toa_manual
from src.vector_mask import get_vector_mask_coords
from src.visualization import set_new_map

def export_image_to_local(image: ee.Image, description: str, file_path: str, region: ee.Geometry, scale: int, crs: str):
    """Export an image to local machine as GeoTIFF."""
    geemap.ee_export_image(
        image=image,
        filename=file_path,
        scale=scale,
        region=region,
        crs=crs,
        file_per_band=False
    )
    print(f"Exporting {description} to local machine as {file_path}")
    
def main():
    # m = init_map()
    # Initialize Earth Engine
    initialize_ee()
    
    # Get Landsat collection
    image_config = EEUtils(
        Config.IMAGE_COLLECTION, 
        ee.Geometry.Polygon(get_vector_mask_coords()), 
        Config.START_DATE, 
        Config.END_DATE, 
        Config.CLOUD_COVER_THRESHOLD, 
        Config.TARGET_CRS, 
        Config.EXPORT_SCALE
    )
    image = get_landsat_image_processed(image_config)
    # map = set_new_map(
    #     image=image, 
    #     viz_params_type='natural', 
    #     name='Landsat 9 Ciampino Natural Color', 
    #     file_path='data/output/landsat_natural_image_map.html'
    # )
    print('Map initialized')
    image_lst = compute_lst(image)
    # export_image_to_local(
    #     image=image_lst,
    #     description='LST_Export',
    #     file_path='data/output/Landsat_LST.tif',
    #     region=ee.Geometry.Polygon(get_vector_mask_coords()),
    #     scale=Config.EXPORT_SCALE,
    #     crs=image_lst.projection().crs().getInfo()
    # )
    map_lst = set_new_map(
        image=image_lst, 
        viz_params_type='lst', 
        name='Landsat 9 Ciampino LST Color', 
        file_path='data/output/landsat_LST.html'
    )
    
    # # Export LST image to local machine as GeoTIFF
    # export_image_to_local(
    #     image=image_lst,
    #     description='LST_Export',
    #     file_path='data/output/Landsat_LST.tif',
    #     region=ee.Geometry.Polygon(get_vector_mask_coords()),
    #     scale=Config.EXPORT_SCALE,
    #     crs=image_lst.projection().crs().getInfo()
    # )
    
    
if __name__ == "__main__":
    main()