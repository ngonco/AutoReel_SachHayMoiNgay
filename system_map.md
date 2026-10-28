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
  → UI: nhập câu + gợi ý footage từng cảnh + nhạc offline + settings
  → core.planner: kế hoạch cảnh duy nhất
      → core.paginator: chia chữ + thời gian đọc
      → core.video_detector: kho clip + thumbnail + ước lượng vị trí
      → core.media: thông tin nguồn thực qua FFprobe
  → core.jobs: hàng đợi một worker
      → core.renderer: nền cắt/làm chậm → crossfade → overlay Pillow → nhạc
      → bản nhẹ 360×640 hoặc Full HD 1080×1920
  → nháp trực tiếp: hai proxy footage + PNG chữ dùng chung renderer; Full HD/preview API cũ phát MP4 đã ghép
```

- `app.py`: `main()`, `--headless`, `--port N`, `--batch`; HTTP API, byte ranges, logging và native file picker.
- `Chay_Ung_Dung_Auto_Reel.bat`: chuyển về thư mục script rồi ưu tiên EXE v11, rồi v10/v9/v8/v7/v6/v5/v4/v3/v2, EXE cũ gốc, EXE dist, cuối cùng Python. Không phụ thuộc thư mục người dùng đang đứng.
- `Mo_App_Auto_Reel.vbs`: launcher tương tự, định vị theo chính file VBS.
- `render_all_reels.py`: batch dùng cùng settings/planner/renderer, mặc định không shutdown.
- `test_and_review.py`: script mẫu cũ vẫn gọi wrapper renderer; kiểm chứng mới dùng `verify_samples.py`.

Chạy phát triển: `python -X utf8 app.py`. Chạy API thử: `python -X utf8 app.py --headless --port 8877`. Dùng thư mục dữ liệu có quyền ghi. Có thể mở nhiều bản trên cổng khác nhau; ứng dụng chưa có khóa một phiên duy nhất.

## 2. Thư mục và dữ liệu

| Vị trí | Vai trò | Git backup |
| --- | --- | --- |
| `core/` | Planner, layout, renderer, settings, jobs, media, đọc câu | Có |
| `ui/` | HTML/CSS/JS; không tự chia chữ hoặc tính lại timeline | Có |
| `assets/thien_chuong.wav` | Asset lịch sử được giữ trên đĩa; v11 không dùng/không bundle | Có |
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

V9 dùng `core.quote_sync.QuoteSyncService` làm catalog cho UI và batch; lấy toàn bộ cột A tab “Đạo lý hay mỗi ngày” từ Sheet công khai khi mở app và mỗi 1.800 giây. PMDX/TXT là nguồn dự phòng khi chưa từng đồng bộ hoặc dùng --no-sheet-sync.

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

`soft_outline(mask, style)` lấy mask glyph, crop vùng có chữ với padding, giãn mask bằng MaxFilter, làm nhòe Gaussian, trừ vùng mực gốc rồi áp màu/opacity. `paint_outlined_text()` composite viền và nét chữ sắc sau cùng. Không blur trực tiếp phần chữ. Tắt viền, opacity 0 hoặc width=blur=0 trả đúng phần chữ không viền. Credit có độ dày/nhòe giảm theo tỷ lệ cỡ chữ để không bết chữ nhỏ. UI có bật/tắt, tự chọn màu, color picker và ba thanh trượt; mọi chỉnh sửa invalidate plan/preview và được lưu cùng settings. Các field outline tự đi vào hash kế hoạch; PLAN_VERSION v9 bao gồm quy tắc căn baseline và preview nhanh mới để không dùng overlay cache cũ.

`scene_overlay()` và `render_overlay()` dùng chung cho ảnh tĩnh, preview và Full HD. Preview thu nhỏ ảnh từ chính overlay Full HD. Renderer chuẩn hóa nền từng cảnh, làm chậm/crop/fps, sau đó ghép xfade và overlay theo timeline. Chốt `format=yuv444p,fps=30` trước xfade để tránh lỗi FFmpeg rate `1/0`. MP4 cuối H.264/yuv420p + AAC, faststart. Nhạc nền liên tục có fade đầu/cuối; âm thanh nguồn bị tắt.

`render_reel_video()` là wrapper tương thích cho script cũ và trả `success/error`. Các tham số `music_path` và `video_volume` cũ chưa được ánh xạ vào planner; V10 chọn nhạc qua music_mode/music_path/music_seed và fingerprint trong plan; luôn tắt âm footage. Tham số music_path của wrapper cũ vẫn chưa được chuyển sang chế độ selected; gọi planner/API mới để chọn bài cụ thể.

## 4. API và giao diện

HTTP chỉ cục bộ. JSON lỗi `{success:false,error}` với HTTP 400. File tĩnh hỗ trợ byte ranges: 200/206/416, streaming theo chunk để tua và không tải cả MP4 vào RAM.

| Method / URL | Chức năng |
| --- | --- |
| GET `/api/health` | version, pid; kiểm tra khởi động |
| GET `/api/quotes` | danh sách câu từ catalog hiện tại, giữ API mảng cũ |
| GET `/api/quote_catalog` | snapshot quotes + sync metadata nhất quán |
| GET/POST `/api/quote_sync` | đọc trạng thái / yêu cầu kiểm tra Sheet nền ngay, POST trả 202 |
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

V9 `core.jobs.JobManager` dùng một worker cho export/batch/save và một worker riêng cho preview; thêm khóa export liên tiến trình và giữ chỗ footage. Preview cùng plan đang chờ/chạy được gộp; preview đã có file hợp lệ dùng cache. Job lưu RAM, không tự tiếp tục sau restart. Batch báo files/failures theo từng câu, không trả thành công giả khi một phần thất bại.

`ui/app.js`: gọi plan sau thay đổi với debounce, dùng revision để bỏ kết quả đến muộn. Không tính timeline hay tự vẽ template nữa. Ảnh tĩnh: thumbnail + overlay máy chủ. Sau kế hoạch ổn định 900 ms, UI chuẩn bị preview ở nền và preload MP4, không tự phát. Play dùng lại file hoặc Promise đang chuẩn bị, rồi bật video controls và tắt canvas. Các chức năng pause/resume/seek/ended dựa trên video thật. Sửa nội dung/clip/settings làm plan/preview/export URL hiện tại hết hiệu lực. Kết quả job cũ vẫn có thể còn trong cache, nhưng không phát nhầm lên thiết lập mới.

Tự lưu v5: `core.settings.load_settings()` đọc `session_state.json`; nếu chưa có mới nhập từ settings.json cũ. Bản v5 ghi file riêng để các EXE cũ còn mở không thể ghi đè bản nháp mới. `save_settings_patch()` nhận patch từng field, không reset field bị bỏ qua; `_client_id` + `_sequence` ngăn request cũ ghi đè request mới cùng trang. File ghi qua temp riêng + fsync + replace, có khóa liên phiên trong `core.persistence`.

Frontend giữ nguyên quote (kể cả dòng trống/trailing Enter), quote_index, video_path, safe_zone và mọi control nội dung/thiết kế/âm lượng. UI báo Đang lưu/Đã lưu tự động/lỗi và tự thử lại; hàng đợi save gửi tuần tự, debounce 250ms, pagehide gửi beacon/keepalive. V10 khởi động vào câu chưa tải đầu tiên và giữ bản soạn cũ trong draft_recovery.json để mở lại; render không thay quote trong bản tự lưu. Safe zone chỉ là trạng thái xem, không vẽ vào MP4. Các field nháp được loại khỏi settings của plan để không tạo cache render vì thay đổi chế độ xem.

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

`AutoReelSachHay.spec` dùng đường dẫn tương đối theo SPECPATH. Gói UI, ba font, audio, FFmpeg/FFprobe và DLL cùng thư mục bin; core được phân tích như module Python, không copy mã nguồn và cache như data. Build không gom cả kho assets/thumbnails/clip. `build_exe.py` và `build_onefile.py` cùng tạo bản single-file; giữ EXE v11 trước ở `AutoReelSachHay_v11.previous.exe`, copy bản mới tên `AutoReelSachHay_v11.exe` sang gốc và dist. Các EXE cũ được giữ nguyên; không cưỡng bức kết thúc tiến trình người dùng.

`multiprocessing.freeze_support()` ở entrypoint trước import module ứng dụng. EXE windowed mở log thay stdout/stderr None. Mọi FFmpeg/FFprobe child dùng CREATE_NO_WINDOW; chạy công cụ trong bundle trước PATH. Không dùng `sys.executable` để giả lập Python child trong EXE.

### Chọn nơi sửa

| Nhu cầu | Nơi sửa chính |
| --- | --- |
| Chia câu / thời gian đọc | paginator + planner + unit tests |
| Chọn clip / cắt nguồn / speed | planner; render_plan áp dụng dữ liệu đã tính |
| Footer/font/theme | layout_overlay/render_overlay, bump PLAN_VERSION, ảnh review |
| Play/tua/chuyển cảnh trong UI | draft_player.js + app.js; nháp dùng proxy + PNG renderer; MP4 Full HD phải ẩn canvas |
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
- V10 không dựng cả Reel khi xem nháp. Footage mới cần chuẩn bị proxy một lần; CPU/RAM/đĩa và độ phân giải nguồn ảnh hưởng thời gian. Nháp trực tiếp có thể khác nhẹ chuyển cảnh/màu so với Full HD.
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


## V9 — Tự cập nhật câu nói từ Google Sheet, chỉ đọc (2026-10-28)

- Nguồn cố định: https://docs.google.com/spreadsheets/d/1Ku40G9gH89W7eRpN6u6NAYnxj2hGf8Gv-QL_34a2teI/edit, tab `Đạo lý hay mỗi ngày`, cột A. Lấy mọi dòng không trống, bao gồm dòng có done ở cột B; giữ thứ tự, câu trùng và xuống dòng trong ô. Đồng bộ thay toàn bộ snapshot để phản ánh thêm/sửa/xóa; không ghi lên Sheet.
- `core/quote_sync.py` dùng urllib GET endpoint gviz/tq với out:csv, sheet theo tên, range A:A và headers=0; không cookie jar/OAuth/API key/quyền Google. Timeout 20 giây, giới hạn 2 MiB/10.000 câu/20.000 ký tự mỗi câu; từ chối HTML/login/CSV lỗi và giữ danh sách tốt gần nhất. Sheet phải tiếp tục cho phép đọc công khai bằng liên kết.
- Worker daemon riêng bắt đầu ngay sau khi HTTP server sẵn sàng, sau mỗi lần thử đợi 1.800 giây (kể cả lỗi). Không dùng render worker hoặc timer trình duyệt để gọi Google. Nút Cập nhật ngay đánh thức cùng worker; gộp yêu cầu khi đang chạy. Không có Codex automation ngoài app và không tự xuất Reel khi có bài mới.
- Cache dữ liệu cá nhân nằm ở `.cache/quotes/google_sheet.json` (version/source/timestamp/quotes), tự loại khỏi Git; đọc cache trước khi kết nối, ghi atomic có khóa riêng. Không sửa PMDX, TXT, session_state.json hoặc footage_usage.json khi đồng bộ. Không có cache thì dùng nguồn cục bộ tạm thời. Snapshot Sheet rỗng hợp lệ xóa danh sách, vẫn giữ bản nháp và cho xuất câu nhập tay.
- GET `/api/quotes` vẫn trả mảng {id,key,quote,credit}. `key` theo hash nội dung + thứ tự bản trùng, giữ lựa chọn khi reorder. GET `/api/quote_catalog` trả {quotes,sync}; GET `/api/quote_sync` trả enabled/syncing/source/count/revision/sheet_name/sheet_url/interval_seconds/last_checked_at/last_success_at/next_check_at/error; timestamp là Unix giây. POST `/api/quote_sync` yêu cầu kiểm tra, trả trạng thái HTTP 202.
- UI hỏi trạng thái local mỗi 15 giây, chỉ lấy catalog khi revision đổi. Cập nhật danh sách/nhãn/số câu trong nền, không gọi loadQuote/invalidate/autosave: giữ nguyên textarea (kể cả dòng trống/trailing Enter), preview plan, export và ngữ cảnh footage. Khi câu đang chọn bị sửa/xóa, hiện Bản nháp hiện tại; người dùng chủ động chọn lại câu mới. Có thông báo cập nhật/lỗi/lần thành công gần nhất và link mở Sheet.
- Batch chụp bản sao catalog ở lúc submit; thay đổi Sheet trong lúc chạy không đổi items. Job thêm total, kết quả thêm total_requested; UI dùng tổng đã chụp để không báo sai khi danh sách đổi. Danh sách rỗng vô hiệu hóa xuất nhiều Reel. CLI --batch kiểm tra Sheet một lần trước khi chụp danh sách.
- `--no-sheet-sync` dành cho profile thử/luồng cục bộ: không mạng và không lấy cache Sheet, vẫn đọc PMDX/TXT/default. Bài kiểm tra cũ về kho riêng cần dùng cờ này khi chạy EXE mới.
- Đợt v9 có thêm sửa giãn dòng và tối ưu preview theo yêu cầu tiếp theo; PLAN_VERSION tăng thành `multi-scene-v9-sheet-sync-baselines-fast-preview-template-4`. Build và launcher dùng v9, giữ v8 và mọi phiên cũ. `tests/test_quote_sync.py`, `node tests/test_quote_sync_ui.js` kiểm tra parser, lỗi/cache, chu kỳ 1.800 giây bằng thời gian giả lập, cập nhật list và batch snapshot. `verify_v9.py --hold` kiểm tra Sheet thật qua EXE/launcher trên profile riêng; không sửa dữ liệu trên Sheet.


### Bổ sung v9 — Giãn dòng đều và preview nhanh

- Lỗi cũ: `anchor=lt` căn mép mực từng dòng khiến vị trí thân chữ đổi theo dấu cao/thấp. Layout mới đo toàn khối bằng `anchor=ls`, tính quote_baseline/credit_baseline chung và tăng Y cố định qline/cline. Dấu tiếng Việt vẫn nằm trong chiều cao khối và vùng an toàn; separator vẫn căn theo credit_y. `paint_outlined_text` nhận anchor tùy chọn, quote và credit dùng ls; các caller cũ vẫn mặc định lt.
- Preview mặc định 360×640, 30 fps, x264 ultrafast CRF 26/AAC 96k; Full HD giữ 1080×1920, veryfast CRF 19/AAC 192k. Cùng `render_plan`, plan, scene_overlay, crop/speed/timeline/xfade/fade/music. Với tối đa 4 cảnh preview đọc trực tiếp đoạn nguồn bằng input seek chính xác và ghép/mã hóa một lượt, bỏ các MP4 nền trung gian. Trên 4 cảnh vẫn chuẩn hóa nền tuần tự ở 360p để giới hạn số decoder nguồn lớn. Preview giảm độ nét để xem nhanh; xuất Full HD giữ chất lượng cũ.
- Preview có worker riêng nên không đứng sau export/batch. Preview hoàn tất trong cache trả job done ngay sau kiểm tra plan, không qua hàng đợi; có khóa cache liên phiên chống hai app ghi chung partial. Preview_client_id từ UI cho phép bỏ future preview cũ còn queued của cùng trang; job cũ trả error/code preview_superseded, không hủy export hoặc preview đã chạy.
- UI debounce plan 350 ms, sau đó chờ ổn định 900 ms để chuẩn bị preview. Dùng chung Promise giữa warm-up và click Play; preload file, không tự phát/không đổi cảnh đang chọn; kết quả revision cũ không được đưa lên player. Poll preview 250 ms; đã sẵn sàng thì Play không gọi dựng lại. Thay nội dung/clip/settings xóa trạng thái và timer preview; đổi danh sách Sheet giữ nguyên preview của bản nháp. JobManager.close đóng cả hai executor.
- Kiểm tra mới: `tests/test_line_spacing.py`, `tests/test_fast_preview.py`, `node tests/test_fast_preview_ui.js`. `verify_v9.py --hold --real-source <clip>` kiểm tra thêm câu trong ảnh mẫu qua overlay/preview/Full HD của EXE và độ trễ lấy cache; clip thật chỉ đọc, mọi dữ liệu/lượt dùng nằm trong profile thử.

Các helper verify_v5/verify_v8/verify_v9 lưu lại quy trình của phiên bản lịch sử; kiểm tra launcher và API mới bằng verify_v10.py. Profile thử mới có thể dùng --no-sheet-sync để tránh thay danh sách TXT bằng Sheet thật.


## V10 — Chọn footage theo cảnh, nháp trực tiếp, lịch sử tải và nhạc offline

- PLAN_VERSION=`multi-scene-v10-instant-draft-offline-music-downloads-2`; EXE/launcher ưu tiên v10, giữ mọi phiên cũ. `verify_v10.py --hold --fullhd` dùng profile riêng, `--source` dành cho chạy nguồn. Các helper v5/v8/v9 giữ để tái hiện bản lịch sử.
- `scene_video_preferences` là map index cảnh → {path,text}, tự lưu cùng `imported_video_paths`. Planner chỉ dùng gợi ý khớp text của cảnh, trong nguồn đang hoạt động/clip thêm riêng; duplicate nội dung vẫn một footage. Gợi ý được xét sau `_candidates` chống lặp/ít lượt dùng; trả `scene_choices` (eligible/effective_count/reason) và `scene_suggestions`, mỗi scene có `suggestion`. Reservation/check_sequence vẫn kiểm chứng cùng tập ứng viên; batch bỏ gợi ý và imports riêng.
- Kịch bản, tìm/lọc, thumbnail và gợi ý footage nằm cùng panel; lựa chọn áp dụng cảnh đang chọn và tự phát cảnh đó. Đổi clip/thiết kế giữ cảnh và vị trí cuộn; thay nội dung hoặc auto_paginate xóa gợi ý. UI chống kết quả revision cũ khi đổi liên tục. `probe` dùng LRU theo path/size/mtime_ns.
- `core.draft_media.DraftMediaService` có một daemon worker: ưu tiên cảnh chọn, cảnh còn lại, rồi kho đang hoạt động; đổi folder bỏ queue cũ, không xóa nguồn/cache. Không nhận việc chuyển đổi mới khi có export/batch/save trong JobManager; một chuyển đổi đã chạy được hoàn tất. Cache `.cache/draft_media/{sha256-32}.mp4` theo fingerprint + proxy version, không phụ thuộc chữ/nhạc; H264/yuv420p 360×640/30fps/GOP15, không âm thanh, faststart. Có khóa liên phiên, partial riêng, kiểm tra nguồn trước khi publish, trạng thái lỗi và retry rõ; không đụng lượt footage.
- POST `/api/draft_prepare` {plan_id,selected_scene} → scenes [{index,key,status,url/error}], library; GET `/api/draft_status/{plan_id}` cùng snapshot. GET `/api/draft_media/{key}.mp4` chỉ cho key đã xác thực từ kho/plan và nguồn không đổi, dùng byte ranges; không nhận đường dẫn tùy ý.
- `ui/draft_player.js` dùng hai video decoder gắn trong DOM và canvas; điều khiển từ plan.start/end/text_start/text_end/source_start/source_end/speed/transition. PlaybackRate có fallback seek khung; pause/buffer đóng băng đồng hồ chung và nhạc. Fade nền/chữ theo plan, preload kế tiếp, hai lớp chỉ dùng cho nháp trực tiếp. PNG vẫn do `scene_overlay`/`render_overlay` Full HD tạo, không layout chữ ở JavaScript. Overlay cache theo text/resolved_pos/các thiết lập thiết kế/version, không theo clip/nhạc/duration; UI dùng overlay_key để dùng lại ảnh. Nguồn decode được giữ khi chỉ đổi thiết kế. API `/api/preview` và renderer MP4 nhẹ v9 vẫn giữ cho tương thích, UI không còn gọi để warm-up/Play. Xem lại MP4 Full HD ẩn canvas để tránh chồng chữ hai lần.
- `core.quote_downloads.QuoteDownloadHistory` lưu `quote_download_history.json` version1, revision và map SHA256 của NFC + gộp whitespace; record quote/count/first_downloaded_at/last_downloaded_at/last_path/last_job_id. Khóa + ghi atomic, không tự reset file lỗi. Chỉ JobManager._save_work sau copy thành công ghi lịch sử, không ghi từ render/batch/preview; dùng quote snapshot của render job. Ghi lịch sử lỗi vẫn trả saved_path thành công với history_warning. Không nhập đoán lịch sử video trước v10.
- GET `/api/download_history` trả revision/records đã bỏ đường dẫn và job nội bộ. GET `/api/quote_catalog` bổ sung downloaded/last_downloaded_at từng quote và download_history; `/api/quote_sync` thêm download_revision để các cửa sổ cập nhật trạng thái. POST `/api/startup_quote` chọn index chưa tải đầu tiên, all_downloaded và recovery_available; giữ nguyên settings cũ trong `draft_recovery.json` trước khi UI chuyển câu. GET `/api/previous_draft` phục hồi bản soạn. Khi mọi câu đã tải: chọn index0 và báo rõ; rỗng: giữ bản nháp. Bản Sheet mới chỉ được chọn tự động trong bước khởi động nếu người dùng chưa tương tác, sau đó luôn giữ bản đang soạn.
- Nhạc offline ở `<background_video_directory>/NHẠC NỀN`, mặc định `CLIP TƯỢNG PHẬT LQ/NHẠC NỀN`. `music_mode=random|selected|bell|none`, music_path/music_seed tự lưu; previous_music_path chỉ là ngữ cảnh request, không autosave. Random theo quote+seed và tập nhạc, loại bài trước khi còn lựa chọn; UI đổi seed khi đổi câu/đổi ngẫu nhiên, thay thiết kế/footage giữ seed. Batch mang previous_music_path qua mỗi Reel thành công. Plan.music giữ fingerprint, thêm music_details và music_url; Full HD dùng cùng nhạc, source fingerprint kiểm tra khi chạy.
- GET `/api/music` trả directory/tracks (id/path/name/url/metadata)/download; POST `/api/download_music` bắt đầu/bổ sung tải nền; POST `/api/open_music_folder` mở folder. GET `/api/music_file/{id}` chỉ phục vụ bài trong kho hiện tại; GET `/api/plan_music/{plan_id}` phục vụ đúng fingerprint nhạc của plan; cả hai hỗ trợ ranges. Nháp dùng audio riêng đồng bộ với timeline, Full HD vẫn dùng stream_loop và fade 0,6s/1,2s. Thiếu kho random có thông báo fallback chuông; selected bị mất báo lỗi.
- `core.music_library` chỉ GET repo Hugging Face công khai `vinhn8n/voicedaoly`, folder `music background`; pin revision khi lấy manifest, 3 worker tải, SHA256 LFS + size + FFprobe audio trước atomic rename. File local cùng tên khác nội dung được giữ và bài tải có hậu tố hash; retry không tải lại file đúng. Tải đủ 175 bài ~430,8 MB từ revision `615a4b33c804a4a8a85aa7791ea3613d4749ad7a` trong đợt v10. Nhạc nằm cùng kho media được ignore, không đóng vào EXE và không đưa lên GitHub. Sau tải, phát nháp/xuất không cần mạng; chuyển folder footage không tự sao chép nhạc, dùng Tải/bổ sung tại folder mới khi cần.
- Dữ liệu cần giữ qua nâng cấp: session_state.json, footage_usage.json, quote_download_history.json, draft_recovery.json và kho nhạc/video cá nhân. Tests mới: test_v10, test_quote_downloads, test_music_library và node test_draft_player; kiểm tra UI/API qua EXE riêng trước bàn giao.


## V11 — Đánh dấu đã tải thủ công, sửa tiếng nháp và bỏ chuông thiền

- PLAN_VERSION=`multi-scene-v11-audible-preview-manual-download-status-no-bell-1`; build/launcher ưu tiên AutoReelSachHay_v11.exe, giữ các phiên cũ. Kiểm tra bản hiện hành bằng `verify_v11.py --hold --fullhd`, có `--source` cho profile thử từ mã nguồn.
- POST `/api/mark_quote_downloaded` nhận {quote,downloaded:true|false}, kiểm tra string không rỗng/tối đa 20.000 ký tự và boolean; trả catalog+download_history+sync+success. Dùng đúng snapshot câu lúc bấm, không đổi bản nháp/plan/cảnh hiện tại. UI có nút đánh dấu/bỏ đánh dấu ngay cạnh trạng thái, khóa khi request đang chạy; lỗi ghi được báo rõ, không giả thành công.
- Lịch sử vẫn version1, thêm optional is_downloaded/status_source/status_at. Record v10 không có flag được hiểu là true. Mark/unmark giữ count, thời điểm/file tải thực tế; manual mới có count=0 và last_downloaded_at=null, UI ghi “Đã đánh dấu thủ công”. Mark lặp cùng trạng thái là idempotent; unmark không xóa audit. Tải file thành công mới tăng count và đặt lại is_downloaded=true/status_source=download. Annotate/startup/UI chỉ coi record có is_downloaded khác false là đã tải. Mark không chạm session_state/footage_usage và không dùng renderer/job/reservation.
- Lỗi v10: mọi rejection của audio.play đều đặt audioBlocked, kể cả AbortError do pause/load lúc buffering; âm thanh sau đó không tự thử lại. V11 requestAudio theo epoch+generation, phân biệt AbortError (retry) và NotAllowedError (hiện nút bật tiếng), bỏ kết quả Promise cũ khi pause/đổi plan. Không phát audio trước khi frame/nhạc sẵn sàng; buffering giữ đồng hồ và tự thử khi sẵn sàng.
- unlockAudio không còn đặt volume=0 rồi để Promise đua với pause. Tạo/resume AudioContext trong click, nối MediaElementSource → Gain → Analyser → destination; HTMLAudio luôn unmuted/volume1 ở chế độ graph, Gain nhận music_volume × fade. Không có AudioContext thì dùng volume HTMLAudio trực tiếp. Nhạc đúng music_url/fingerprint từ plan, không đổi layout/timeline/crop; âm footage vẫn mute. `previewAudioStatus`, `previewAudioLevel` hiển thị trạng thái/âm lượng và mức tín hiệu sau gain. Chỉ khi bị chặn thật mới hiện `btnEnablePreviewAudio`; zero-volume/none không bị tự nâng âm lượng.
- Bỏ bell khỏi enum settings; giá trị cũ bell được normalize sang random. Kho random rỗng trả music=null cùng lý do chưa có nhạc; không fallback chuông. Bỏ lựa chọn chuông, nút nghe chuông, route /assets/thien_chuong.wav và data asset trong spec. File chuông lịch sử trên đĩa và EXE v10/cũ được giữ nguyên, không được v11 phát hoặc ghép. Nhạc offline người dùng không thay đổi.
- Regression: Python manual mark/unmark/idempotency/restart/audit/invalid input; music legacy migration/empty no-bell; Node play-abort buffering → tự có tiếng lại, autoplay denial → enable, stale play rejection, manual status cập nhật khi đang sửa câu và lỗi ghi. Test trên profile --workspace riêng; dùng tín hiệu PCM/RMS của nguồn và Full HD, cùng RMS Analyser từ UI thật, không chỉ kiểm tra paused=false.
