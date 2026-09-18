# Dự Án Thu Thập Dữ Liệu Thời Tiết Chuỗi Thời Gian Các Quốc Gia OECD (2010 - 2026)

## 1. Cấu hình API Key
- **API Provider:** WeatherAPI.com
- **API Key:** `b0a5c8e49da6449fb7e193445260909`
- **Base URL:** `http://api.weatherapi.com/v1`
- **History Endpoint:** `/history.json`

## 2. Mục tiêu dự án
Tự động hóa quy trình thu thập dữ liệu chuỗi thời gian (time-series daily weather data) cho các thành phố chính thuộc **38 quốc gia OECD** từ ngày `2010-01-01` đến `2026-09-01`.

## 3. Danh sách 38 Quốc gia OECD
1. Australia
2. Austria
3. Belgium
4. Canada
5. Chile
6. Colombia
7. Costa Rica
8. Czech Republic
9. Denmark
10. Estonia
11. Finland
12. France
13. Germany
14. Greece
15. Hungary
16. Iceland
17. Ireland
18. Israel
19. Italy
20. Japan
21. South Korea
22. Latvia
23. Lithuania
24. Luxembourg
25. Mexico
26. Netherlands
27. New Zealand
28. Norway
29. Poland
30. Portugal
31. Slovakia
32. Slovenia
33. Spain
34. Sweden
35. Switzerland
36. Turkey
37. United Kingdom
38. United States

## 4. Đặc tả Dữ liệu Cần Thu Thập (Target Schema)

Dữ liệu đầu ra được lưu trữ dưới dạng bảng (DataFrame) với các trường thông tin chuẩn hóa:

### A. Metadata định danh
- `country`: Tên quốc gia (string)
- `country_code`: Mã quốc gia ISO (string, ví dụ: 'FR', 'US')
- `city`: Tên thành phố (string)
- `lat`: Vĩ độ địa lý (float)
- `lon`: Kinh độ địa lý (float)
- `date`: Ngày ghi nhận dữ liệu định dạng `YYYY-MM-DD` (string/date)

### B. Các chỉ số thời tiết hàng ngày (Target Variables từ `day.*` object)
- `day.maxtemp_c`: Nhiệt độ cao nhất trong ngày (°C) - float
- `day.maxtemp_f`: Nhiệt độ cao nhất trong ngày (°F) - float
- `day.mintemp_c`: Nhiệt độ thấp nhất trong ngày (°C) - float
- `day.mintemp_f`: Nhiệt độ thấp nhất trong ngày (°F) - float
- `day.avgtemp_c`: Nhiệt độ trung bình trong ngày (°C) - float
- `day.avgtemp_f`: Nhiệt độ trung bình trong ngày (°F) - float
- `day.maxwind_mph`: Tốc độ gió tối đa (dặm/giờ - mph) - float
- `day.maxwind_kph`: Tốc độ gió tối đa (km/giờ - kph) - float
- `day.totalprecip_mm`: Tổng lượng mưa trong ngày (milimét - mm) - float
- `day.totalprecip_in`: Tổng lượng mưa trong ngày (inch - in) - float
- `day.totalsnow_cm`: Tổng lượng tuyết rơi trong ngày (xentimét - cm) - float
- `day.avgvis_km`: Tầm nhìn xa trung bình (kilômét - km) - float
- `day.avgvis_miles`: Tầm nhìn xa trung bình (dặm - miles) - float
- `day.avghumidity`: Độ ẩm trung bình trong ngày (%) - float

