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
            'DNs': image.select('B11'),
            'AR': ee.Number(radiance_add)
    })
    
    # Apply solar angle correction
    toa_corrected = toa_raw.expression(
        'TOA / cos((90 - SE) * pi/180)', {
            'TOA': toa_raw,
            'SE': ee.Number(solar_angle),
            'pi': ee.Number(np.pi)
    }).rename('TOA')

    return image.addBands(toa_corrected)

#SECOND
def compute_brightness_temperature(image: ee.Image) -> ee.Image:
    """
    Calculate Brightness Temperature (BT) from TOA radiance.
    BT = (K2 / (ln(K1/L) + 1)) - 273.15
    """
    # Get calibration constants
    k1 = image.get('K1_CONSTANT_BAND_10').getInfo()
    k2 = image.get('K2_CONSTANT_BAND_10').getInfo()
    
    # image = compute_toa_manual(image)
    # Calculate BT
    bt = image.expression(
        '(K2 / (log(K1/L) + 1)) - 273.15', {
            'K1': k1,
            'K2': k2,
            'log': ee.Number(math.e), # natural logarithm base
            'L': image.select('TOA')
        }
    ).rename('BT')
    
    return image.addBands(bt)

# THIRD
def compute_ndvi(image: ee.Image) -> ee.Image:
    """
    Calculate NDVI using image expression.
    NDVI = (NIR - RED)/(NIR + RED)
    """
    ndvi = image.expression(
        '(NIR - RED)/(NIR + RED)', {
            'NIR': image.select('B5'),
            'RED': image.select('B4')
        }
    ).rename('NDVI')
    return image.addBands(ndvi)

# FOURTH
def compute_proportion_vegetation(image: ee.Image):
    """
    Calculate proportion of vegetation (Pv) from NDVI.
    Pv = ((NDVI – NDVImin) / (NDVImax – NDVImin))²
    """
    # Get statistics from NDVI band
    # image = compute_ndvi(image)
    ndvi_stats = image.select('NDVI').reduceRegion(
        reducer=ee.Reducer.minMax(),
        geometry=image.geometry(),
        scale=Config.EXPORT_SCALE,
        maxPixels=1e9
    )
    print('pv', image.bandNames().getInfo())
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
    print(type(pv))
    return image.addBands(pv)

# FIFTH
def compute_emissivity(image: ee.Image) -> ee.Image:
    """
    Calculate surface emissivity.
    """
    pv = image.select('PV')
    print('emiss', image.bandNames().getInfo(), type(pv))
    emissivity = image.expression(
        'LSE_COEFFICIENT * PV + LSE_CONSTANT', {
            'LSE_COEFFICIENT': Config.LSE_COEFFICIENT,
            'LSE_CONSTANT': Config.LSE_CONSTANT,
            'PV': pv
        }
    ).rename('EMISSIVITY')
    
    return image.addBands(emissivity)

# FINAL
def compute_lst(image: ee.Image) -> ee.Image:
    """
    Calculate Land Surface Temperature (LST).
    LST = BT / (1 + (λ * BT / ρ) * ln(ε))
    """     
    # Calculate LST
    image = compute_toa_manual(image)
    print('TOA:', image.select('TOA').getInfo())
    with open('data/output/toa_info.txt', 'w') as f:
        f.write(f"TOA: {image.select('TOA').getInfo()}\n")
    
    image = compute_brightness_temperature(image)
    print('Brightness Temperature:', image.select('BT').getInfo())
    with open('data/output/bt_info.txt', 'w') as f:
        f.write(f"Brightness Temperature: {image.select('BT').getInfo()}\n")
    
    image = compute_ndvi(image)
    print('NDVI:', image.select('NDVI').getInfo())
    with open('data/output/ndvi_info.txt', 'w') as f:
        f.write(f"NDVI: {image.select('NDVI').getInfo()}\n")
    
    image = compute_proportion_vegetation(image)
    print('Proportion Vegetation:', image.select('PV').getInfo())
    with open('data/output/pv_info.txt', 'w') as f:
        f.write(f"PV: {image.select('PV').getInfo()}\n")
    
    print('BEFORE Emissivity:', image.bandNames().getInfo())
    image = compute_emissivity(image)
    print('Emissivity:', image.select('EMISSIVITY').getInfo())
    with open('data/output/emissivity_info.txt', 'w') as f:
        f.write(f"Emissivity: {image.select('EMISSIVITY').getInfo()}\n")

    lst = image.expression(
        'BT / (1 + (wavelength * BT / rho) * log(E))', {
            'BT': image.select('BT'),
            'wavelength': Config.WAVELENGTH,
            'rho': Config.CONSTANT_PLANCK,
            'E': image.select('EMISSIVITY'),
            'log': ee.Number(math.e)
        }
    ).rename('LST')
    
    image = add_band_to_image(image, lst)
    # Inspect DN values for the specific LST band
    lst_values = image.select('LST').reduceRegion(
        reducer=ee.Reducer.toList(),
        geometry=image.geometry(),
        scale=Config.EXPORT_SCALE,
        maxPixels=1e9
    ).get('LST').getInfo()
    with open('data/output/lst_info.txt', 'w') as f:
        f.write(f"LST: {image.select('LST').getInfo()}\n")
    print("LST DN VALUES:", lst_values)
    return image