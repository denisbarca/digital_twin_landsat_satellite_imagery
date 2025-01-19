# config/config.py
class Config:
    # Earth Engine parameters
    IMAGE_COLLECTION = 'LANDSAT/LC09/C02/T1_TOA'
    CLOUD_COVER_THRESHOLD = 10
    EXPORT_SCALE = 10
    TARGET_CRS = 'EPSG:4326'
    
    # LST calculation parameters
    LSE_COEFFICIENT = 0.004
    LSE_CONSTANT = 0.986
    WAVELENGTH = 0.00115
    CONSTANT_PLANCK = 1.4388        
    
    # Visualization parameters
    MAP_ZOOM_START = 13
    LST_MIN_TEMP = 20
    LST_MAX_TEMP = 40
    LST_PALETTE = ['blue', 'yellow', 'red']
    
    # Export parameters
    EXPORT_SCALE = 30
    MAX_PIXELS = 1e9
    
    # Vector mask parameters
    FILE_PATH_LOCAL = 'data/vector_mask/'