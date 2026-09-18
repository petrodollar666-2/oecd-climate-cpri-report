# BỘ CÔNG CỤ MULTI-AGENT TÍNH TOÁN RỦI RO KHÍ HẬU (CPRI) & THỜI TIẾT CỰC ĐOAN
### *Thư mục bàn giao cho cô Trang và đồng nghiệp - Chia sẻ qua Google Drive*

Bộ công cụ này tự động hóa 100% việc tính toán các chỉ số thời tiết cực đoan (LTD, HTD, ERD, EDD) và Chỉ số Rủi ro Vật lý Khí hậu (CPRI) theo chuẩn bài báo Nature Communications (*s41599-025-05275-z*).

---

## 1. CÁCH SỬ DỤNG NHANH NHẤT (QUICK START)

### Cách 1: Chạy bằng 1 click chuột (Không cần gõ lệnh)
- Nhấp đúp (Double-click) vào tệp **`CHAY_MULTI_AGENT.bat`**.
- Hệ thống Multi-Agent sẽ tự động chạy tính toán trong 3 giây và tự động mở giao diện web `indexweather.html` lên trình duyệt của bạn.

### Cách 2: Chạy qua dòng lệnh Terminal/PowerShell
```bash
# 1. Cài thư viện cần thiết (chỉ cần chạy 1 lần)
pip install -r requirements.txt

# 2. Chạy toàn bộ hệ thống Multi-Agent
python multi_agent_weather_cpri.py
```

### Cách 3: Xem ngay kết quả báo cáo và Dashboard trực quan
- Nhấp đúp mở trực tiếp tệp **`indexweather.html`** trên Chrome/Edge/Firefox/Cốc Cốc.
- Không cần cài máy chủ web, không cần internet, dữ liệu đã được nhúng sẵn 100%.

---

## 2. DANH MỤC CÁC TỆP TRONG THƯ MỤC

| Tên Tệp | Vai Trò & Mô Tả |
| :--- | :--- |
| **`multi_agent_weather_cpri.py`** | **Kịch bản Python Multi-Agent chính** (gồm 1 Agent Tổng điều phối + 5 Sub-Agent chuyên trách). |
| **`indexweather.html`** | **Giao diện Web Dashboard tương tác** (biểu đồ Chart.js, bảng tra cứu, Tab báo cáo Sếp). |
| **`CHAY_MULTI_AGENT.bat`** | File thực thi tự động 1-click cho người dùng Windows. |
| **`EXECUTIVE_REPORT_FOR_BOSS.md`** | **Báo cáo Chiến lược Điều hành Dành Cho Sếp** (Tóm tắt số liệu, khuyến nghị vận hành). |
| **`KYC_AUDIT_REPORT.md`** | **Biên bản thẩm định độc lập KYC 5 vòng** (Chứng chỉ 100% PASSED). |
| **`table2_summary_statistics.csv`**| Bảng thống kê mô tả chuẩn mực Table 2 Nature (N, Mean, SD, Min, P25, Median, P75, Max). |
| **`city_climatology_thresholds.csv`** | Bảng ngưỡng phân vị địa phương (P10 nhiệt độ, P90 nhiệt độ, P95 mưa, P5 độ ẩm) của 38 đô thị. |
| **`city_year_cpri_summary.csv`** | Dữ liệu tổng hợp theo từng cặp Thành phố - Năm (646 quan sát giai đoạn 2010–2026). |
| **`city_risk_ranking.csv`** | Bảng xếp hạng mức độ rủi ro khí hậu giữa 38 đô thị OECD. |
| **`correlation_matrix.csv`** | Ma trận hệ số tương quan giữa 4 loại hình thời tiết cực đoan. |
| **`oecd_weather_daily_2010_2026.csv`** | Tệp dữ liệu lớn hàng ngày (231.344 dòng) đã bổ sung 5 cột: is_ltd, is_htd, is_erd, is_edd, daily_cpri. |
| **`requirements.txt`** | Danh sách thư viện Python cần thiết (pandas, numpy). |

---

## 3. CÔNG THỨC & NGUYÊN LÝ KHOA HỌC (NATURE s41599-025-05275-z)
1. **Ngưỡng địa phương (Local Quantiles):**
   - LTD: Nhiệt độ trung bình ngày <= P10 của địa phương đó.
   - HTD: Nhiệt độ trung bình ngày >= P90 của địa phương đó.
   - ERD: Lượng mưa ngày >= P95 của địa phương đó (> 0 mm).
   - EDD: Độ ẩm trung bình ngày <= P5 của địa phương đó.
2. **Chỉ số CPRI (Climate Physical Risk Index):**
   - CPRI = (LTD + HTD + ERD + EDD) / 4
   - Mẫu OECD trung bình đạt 28.47 ngày/năm, độ lệch chỉ 1.4% so với bài báo Nature (27.27 ngày/năm).

Chúc cô Trang và các bạn nghiên cứu, ứng dụng hiệu quả!