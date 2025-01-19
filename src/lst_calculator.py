import ee
import numpy as np
import math

from config.config import Config

def add_band_to_image(image: ee.Image, band) -> ee.Image:
    image = image.addBands(band)
    print("IMAGE BANDS:", image.bandNames().getInfo())
    return image
    
# FIRST
def compute_toa_manual(image):
    """
    Calculate TOA reflectance using the manual formula:
    ρλ' = Mρ*Qcal + Aρ
    where:
    ρλ' = TOA planetary reflectance, without correction for solar angle
    Mρ = Band-specific multiplicative rescaling factor
    Qcal = Quantized and calibrated standard product pixel values (DN)
    Aρ = Band-specific additive rescaling factor
    
    Then apply the solar angle correction:
    ρλ = ρλ' / cos(θSZ) = ρλ' / sin(θSE)
    where:
    ρλ = TOA planetary reflectance
    θSE = Local sun elevation angle
    θSZ = Local solar zenith angle, θSZ = 90° - θSE
    """
    
    # Get the constant values for the Landsat 9 TOA calculation
    solar_angle = image.get('SUN_ELEVATION').getInfo()
    radiance_mult = image.get('RADIANCE_MULT_BAND_10').getInfo()
    radiance_add = image.get('RADIANCE_ADD_BAND_10').getInfo()
    print("SOLAR ANGLE:", solar_angle)
    print("RADIANCE MULT:", radiance_mult)
    print("RADIANCE ADD:", radiance_add)
    
    # Calculate TOA without solar angle correction
    toa_raw = image.expression(
        '(MR * DNs + AR)', {
            'MR': ee.Number(radiance_mult),
            'DNs': image.select('B10'),
            'AR': ee.Number(radiance_add)
    })
    
    # Apply solar angle correction
    toa_corrected = toa_raw.expression(
        'TOA / cos((90 - SE) * pi/180)', {
            'TOA': toa_raw,
            'SE': ee.Number(solar_angle),
            'pi': ee.Number(np.pi)
    }).rename('TOA_B10')

    image = add_band_to_image(image, toa_corrected)
    return image

#SECOND
def compute_brightness_temperature(image: ee.Image) -> ee.Image:
    """
    Calculate Brightness Temperature (BT) from TOA radiance.
    BT = (K2 / (ln(K1/L) + 1)) - 273.15
    """
    # Get calibration constants
    k1 = image.get('K1_CONSTANT_BAND_10').getInfo()
    k2 = image.get('K2_CONSTANT_BAND_10').getInfo()
    
    # Calculate BT
    bt = image.expression(
        '(K2 / (ln(K1/L) + 1)) - 273.15', {
            'K1': k1,
            'K2': k2,
            'ln': ee.Number(math.e)  # natural logarithm base
        }
    ).rename('BT')
    
    image = add_band_to_image(image, bt)
    return image

# THIRD
def compute_ndvi(image: ee.Image) -> ee.Image:
    """
    Calculate NDVI using image expression.
    NDVI = (NIR - RED)/(NIR + RED)
    """
    ndvi = image.expression(
        '(NIR - RED)/(NIR + RED)', {
            'NIR': image.select('SR_B5'),
            'RED': image.select('SR_B4')
        }
    ).rename('NDVI')
    image = add_band_to_image(image, ndvi)
    return image

# FOURTH
def compute_proportion_vegetation(image: ee.Image):
    """
    Calculate proportion of vegetation (Pv) from NDVI.
    Pv = ((NDVI – NDVImin) / (NDVImax – NDVImin))²
    """
    # Get statistics from NDVI band
    image = compute_ndvi(image)
    ndvi_stats = image.select('NDVI').reduceRegion(
        reducer=ee.Reducer.minMax(),
        geometry=image.geometry(),
        scale=Config.EXPORT_SCALE,
        maxPixels=1e9
    )
    
    ndvi_min = ee.Number(ndvi_stats.get('NDVI_min'))
    ndvi_max = ee.Number(ndvi_stats.get('NDVI_max'))
    
    # Calculate Pv
    pv = image.expression(
        'pow((NDVI - NDVImin) / (NDVImax - NDVImin), 2)', {
            'NDVI': image.select('NDVI'),
            'NDVImin': ndvi_min,
            'NDVImax': ndvi_max
        }
    ).rename('PV')
    image = add_band_to_image(image, pv)
    return image

# FIFTH
def compute_emissivity(image: ee.Image):
    return Config.LSE_COEFFICIENT * compute_proportion_vegetation(image) + Config.LSE_CONSTANT

# FINAL
def compute_lst(image: ee.Image) -> ee.Image:
    """
    Calculate Land Surface Temperature (LST).
    LST = BT / (1 + (λ * BT / ρ) * ln(ε))
    """     
    # Calculate LST
    lst = image.expression(
        'BT / (1 + (wavelength * BT / rho) * ln(E))', {
            'BT': compute_brightness_temperature(image),
            'wavelength': Config.WAVELENGTH,
            'rho': Config.CONSTANT_PLANCK,
            'E': compute_emissivity(image.select('PV')),
            'ln': ee.Number(math.E)
        }
    ).rename('LST')
    
    image = add_band_to_image(image, lst)
    return image