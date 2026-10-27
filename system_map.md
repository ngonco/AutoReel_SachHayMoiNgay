# System map — Auto Reel Sách Hay Mỗi Ngày

Cập nhật: 2026-10-27. Đọc tài liệu này trước khi nâng cấp hoặc sửa chữa. Repo backup: https://github.com/ngonco/AutoReel_SachHayMoiNgay (nhánh `main`).

## Quy tắc bắt buộc sau mỗi đợt chỉnh sửa

**Sau khi sửa xong: chạy kiểm tra phù hợp → cập nhật tài liệu → commit → push GitHub → xác nhận remote HEAD trùng local HEAD. Luôn backup sau mỗi đợt sửa hoàn tất theo yêu cầu của chủ dự án.**

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
- `Chay_Ung_Dung_Auto_Reel.bat`: chuyển về thư mục script rồi ưu tiên EXE v2, rồi EXE cũ gốc, EXE dist, cuối cùng Python. Không phụ thuộc thư mục người dùng đang đứng.
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
| `settings.json` | Thiết lập cá nhân, lưu tên chuẩn snake_case | Không |
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

- `plan_id`: SHA256 rút gọn 24 hex; `version`, `settings`, `quote`, `duration`, `transition`, `music`, `scenes`.
- Mỗi scene có `index`, `text`, `video_name`, `video_path`, `thumb_url`, `resolved_pos`.
- `start/end`: khoảng nền gồm phần overlap. `text_start/text_end`: khoảng phần chữ độc lập; không chồng hai phần chữ.
- `source_start/source_end`, `speed`: đoạn gốc và tốc độ. `source/source_info`: fingerprint và metadata FFprobe.
- Hash gồm settings, nội dung, phiên bản planner/template, nguồn và nhạc (đường dẫn + size + mtime_ns). Sửa template/quy tắc render cần tăng `PLAN_VERSION` để tránh cache cũ.
- `load_plan()` kiểm tra phiên bản và fingerprint cả lúc nhận API và lúc job chạy. Nguồn đã sửa/xóa sẽ yêu cầu lập lại kế hoạch.

### Chia chữ và thời gian

`core.paginator`: chia theo token whitespace, giữ nguyên chữ, dấu câu và thứ tự sau NFC; quy hoạch động ưu tiên ranh giới dấu câu, tránh tách các cụm từ tiếng Việt phổ biến hoặc để hư từ ở cuối cảnh, và cân đối độ dài. Mục tiêu 12–18 từ, trần 24 từ. Tắt auto_paginate thì giữ toàn bộ câu một cảnh.

Thời gian đọc cơ sở mỗi phần `max(4, số từ/3 + 0.8)` giây, làm tròn lên khung 30 fps. Nếu tổng thấp hơn thời lượng tối thiểu đã chọn, phân bổ phần còn lại theo số từ. Không ép câu dài vào 10–15 giây. Chữ fade 0,2 giây ở hai đầu mỗi phần; đủ thời gian đọc ổn định sau fade.

Nền chồng 12 khung (0,4 giây). Text đổi ở giữa khoảng crossfade; một phần đã tắt trước khi phần sau hiện. Tổng duration là cuối scene cuối, bao gồm tính overlap chính xác.

### Chọn và cắt clip

Cảnh đầu dùng clip đang chọn, nếu bỏ trống dùng clip đầu danh sách. Các cảnh sau dùng clip khác theo thứ tự tên, ưu tiên dọc; hết kho mới lặp. Một clip trong kho vẫn dựng được nhiều cảnh bằng cách dùng lại clip đó.

Đoạn nguồn bắt đầu 0,5 giây, hoặc 1/4 độ dài với nguồn ngắn hơn 2 giây. Lấy tối đa đủ thời gian cảnh; nếu thiếu thì `speed = available / needed`, dùng setpts làm chậm. Không lặp nguồn. FPS cuối luôn 30; có pad rất ngắn để bù làm tròn khung cuối.

`core.video_detector` đo kích thước/thời lượng/rotation thực, tạo thumbnail crop dọc. Dùng Haar cascade rồi heuristic màu để gợi ý nửa trên/dưới; đây là **ước lượng một ảnh mẫu**, không theo dõi mặt toàn clip, không bảo đảm tránh mặt khi tượng/camera di chuyển. Có vị trí thủ công. Cache dùng đường dẫn đầy đủ + mtime_ns + size, có khóa trong phiên và ghi file tạm riêng.

### Template và render

`core.renderer.layout_overlay()` tính trước toàn khối: ornament, quote, separator, credit nhiều dòng và padding. Đáy khối tối đa `int(1920 * .86) = 1651`; vị trí được clamp theo chiều cao thật, không chỉ clamp Y ban đầu. Credit được wrap theo chiều rộng; font dùng bounding box để tính dấu tiếng Việt. Chuỗi không có khoảng trắng được ngắt ký tự để không tràn ngang.

Năm theme: Thiền Vàng, Tinh Khôi, Kinh Điển, Điện Ảnh, Sen Giấy. Font serif `timesbd.ttf`; sans `segoeuib.ttf`; credit `segoeui.ttf`. Tìm trong assets workspace, bundle, rồi Windows Fonts. Thiếu font báo lỗi rõ.

`scene_overlay()` và `render_overlay()` dùng chung cho ảnh tĩnh, preview và Full HD. Preview thu nhỏ ảnh từ chính overlay Full HD. Renderer chuẩn hóa nền từng cảnh, làm chậm/crop/fps, sau đó ghép xfade và overlay theo timeline. Chốt `format=yuv444p,fps=30` trước xfade để tránh lỗi FFmpeg rate `1/0`. MP4 cuối H.264/yuv420p + AAC, faststart. Nhạc nền liên tục có fade đầu/cuối; âm thanh nguồn bị tắt.

