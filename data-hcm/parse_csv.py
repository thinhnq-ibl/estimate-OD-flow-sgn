import pdfplumber
import csv

def extract_pdf_to_csv(pdf_path, output_csv):
    all_data = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Trích xuất bảng từ mỗi trang
            table = page.extract_table()
            if table:
                # Loại bỏ các dòng trống hoặc làm sạch dữ liệu
                clean_table = [[cell.replace('\n', ' ').strip() if cell else "" for cell in row] for row in table]
                all_data.extend(clean_table)

    # Ghi dữ liệu ra tệp CSV
    with open(output_csv, mode='w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(all_data)

    print(f"Đã chuyển đổi thành công sang: {output_csv}")

# Sử dụng chương trình
extract_pdf_to_csv("Phụ lục excel.pdf", "ket_qua_quan_trac.csv")