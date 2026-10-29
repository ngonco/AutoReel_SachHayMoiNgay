# V13 — Điều chỉnh cỡ chữ, số dòng, viền và hai mép mờ (2026-10-29)

- **83/83 test Python đạt** (89,42s), **6 bộ kiểm tra Node đạt**. Bao gồm5 dòng đầy đủ có dấu tiếng Việt; 28/48/80px ×2/5/8 dòng; khung giữ đáy y1581 và nở lên; mask trên/dưới độc lập/cả hai0; lưu riêng thông số chữ cuộn; so khớp pixel giữa tile ghép và raster liên tục với cỡ80/viền16/blur24 để phát hiện đứt viền.
- Build cuối `python -X utf8 build_onefile.py` đạt: **AutoReelSachHay_v13.exe**, **203.773.164 byte**. BAT/VBS ưu tiên v13, giữ v12 và phiên cũ; health/version/PID/đường dẫn EXE thực được kiểm tra qua launcher.
- `python -X utf8 verify_v13.py --fullhd --hold` đạt trên profile riêng `.cache/v13_smoke_1793286075386679100`; kết quả trong `verification.json`. Mặc định48px/5 dòng; cấu hình tùy chỉnh64px/5 dòng, viền5px/blur10/màu#1f2f55/opacity70%, mép trên0/mép dưới72px → rect{x119,y1022,width842,height559}, cùng đáy1581. Cực trị28/80px ×2/8 dòng với viền/fade cực đại vẫn trong vùng an toàn.
- Nháp360×640 đạt (39,08s dựng); Full HD1080×1920,20,8s/3 footage đạt (34,97s dựng), decode toàn file đạt. Pixel nét chữ so với scroll_frame tại đầu/chuyển footage/giữa/cuối: **99,9978–100%** qua ngưỡng nén; không có chữ ngoài rect. Nhạc PCM RMS **0,0713**. Preview không đổi lịch sử footage, chỉ xuất thành công qua JobManager mới tính lượt trong profile thử.
- Mở lại EXE qua VBS giữ toàn bộ cỡ/số dòng/màu/dày/nhòe/đậm viền và fade trên/dưới. Cỡ chữ tĩnh84/offset−100 vẫn nguyên; cả năm style tĩnh tạo plan và PNG được. UI trong EXE khớp byte với nguồn cuối.
- Giao diện EXE thực: nhập52px và8 dòng bằng ô số cập nhật đúng slider/nhãn, nở khung lên trên. Tắt viền khóa riêng control viền, hai control mép vẫn chỉnh được. Đã đặt lại48px/5 dòng và viền2/blur3/85%/hai mép18 để kiểm tra nháp; khung mặc định371px, phát/tua/nhạc và chữ chuyển động hoạt động. Ảnh bảng thông số: `test_renders/verification/v13_scroll_controls.jpg`.
- Các kiểm tra chỉ dùng --workspace riêng, không sửa hoặc reset dữ liệu/media/lượt footage thật. PLAN_VERSION tăng v13 để loại cache bố cục cũ.

# Bổ sung V12 — CHỮ CUỘN ở đầu giao diện, mặc định bật (2026-10-29)

- Đổi tên hiển thị thành **CHỮ CUỘN**, thay nút mẫu06 bằng công tắc bật/tắt ở panel đầu tiên, phía trên nội dung câu nói. Năm style tĩnh có nút riêng phía dưới; chọn style tĩnh tự tắt công tắc.
- **80/80 test Python đạt** (55,68s), **6 bộ kiểm tra Node đạt**, diff check đạt. Tests mới kiểm tra bật/tắt, nhớ style tĩnh, giữ cỡ84/offset−100, migration một lần và restart sau khi tắt. Đọc settings không viết lại bản nháp.
- Build cuối bằng `python -X utf8 build_onefile.py` đạt: **AutoReelSachHay_v12.exe**, **203.770.087 byte**, launcher hiện có mở đúng EXE/PID đã xác minh. Giữ EXE cũ trong v12.previous và các phiên làm việc khác.
- Kiểm chứng API/khởi động qua VBS trên profile riêng `.cache/v12_smoke_1793283052291310100`: profile cũ theme3, chưa có marker → mặc định theme5, nhớ theme3, giữ quote/cỡ84/offset−100; tắt rồi đóng/mở lại vẫn theme3; bật rồi đóng/mở lại vẫn theme5. Plan hai chế độ đúng, hai field nội bộ công tắc không đi vào settings/hash render. UI trong EXE khớp byte với nguồn cuối.
- Kiểm tra giao diện thật trên EXE mới: công tắc nằm ngay đầu, mặc định Đang bật; bấm đủ năm style đều đổi đúng badge và Đã tắt, bật lại chuyển CHỮ CUỘN và 3 footage/chữ liên tục. Chờ bản nháp mới sẵn sàng rồi lưu ảnh `test_renders/verification/chu_cuon_toggle.jpg`.
- Các profile kiểm chứng độc lập với session_state/footage_usage/media thật. Renderer/timing/PLAN_VERSION không đổi trong đợt này; không xuất video sản xuất để thử công tắc.

