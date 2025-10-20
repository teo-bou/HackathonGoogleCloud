import geopandas as gpd
from shapely.geometry import Polygon
import os

# Define 3 square polygons
square1 = Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])
square2 = Polygon([(2, 2), (2, 3), (3, 3), (3, 2)])
square3 = Polygon([(4, 4), (4, 5), (5, 5), (5, 4)])

# Create GeoDataFrame
gdf = gpd.GeoDataFrame({"id": [1, 2, 3]}, geometry=[square1, square2, square3])
gdf.set_crs("EPSG:4326", inplace=True)

# Save as Shapefile
output_folder = "squares_shapefile"
os.makedirs(output_folder, exist_ok=True)
gdf.to_file(os.path.join(output_folder, "squares.shp"), driver="ESRI Shapefile")

print(f"Shapefile saved to: {output_folder}")