`render_reel_video()` là wrapper tương thích cho script cũ và trả `success/error`. Các tham số `music_path` và `video_volume` cũ chưa được ánh xạ vào planner; luồng mới dùng chuông thiền và tắt âm nguồn. Muốn thêm nhạc tùy chọn phải bổ sung fingerprint/API/settings đồng bộ, không chỉ sửa lệnh FFmpeg.

## 4. API và giao diện

HTTP chỉ cục bộ. JSON lỗi `{success:false,error}` với HTTP 400. File tĩnh hỗ trợ byte ranges: 200/206/416, streaming theo chunk để tua và không tải cả MP4 vào RAM.

| Method / URL | Chức năng |
| --- | --- |
| GET `/api/health` | version, pid; kiểm tra khởi động |
| GET `/api/quotes` | danh sách câu |
| GET `/api/videos` | danh sách clip phân tích được |
| GET/POST `/api/settings` | đọc chuẩn hóa / lưu atomically |
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
| POST `/api/open_folder` | mở output_videos |

`core.jobs.JobManager` dùng ThreadPoolExecutor một worker cho mọi job; tránh nhiều FFmpeg lớn cùng lúc. Preview cùng plan đang chờ/chạy được gộp; preview đã có file hợp lệ dùng cache. Job lưu RAM, không tự tiếp tục sau restart. Batch báo files/failures theo từng câu, không trả thành công giả khi một phần thất bại.

`ui/app.js`: gọi plan sau thay đổi với debounce, dùng revision để bỏ kết quả đến muộn. Không tính timeline hay tự vẽ template nữa. Ảnh tĩnh: thumbnail + overlay máy chủ. Play: tạo/poll preview job rồi bật video controls và tắt canvas. Các chức năng pause/resume/seek/ended dựa trên video thật. Sửa nội dung/clip/settings làm plan/preview/export URL hiện tại hết hiệu lực. Kết quả job cũ vẫn có thể còn trong cache, nhưng không phát nhầm lên thiết lập mới.

`core.settings.normalize_settings()` là nơi duy nhất chuyển camelCase cũ sang snake_case, chuẩn hóa shade/volume 0..1 từ giá trị phần trăm cũ và giới hạn giá trị. UI lưu snake_case. File mẫu dùng snake_case. Không lặp mapping ở renderer/UI.

## 5. Kiểm tra, build và sửa lỗi

```powershell
python -X utf8 -m unittest discover -s tests -v
python -X utf8 verify_samples.py
python -X utf8 build_onefile.py
```

- Unit: đủ chữ/dấu, trần số từ, timeline/overlap, migration settings, bố cục footer 5 theme × 3 vị trí × 2 offset, clip ngắn, kho trống/một clip, vòng chọn clip và plan lỗi thời.
- `verify_samples.py`: 3 quote (1/2/3 cảnh) × 2 độ phân giải; probe kích thước/duration, decode toàn video, ảnh tại từng cảnh/transition/cuối và bảng stress credit dài.
- `verify_api.py --base http://127.0.0.1:8767` kiểm tra server đang chạy (đổi cổng theo phiên): health, plan/overlay, dedup/hàng đợi, không chặn health trong render, byte ranges/416, preview/export và lỗi đầu vào. Script không sửa settings cá nhân.
- Sau đổi player/API phải kiểm tra giao diện thật: Play hết câu, pause/resume, click scene/tua, phát lại, sửa settings rồi Play lại, không vẽ chữ hai lần, export đúng duration.
- Sau đổi build/runtime phải kiểm tra EXE mới, health API, preview và render qua EXE, rồi mở BAT. Không kết luận build thành công chỉ từ việc PyInstaller không lỗi.

`AutoReelSachHay.spec` dùng đường dẫn tương đối theo SPECPATH. Gói UI, ba font, audio, FFmpeg/FFprobe và DLL cùng thư mục bin; core được phân tích như module Python, không copy mã nguồn và cache như data. Build không gom cả kho assets/thumbnails/clip. `build_exe.py` và `build_onefile.py` cùng tạo bản single-file; giữ EXE v2 trước ở `AutoReelSachHay_v2.previous.exe`, copy bản mới tên `AutoReelSachHay_v2.exe` sang gốc và dist. Bản `AutoReelSachHay.exe` cũ không bị thay khi còn phiên đang chạy; không cưỡng bức kết thúc tiến trình người dùng.

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
| Nhận diện/chất lượng nguồn | video_detector + media.probe |
| Cài đặt cũ/mới | settings.py + settings.example.json |
| EXE/đường dẫn/FFmpeg bundle | app.py bootstrap, media.py, spec/build |
| Backup | quy tắc đầu tài liệu này + .gitignore + README |

### Giới hạn đã biết

- Không có AI ngữ nghĩa để chọn clip theo ý câu, không có TTS; chọn clip theo quy tắc đã chốt.
- Vị trí mặt là gợi ý từ ảnh mẫu; người dùng cần xem toàn reel trước khi xuất.
- Preview lần đầu phải chờ render; CPU/RAM và độ phân giải nguồn ảnh hưởng thời gian.
- Cache chưa tự dọn, job chưa có hủy/tự phục hồi; xóa cache chỉ khi không có render đang chạy.
- Kho clip hỏng được bỏ qua trong scan; clip người dùng chọn trực tiếp bị lỗi sẽ báo rõ.
- Nguồn ngoài chọn qua picker dùng được trong phiên, chưa được tự copy vào kho hoặc nhớ lại sau restart.
- Không có kiểm thử UI tự động ở CI; cần clip thật cho kiểm thử tích hợp. File kết quả kiểm tra thực tế ở VERIFICATION.md.
