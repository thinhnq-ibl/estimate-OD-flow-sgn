import numpy as np

def radiation_model_5x5(population_matrix, poi_matrix, total_outflow):
    rows, cols = 5, 5
    center_r, center_c = 2, 2 # Ô chính giữa (3,3)
    
    # 1. Lấy thông tin tại ô nguồn (i)
    m_i = population_matrix[center_r, center_c]
    n_i = poi_matrix[center_r, center_c]
    T_i = total_outflow # Tổng luồng thoát ra từ ô trung tâm
    
    # 2. Tạo ma trận tọa độ để tính khoảng cách
    r, c = np.ogrid[:rows, :cols]
    distances = np.sqrt((r - center_r)**2 + (c - center_c)**2)
    
    # 3. Khởi tạo ma trận luồng T_ij
    flow_matrix = np.zeros((rows, cols))
    
    # 4. Duyệt qua từng ô đích (j) để tính luồng
    for r_j in range(rows):
        for c_j in range(cols):
            # Bỏ qua chính ô nguồn
            if r_j == center_r and c_j == center_c:
                continue
            
            n_j = poi_matrix[r_j, c_j]
            d_ij = distances[r_j, c_j]
            
            # Tính s_ij: Tổng POIs của các ô k có d_ik <= d_ij 
            # (Loại trừ POIs của ô nguồn i và ô đích j)
            mask_s = (distances <= d_ij)
            s_ij = np.sum(poi_matrix[mask_s]) - n_i - n_j
            
            # Tránh trường hợp s_ij âm do sai số làm tròn (nếu có)
            s_ij = max(0, s_ij)
            
            # Áp dụng công thức Radiation
            # T_ij = T_i * (n_i * n_j) / [(n_i + s_ij) * (n_i + n_j + s_ij)]
            numerator = n_i * n_j
            denominator = (n_i + s_ij) * (n_i + n_j + s_ij)
            
            if denominator > 0:
                flow_matrix[r_j, c_j] = T_i * (numerator / denominator)
                
    return flow_matrix

# --- Dữ liệu giả lập ---
# Giả sử dân số đồng nhất nhưng POIs tập trung ở một vài điểm
pop_map = np.full((5, 5), 100) 
poi_map = np.array([
    [1, 2, 1, 2, 1],
    [2, 5, 8, 5, 2],
    [1, 8, 20, 8, 1], # Ô trung tâm có 20 POIs
    [2, 5, 8, 5, 2],
    [1, 2, 1, 2, 1]
])
total_outflow_center = 500 # Giả sử có 500 lượt đi từ tâm

result = radiation_model_5x5(pop_map, poi_map, total_outflow_center)

print("Ma trận luồng từ ô trung tâm ra xung quanh:")
print(np.round(result, 2))
print(f"\nTổng luồng đã phân phối: {np.sum(result):.2f}")