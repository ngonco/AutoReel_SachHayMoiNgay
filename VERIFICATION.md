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


## Bổ sung v3 — Enter chia cảnh và Y rộng (2026-10-27)

- `python -X utf8 -m unittest discover -s tests -v`: **7/7 test đạt**. Thêm trường hợp Enter/CRLF/dòng trống, mỗi dòng dài giữ nguyên một cảnh, ưu tiên xuống dòng cả khi tắt tự chia; planner giữ ranh giới dòng và báo `manual_lines`.
- Y mở rộng −1600..+1600 px; kiểm tra settings snake_case/camelCase, clamp giá trị vượt giới hạn, đi hết vùng an toàn với cả ba chế độ vị trí và footer năm template ở hai cực Y.
- Build thành công `AutoReelSachHay_v3.exe`, giữ nguyên v2; mở được qua BAT. Kích thước **204.323.742 byte**, SHA256 `CC8EC241382101383931D2C3C1698C01560D36FBB91922DF6E9DF404FA794657`.
- `verify_manual_lines.py --base http://127.0.0.1:8769`: đạt trên chính EXE v3; kiểm tra đúng ba dòng → ba cảnh khi auto bật/tắt, API Y ở −1600, −900, +650, +1200, +1600.
- Đã xuất và giải mã toàn bộ hai mẫu ba dòng, cùng **14,4 giây**: `output_videos/verification/v3_manual_lines_preview.mp4` (540×960), `v3_manual_lines_fullhd.mp4` (1080×1920).
- Đã xem ảnh cảnh 2 và bảng so sánh Y cục bộ; chữ, nguồn và dấu tiếng Việt không bị cắt.
- Kiểm tra giao diện EXE: nhập ba dòng tạo badge “3 cảnh theo dòng”; nhập bằng bàn phím −900 đồng bộ ô số, thanh trượt và nhãn, vượt được giới hạn ±350 trước đây.
- Phiên v2 và dữ liệu người dùng được giữ nguyên. Cài đặt dùng trong kiểm tra giao diện được khôi phục sau khi kiểm tra.
- Play trên giao diện EXE v3 với ba dòng và Y −900 đã phát hết tới cảnh 3/3, thời lượng 14,4 giây; sau đó khôi phục Y ban đầu. Ảnh bàn giao: `test_renders/verification/v3_studio.png`.

## Quy trình đóng gói bắt buộc — 2026-10-27

Đã ghi yêu cầu luôn build lại và kiểm tra EXE sau mỗi đợt sửa code vào AGENTS.md, system_map.md và README.md. Đợt cập nhật này chỉ sửa tài liệu; không đổi code hoặc bản EXE v3 đã kiểm tra. Kiểm tra bằng `git diff --check` và xem nội dung diff; không chạy lại build hay test runtime cho thay đổi tài liệu.


## Bổ sung v4 — Viền chữ mềm có thể chỉnh (2026-10-27)

- **10/10 unit test đạt**, gồm alpha viền nhạt dần theo khoảng cách, không che phần mực đặc, giữ màu/nét glyph sắc, bật/tắt/opacity 0, kiểm tra màu và giới hạn settings. Giữ các kiểm tra nội dung, xuống dòng, timeline và footer năm theme.
- Đã xem bảng ảnh 5 theme × 3 mức viền (tắt/mặc định/đậm): `test_renders/verification/v4_outline_comparison.jpg`. Chế độ màu tự động dùng màu tối với chữ sáng, màu giấy với chữ tối ở Sen Giấy; có màu tự chọn.
- Đóng gói thành công `AutoReelSachHay_v4.exe` và bản sao dist, mở qua BAT; kích thước **204.326.486 byte**, SHA256 `A8EAC4CC0EFA80C207D01C063C0CCBFC14FB7DB614CEE70776DD47207674C4C3`. Giữ nguyên các phiên cũ.
- `verify_outline.py --base http://127.0.0.1:8772` đạt trên EXE v4: đổi cấu hình viền tạo plan_id mới; PNG viền bật khác viền tắt; opacity 0 giống tắt; màu trắng khác màu tối.
- Đã xuất và giải mã toàn bộ `output_videos/verification/v4_soft_outline_preview.mp4` (540×960) và `v4_soft_outline_fullhd.mp4` (1080×1920), cùng **5,0 giây**. Cấu hình mẫu: viền 7 px, nhòe 10 px, đậm 90%; ảnh trích xuất `test_renders/verification/v4_outline_export.jpg`.
- Kiểm tra UI v4: bật/tắt và các thanh viền hoạt động. Kết quả khôi phục cài đặt chưa ổn định khi các phiên cũ còn mở; phần tự lưu đã được thay thế và kiểm tra đầy đủ ở v5 bên dưới.


## Bổ sung v5 — Tự lưu đầy đủ và chống trùng footage (2026-10-27)

- **22/22 unit test đạt**. Kiểm tra quote nguyên văn/trailing Enter, patch từng field, thứ tự request, nhiều luồng lưu, nhập settings cũ và tránh phiên cũ ghi đè session mới; giữ toàn bộ kiểm tra viền, font và footer.
- Footage tests: SHA256 gộp file sao chép, hết kho mới quay vòng, preview không tiêu hao lượt, reservation tránh trùng khi queue đồng thời, trả lượt khi lỗi/tiến trình đã thoát; batch lấy lịch sử cập nhật sau từng reel. Sau bổ sung retry khi xung đột, chạy lại **12/12 test persistence/job đạt**.
- Kiểm tra cú pháp Python/JavaScript đạt. Các bài kiểm tra atomic rename/lock chạy ở môi trường Windows có quyền ghi đầy đủ; không thay atomic write bằng ghi trực tiếp khi môi trường hạn chế chặn rename.
- Build EXE v5 thành công, kích thước **204.342.396 byte**, SHA256 `8FD92F9B35A8EE68BFF6E5AF9D9DB54C57919AB6D507381CFBB1C9E4B5D4EBCB`. BAT/VBS ưu tiên v5, bản gốc và các phiên cũ giữ nguyên.
- `verify_v5.py --exe AutoReelSachHay_v5.exe --hold`: đạt trên profile riêng với 3 clip màu. Đã xuất 2 reel đơn + 2 reel batch Full HD, probe và giải mã toàn bộ, đối chiếu màu frame: ba lượt đầu khác nhau, lượt thứ tư mới quay vòng. Preview không tăng counts; plan đã tiêu hao bị từ chối 409.
- Đã đóng rồi khởi động lại chính EXE thử: draft có dòng trống/trailing Enter, clip đã chọn, các setting và lịch sử footage được giữ nguyên. Công cụ chỉ đóng tiến trình thử do nó tạo; không thay đổi profile người dùng.
- Kiểm tra UI EXE: sửa quote thành ba dòng, tăng viền 9→10, tắt safe zone, chờ báo Đã lưu tự động rồi reload: giữ đúng ba dòng và trailing Enter, viền 10 px, safe zone tắt. Thử gõ hai dòng rồi reload ngay trước debounce cũng khôi phục đủ nội dung.
- Bản thử và báo cáo chi tiết ở `.cache/v5_smoke_1793076959054826600/verification.json`; không đưa dữ liệu thử hoặc session/history cá nhân lên Git.
- Mở bản v5 qua BAT với kho thật: hiển thị 59/59 footage chưa dùng, viền mềm và báo tự lưu hoạt động. Ảnh bàn giao `test_renders/verification/v5_studio.png`. Chưa đốt lượt kho thật trong bài thử; lịch sử chỉ bắt đầu ghi các lần xuất v5.