# Kết quả kiểm tra V12 — 2026-10-29

- Mã cuối: **78/78 kiểm tra Python đạt** (92,2s), năm bộ kiểm tra Node đạt, compileall và git diff --check đạt. Bao gồm giữ Enter/đoạn trống, tiếng Việt, token dài, PNG giới hạn512px, mask mép, đầu/cuối giữ2s, thay tốc độ, lưu/restoration settings, footage reservation/rollback/commit và hồi quy v11.
- Build `python -X utf8 build_onefile.py` thành công: **AutoReelSachHay_v12.exe**, 203.768.068 byte. Launcher BAT/VBS ưu tiên v12, giữ phiên/EXE trước. Bundle có Segoe UI Semibold; không đưa font/EXE/media vào Git.
- `python -X utf8 verify_v12.py --fullhd --hold` đạt trên **EXE v12 mở qua VBS**, PID/đường dẫn thực được kiểm tra. Profile riêng `.cache/v12_smoke_1793261206301475700`, báo cáo `verification.json`. Không dùng thiết lập hoặc lịch sử footage thật.
- Quote dài có đoạn trống: **20,8s / 3 footage**, preview360×640 (11,41s dựng), Full HD1080×1920 (34,60s dựng). Decode toàn file đạt; nhạc PCM RMS **0,0713**. So khớp glyph với renderer tại1s, điểm đổi footage, giữa, gần cuối: **96,58–97,56% pixel nét chữ** qua ngưỡng nén; không có chữ ngoài khung. Phát hiện và sửa rounding tọa độ lẻ của overlay bằng format=yuv444 trước encode cuối.
- Câu ngắn không credit: **4,0s / 1 footage**, text_track.distance=0, xuất Full HD đạt. Câu dài hơn: **35,2s / 5 footage**, preview qua nhánh chuẩn hóa tuần tự đạt (36,15s dựng). Preview không thay counts, export chỉ tăng số footage sau thành công; rollback lỗi được kiểm tra tự động.
- Mở lại qua launcher trên cùng profile: theme5, tốc độ0,80×, quote có Enter, quote_size84 và vertical_offset−100 được giữ. Năm theme cũ lập kế hoạch và tạo PNG được. Static ảnh của từng footage nằm trong x119..961/y1325..1581.
- Giao diện thật từ EXE: preset06 hiện, hướng dẫn Enter đổi theo style, panel thiết kế cũ ẩn. Chuyển qua01 cho thấy cỡ84/offset−100 còn nguyên; quay lại06 giữ0,80×. Phát nháp có tiếng thật qua Analyser (RMS mẫu **0,0314**), pause và tua đến22,47s chuyển đúng Footage4/4, không reset chữ.
- Kiểm tra thêm hai clip thật IMG_3381.MOV/IMG_3387.MOV được sao chép vào profile riêng: xuất20,8s/3 footage qua JobManager của EXE đạt. Đã xem ảnh đầu/giữa/cuối: chữ nhỏ, rõ trên footage sáng; credit ở cuối, mép mờ và khung cố định. Ảnh minh họa `test_renders/verification/v12_chu_cuon.jpg`; video `output_videos/Reel_fb3c04d3eb33.mp4` bên trong profile thử, không tính vào lịch sử thật.
- Kiểm tra socket nội bộ cần chạy ngoài giới hạn mạng của môi trường kiểm thử; lượt chạy bị chặn được chạy lại đầy đủ và đạt, không bỏ qua test.

---

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
# Kiểm tra v6 — tải video (2026-10-27)

