import geopandas as gpd
from shapely.geometry import Polygon
import os

def generate_shapefile(gdf, filename, output_folder="."):
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, filename)
    gdf.to_file(output_path, driver="ESRI Shapefile")
    print(f"Shapefile saved to: {output_path}")


# Define 3 square polygons
square1 = Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])
square2 = Polygon([(2, 2), (2, 3), (3, 3), (3, 2)])
square3 = Polygon([(4, 4), (4, 5), (5, 5), (5, 4)])

# Create GeoDataFrame
gdf = gpd.GeoDataFrame({"id": [1, 2, 3]}, geometry=[square1, square2, square3])
gdf.set_crs("EPSG:4326", inplace=True)

# Save as Shapefile
generate_shapefile(gdf, "squares.shp", "shapes")


# Define 3 triangle polygons
triangle1 = Polygon([(0.1, 0.1), (0.1, 0.5), (0.5, 0.1)])  # Inside square1
triangle2 = Polygon([(6, 6), (6, 7), (7, 6)])
triangle3 = Polygon([(-1, -1), (-1, -2), (-2, -1)])

triangles_gdf = gpd.GeoDataFrame({"id": [101, 102, 103]}, geometry=[triangle1, triangle2, triangle3])
triangles_gdf.set_crs("EPSG:4326", inplace=True)

# Save triangles as a separate Shapefile
generate_shapefile(triangles_gdf, "triangles.shp", "shapes")