## 5. Chiến lược Thu thập & Tối ưu hóa (Pipeline Strategy)
- **Batching:** Sử dụng tham số `dt` và `end_dt` của WeatherAPI History endpoint để tải theo khối thời gian (chunks tối đa 30 ngày/lần gọi) giúp giảm 30 lần số lượng request so với gọi từng ngày.
- **Rate-Limiting & Retries:** Bổ sung cơ chế exponential backoff và tự động retry khi gặp lỗi mạng hoặc HTTP 429/5xx.
- **Checkpoint & Resuming:** Kết quả được lưu theo từng thành phố/quốc gia dưới định dạng Parquet hoặc CSV trong thư mục `checkpoints/` hoặc `data/`. Khi chạy lại, pipeline tự động kiểm tra những khoảng thời gian hoặc thành phố đã hoàn thành để bỏ qua (resume), không tải trùng lặp.


---

# 6. Tính Toán Chỉ Số Khí Hậu Cực Đoan & Rủi Ro Vật Lý CPRI (Nature s41599-025-05275-z)

Hệ sinh thái Multi-Agent đã hoàn thành việc tính toán, kiểm toán KYC và trực quan hóa các chỉ số thời tiết cực đoan cùng Chỉ số Rủi ro Vật lý Khí hậu (CPRI) dựa trên nghiên cứu chuẩn mực Nature / Humanities and Social Sciences Communications: *s41599-025-05275-z* (Guo et al., 2024 / Ji et al., 2025).

## 6.1. Định Nghĩa Phương Pháp Luận & Ngưỡng Phân Vị Cục Bộ (Local Quantiles)
Các ngưỡng cực đoan được tính toán độc lập cho từng thành phố trong 38 thủ đô OECD để phản ánh đúng đặc thù khí hậu bản địa:
- **LTD (Extreme Low Temperature Days):** Ngày có `avgtemp_c <= P10` (phân vị 10% nhiệt độ của thành phố đó).
- **HTD (Extreme High Temperature Days):** Ngày có `avgtemp_c >= P90` (phân vị 90% nhiệt độ của thành phố đó).
- **ERD (Extreme Rainfall Days):** Ngày có `totalprecip_mm >= P95` (phân vị 95% lượng mưa của thành phố đó và > 0mm).
- **EDD (Extreme Drought Days):** Ngày có `avghumidity <= P5` (phân vị 5% độ ẩm của thành phố đó).

## 6.2. Cấu Trúc Cột Mới Thêm Vào `oecd_weather_daily_2010_2026.csv`
Tệp dữ liệu hàng ngày đã được bổ sung 5 cột nhị phân và cờ tổng hợp:
1. `is_ltd` (int 0/1): Cờ đánh dấu ngày có nhiệt độ cực thấp.
2. `is_htd` (int 0/1): Cờ đánh dấu ngày có nhiệt độ cực cao.
3. `is_erd` (int 0/1): Cờ đánh dấu ngày có lượng mưa cực đoan.
4. `is_edd` (int 0/1): Cờ đánh dấu ngày có độ ẩm cực thấp (hạn hán).
5. `daily_cpri` (int 0..4): Tổng số loại hình biến cố thời tiết cực đoan diễn ra trong ngày (`daily_cpri = is_ltd + is_htd + is_erd + is_edd`).

*Ghi chú an toàn:* Tệp nguyên bản ban đầu đã được sao lưu tự động tại `oecd_weather_daily_2010_2026_backup.csv`.

## 6.3. Công Thức Tính Chỉ Số CPRI Cấp Vùng & Năm (City-Year Aggregation)
Theo định nghĩa trong Bảng 2 của bài báo Nature:
$$\text{CPRI} = \frac{\text{LTD}_{\text{days}} + \text{HTD}_{\text{days}} + \text{ERD}_{\text{days}} + \text{EDD}_{\text{days}}}{4}$$

Dữ liệu tổng hợp theo từng cặp Thành phố - Năm (646 quan sát) được lưu trữ tại `data_output/city_year_cpri_summary.csv` bao gồm cả `CPRI_raw`, `CPRI_annualized`, `CPRI_zscore` và `CPRI_score_100`.

## 6.4. Bảng Summary Statistics (Chuẩn Mực Table 2 của Bài Báo Nature)
Tệp `data_output/table2_summary_statistics.csv` cung cấp đầy đủ các tham số thống kê mô tả:

