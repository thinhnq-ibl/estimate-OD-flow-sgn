import requests
import folium

def truc_quan_hoa_osm():
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Câu lệnh tìm tọa độ hai điểm giao cắt
    overpass_query = """
    [out:json][timeout:180];
    area["name"="Thành phố Hồ Chí Minh"]->.searchArea;
    
    way(area.searchArea)["name"~"Điện Biên Phủ"]->.dbp;
    way(area.searchArea)["name"~"Cách Mạng Tháng (Tám|8)"]->.cmt8;
    way(area.searchArea)["name"~"Nguyễn Thượng Hiền"]->.nth;
    
    node(w.dbp)(w.cmt8)->.giao_lo_1;
    node(w.dbp)(w.nth)->.giao_lo_2;
    
    (.giao_lo_1; .giao_lo_2;);
    out body;
    """
    
    print("Đang tải dữ liệu từ OpenStreetMap...")
    response = requests.post(overpass_url, data={'data': overpass_query})
    
    if response.status_code == 200:
        data = response.json()
        elements = data.get('elements', [])
        print(f"Đã tải được {len(elements)} điểm giao cắt.")
        
        if len(elements) >= 2:
            # Lấy danh sách tọa độ (Vĩ độ, Kinh độ)
            coords = [(node['lat'], node['lon']) for node in elements]
            
            # Tính tọa độ trung tâm để căn giữa bản đồ khi mở lên
            center_lat = sum(lat for lat, lon in coords) / len(coords)
            center_lon = sum(lon for lat, lon in coords) / len(coords)
            
            # Khởi tạo bản đồ Folium với mức zoom chi tiết
            m = folium.Map(location=[center_lat, center_lon], zoom_start=16)
            
            # Gắn ghim (Marker) cho điểm cắt Cách Mạng Tháng Tám (Ví dụ ghim đỏ)
            folium.Marker(
                location=coords[0],
                popup="Giao lộ 1",
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(m)
            
            # Gắn ghim cho điểm cắt Nguyễn Thượng Hiền (Ví dụ ghim xanh)
            folium.Marker(
                location=coords[1],
                popup="Giao lộ 2",
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(m)
            
            # Vẽ một đường thẳng nối hai điểm để đánh dấu ranh giới đoạn đường
            folium.PolyLine(
                locations=coords,
                color="green",
                weight=5,
                opacity=0.7,
                tooltip="Phạm vi đoạn đường Điện Biên Phủ"
            ).add_to(m)
            
            # Xuất ra file HTML
            file_name = "ban_do_kiem_tra.html"
            m.save(file_name)
            print(f"\nThành công! Hãy mở file '{file_name}' vừa được tạo trong cùng thư mục bằng trình duyệt web (Chrome, Edge, Safari...) để xem bản đồ.")
        else:
            print("Không tìm thấy đủ dữ liệu hai giao lộ. Vui lòng kiểm tra lại cấu trúc tên đường.")
    else:
        print(f"Có lỗi xảy ra khi kết nối. Mã lỗi: {response.status_code}")

if __name__ == "__main__":
    truc_quan_hoa_osm()