# System map — Auto Reel Sách Hay Mỗi Ngày

Cập nhật: 2026-10-28. Đọc tài liệu này trước khi nâng cấp hoặc sửa chữa. Repo backup: https://github.com/ngonco/AutoReel_SachHayMoiNgay (nhánh `main`).

## Quy tắc bắt buộc sau mỗi đợt chỉnh sửa

**Sau mỗi đợt sửa code: kiểm tra phù hợp → đóng gói lại `.exe` từ code cuối cùng → kiểm tra bản EXE mới → cập nhật tài liệu → commit → push GitHub → xác nhận remote HEAD trùng local HEAD. Luôn đóng gói lại EXE và backup sau khi sửa code xong theo yêu cầu của chủ dự án.**

- Bắt buộc build lại bằng `python -X utf8 build_onefile.py` sau mọi thay đổi Python, UI HTML/CSS/JavaScript, thư viện hoặc cấu hình đóng gói, kể cả sửa nhỏ. Mở qua launcher và kiểm tra chức năng vừa sửa trên chính EXE mới trước khi bàn giao; không chỉ chạy thử mã Python rồi giao EXE cũ. Nếu cần đổi tên EXE vì bản cũ đang chạy, cập nhật BAT/VBS và giữ nguyên phiên người dùng. Build hoặc kiểm tra lỗi thì báo chưa hoàn tất, không nói EXE đã được cập nhật. Chỉ sửa tài liệu thì không cần build lại.
- Chỉ stage các file nguồn/tài liệu có chủ đích; đọc `git diff --cached` và kiểm tra bí mật trước khi push.
- Không commit kho clip, video xuất, cache, log, EXE, DLL, font Microsoft, cài đặt cá nhân, khóa/token hoặc file `.env`. `.gitignore` đã loại chúng.
- Không force-push, không xóa lịch sử để xử lý xung đột. Fetch và tích hợp thay đổi remote trước; dừng và báo nếu có xung đột không thể giải quyết an toàn.
- Cập nhật kết quả kiểm tra trong `VERIFICATION.md`; khi thay đổi kiến trúc/API/quy tắc dựng, cập nhật ngay tài liệu này.
- Nếu push lỗi hoặc thiếu đăng nhập, giữ commit cục bộ, báo rõ backup GitHub chưa hoàn thành. Không nói đã backup khi chưa xác nhận remote.
- Commit là bản backup mã nguồn. Phục hồi đầy đủ ứng dụng cần kho clip, PMDX/TXT cá nhân và các dữ liệu bị ignore được sao lưu riêng; EXE có thể build lại.
- Không chạy lệnh tắt máy trong kiểm tra. `render_all_reels.py` chỉ tắt máy khi người dùng chủ động thêm `--shutdown`.

Ví dụ sau khi đã stage đúng các file:

```powershell
git diff --cached --stat
git diff --cached
git commit -m "Describe completed change and verification"
git push origin main
git rev-parse HEAD
git ls-remote origin refs/heads/main
```

## 1. Hệ thống và điểm vào

Ứng dụng desktop Windows thực chất là máy chủ HTTP chỉ nghe `127.0.0.1`, mở Edge/Chrome ở app mode. Python 3.11, Pillow, OpenCV/Numpy, FFmpeg/FFprobe. Không cần dịch vụ AI hoặc API bên ngoài để dựng reel.

```text
BAT / VBS / EXE / python app.py
  → app.py: đường dẫn dữ liệu, ThreadingHTTPServer, API
  → UI: nhập câu + clip cảnh đầu + settings
  → core.planner: kế hoạch cảnh duy nhất
      → core.paginator: chia chữ + thời gian đọc
      → core.video_detector: kho clip + thumbnail + ước lượng vị trí
      → core.media: thông tin nguồn thực qua FFprobe
  → core.jobs: hàng đợi một worker
      → core.renderer: nền cắt/làm chậm → crossfade → overlay Pillow → nhạc
      → bản nhẹ 540×960 hoặc Full HD 1080×1920
  → trình duyệt phát MP4 đã có chữ; không vẽ chồng canvas
```

- `app.py`: `main()`, `--headless`, `--port N`, `--batch`; HTTP API, byte ranges, logging và native file picker.
- `Chay_Ung_Dung_Auto_Reel.bat`: chuyển về thư mục script rồi ưu tiên EXE v8, rồi v7/v6/v5/v4/v3/v2, EXE cũ gốc, EXE dist, cuối cùng Python. Không phụ thuộc thư mục người dùng đang đứng.
- `Mo_App_Auto_Reel.vbs`: launcher tương tự, định vị theo chính file VBS.
- `render_all_reels.py`: batch dùng cùng settings/planner/renderer, mặc định không shutdown.
- `test_and_review.py`: script mẫu cũ vẫn gọi wrapper renderer; kiểm chứng mới dùng `verify_samples.py`.