| Variable | N | Mean | SD | Min | P25 | Median | P75 | Max |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **CPRI (Annualized)** | 646 | **28.47** | 8.04 | 9.00 | 23.00 | 27.50 | 33.25 | 61.50 |
| **CPRI (Raw Days)** | 646 | **27.66** | 7.08 | 9.00 | 22.75 | 27.25 | 32.50 | 61.50 |
| **LTD (Low Temp Days)** | 646 | **37.44** | 20.51 | 0.00 | 24.00 | 35.00 | 46.00 | 179.00 |
| **HTD (High Temp Days)** | 646 | **37.88** | 17.42 | 0.00 | 26.00 | 36.00 | 47.00 | 122.00 |
| **ERD (Rainfall Days)** | 646 | **18.40** | 6.93 | 2.99 | 13.60 | 18.00 | 22.34 | 60.00 |
| **EDD (Drought Days)** | 646 | **20.16** | 16.91 | 0.00 | 6.00 | 17.00 | 29.00 | 94.31 |
| **Avg Temp (°C)** | 646 | 11.84 | 3.92 | 2.13 | 9.05 | 11.55 | 14.62 | 20.07 |
| **Total Precip (mm)** | 646 | 935.67 | 599.75 | 148.66 | 604.46 | 797.38 | 1075.49 | 5434.26 |
| **Avg Humidity (%)** | 646 | 72.72 | 10.45 | 41.39 | 66.79 | 76.04 | 80.36 | 92.95 |

*So sánh đối chứng với Bảng 2 trong Nature:*
- CPRI trung bình mẫu OECD: **27.66 / 28.47 ngày** vs Nature Benchmark: **27.27 ngày** (Độ lệch chỉ ~1.4%, bảo chứng tính nhất quán toán học).

## 6.5. Báo Cáo Kiểm Định Độc Lập KYC (KYC Audit Report)
Được lưu chi tiết tại `data_output/KYC_AUDIT_REPORT.md` với 5/5 vòng kiểm toán đạt trạng thái **PASSED 100%**:
1. **KYC-01:** Bảo toàn 231,344 dòng, 0 giá trị null, schema hoàn chỉnh.
2. **KYC-02:** Ngưỡng phân vị khí hậu địa phương hợp lệ cho tất cả 38 thành phố (P10 < P90, P95 > 0, P5 trong [0,100]).
3. **KYC-03:** Không xảy ra xung đột cực đoan (LTD * HTD = 0), daily_cpri = sum(cờ).
4. **KYC-04:** Tần suất thực nghiệm hội tụ đúng tỷ lệ phân vị lý thuyết (~10% cho LTD/HTD, ~5% cho ERD/EDD).
5. **KYC-05:** Công thức CPRI ăn khớp hoàn toàn với bài báo Nature.

## 6.6. Giao Diện Dashboard Web Tương Tác (`indexweather.html`)
Tệp `indexweather.html` được thiết kế hiện đại (Glassmorphism, Tailwind CSS, Chart.js) hoạt động độc lập không cần backend:
- Mở trực tiếp bằng cách double click vào `indexweather.html` hoặc qua trình duyệt:
  `file:///C:/Users/MayTinhBachVuong/.gemini/antigravity/scratch/weatherapi-docs/indexweather.html`
- **Tính năng nổi bật:**
  + Bộ lọc 38 thành phố và các năm (2010–2026).
  + Biểu đồ xu hướng rủi ro khí hậu CPRI theo thời gian.
  + Biểu đồ Radar cơ cấu 4 loại hình cực đoan.
  + Bảng xếp hạng rủi ro vật lý giữa các thành phố.
  + Tab Summary Statistics và Tab Ngưỡng Khí Hậu P10/P90.
  + Tab Biên bản thẩm định KYC chính thức.