- Build `AutoReelSachHay_v6.exe`: 204349041 bytes, SHA256 `769C4B1BA7E768A4743FC0464FDA0E1856F60DB723310F14334185FCB63EF12D`. Launcher BAT/VBS ưu tiên v6; giữ nguyên EXE và phiên cũ.
- 28/28 unit tests đạt; `node --check ui/app.js`, compileall và `node tests/test_download_ui.js` đạt. Kiểm tra tên tiếng Việt/5 từ/Enter/tên thiết bị/ký tự cấm, nhớ thư mục và fallback, cancel, job/token sai, từ chối preview, copy/ghi đè nguyên tử, giữ file cũ khi lỗi và thử lại. Folder không đổi hash plan; autosave không gửi lại folder cũ.
- Luồng UI được kiểm tra tự động: chưa có Full HD thì dựng; tải lại dùng đúng export, đổi nội dung thì dựng mới; sửa trong lúc chọn/lưu vẫn dùng snapshot lúc click; copy lỗi dùng lại bản render; cancel không gọi render.
- Chạy `verify_v5.py --exe AutoReelSachHay_v6.exe --hold` trên profile riêng `.cache/v5_smoke_1793079131753518000`: preview, hai xuất đơn, hai batch Full HD, vòng footage, restart giữ draft/settings/history đều đạt. Không sửa lịch sử hay media người dùng.
- Trên UI của chính EXE v6, bấm Tải video và xác nhận hộp thoại Windows đã lưu `Hạnh phúc không phải đến.mp4`: probe 1080×1920, 4.0 giây; API settings giữ đúng last_save_directory. Chủ dự án xác nhận hộp thoại lưu xuất hiện. Lần đầu tải tăng đúng một lượt dựng; copy không tăng lượt riêng.
- Lỗi ghi đè/quyền ghi được giả lập ở cấp file-copy, không thay quyền Windows hay thư mục cá nhân. Tính khớp snapshot và tải lại kiểm tra bằng bộ kiểm tra UI độc lập; hộp thoại thật có thao tác xác nhận của người dùng.
- Mở qua BAT tại cổng 8777, đối chiếu PID/đường dẫn là AutoReelSachHay_v6.exe; UI giữ bản nháp và kho 59 clip. Ảnh nút tải: `test_renders/verification/v6_download.png`. File tải trùng SHA256 với bản render nội bộ (`ed365bb2b29b1a90c6b766a53655fa64346beebc2c6a5994040b5bb01ad1e9b1`). Phiên thử riêng được đóng bằng helper sở hữu tiến trình; bản chính v6 được giữ mở.

## Bổ sung v7 — nút tải trên thanh đầu (2026-10-27)

- Chuyển duy nhất btnDownloadVideo vào header cạnh nút thư mục, giữ nguyên xử lý tải. Kiểm tra HTML có đúng một ID và thuộc header; bộ kiểm tra luồng tải JavaScript và kiểm tra cú pháp đều đạt.
- Build lại `AutoReelSachHay_v7.exe`: 204348291 bytes, SHA256 `9CB9D189894CE8049801D967EA87C0195AD5BDCD25C5535A9321EC6D8A98314C`. BAT/VBS ưu tiên v7, không thay EXE cũ đang chạy.
- Mở qua BAT tại cổng 8778, xác nhận PID thuộc EXE v7. Kiểm tra UI thật: nút ở trên đầu, màu vàng, cạnh thư mục; cuộn đến cuối vẫn nhìn thấy nút. Ảnh `test_renders/verification/v7_download_top.png`. Không đổi renderer/planner và không cần dựng lại video mẫu cho thay đổi vị trí nút.


## Bổ sung v8 — Folder nền, tách cảnh theo ý, cân dòng và chống lặp câu trước (2026-10-28)