Chạy phát triển: `python -X utf8 app.py`. Chạy API thử: `python -X utf8 app.py --headless --port 8877`. Dùng thư mục dữ liệu có quyền ghi. Có thể mở nhiều bản trên cổng khác nhau; ứng dụng chưa có khóa một phiên duy nhất.

## 2. Thư mục và dữ liệu

| Vị trí | Vai trò | Git backup |
| --- | --- | --- |
| `core/` | Planner, layout, renderer, settings, jobs, media, đọc câu | Có |
| `ui/` | HTML/CSS/JS; không tự chia chữ hoặc tính lại timeline | Có |
| `assets/thien_chuong.wav` | Nhạc chuông thiền | Có |
| `assets/fonts/` | Font cục bộ tùy chọn; fallback Windows Fonts | Không chứa font Microsoft trong Git |
| `CLIP TƯỢNG PHẬT LQ/DỌC`, `NGANG` | Kho MOV/MP4/M4V/MKV | Không |
| `assets/imports/` | Kho phụ nếu chủ dự án tự thêm file | Không |
| `assets/thumbnails/` | Thumbnail + video cache v3 | Không |
| `session_state.json` | Bản tự lưu v5: toàn bộ thiết lập, quote nguyên văn, quote_index, video_path, safe_zone và thứ tự lần lưu | Không |
| `settings.json` | Thiết lập cũ, chỉ đọc để nhập lần đầu nếu chưa có session_state | Không |
| `footage_usage.json` | Lượt dùng theo nội dung footage, dấu vân tay và lượt giữ chỗ | Không |
| `*.lock` của session/footage/export | Khóa liên phiên, không xóa khi app đang làm việc | Không |
| `settings.example.json` | Mẫu thiết lập chuẩn | Có |
| `New PlanMaker document.pmdx`, `quotes.txt` | Nội dung cá nhân nếu có | PMDX không; TXT chỉ thêm có chủ đích |
| `.cache/plans/` | Kế hoạch JSON theo hash | Không |
| `.cache/overlays/`, `.cache/previews/` | PNG chữ và MP4 xem trước | Không |
| `output_videos/` | Reel hoàn chỉnh, kể cả xuất hàng loạt | Không |
| `test_renders/verification/` | Ảnh kiểm tra + report.json | Không |
| `build/`, `dist/`, `.cache/package/` | Artifact build | Không |
| `logs/app.log`, `logs/console.log` | Lỗi runtime/render và stdout EXE | Không |

Đường dẫn chạy nguồn lấy từ `app.py`. Bản frozen lấy UI/font/FFmpeg trong `sys._MEIPASS`; dữ liệu ghi được nằm cạnh EXE hoặc thư mục cha có kho clip. Ưu tiên vị trí EXE trước CWD. Không đưa thư mục dữ liệu tùy ý vào `sys.path` khi frozen.

`core.pmdx_reader.get_all_quotes()` thử PMDX có `xl/sharedStrings.xml`, rồi TXT từng dòng; fallback 16 câu chuẩn. Tên `quotes.xlsx` hiện còn trong danh sách ứng viên nhưng **chưa có bộ đọc XLSX**. Không hứa hỗ trợ workbook XLSX tổng quát. Mọi text vẽ được chuẩn hóa NFC.

## 3. Quy tắc dựng — nguồn sự thật duy nhất

### Planner và cache

`core.planner.build_plan(payload, workspace_dir, detector)` nhận quote, video_path tùy chọn và settings. Trả JSON plan gồm:

- `plan_id`: SHA256 rút gọn 24 hex; `version`, `settings`, `quote`, `segmentation_mode`, `duration`, `transition`, `music`, `scenes`. `quote` giữ ranh giới xuống dòng; `segmentation_mode` là manual_lines/auto/single.
- Mỗi scene có `index`, `text`, `video_name`, `video_path`, `thumb_url`, `resolved_pos`.
- `start/end`: khoảng nền gồm phần overlap. `text_start/text_end`: khoảng phần chữ độc lập; không chồng hai phần chữ.
- `source_start/source_end`, `speed`: đoạn gốc và tốc độ. `source/source_info`: fingerprint và metadata FFprobe.
- Hash gồm settings, nội dung, phiên bản planner/template, nguồn và nhạc (đường dẫn + size + mtime_ns). Sửa template/quy tắc render cần tăng `PLAN_VERSION` để tránh cache cũ.
- `load_plan()` kiểm tra phiên bản và fingerprint cả lúc nhận API và lúc job chạy. Nguồn đã sửa/xóa sẽ yêu cầu lập lại kế hoạch.

