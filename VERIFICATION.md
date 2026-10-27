# Kết quả kiểm tra — 2026-10-27

Đợt nâng cấp: dựng reel nhiều cảnh, Play toàn bộ câu nói, template chung preview/export và backup mã nguồn.

## Kiểm tra tự động

- `python -X utf8 -m unittest discover -s tests -v`: **5/5 test đạt**. Bao gồm toàn bộ 16 câu có sẵn, câu dài và Unicode phân rã, giữ nguyên chữ/dấu/thứ tự, giới hạn cảnh, thời gian đọc, overlap, migration settings, kho trống/một clip, chọn clip, làm chậm nguồn và vô hiệu plan khi file đổi.
- Bố cục: 5 theme × 3 vị trí × 2 offset, quote size 108 và credit dài cỡ 32. Khối nằm trong vùng an toàn, không cắt footer. Có dựng ảnh thật để kiểm tra.
- `python -X utf8 verify_samples.py`: **6/6 video đạt**; kiểm tra bằng FFprobe và giải mã toàn bộ file qua FFmpeg.
- `python -X utf8 verify_api.py`: đạt trên server Python thử nghiệm.
- `python -X utf8 verify_api.py --base http://127.0.0.1:8767`: đạt trên **EXE v2** mở qua BAT. Kiểm tra health, plan, PNG, preview, export, hàng đợi/dedup, health không bị chặn khi render, byte ranges 206/suffix/416, lỗi đầu vào và chặn tên file vượt thư mục.
- `compileall`: đạt. Kiểm tra diff đã stage: xử lý khoảng trắng thừa ở ba dòng HTML.

## Các video mẫu

| Mẫu | Cảnh | Thời lượng | Bản nhẹ | Full HD |
| --- | --- | --- | --- | --- |
| `01_short` | 1 | 12,0s | 540×960 | 1080×1920 |
| `02_two_scenes` | 2 | 13,6s | 540×960 | 1080×1920 |
| `03_three_scenes` | 3 | 16,4s | 540×960 | 1080×1920 |

Đường dẫn cục bộ: `output_videos/verification`. Ảnh từng cảnh, điểm chuyển, gần cuối và stress footer: `test_renders/verification`. Metadata chi tiết: `test_renders/verification/report.json`. Đã xem trực tiếp bảng ảnh `review_sheet.jpg` sau lần xuất cuối.

## Kiểm tra giao diện

- Play câu dài hai cảnh chạy hết tới cảnh 2/2; câu dài ba cảnh chạy hết tới cảnh 3/3.
- Phát lại bắt đầu từ 0; pause/resume hoạt động; chọn tab cảnh tua tới vị trí tương ứng.
- Bản nhẹ xác nhận thực tế 540×960; xuất từ nút trong giao diện EXE hoàn tất với reel 13,6s.
- Xem lại bản xuất xác nhận 1080×1920, duration 13,6s; canvas bị ẩn, không vẽ chồng chữ.
- Đổi credit khi đã có bản dựng: dừng/ẩn video cũ, bật canvas, ẩn nút xem lại cũ, thông báo cần cập nhật. Sau test đã khôi phục credit ban đầu.
- Năm theme và credit dài đã kiểm tra hình ảnh; chưa có kiểm tra bằng mắt toàn bộ mọi frame của 16 câu. Vị trí mặt vẫn là ước lượng từ ảnh mẫu, cần xem lại khi nguồn chuyển động.

## Bản đóng gói

- Build PyInstaller thành công, gồm UI, các module core, ba font, âm thanh, FFmpeg/FFprobe và DLL cần thiết.
- File mới: `AutoReelSachHay_v2.exe`, đồng thời có bản sao ở `dist/AutoReelSachHay/AutoReelSachHay_v2.exe`.
- Kích thước: **204.322.398 byte**.
- SHA256: `ECCD90B1439858A64F39AC0E29A77AF496F8E27257D807DC4E28935C46C0FE3E`.
- Mở bằng `Chay_Ung_Dung_Auto_Reel.bat`, health và render hoạt động; hai tiến trình cùng EXE là parent/child bình thường của PyInstaller onefile, không phải vòng khởi động lại.
- Bản EXE cũ được giữ nguyên vì đang có phiên người dùng mở; không cưỡng bức đóng các phiên đó. BAT/VBS ưu tiên EXE v2.
- Sau khi build chỉ sửa khoảng trắng ở ba dòng HTML, tài liệu và fallback launcher; không thay đổi logic đóng gói đã kiểm tra.

## Backup

Nguồn và tài liệu được quản lý trong repo `ngonco/AutoReel_SachHayMoiNgay`, nhánh `main`. Không đưa video nguồn/xuất, cache, log, font Microsoft, file EXE hoặc settings cá nhân lên Git. Xác nhận commit remote trùng local là bước cuối của quy trình backup, theo `system_map.md` và `AGENTS.md`.