- **37/37 unit tests đạt**, `node --check ui/app.js`, `node tests/test_download_ui.js`, compileall/py_compile và kiểm tra diff đạt. Bộ kiểm tra mới gồm quét folder đệ quy, chọn/hủy/kho mặc định/folder mất hoặc rỗng/restart; dấu kết câu, ngoặc kép, viết tắt, số thập phân, từ nối đầu cảnh sau, giữ nguyên nội dung và giới hạn token; cân dòng, giữ cụm từ và token quá rộng.
- Kiểm tra footage: chỉ chọn trong kho hoạt động; giữ counts khi chuyển kho rồi quay lại; gộp clip trùng nội dung; ưu tiên ít lượt dùng trong tập phù hợp; tránh toàn bộ footage câu trước dù chỉ xem trước; fallback sau khi hết clip mới và chỉ lặp trong reel sau khi đi hết kho; kho một clip, job đồng thời, xuất lỗi giữ last_export và restart giữ lịch sử. Reservation và kiểm tra trước render dùng cùng quy tắc.
- Các bài kiểm tra atomic replace/lock được chạy với quyền ghi đầy đủ sau khi môi trường hạn chế chặn rename trên file tạm (WinError 5). Giữ nguyên cơ chế atomic save, không thay bằng ghi trực tiếp.
- Build cuối bằng `python -X utf8 build_onefile.py`: `AutoReelSachHay_v8.exe` và bản sao dist, **204.358.435 byte**, SHA256 **9392095E450F0CCA8B4AA2FB723FD646DF9413016994DB803BF118D20840FD36**. Giữ các EXE cũ; BAT/VBS ưu tiên v8. Đã đối chiếu startup/PID/tên EXE và --workspace qua cả VBS và BAT.
- `python -X utf8 verify_v8.py --hold` đạt trên profile riêng `.cache/v8_smoke_1793143693643412100`, gồm 2 clip mặc định + 3 clip trong folder riêng có thư mục con. Preview và Full HD cùng kế hoạch 2 cảnh, **8,0 giây**, đúng 540×960 và 1080×1920; giải mã toàn video và đối chiếu màu footage từng cảnh với kế hoạch. Preview không tăng lượt.
- Xuất thêm một Reel khác và hai Reel batch qua API; đổi folder đã nhớ ở phiên khác trong khi batch đang chạy vẫn giữ đúng folder đã chụp lúc submit. Folder mất trả HTTP 400, không tự fallback; trở về mặc định hoạt động. Restart EXE giữ nguyên folder, draft có dòng trống/trailing Enter, settings, counts và last_export. Báo cáo tại profile thử `verification.json`.
- Đối chiếu PNG chữ từ API overlay của EXE với renderer nguồn: **cả 5 theme khớp từng pixel**, với câu và credit dài. Đã xem bảng ảnh `balanced_lines.jpg` và `packaged_balanced_lines.jpg` trong profile thử: dấu tiếng Việt đủ, các cụm biết ơn/yêu thương/bình an không bị tách, không tràn vùng an toàn. Một số trường hợp khung/token đặc biệt vẫn ưu tiên đủ chữ hơn cân dòng tuyệt đối.
- Kiểm tra UI trên chính EXE: nút Tải video/Xuất nhiều Reel/thư mục xuất ở header và còn nhìn thấy khi cuộn; không còn nút Xuất Reel riêng. Modal hiển thị đúng 2 câu theo dữ liệu thử; xuất từ UI hoàn tất **2/2 reel**. Tổng **6 bản Full HD** từ kiểm tra API và UI đều probe đúng kích thước và giải mã hết không lỗi.
- Hộp thoại chọn folder thật đã xuất hiện (chủ dự án xác nhận và đóng); UI báo đã hủy, giữ nguyên folder và danh sách. Chuyển câu trên UI đổi từ các clip 4/2 của bản nháp sang clip 3 cho câu mới; Play phát hết tới 4,0/4,0 giây, báo có thể phát lại. Nút Dùng kho mặc định cập nhật từ 3 clip riêng về 2 clip mặc định đúng trên UI. Lưu folder tùy chọn thành công được kiểm tra qua API settings/restart và service với hộp thoại giả lập trong unit test; không tự khẳng định đã xác nhận lựa chọn folder mới qua hộp thoại thật.
- Toàn bộ mutation test dùng profile riêng. Đối chiếu SHA256 xác nhận `session_state.json` và `footage_usage.json` thật không đổi; giữ nguyên media, XLSX chưa theo dõi và các phiên khác. Chỉ đóng server/cửa sổ thử do đợt kiểm tra tạo. Không chạy lệnh tắt máy.


## Bổ sung v9 — Đồng bộ Sheet, giãn dòng đều và preview nhanh (2026-10-28)