### Chia chữ và thời gian

`core.paginator`: chia theo token whitespace, giữ nguyên chữ, dấu câu và thứ tự sau NFC; quy hoạch động ưu tiên ranh giới dấu câu, tránh tách các cụm từ tiếng Việt phổ biến hoặc để hư từ ở cuối cảnh, và cân đối độ dài. V8 tách dấu kết câu `. ! ? …` kể cả câu ngắn, giữ dấu ngoặc/ngoặc kép đóng và tránh viết tắt/initial/số thập phân. Ranh giới mềm tại dấu phẩy/chấm phẩy/hai chấm hoặc từ nối phù hợp mệnh đề, mỗi vế ít nhất 6 token; từ nối nằm đầu cảnh sau. Mục tiêu 12–18 từ, trần 24 từ. Nếu nội dung có từ hai dòng có chữ, mỗi dòng là đúng một cảnh thủ công, không tự chia nhỏ thêm và không ghép qua dòng; bỏ dòng trống, chuẩn hóa CRLF/NFC/khoảng trắng trong dòng. Quy tắc xuống dòng ưu tiên cả khi auto_paginate tắt. Với một dòng, vẫn dùng tự chia cảnh như trước; tắt auto_paginate thì giữ nguyên một cảnh. Bọc chữ theo chiều ngang trong textarea không phải Enter và không tạo cảnh mới. Dòng thủ công rất dài vẫn phải vừa layout; nếu không vừa sẽ yêu cầu rút ngắn hoặc thêm Enter.

Thời gian đọc cơ sở mỗi phần `max(4, số từ/3 + 0.8)` giây, làm tròn lên khung 30 fps. Nếu tổng thấp hơn thời lượng tối thiểu đã chọn, phân bổ phần còn lại theo số từ. Không ép câu dài vào 10–15 giây. Chữ fade 0,2 giây ở hai đầu mỗi phần; đủ thời gian đọc ổn định sau fade.

Nền chồng 12 khung (0,4 giây). Text đổi ở giữa khoảng crossfade; một phần đã tắt trước khi phần sau hiện. Tổng duration là cuối scene cuối, bao gồm tính overlap chính xác.

### Chọn và cắt clip

V5 dùng `core.footage_pool.FootagePool` cho mọi lần xuất đơn, hàng loạt và wrapper CLI. Footage được nhận dạng bằng SHA256 nội dung file (rút gọn 24 hex); các bản sao giống hệt nội dung chỉ là một footage dù khác tên/đường dẫn. Hash được cache theo đường dẫn + size + mtime_ns trong `footage_usage.json`, chỉ đọc lại nội dung khi file thay đổi.

Mỗi footage có số lượt xuất thành công. V8 chỉ chọn trong active_ids của kho hiện tại, không chọn từ toàn bộ inventory lịch sử. Mỗi cảnh ưu tiên clip chưa dùng trong reel và không thuộc câu trước; khi hết clip mới phù hợp, dùng clip câu trước chưa dùng trong reel; chỉ lặp trong reel sau khi hết kho. Trong tập đủ điều kiện lấy lượt hiệu dụng thấp nhất (thành công + giữ chỗ + giả lập trong reel), tránh clip liền trước khi ngang lượt, rồi xét clip được chọn cho cảnh đầu và thứ tự clip dọc/tên file. Quy tắc tránh câu trước/đi hết kho được ưu tiên hơn lượt nhỏ nhất toàn kho. Clip được chọn nhưng đã dùng nhiều hơn sẽ được đổi; UI hiển thị clip thực tế và số clip còn ở lượt hiện tại.

Preview/lập kế hoạch không tiêu hao lượt. Khi submit export, giữ chỗ nguyên tử theo job; các job/phiên khác thấy lượt đã giữ và không chọn trùng. `footage_pool.revision` trong plan phát hiện kế hoạch cũ (HTTP 409, code footage_conflict). UI lập lại kế hoạch trước mỗi lần xuất và tự thử lại một lần nếu xung đột. Batch lập từng kế hoạch ngay trước từng reel sau khi reel trước đã ghi nhận lượt.

