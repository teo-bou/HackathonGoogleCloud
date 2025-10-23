import geopandas as gpd
import matplotlib.pyplot as plt

# Charger le shapefile
path = rf"C:\Users\jana_\Downloads\wetransfer_fichier-carto_2025-10-20_2024\Shape QGis-20251020T200729Z-1-001\Shape QGis\GPS_paysage.shp"
gdf = gpd.read_file(path)

# Afficher le contenu du GeoDataFrame
print(gdf)

# Tracer les polygones
gdf.plot(edgecolor='black', facecolor='lightblue')

# Personnaliser le graphique
plt.title("Visualisation des carrés (squares.shp)")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.axis("equal")  # pour garder les proportions réelles
plt.show()