- **55/55 unit tests đạt** trên mã cuối. `node tests/test_quote_sync_ui.js`, `node tests/test_fast_preview_ui.js`, `node tests/test_download_ui.js`, `node --check ui/app.js`, compileall và kiểm tra diff đạt. Các kiểm tra file nguyên tử/khóa chạy với quyền ghi đầy đủ trên profile tạm; không sửa cơ chế bảo vệ dữ liệu để né hạn chế môi trường.
- Đọc thành công Sheet thật bằng HTTP GET không cookie/OAuth/API key, đúng tab Đạo lý hay mỗi ngày và toàn bộ cột A: **16 câu** lúc kiểm tra, kể cả các dòng có done ở cột B. Parser giữ NFC, dấu câu, ô có nhiều dòng, thứ tự và câu trùng; bỏ dòng trống. Kiểm tra BOM/CSV lỗi/HTML đăng nhập/quá giới hạn, HTTP 403/mất mạng, cache hỏng và lỗi ghi cache đều giữ nguồn tốt trước đó hoặc quay về nguồn cục bộ khi chưa từng tải thành công.
- Đồng bộ snapshot thêm/sửa/xóa/reorder/rỗng và giữ nguyên draft/plan/export đang mở được kiểm tra bằng dữ liệu giả lập; không sửa Sheet thật để làm kiểm tra. Chu kỳ **1.800 giây** được kiểm tra bằng thời gian giả lập, gồm lần mở đầu và lần thử lại khi lỗi; EXE trả next_check_at đúng 30 phút. Không chờ 30 phút thực tế và không tạo automation ngoài ứng dụng.
- Giãn dòng: tái hiện đúng câu “Chỉ những người tu / đến mức không thấy / mình quan trọng nữa”. Baseline cũ [1306,1415,1496] có bước 109/81 px; mới [1320,1415,1510] có bước **95/95 px**. Regression kiểm tra thân chữ giống nhau giữ đúng baseline khi dòng có dấu cao/thấp, quote/credit dùng anchor ls, năm theme và vùng an toàn/footer. Ảnh so sánh `.cache/v9_line_spacing/comparison.jpg` đã xem trực tiếp.
- Tối ưu preview: 360×640/30 fps, ultrafast; một lượt mã hóa khi tối đa 4 cảnh, worker riêng, cache trả done tức thì, bỏ preview cũ còn chờ và khóa cache giữa các phiên. Full HD vẫn 1080×1920/30 fps/veryfast CRF 19. Unit kiểm tra preview không đứng sau export, không reserve footage, gộp yêu cầu cùng plan, bỏ queued cũ đúng client, stale result không thay player, preload không autoplay và Play dùng lại Promise/file đã chuẩn bị.
- Benchmark nguồn trên cùng plan và cùng overlay đã sửa baseline: ba cảnh 12,8 giây, preview cũ 540p **8,85 s** → mới 360p **3,72 s** (**2,38×**); trên clip thật IMG_3397.MOV 1080×1920, reel 4,8 giây: **5,12 s → 3,29 s** (**1,56×**). Cả hai cặp đã giải mã hết. Báo cáo ở `.cache/preview_bench_1793148664907289300/benchmark.json` và `.cache/real_preview_bench_1793148852246338500/benchmark.json`. Đây là mẫu đo trên máy hiện tại, có đánh đổi độ nét của bản xem nhanh, không phải bảo đảm cho mọi kho clip.
- Build cuối `python -X utf8 build_onefile.py`: **AutoReelSachHay_v9.exe**, **204.370.681 byte**, SHA256 **E29E0CB5ECAFB791CC0F0ABB860565EB8363791F58A3B05A8A2CE8D1DFCBBCA9**. Bản root/dist cùng hash; startup qua cả VBS và BAT đối chiếu đúng EXE v9/PID/--workspace. Giữ v8 và các bản cũ.
- `verify_v9.py --hold --real-source <clip thật>` đạt trên profile riêng `.cache/v9_smoke_1793149397572309700`: startup/manual sync đọc Sheet thật, cache/restart, --no-sheet-sync dùng TXT riêng, bản nháp có khoảng trắng/dòng trống/trailing Enter giữ nguyên, lịch sử footage không reset. Preview không tăng counts. Đã dựng/giải mã hai cặp preview/Full HD, gồm câu lấy từ Sheet và câu trong ảnh trên clip thật. Thời lượng khớp; PNG overlay từ EXE khớp từng pixel với renderer nguồn. Frame preview so với Full HD thu về cùng kích thước có sai khác RGB trung bình **4,946/255**, phù hợp bản nén nhẹ.
- Preview có sẵn qua API EXE trả job done/cache trong **0,015 giây**; mẫu clip thật trong EXE dựng preview **3,05 giây**. Trên UI do chính EXE phục vụ, trạng thái Sẵn sàng xem xuất hiện ở nền; bấm Cập nhật ngay giữ nguyên textarea và vẫn đủ 16 câu; bấm Phát dùng preview đã chuẩn bị, phát hết **8,0/8,0 giây**, chuyển đúng cảnh 2/2, không tự phát lúc warm-up và không có hai lớp chữ. Thao tác UI cuối được kiểm tra trong trình duyệt thử nền để không tranh chuột với người dùng. Ảnh `.cache/v9_smoke_1793149397572309700/v9_ui_proof.png`; báo cáo `verification.json` cùng profile.
- Mọi mutation test, cache Sheet, video xuất và lượt footage thử nằm trong `.cache` profile riêng. Clip thật chỉ đọc. SHA256 của session_state.json/footage_usage.json thật trước và sau đợt kiểm tra EXE không đổi; giữ media, XLSX chưa theo dõi và phiên người dùng. Chỉ dừng server/profile/tab thử do kiểm tra tạo; không chạy lệnh tắt máy. Nguồn/tài liệu được commit và backup main theo quy trình bắt buộc; xác nhận remote HEAD là bước cuối.