`reel_export.lock` tuần tự hóa export giữa các phiên v5. Ngay trước render, phát lại cùng quy tắc lựa chọn trên active_ids, lượt thực tế và câu xuất thành công gần nhất; xung đột yêu cầu lập lại kế hoạch. Chỉ tăng counts sau khi MP4 hoàn tất; export lỗi trả lại lượt. Lượt giữ chỗ từ tiến trình đã thoát được giải phóng khi lập kế hoạch tiếp. Lịch sử có hiệu lực cho các lần xuất bằng v5 trở đi; không suy đoán footage của video cũ không có lịch sử. File lịch sử lỗi sẽ báo lỗi thay vì tự reset và gây lặp. Không xóa lịch sử hoặc dùng cache preview để tính lượt.

Đoạn nguồn bắt đầu 0,5 giây, hoặc 1/4 độ dài với nguồn ngắn hơn 2 giây. Lấy tối đa đủ thời gian cảnh; nếu thiếu thì `speed = available / needed`, dùng setpts làm chậm. Không lặp nguồn. FPS cuối luôn 30; có pad rất ngắn để bù làm tròn khung cuối.

`core.video_detector` đo kích thước/thời lượng/rotation thực, tạo thumbnail crop dọc. Dùng Haar cascade rồi heuristic màu để gợi ý nửa trên/dưới; đây là **ước lượng một ảnh mẫu**, không theo dõi mặt toàn clip, không bảo đảm tránh mặt khi tượng/camera di chuyển. Có vị trí thủ công. Cache dùng đường dẫn đầy đủ + mtime_ns + size, có khóa trong phiên và ghi file tạm riêng.

### Template và render

`core.renderer.layout_overlay()` tính trước toàn khối: ornament, quote, separator, credit nhiều dòng và padding. Đáy khối tối đa `int(1920 * .86) = 1651`; vị trí được clamp theo chiều cao thật, không chỉ clamp Y ban đầu. V8 dùng quy hoạch động theo chiều rộng font thực để cân dòng cho quote và credit, phạt mạnh dòng cuối một token hoặc hai token ngắn, ưu tiên giữ cụm tiếng Việt và tránh hư từ ở cuối dòng. Không bảo đảm tránh mọi từ mồ côi nếu khung hoặc token quá dài. Credit được wrap theo chiều rộng; font dùng bounding box để tính dấu tiếng Việt. Chuỗi không có khoảng trắng được ngắt ký tự để không tràn ngang.

Năm theme: Thiền Vàng, Tinh Khôi, Kinh Điển, Điện Ảnh, Sen Giấy. Font serif `timesbd.ttf`; sans `segoeuib.ttf`; credit `segoeui.ttf`. Tìm trong assets workspace, bundle, rồi Windows Fonts. Thiếu font báo lỗi rõ.

