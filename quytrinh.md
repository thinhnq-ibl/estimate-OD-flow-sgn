graph TD
    %% --- CÁC BÊN THAM GIA ---
    User((Người dùng))
    DoanhNghiep[Doanh nghiệp sản xuất]
    NhaNuoc[Cơ quan Nhà nước (Ông X)]
    HeThong[Hệ thống Quản lý / Blockchain]
    AI_Bot{{Trợ lý AI}}

    %% --- BƯỚC 1: ĐĂNG KÝ ---
    subgraph "1. Đăng ký & Phê duyệt"
        DoanhNghiep -- "1a. Nộp Form viết tay" --> NhaNuoc
        NhaNuoc -- "1b. Chụp/Quét Form" --> HeThong
        HeThong -- "1c. OCR chuyển đổi" --> AI_Bot
        AI_Bot -- "1d. Dữ liệu số hóa" --> HeThong
        NhaNuoc -- "1e. Approve (có thể có 'phong bì')" --> HeThong
    end

    %% --- BƯỚC 2: SẢN XUẤT ---
    subgraph "2. Sản xuất & Đóng gói"
        DoanhNghiep -- "2a. Thu hoạch (Củ khoai)" --> DoanhNghiep
        DoanhNghiep -- "2b. Đóng gói & Dán nhãn (Quả mít + Mã QR)" --> HeThong
        DoanhNghiep -- "2c. Nhập số liệu xuất hàng" --> HeThong
    end

    %% --- BƯỚC 3: KIỂM TRA ---
    subgraph "3. Hậu kiểm (Định kỳ/Đột xuất)"
        NhaNuoc -- "3a. Xuống cơ sở" --> DoanhNghiep
        NhaNuoc -- "3b. Chụp ảnh hiện trường/sản phẩm" --> HeThong
        HeThong -- "3c. Computer Vision phân tích" --> AI_Bot
        AI_Bot -- "3d. Xác nhận đúng 'khoai' hay 'mít'?" --> HeThong
        HeThong -. "3e. Cảnh báo sai phạm" .-> NhaNuoc
    end

    %% --- BƯỚC 4: TIÊU DÙNG ---
    subgraph "4. Tiêu dùng & Phản hồi"
        HeThong -- "4a. Phân phối hàng hóa" --> User
        User -- "4b. Ăn không ngon / Nghi giả" --> User
        User -- "4c. Quét mã QR" --> HeThong
        HeThong -- "4d. Hiển thị thông tin (Doanh nghiệp ABC)" --> User
        User -- "4e. Khiếu nại/Kiện" --> DoanhNghiep
    end

    %% --- KẾT NỐI AI NÂNG CAO ---
    AI_Bot -. "Giám sát bất thường số lượng" .-> HeThong

    %% --- STYLE ---
    style DoanhNghiep fill:#f9f,stroke:#333,stroke-width:2px
    style NhaNuoc fill:#ccf,stroke:#333,stroke-width:2px
    style HeThong fill:#ff9,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
    style AI_Bot fill:#9f9,stroke:#333,stroke-width:2px