## V10 — Scene footage, live draft, download history and offline music (2026-10-28)

- Final application built with `python -X utf8 build_onefile.py` (exit 0). Root/dist `AutoReelSachHay_v10.exe`: 204,406,485 bytes; SHA256 `042eb62deead8995636024658b94afc5004ab046201ab43f46ead1a800f4e071`. V9/older EXEs and user sessions preserved. The four UI resources served by EXE match final source byte-for-byte.
- Python unittest discovery: 71/71 passed. Music-specific tests rerun after final whitespace normalization change: 3/3 passed. Node download, instant-preview UI, catalog/download-status UI and DraftPlayer suites all passed; JS syntax, compileall and git diff whitespace checks passed. Windows restricted temp atomic-rename checks need the normal test process permission; did not weaken atomic writes.
- Packaged VBS launch, headless `--workspace` isolated profile `.cache/v10_smoke_1793156645973648000`, health PID/executable/version and command-line ownership verified. BAT restart also verified independently on the same isolated profile. Source smoke profiles were separate; no reset of real footage history.
- Proxy API: selected scene priority, byte ranges (206/32 bytes), decode to end, 360×640, cache reuse and no preview footage/download turns verified. Two-scene synthetic cold scene proxies: 0.562 s; warm prepare: 0.047 s. Actual rotated HEVC MOV `IMG_3397.MOV` first full-clip proxy: 10.187 s (one-time preparation), duration 17.133 s. Initial proxy cost is explicitly distinguished from warm playback.
- GUI smoke against EXE: selecting cached footage automatically plays the affected scene; measured first live frame 103 ms from selection. Source two-scene repeated replacements measured 124/154 ms and played to end. UI submits no whole-Reel preview job. Checked GUI scene selection, pause/resume, seek-to-start, replay, selected offline-track listening and automatic scene play; source-time mapping and buffer/error handling also covered by player tests; attached decoder/audio DOM state used for verification. PNG overlay resources for all five themes matched `scene_overlay` pixel-for-pixel. Mean RGB difference live proxy+overlay vs resized actual Full HD at t=2 s: 3.13/255. Full HD 1080×1920 synthetic 8.8 s and actual MOV 4.8 s both decoded completely, with music.
- Persistent quote status: native Save dialog appeared; user manually saved the test video on Desktop. Saved file verified 1080×1920. Catalog/UI showed quote one downloaded, quote two pending, one saved event; green badge/time/count visible. After stopping only the owned test process and reopening via BAT, ledger persisted and startup API plus GUI selected quote two (pending). Screenshot proof `v10_download_status.png`, report `download_verification.json` in the isolated profile. This does not import guessed download history from pre-v10.
- Unit/integration cases cover exact draft recovery; add/edit/delete/reordered/duplicate Sheet rows; only successful save marks downloaded; cancel/failure/render/preview/batch exclusions; copy success with history-write warning; corrupt history preserved. Footage tests include preferences per scene, lower-count/previous/Reel reuse exclusions, changed-text hints ignored, atomic reservation validation and cache restart/source invalidation. Existing concurrent/error/export-turn checks still pass.
- Offline music: public Hugging Face revision `615a4b33c804a4a8a85aa7791ea3613d4749ad7a`, all 175 MP3s / 430,821,487 bytes downloaded to `CLIP TƯỢNG PHẬT LQ/NHẠC NỀN` in 114.0 s, zero failures. Every file rechecked for exact size and LFS SHA256; audio probed before publish. Files/media/locks remain ignored and are not bundled or committed. Tests cover stable random selection, changed seed/previous-track avoidance, selected/mute/bell modes, offline range playback, folder derivation, retry reuse, hash mismatch, preserving conflicting local filenames. Isolated EXE profile used two generated music tracks plus one read-only copy from the downloaded library; no Internet used for playback/render. GUI audio was playing from `/api/plan_music` while draft time advanced.

