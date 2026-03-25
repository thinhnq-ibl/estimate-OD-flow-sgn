import osmnx as ox
import matplotlib.pyplot as plt

# 1. Xác định địa điểm muốn lấy dữ liệu
place_name = "District 1, Ho Chi Minh City, Vietnam"

# 2. Định nghĩa các tag landuse muốn lấy (hoặc lấy tất cả bằng True)
# Các tag phổ biến: residential, commercial, industrial, grass, forest, retail
tags = {"landuse": True} 

# 3. Tải dữ liệu từ OpenStreetMap
print(f"Đang tải dữ liệu land use cho: {place_name}...")
gdf = ox.features_from_place(place_name, tags)

# 4. Hiển thị thông tin cơ bản
print(f"Tìm thấy {len(gdf)} khu vực sử dụng đất.")
print(gdf[['landuse', 'geometry']].head())

landuse_count = gdf[gdf['landuse'] == 'residential'].shape[0]
print(f"Số lượng khu vực residential: {landuse_count}")

# group by landuse type and count
landuse_summary = gdf.groupby('landuse').size().reset_index(name='count')
print("\nTóm tắt số lượng khu vực theo loại landuse:")
print(landuse_summary)  

# 5. Vẽ bản đồ minh họa
gdf.plot(column='landuse', cmap='tab20', figsize=(10, 10), legend=True)
plt.title(f"Land Use Map - {place_name}")
plt.xlabel("Longitude")
plt.ylabel("Latitude")

# Lưu file nếu cần
# gdf.to_file("land_use_dist1.geojson", driver='GeoJSON')

plt.show()