Viền chữ mềm dùng chung cho quote và credit, chỉnh qua settings: `outline_enabled` (mặc định true), `outline_color` (`auto` hoặc #RRGGBB, mặc định auto), `outline_width` (0–16 px Full HD, mặc định 4), `outline_blur` (0–24 px, mặc định 8), `outline_opacity` (0..1, mặc định 0.85; nhận phần trăm cũ). Các tên camelCase tương ứng được chuẩn hóa. `auto` dùng màu tối #101018 cho chữ sáng và màu giấy #fff8e9 cho chữ tối của Sen Giấy. Màu tự chọn được giữ khi đổi theme.

`soft_outline(mask, style)` lấy mask glyph, crop vùng có chữ với padding, giãn mask bằng MaxFilter, làm nhòe Gaussian, trừ vùng mực gốc rồi áp màu/opacity. `paint_outlined_text()` composite viền và nét chữ sắc sau cùng. Không blur trực tiếp phần chữ. Tắt viền, opacity 0 hoặc width=blur=0 trả đúng phần chữ không viền. Credit có độ dày/nhòe giảm theo tỷ lệ cỡ chữ để không bết chữ nhỏ. UI có bật/tắt, tự chọn màu, color picker và ba thanh trượt; mọi chỉnh sửa invalidate plan/preview và được lưu cùng settings. Các field outline tự đi vào hash kế hoạch; PLAN_VERSION v8 bao gồm quy tắc cân dòng mới để không dùng overlay cache cũ.

`scene_overlay()` và `render_overlay()` dùng chung cho ảnh tĩnh, preview và Full HD. Preview thu nhỏ ảnh từ chính overlay Full HD. Renderer chuẩn hóa nền từng cảnh, làm chậm/crop/fps, sau đó ghép xfade và overlay theo timeline. Chốt `format=yuv444p,fps=30` trước xfade để tránh lỗi FFmpeg rate `1/0`. MP4 cuối H.264/yuv420p + AAC, faststart. Nhạc nền liên tục có fade đầu/cuối; âm thanh nguồn bị tắt.

`render_reel_video()` là wrapper tương thích cho script cũ và trả `success/error`. Các tham số `music_path` và `video_volume` cũ chưa được ánh xạ vào planner; luồng mới dùng chuông thiền và tắt âm nguồn. Muốn thêm nhạc tùy chọn phải bổ sung fingerprint/API/settings đồng bộ, không chỉ sửa lệnh FFmpeg.

## 4. API và giao diện

HTTP chỉ cục bộ. JSON lỗi `{success:false,error}` với HTTP 400. File tĩnh hỗ trợ byte ranges: 200/206/416, streaming theo chunk để tua và không tải cả MP4 vào RAM.

| Method / URL | Chức năng |
| --- | --- |
| GET `/api/health` | version, pid; kiểm tra khởi động |
| GET `/api/quotes` | danh sách câu |
| GET `/api/videos` | danh sách clip phân tích được |
| GET/POST `/api/settings` | đọc session chuẩn hóa / merge patch atomically; hỗ trợ `{_client_id,_sequence,_patch}` và body field cũ |
| POST `/api/plan` | payload quote + video_path + settings → plan |
| GET `/api/overlay/{plan_id}/{index}` | PNG dùng chung với renderer |
| POST `/api/preview` | plan_id hoặc payload cũ → job HTTP 202 |
| POST `/api/render` | plan_id hoặc payload cũ; `async:true` → job 202, mặc định chờ result tương thích cũ |
| POST `/api/batch_render` | settings → job nếu `async:true`, mặc định chờ; áp dụng cùng planner cho mỗi câu |
| GET `/api/jobs/{id}` | queued/running/done/error, progress, message, result/error |
| GET `/api/preview_video/{filename}` | MP4 nhẹ đã có chữ và nhạc |
| GET `/api/rendered_video/{filename}` | MP4 Full HD |
| GET `/api/thumb/{filename}` | thumbnail ảnh |
| POST `/api/select_video` | native picker, trả local video metadata; cancel → video:null |
| POST `/api/select_video_directory` | chọn folder nền hoặc use_default:true; validate, nhớ folder và trả videos/settings |
| POST `/api/select_save_video` | quote → hộp thoại Lưu video; trả cancelled hoặc save_token + filename |
| POST `/api/save_video` | save_token + render_job_id Full HD hoàn tất → job sao chép HTTP 202; result.saved_path khi xong |
| POST `/api/open_folder` | mở output_videos |

`core.jobs.JobManager` dùng ThreadPoolExecutor một worker cho mọi job; thêm khóa export liên tiến trình và giữ chỗ footage. Preview cùng plan đang chờ/chạy được gộp; preview đã có file hợp lệ dùng cache. Job lưu RAM, không tự tiếp tục sau restart. Batch báo files/failures theo từng câu, không trả thành công giả khi một phần thất bại.

`ui/app.js`: gọi plan sau thay đổi với debounce, dùng revision để bỏ kết quả đến muộn. Không tính timeline hay tự vẽ template nữa. Ảnh tĩnh: thumbnail + overlay máy chủ. Play: tạo/poll preview job rồi bật video controls và tắt canvas. Các chức năng pause/resume/seek/ended dựa trên video thật. Sửa nội dung/clip/settings làm plan/preview/export URL hiện tại hết hiệu lực. Kết quả job cũ vẫn có thể còn trong cache, nhưng không phát nhầm lên thiết lập mới.

Tự lưu v5: `core.settings.load_settings()` đọc `session_state.json`; nếu chưa có mới nhập từ settings.json cũ. Bản v5 ghi file riêng để các EXE cũ còn mở không thể ghi đè bản nháp mới. `save_settings_patch()` nhận patch từng field, không reset field bị bỏ qua; `_client_id` + `_sequence` ngăn request cũ ghi đè request mới cùng trang. File ghi qua temp riêng + fsync + replace, có khóa liên phiên trong `core.persistence`.

Frontend giữ nguyên quote (kể cả dòng trống/trailing Enter), quote_index, video_path, safe_zone và mọi control nội dung/thiết kế/âm lượng. UI báo Đang lưu/Đã lưu tự động/lỗi và tự thử lại; hàng đợi save gửi tuần tự, debounce 250ms, pagehide gửi beacon/keepalive. Reload khôi phục bản nháp và clip đã chọn; render không thay quote trong bản tự lưu. Safe zone chỉ là trạng thái xem, không vẽ vào MP4. Các field nháp được loại khỏi settings của plan để không tạo cache render vì thay đổi chế độ xem.

### Tải video v6

V7 chuyển duy nhất nút btnDownloadVideo lên .top-actions trong header sticky, cạnh nút mở thư mục; giữ ID và luồng xử lý. Bố cục thu gọn badge trên màn hình hẹp và cho header xuống hàng để nút không tràn. Chỉ thay giao diện, không đổi renderer hoặc PLAN_VERSION.

`core.downloads.SaveVideoService` tuần tự hóa hộp thoại tkinter Lưu video, dùng thư mục `last_save_directory` từ session_state.json; nếu không tồn tại dùng output_videos. Sau xác nhận mới ghi nhớ thư mục bằng merge patch. Frontend không gửi lại field này trong autosave để tránh giá trị cũ ghi đè thư mục vừa chọn. Field bị loại khỏi plan/settings/hash; không đổi PLAN_VERSION vì không đổi dựng/layout/planning.

Tên gợi ý là 5 token whitespace đầu sau NFC, bỏ ký tự Windows cấm và dấu chấm/khoảng trắng cuối, tối đa 160 ký tự; fallback Reel, bảo vệ tên thiết bị CON/PRN/COM…; đuôi .mp4. Hộp thoại cho sửa tên và xác nhận ghi đè. Hủy trả cancelled:true, không submit export. Đường dẫn đích do native picker cấp, giữ sau save_token trong RAM (tối đa 100 lựa chọn), không nhận đường dẫn tùy ý từ API save. Token mất khi server khởi động lại; thư mục vẫn được nhớ.

Frontend chụp payload tại lúc bấm Tải, chọn nơi lưu rồi dùng lại lastExport nếu khóa nội dung/thiết lập khớp và MP4 còn tồn tại (Range 0–0). Nếu cần dựng, renderSnapshot gọi planner và JobManager export hiện tại, tự thử lại một lần khi footage_conflict; không thay preview của bản nháp mới khi nội dung đã đổi. lastExport chỉ nằm trong trang hiện tại; reload/restart cần dựng lại khi tải, còn bản xuất cũ vẫn ở output_videos.

Job export có kind=export/preview. JobManager.save_video chỉ nhận ID kind=export đã done, file thực trong output_videos; không nhận preview, file ngoài hay job lỗi. Save job kind=save chạy trên hàng đợi hiện có, sao chép thành file tạm cùng thư mục đích, fsync rồi replace; lỗi không phá file đích cũ và vẫn giữ bản Full HD. Tải/copy không reserve hoặc tăng footage. Cùng token đã submit trả lại save job trước, lỗi cho thử lại. UI có tiến độ/lỗi/đường dẫn thành công; khóa nút xuất và tải trong khi tải.

`core.settings.normalize_settings()` là nơi duy nhất chuyển camelCase cũ sang snake_case, chuẩn hóa shade/volume 0..1 từ giá trị phần trăm cũ và giới hạn giá trị. UI lưu snake_case. File mẫu dùng snake_case. Không lặp mapping ở renderer/UI. `vertical_offset` nhận −1600..+1600 px (tên cũ verticalOffset vẫn đọc được); thanh trượt và ô số đồng bộ từng pixel. Layout vẫn clamp toàn khối vào 180..1651 để không cắt chân. Giá trị Y là độ dịch yêu cầu, có thể chạm giới hạn an toàn trước khi hết thanh trượt.

## 5. Kiểm tra, build và sửa lỗi

```powershell
python -X utf8 -m unittest discover -s tests -v
python -X utf8 verify_samples.py
python -X utf8 build_onefile.py
```

- Unit: đủ chữ/dấu, trần số từ, timeline/overlap, migration settings, bố cục footer 5 theme × 3 vị trí × 2 offset, clip ngắn, kho trống/một clip, vòng chọn clip và plan lỗi thời.
- Download: `tests/test_downloads.py` kiểm tra tên, nhớ thư mục, cancel, token/job hợp lệ, copy/ghi đè nguyên tử, lỗi lưu và cache không đổi. `node tests/test_download_ui.js` kiểm tra cancel, dùng lại export, đổi thiết lập, snapshot lúc click, thử lại copy và không ghi đè thư mục bằng autosave. Kiểm tra hộp thoại thật trên EXE mới.
- `verify_v5.py --exe AutoReelSachHay_v5.exe --hold`: kiểm tra EXE trên profile riêng với 3 clip màu, lưu draft/late request, preview không tiêu hao, 2 xuất đơn + 2 batch, đối chiếu màu frame, restart EXE và có thể giữ phiên để kiểm tra UI. Cần psutil (máy phát triển hiện dùng 7.0.0); chỉ đóng tiến trình thử do helper tạo.
- `verify_outline.py --base URL`: tạo bảng so sánh 5 theme với viền tắt/mềm/đậm, kiểm tra API màu/tắt/opacity 0 và xuất cặp preview/Full HD có viền bằng EXE đang chạy. Không sửa settings cá nhân.
- `verify_manual_lines.py --base URL`: kiểm tra Enter/CRLF/dòng trống, ưu tiên thủ công khi auto tắt, API Y rộng và xuất cặp preview/Full HD với đúng ba dòng.
- `verify_samples.py`: 3 quote (1/2/3 cảnh) × 2 độ phân giải; probe kích thước/duration, decode toàn video, ảnh tại từng cảnh/transition/cuối và bảng stress credit dài.
- `verify_api.py --base http://127.0.0.1:8767` kiểm tra server đang chạy (đổi cổng theo phiên): health, plan/overlay, dedup/hàng đợi, không chặn health trong render, byte ranges/416, preview/export và lỗi đầu vào. Script không sửa settings cá nhân.
- Sau đổi player/API phải kiểm tra giao diện thật: Play hết câu, pause/resume, click scene/tua, phát lại, sửa settings rồi Play lại, không vẽ chữ hai lần, export đúng duration.
- Sau đổi build/runtime phải kiểm tra EXE mới, health API, preview và render qua EXE, rồi mở BAT. Không kết luận build thành công chỉ từ việc PyInstaller không lỗi.

`AutoReelSachHay.spec` dùng đường dẫn tương đối theo SPECPATH. Gói UI, ba font, audio, FFmpeg/FFprobe và DLL cùng thư mục bin; core được phân tích như module Python, không copy mã nguồn và cache như data. Build không gom cả kho assets/thumbnails/clip. `build_exe.py` và `build_onefile.py` cùng tạo bản single-file; giữ EXE v8 trước ở `AutoReelSachHay_v8.previous.exe`, copy bản mới tên `AutoReelSachHay_v8.exe` sang gốc và dist. Các EXE cũ được giữ nguyên; không cưỡng bức kết thúc tiến trình người dùng.

`multiprocessing.freeze_support()` ở entrypoint trước import module ứng dụng. EXE windowed mở log thay stdout/stderr None. Mọi FFmpeg/FFprobe child dùng CREATE_NO_WINDOW; chạy công cụ trong bundle trước PATH. Không dùng `sys.executable` để giả lập Python child trong EXE.

### Chọn nơi sửa

| Nhu cầu | Nơi sửa chính |
| --- | --- |
| Chia câu / thời gian đọc | paginator + planner + unit tests |
| Chọn clip / cắt nguồn / speed | planner; render_plan áp dụng dữ liệu đã tính |
| Footer/font/theme | layout_overlay/render_overlay, bump PLAN_VERSION, ảnh review |
| Play/tua/chuyển cảnh trong UI | app.js; kiểm tra dùng MP4 đã dựng, không thêm overlay client |
| API/streaming | app.py; byte range tests |
| Hàng đợi/progress/cache job | jobs.py |
| Tự lưu/khôi phục bản nháp | settings.py + persistence.py + app.js |
| Tải video/chọn nơi lưu/tên 5 từ | downloads.py + jobs.py + app.js; không dựng lại khi chỉ sao chép |
| Lượt footage/chống bản sao nội dung | footage_pool.py + planner.py + jobs.py; không bỏ khóa/reservation |
| Nhận diện/chất lượng nguồn | video_detector + media.probe |
| Cài đặt cũ/mới | settings.py + settings.example.json |
| EXE/đường dẫn/FFmpeg bundle | app.py bootstrap, media.py, spec/build |
| Backup | quy tắc đầu tài liệu này + .gitignore + README |

### Giới hạn đã biết

- Không có AI ngữ nghĩa để chọn clip theo ý câu, không có TTS; chọn clip theo quy tắc đã chốt.
- Vị trí mặt là gợi ý từ ảnh mẫu; người dùng cần xem toàn reel trước khi xuất.
- Preview lần đầu phải chờ render; CPU/RAM và độ phân giải nguồn ảnh hưởng thời gian.
- Cache chưa tự dọn, job chưa có hủy/tự tiếp tục render sau restart; lượt giữ chỗ của tiến trình đã thoát được trả lại. Chỉ xóa cache khi không có render; session_state và footage_usage là dữ liệu bền vững, không phải cache.
- Kho clip hỏng được bỏ qua trong scan; clip người dùng chọn trực tiếp bị lỗi sẽ báo rõ.
- Nguồn ngoài chọn qua picker được nhớ đường dẫn và đăng ký trong kho lượt; không tự copy file vào dự án. Nếu nguồn bị di chuyển/xóa, cần chọn lại.
- Không có kiểm thử UI tự động ở CI; cần clip thật cho kiểm thử tích hợp. File kết quả kiểm tra thực tế ở VERIFICATION.md.

Chạy thử với dữ liệu riêng: `app.py --headless --workspace <thư mục đã tồn tại> --port N`. Tùy chọn --workspace đổi BASE_DIR ghi dữ liệu; tài nguyên UI/font/FFmpeg vẫn lấy từ bundle. Không trỏ test vào profile người dùng khi thử reset lịch sử hoặc tạo clip giả.


## V8 — Folder nền, chia cảnh theo ý và chống lặp câu trước (2026-10-28)

- `background_video_directory` lưu trong session_state.json, rỗng = kho mặc định. `VideoDetector.scan_all_videos(directory=None)` đọc folder đã nhớ khi None; chuỗi rỗng dùng mặc định. Quét đệ quy MOV/MP4/M4V/MKV; folder tùy chọn bị mất/rỗng/lỗi báo rõ, không fallback. Clip chọn riêng vẫn được bổ sung có chủ đích.
- POST `/api/select_video_directory` mở hộp thoại folder; `{use_default:true}` trở về kho mặc định. Trả cancelled hoặc directory/videos/settings; chỉ ghi nhớ sau khi scan thành công và xóa video_path cũ. GET `/api/videos` quét lại. UI vẫn khởi tạo được khi kho lỗi để chọn folder khác; autosave không gửi lại background_video_directory.
- Payload `/api/plan` thêm `previous_footage_ids` (danh sách SHA256 rút gọn 24 hex), không phải setting tự lưu. UI giữ kế hoạch đã nhận gần nhất để chụp toàn bộ footage khi đổi nội dung; sửa thiết kế không thay ngữ cảnh. Preview không tăng counts hoặc last_export.
- Footage history giữ version 1 và counts cũ, bổ sung last_export={quote,ids} sau xuất thành công. Khi quote khác, kết hợp last_export với ngữ cảnh preview từ UI. Reservation bổ sung active_ids/requested_avoid_ids/quote để kiểm tra cùng quy tắc lúc submit và trước render. Không xóa lịch sử kho cũ khi đổi folder.
- Plan.footage_pool bổ sung active_ids, avoid_ids, requested_avoid_ids, quote, fallback_scenes, repeated_scenes; danh sách cảnh dùng index từ 0. UI báo quay vòng khi không đủ footage mới và đánh dấu từng cảnh liên quan. PLAN_VERSION=`multi-scene-v8-library-clauses-balanced-lines-footage`.
- Batch chụp background_video_directory tại lúc submit (kể cả mặc định), bỏ ngữ cảnh preview của câu đang sửa, lập kế hoạch từng câu theo last_export mới nhất. Đổi folder ở phiên khác không đổi kho của batch đang chạy.
- Bỏ btnRenderSingle và luồng renderSingle; giữ renderSnapshot dùng cho Tải video. btnBatchRender nằm trong header sticky, số câu và modal lấy từ danh sách thực. Âm lượng và tiến độ vẫn ở panel cuối.
- Build tạo AutoReelSachHay_v8.exe; BAT/VBS ưu tiên v8 và chuyển tiếp tham số --workspace/--port để kiểm tra profile riêng. Không đóng phiên cũ.
- `tests/test_v8.py` và `node tests/test_download_ui.js` kiểm tra folder/cancel/restart, chia câu, cân dòng, kho hoạt động, lượt dùng và ngữ cảnh câu trước. `python -X utf8 verify_v8.py --hold` mở EXE qua VBS trên profile riêng, kiểm tra preview/Full HD/batch, decode và đối chiếu màu footage, đổi kho giữa batch, lỗi kho và restart; giữ phiên riêng để kiểm tra UI.