- Packaged batch smoke: 2/2 Full HD Reels succeeded; consecutive music selections differed (Test music 1 / downloaded piano track), stale draft scene hints ignored, download ledger unchanged (second quote still pending). Reports in batch_verification.json. Exact real MOV overlay/composite visually reviewed; all five theme PNG checks and full decodes passed.
- Personal files checked before/after the packaged verification window: session_state.json: unchanged, footage_usage.json: unchanged, quote_download_history.json: unchanged, draft_recovery.json: unchanged, dao_ly_thien_ton_phat_quang.xlsx: unchanged. The Desktop video saved by the user was verified read-only and preserved.


## V11 — Manual downloaded marker, audible live preview and no meditation bell (2026-10-28)

- Built final app with `python -X utf8 build_onefile.py`, exit 0. `AutoReelSachHay_v11.exe` root/dist: 203,218,317 bytes, SHA256 `c5e66c0ed6a2d17da43519d215b98e5d91c1190e83756cf9e7f53e1991725752`. PyInstaller archive inspected: no thien_chuong asset. Bell choice/button/endpoint/fallback removed, old bell mode normalizes to random. Legacy source WAV and previous EXEs preserved outside the new bundle.
- Python unittest discovery: 74/74 passed (63.787 s); final Node suites for download, instant UI, quote catalog/manual flags, and DraftPlayer passed, plus syntax/compileall/diff checks. New regressions reproduce pending audio.play rejected after buffering pause, verify retry instead of permanent audioBlocked; genuine NotAllowedError can be enabled; old plan Promise rejection cannot mute a new plan. Manual marker tests cover idempotency, undo, restart, validation, edited draft while waiting, write errors and preserving real download counts/audit.
- Isolated packaged profile `.cache/v11_smoke_1793159631359721100`, VBS startup verified executable/version/PID/workspace. Static UI resources from EXE matched final source byte-for-byte. API mark/unmark changed only status ledger, not draft/footage bytes, and manual entries retained count=0/last_downloaded_at=null. Repeated marking did not increase revision. GUI marked the active quote during playback without changing text/plan or interrupting audio; undo returned it to pending.
- Actual live output checked through the AudioContext Analyser AFTER Gain and connected to destination: playing state, volume 0.85, RMS 0.0712614 at ~1 s. Paused then resumed on EXE: RMS 0.0714899 at ~0.8 s, still playing. Source smoke also had RMS 0.0556809 during fade-in. This verifies PCM signal, not just paused=false. UI exposes audio status/level and an enable button only on a real denial; no global volume/device settings changed. Regression reference: [Chrome play/pause Promise interruption](https://developer.chrome.com/blog/play-request-was-interrupted).
- Full HD packaged render 1080×1920 / 4.0 s decoded to end with audio. Source tone RMS at t=1..2 s: 0.0803645; exported AAC PCM RMS: 0.0713122 (>0.01 threshold). Download flags remained [true,false] after rendering. Bell endpoint returned 404, no bell controls in HTML, no whole-Reel preview job created for live playback. Existing offline music files unchanged.
- Stopped only the owned test process, restarted SAME isolated workspace through BAT; health again v11, ledger exactly preserved, startup selected index1 (first pending quote), manual/undone flags [true,false]. Reports: verification.json, ui_audio_verification.json, ui_resume_verification.json, restart_verification.json; GUI proof v11_ui_proof.png in that profile.
- Before/after packaged tests: session_state.json, footage_usage.json, quote_download_history.json, draft_recovery.json, personal XLSX and legacy bell WAV all unchanged in the real workspace. Tests did not reset real history, alter user media, close user sessions, or create a new Desktop video. Owned test servers/tabs are cleaned up after checks. Downloaded 175-track library remains offline alongside footage and outside Git/EXE.
