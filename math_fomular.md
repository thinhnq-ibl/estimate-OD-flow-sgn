# OD Flow Generation with Radiation Opportunity and Distance-Bin Calibration

## 1. Notation and Data Inputs

Giả sử vùng nghiên cứu được chia thành $N$ **subzones**.

Origins và destinations thuộc cùng một tập zone:

$$
i,j \in \{1,\dots,N\}
$$

Các biến quan sát:

| Symbol | Description |
|------|-------------|
| $P_i$ | population tại subzone $i$ |
| $d_{ij}$ | khoảng cách giữa $i$ và $j$ |
| $n_{jc}$ | số POI loại $c$ tại zone $j$ |
| $w_c$ | trọng số của POI loại $c$ |
| $p_k$ | tỷ lệ trips trong distance bin $k$ (Meta mobility data) |
| $T$ | tổng số trips trong hệ thống |
| $Pr_{ij}$ | xác suất di chuyển từ $i$ đến $j$ |


Distance bins:

- $[0,1)$ km  
- $[1,10)$ km  
- $[10,100)$ km  

---

# 2. Model Structure

## 2.1 Origin Mass

Origin mass được xác định từ population:

$$
O_i = P_i + 1
$$

(+1 nhằm tránh giá trị bằng 0)

---

## 2.2 Destination Attractiveness from POIs

Destination attractiveness của zone $j$:

$$
D_j =
\sum_{c \in C} w_c n_{jc} + 1
$$

Trong đó tập POI categories:

$$
C = \{\text{office},\text{public\-transport},\text{shop},\text{amenity},\text{tourism},\text{leisure}\}
$$

---

## 2.3 Intervening Opportunities

Theo nguyên lý **radiation model**, tổng opportunity nằm giữa origin $i$ và destination $j$:

$$
s_{ij} =
\sum_{d_{ik} < d_{ij}} D_k
$$

Với điều kiện: 

$$ 
k \ne i,j 
$$

---

## 2.4 Radiation Interaction Function

Score tương tác giữa $i$ và $j$:

$$
A_{ij} =
\frac{O_i D_j}
{(O_i + s_{ij})(O_i + D_j + s_{ij})}
$$

Trong đó

- $O_i$ là origin mass  
- $D_j$ là destination attractiveness  
- $s_{ij}$ là intervening opportunities  

---

# 3. Distance-Bin Probability Calibration

Meta mobility dataset cung cấp phân bố khoảng cách di chuyển:

$$
p_1 = P(d < 1 \text{ km})
$$

$$
p_2 = P(1 \le d < 10 \text{ km})
$$

$$
p_3 = 1 - p_1 - p_2
$$

Define bin indicator:

$$
\delta_{ij}^{(k)} =
\begin{cases}
1 & d_{ij} \in bin_k \\
0 & otherwise
\end{cases}
$$

Tổng interaction score trong mỗi bin:

$$
S_k =
\sum_i \sum_j
A_{ij} \delta_{ij}^{(k)}
$$

---

# 4. Trip Probability
Xác suất di chuyển từ $i$ đến $j$:

$$
Pr_{ij} =
\sum_{k=1}^{3}
\delta_{ij}^{(k)}
\frac{A_{ij}}{S_k}
p_k
$$

---

# 5. Expected OD Flow

Giả sử tổng số trips trong hệ thống xuất phát từ $i$ là $T$.

OD flow được sinh ra từ $i$ đến $j$ bởi mô hình:

$$
\hat{T}_{ij} =
T \cdot Pr_{ij}
$$

---

# 6. Flow Normalization

Tổng flows:

$$
T^{gen} =
\sum_i \sum_j \hat{T}_{ij}
$$

Normalized flow:

$$
\tilde{T}_{ij} =
\frac{\hat{T}_{ij}}{T^{gen}}
$$

---

# 7. Ground Truth Normalization

Giả sử ground truth OD matrix là $G_{ij}$.

Tổng trips:

$$
T^{GT} =
\sum_{i,j} G_{ij}
$$

Normalized matrix:

$$
\tilde{G}_{ij} =
\frac{G_{ij}}{T^{GT}}
$$

---

# 8. Evaluation Metric: Common Part of Commuters (CPC)

Độ tương đồng giữa OD dự đoán và ground truth:

$$
CPC =
\frac{
2\sum_{i,j}
\min(\hat{T}_{ij}, G_{ij})
}{
\sum_{i,j} \hat{T}_{ij}
+
\sum_{i,j} G_{ij}
}
$$

Nếu dùng normalized matrices:

$$
CPC =
\sum_{i,j}
\min(\tilde{T}_{ij}, \tilde{G}_{ij})
$$

---

# 9. Model Interpretation

Mô hình kết hợp ba nguồn thông tin:

### Urban Opportunity Structure

$$
D_j
$$

→ derived from **OSM POIs**

---

### Spatial Opportunity Competition

$$
s_{ij}
$$

→ **intervening opportunities**

---

### Empirical Mobility Pattern

$$
p_k
$$

→ **Meta mobility distance distribution**

---

Do đó mô hình có thể **sinh OD matrix ngay cả khi không có dữ liệu khảo sát OD trực tiếp**.