from config.config import Config
import geopandas as gpd
import json
import os

def open_local_file(directory_path):
    """
    Opens a file from the given local directory path.

    :param directory_path: The path of the directory containing the file to open.
    :return: The content of the file.
    """
    file_name = os.listdir(directory_path)[0]
    file_path = os.path.join(directory_path, file_name)
    if file_path.endswith('.geojson'):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = json.load(file)
    elif file_path.endswith('.shp') or file_path.endswith('.gpkg'):
        content = gpd.read_file(file_path)
    else:
        raise ValueError("Unsupported file format")
    return content

def convert_crs(gdf, crs):
    """
    Convert the CRS of a GeoDataFrame.

    :param gdf: The GeoDataFrame to convert.
    :param crs: The CRS to convert to.
    :return: The converted GeoDataFrame.
    """
    return gdf.to_crs(crs)

def get_coordinates(gdf):
    """
    Get the coordinates from a GeoDataFrame.

    :param gdf: The GeoDataFrame to extract coordinates from.
    :return: A list of coordinates.
    """
    coordinates = []
    for geom in gdf.geometry:
        if geom.geom_type == 'Polygon':
            coordinates.append(list(geom.exterior.coords))
        elif geom.geom_type == 'MultiPolygon':
            for poly in geom.geoms:
                coordinates.append(list(poly.exterior.coords))
    return coordinates

def get_vector_mask():
    """
    Get the vector mask coordinates.

    :return: The vector mask coordinates.
    """
    content = open_local_file(Config.FILE_PATH_LOCAL)
    if isinstance(content, dict) and "features" in content:
        gdf = gpd.GeoDataFrame.from_features(content["features"])
    else:
        gdf = content
    gdf = convert_crs(gdf, Config.TARGET_CRS)
    return gdf

def get_vector_mask_coords():
    gdf = get_vector_mask()
    coordinates = get_coordinates(gdf)
    return coordinates

def get_vector_mask_centroid():
    """
    Get the centroid of the vector mask.

    :return: The centroid coordinates.
    """
    gdf = get_vector_mask()
    centroid = gdf.geometry.to_crs(Config.TARGET_CRS).centroid
    return centroid