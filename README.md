# Auto Reel Sách Hay Mỗi Ngày

Ứng dụng Windows dựng reel dọc với câu nói tiếng Việt, video tượng Phật, sáu template và kho nhạc nền offline.

- Câu dài tự chia thành nhiều cảnh, giữ đủ nội dung và dấu câu.
- Công tắc **CHỮ CUỘN** ở đầu giao diện, mặc định bật, khung mặc định 5 dòng, chỉnh được cỡ chữ, 2–8 dòng, viền chữ và hai mép mờ; footage chuyển độc lập khoảng 7 giây/clip.
- Mỗi cảnh dùng một clip khác; clip ngắn được làm chậm vừa đủ.
- Nháp tức thì phát footage nhẹ và lớp chữ từ renderer, không dựng MP4 toàn Reel sau mỗi lần sửa.
- Xuất Full HD 1080×1920 từ chính kế hoạch đã xem trước.
- Tổng thời lượng tự tăng để đủ đọc, tối thiểu theo nút 10/12/15 giây đã chọn.

## Chạy

Bản đã đóng gói: mở `Chay_Ung_Dung_Auto_Reel.bat` hoặc `AutoReelSachHay_v13.exe` trong thư mục có dữ liệu. File EXE đi kèm FFmpeg, FFprobe và font bên trong. Nhạc nằm trong kho offline riêng. Có thể chọn folder clip ở vị trí khác; ứng dụng tự nhớ.

Chạy từ mã nguồn trên Windows, Python 3.11:

```powershell
python -m pip install -r requirements.txt
python -X utf8 app.py
```

Cần FFmpeg và FFprobe trên PATH khi chạy từ nguồn. Đặt clip trong `CLIP TƯỢNG PHẬT LQ/DỌC` hoặc `CLIP TƯỢNG PHẬT LQ/NGANG`, hoặc chọn **Folder video nền** (bao gồm thư mục con), hoặc bấm **Chọn video khác** để dùng file cục bộ.

Font dùng Times New Roman Bold và Segoe UI có sẵn trong `C:/Windows/Fonts`. Có thể đặt bản font được phép sử dụng trong `assets/fonts`. Repo không chứa các font Microsoft này. Nội dung câu nói tự đồng bộ từ Google Sheet công khai; PMDX/TXT hoặc 16 câu có sẵn là nguồn dự phòng khi chưa có bản đồng bộ.

## Sử dụng

1. Chọn style ngay đầu giao diện, phía trên mục nhập câu nói. **CHỮ CUỘN** là công tắc đầu tiên, bật sẵn khi mở bản nâng cấp lần đầu. App nhớ lựa chọn bật/tắt sau đó; tắt trở về style chữ tĩnh trước đó hoặc chọn một trong năm nút style bên dưới. Với mẫu 01–05, Enter chia mỗi dòng thành một cảnh riêng; với CHỮ CUỘN, Enter giữ ngắt dòng/đoạn trong cùng dải chữ cuộn.
2. Trong **Kịch bản Reel & Video tượng Phật nền**, bấm cảnh rồi chọn footage ngay bên dưới. Tìm theo tên hoặc lọc clip phù hợp; clip gợi ý vẫn tuân thủ chống lặp và ưu tiên ít lượt dùng.
3. Đổi footage tự phát cảnh vừa đổi. Bấm **Phát toàn Reel** để xem liên tục; có thể dừng, tua và phát lại. Clip mới cần chuẩn bị bản nhẹ một lần, dùng lại sau restart.
4. Bấm **Tải video**, chọn nơi lưu và tên file. Ứng dụng tự xuất Full HD nếu cần; nếu đã xuất đúng thiết lập trong phiên này thì lưu ngay. Nút **Xuất nhiều Reel** trên thanh đầu xuất toàn bộ danh sách câu; nút Xuất Reel riêng đã bỏ.

Thay đổi thiết lập sẽ làm bản xem trước cũ hết hiệu lực. Cỡ chữ và credit được giới hạn trong vùng an toàn; nếu chủ thể di chuyển, hãy xem lại vị trí chữ trước khi xuất.

## Kiểm tra và build

```powershell
python -X utf8 -m unittest discover -s tests -v
python -X utf8 verify_samples.py
python -X utf8 build_onefile.py
```

`verify_samples.py` cần kho clip thật và xuất ba mẫu (một, hai, ba cảnh) ở cả bản nhẹ và Full HD. Kết quả ở `output_videos/verification`; ảnh kiểm tra và báo cáo ở `test_renders/verification`.

Build đọc `AutoReelSachHay.spec`, gom FFmpeg/FFprobe và DLL cạnh chúng cùng bốn font cần thiết; ghi EXE mới vào thư mục gốc và `dist/AutoReelSachHay`. EXE v13 trước đó được giữ ở `AutoReelSachHay_v13.previous.exe`; giữ nguyên EXE/phiên cũ.

Kiểm tra bản hiện hành qua launcher bằng `python -X utf8 verify_v13.py --fullhd --hold`. Script tạo profile riêng, không sử dụng lịch sử footage hoặc thiết lập thật.

Bắt buộc sau mỗi đợt sửa code, kể cả giao diện: đóng gói lại EXE từ code cuối cùng, mở qua launcher và kiểm tra chức năng vừa sửa trên bản đóng gói trước khi bàn giao. Không giao EXE cũ sau khi chỉ kiểm tra mã nguồn. Chỉ sửa tài liệu thì không cần build lại.

Xem [system_map.md](system_map.md) trước khi nâng cấp hoặc sửa lỗi. Đọc [VERIFICATION.md](VERIFICATION.md) để xem kết quả kiểm tra đợt nâng cấp.

## Backup

Repo nguồn: https://github.com/ngonco/AutoReel_SachHayMoiNgay

Sau mỗi đợt sửa hoàn tất: cập nhật tài liệu, chạy kiểm tra liên quan, commit và push; xác nhận commit trên GitHub trùng commit cục bộ. Không force-push. Clip, file xuất, cache, font Microsoft, EXE và cài đặt cá nhân được giữ cục bộ theo `.gitignore`; phục hồi đầy đủ cần sao lưu riêng các dữ liệu này.

Điều chỉnh Y: kéo thanh trượt hoặc nhập số từ −1600 đến +1600 px. Toàn bộ chữ và nguồn vẫn được giữ trong vùng an toàn. Với nội dung có nhiều dòng, ranh giới dòng được ưu tiên; một dòng quá dài nên thêm Enter để dễ đọc.


### Viền chữ mềm

Trong mục vị trí chữ, bật **Viền chữ mềm** để chữ nổi rõ hơn trên nền. Chỉnh **Độ dày viền**, **Độ nhòe ra ngoài**, **Độ đậm viền** và **Màu viền**; viền nhạt dần ra ngoài, nét chữ vẫn sắc. Mặc định màu tự động theo mẫu; chọn màu riêng sẽ tắt chế độ màu tự động. Viền áp dụng cho câu nói và nguồn, được lưu lại và dùng giống nhau khi xem trước hoặc xuất Full HD. Lớp chữ cập nhật trong nháp mà không dựng lại video nền.

### Tải video về nơi đã chọn

Nút **Tải video** nằm trên thanh đầu ứng dụng, cạnh nút thư mục video đã xuất, luôn nhìn thấy khi cuộn. Nút mở hộp thoại Lưu video của Windows trước khi dựng. Tên gợi ý lấy 5 từ đầu câu nói (Enter tính như khoảng trắng), giữ dấu tiếng Việt và bỏ ký tự không hợp lệ; bạn có thể sửa tên. Thư mục được nhớ sau khi xác nhận, kể cả khi mở lại ứng dụng. Hủy thì không dựng và không tính lượt footage. File trùng tên được hỏi ghi đè.

Video tải là MP4 Full HD 1080×1920. Tải lại bản vừa xuất không dựng lại và không tăng lượt footage. Nếu chỉnh nội dung trong lúc chờ, file tải vẫn dùng nội dung lúc bấm nút. Lưu lỗi không làm mất bản xuất nội bộ; chọn nơi khác rồi tải lại. Bản xuất nội bộ vẫn nằm trong `output_videos`; xuất hàng loạt giữ nguyên.


### Tự lưu và footage không trùng

Mỗi lần sửa chữ (kể cả xuống dòng), chọn câu/clip hoặc chỉnh thiết kế/âm lượng, ứng dụng tự lưu và báo **Đã lưu tự động**. V10 giữ các cài đặt và mở vào câu chưa tải đầu tiên; bấm **Mở bản nháp trước** để khôi phục bản soạn trước khi khởi động. V5 lưu trong `session_state.json`, nhập thiết lập cũ lần đầu và giữ riêng để các cửa sổ phiên bản cũ không ghi đè.

V8 tránh toàn bộ footage của câu trước khi đổi câu (kể cả chỉ xem trước trong phiên), ưu tiên clip có ít lượt dùng nhất trong nhóm phù hợp. Khi hết clip mới mới quay lại footage của câu trước; chỉ lặp trong cùng reel sau khi đi hết kho. Cảnh phải quay vòng được ghi rõ trong kịch bản. Kho chọn mới thay kho cũ, nhưng lịch sử số lượt mọi clip vẫn giữ nguyên. Các file sao chép giống hệt nội dung được tính là một footage. Xem trước không tính lượt; xuất lỗi trả lại lượt. Nếu clip đã chọn đã dùng trước các clip còn lại, ứng dụng tự chọn clip chưa dùng và hiển thị trong kịch bản. Lịch sử lưu ở `footage_usage.json`, không đưa lên GitHub; giữ file này nếu muốn tiếp tục vòng footage khi chuyển máy. Quy tắc có hiệu lực với các lần xuất từ v5.


### Folder nền và chia cảnh v8

Ở phần video nền, bấm **Chọn folder** để thay kho và tự nhớ; **Quét lại** khi thêm clip; **Dùng kho mặc định** để trở về kho đi kèm. Folder bị xóa/mất kết nối hoặc không có clip hợp lệ sẽ báo lỗi và cho chọn lại, không âm thầm đổi nguồn. Folder nền độc lập với thư mục lưu video tải xuống.

Với nội dung một dòng, tự chia theo dấu kết câu và ưu tiên dấu phẩy/từ nối khi hai vế đủ dài, từ nối nằm ở cảnh sau. Nhấn Enter vẫn chủ động đặt mỗi dòng thành một cảnh. Chữ hiển thị tự cân dòng, tránh đuôi một từ hoặc hai từ ngắn và giữ các cụm như “hạnh phúc”, “biết ơn”, “yêu thương” khi khung cho phép. Tắt tự chia để giữ nguyên một cảnh cho nội dung một dòng.

Bài kiểm tra v8 được giữ cho phiên bản lịch sử; bản đóng gói hiện tại dùng `python -X utf8 verify_v11.py --hold --fullhd`. Script tạo profile dưới `.cache`, dùng clip màu riêng và không sửa bản nháp/lịch sử/video thật.


### Tự cập nhật câu nói từ Google Sheet — v9

Ứng dụng tự đọc tab **Đạo lý hay mỗi ngày** trong [Sheet nguồn](https://docs.google.com/spreadsheets/d/1Ku40G9gH89W7eRpN6u6NAYnxj2hGf8Gv-QL_34a2teI/edit) khi mở app và **mỗi 30 phút khi app đang chạy**. Lấy toàn bộ cột A, kể cả dòng đã đánh dấu done ở cột B; thêm/sửa/xóa câu trong app theo Sheet. Bấm **Cập nhật ngay** nếu cần kiểm tra sớm hơn. Chỉ đọc công khai, không đăng nhập, không khóa API, không xin quyền hoặc ghi lên Google Sheet.

Danh sách cập nhật ở nền, giữ nguyên câu đang soạn và các Reel đang xuất. Nếu câu đang chọn bị sửa/xóa trên Sheet, phần đang soạn được giữ làm bản nháp để bạn chủ động chọn lại. Mất mạng hoặc Sheet không còn công khai: app giữ danh sách đã tải gần nhất và báo lỗi, tiếp tục thử lại sau 30 phút. Chưa từng tải thành công thì tạm dùng câu trong PMDX/TXT/có sẵn. Bản lưu Sheet nằm trong `.cache/quotes/google_sheet.json`; không phải bản nháp và không đưa lên GitHub.

Nút Xuất nhiều Reel dùng danh sách tại lúc bắt đầu, nên bài mới xuất hiện giữa chừng sẽ dành cho lần xuất tiếp theo. Nếu Sheet rỗng, vẫn có thể nhập và tải một Reel riêng. Khi tiến trình ứng dụng dừng, việc kiểm tra cũng dừng; lần mở tiếp theo kiểm tra ngay.

Kiểm tra bản đóng gói hiện tại: `python -X utf8 verify_v11.py --hold --fullhd`. Với bài thử cục bộ không muốn đọc Sheet, thêm `--no-sheet-sync` khi chạy ứng dụng. Không thay đổi thiết lập chia sẻ của Sheet qua app.


### Xem trước nhanh và giãn dòng đều — v9

V9 dùng MP4 preview dựng ở nền; v10 thay bằng nháp trực tiếp từ footage cache, xem phần dưới. Full HD vẫn dùng renderer và plan chung, preview không tăng lượt footage.

Giãn dòng câu nói và nguồn được căn theo đường chân chữ chung, giữ đều bước dòng dù các dòng có dấu tiếng Việt cao/thấp khác nhau. App tạo lại cache kế hoạch/preview để áp dụng bản sửa; bản video đã xuất trước đây cần xuất lại nếu muốn bố cục mới.


### Chọn footage và nháp tức thì — v10

Kịch bản nằm ngay trên kho footage. Mỗi thẻ có ảnh, chữ, thời gian và tốc độ; chọn cảnh rồi bấm thumbnail để gợi ý thay clip cho đúng cảnh đó. App giữ vị trí đang chọn và cuộn; khi quy tắc chống lặp/lượt dùng cần chọn clip khác, tên clip thực tế và lý do được hiển thị rõ. Gợi ý từng cảnh được tự lưu, giữ khi chỉnh thiết kế và xóa khi đổi nội dung hoặc cách chia cảnh. Batch không dùng các gợi ý riêng của bản nháp.

Nháp dùng hai video nền nhẹ 360×640 và PNG chữ do chính renderer Full HD tạo. Đổi chữ không dựng lại nền; mỗi clip chỉ cần tạo bản nhẹ lần đầu, lưu trong `.cache/draft_media` và chuẩn bị dần cả kho. Clip đang dùng được ưu tiên. Nháp giữ timeline, cắt nguồn, làm chậm, fade chữ và nhạc từ server; chuyển cảnh/độ mượt/màu có thể khác nhẹ Full HD. Khi thiếu dữ liệu, hình, chữ và nhạc cùng dừng chờ. API preview MP4 cũ vẫn dành cho kiểm tra/tương thích, giao diện mới không gọi dựng Reel để xem nháp.

### Ghi nhớ câu đã tải — v10

**Tải video lưu file thành công** tự đánh dấu **ĐÃ TẢI VIDEO**. V11 bổ sung **Đánh dấu đã tải** và **Bỏ đánh dấu đã tải** ngay cạnh trạng thái, dùng cho câu bạn đã tải trước đây hoặc cần sửa trạng thái. Hủy hộp thoại, lỗi dựng/lưu, chỉ xem nháp hoặc Xuất nhiều Reel không tự đánh dấu. Có ngày tải gần nhất, số lần tải, bộ đếm đã/chưa tải và nút **Câu chưa tải tiếp theo**. Lịch sử theo nội dung sau NFC và gộp khoảng trắng: các dòng Sheet trùng nội dung cùng trạng thái; sửa nội dung tạo câu chưa tải mới. Không suy đoán video tải trước v10 vì các bản cũ chưa lưu liên kết câu–file; có thể đánh dấu thủ công các câu đó trong v11.

Lúc mở app, chọn câu chưa tải đầu tiên theo thứ tự Sheet. Nếu đã tải hết, hiển thị rõ và chọn câu đầu; Sheet rỗng giữ bản nháp. Bản soạn/cài đặt trước khi chuyển câu được giữ trong `draft_recovery.json` và mở lại bằng nút trong phần câu nói. `quote_download_history.json` là dữ liệu cá nhân bền vững, độc lập `footage_usage.json`; sao lưu riêng cả hai khi chuyển máy. Sheet cập nhật trong phiên không thay bản đang soạn.

### Nhạc nền offline — v10

Kho nguồn: [music background của vinhn8n/voicedaoly](https://huggingface.co/datasets/vinhn8n/voicedaoly/tree/main/music%20background). Các bài được tải thành file cục bộ vào `CLIP TƯỢNG PHẬT LQ/NHẠC NỀN` ở kho mặc định, hoặc `NHẠC NỀN` bên trong folder footage tự chọn. Tải/bổ sung ở nền, kiểm tra SHA256 và giữ nguyên file cũ nếu trùng tên nhưng khác nội dung. Không cần tài khoản hoặc token Hugging Face; xem nháp/xuất dùng file offline, không gọi mạng để phát.

Mặc định mỗi Reel chọn ngẫu nhiên một bài; đổi câu/nhấn **Đổi bài ngẫu nhiên** tránh bài ngay trước khi còn lựa chọn. Chỉnh chữ hoặc footage giữ nguyên bài. Có tìm tên, chọn bài cố định, nghe thử, mở kho, hoặc tắt nhạc. V11 đã bỏ lựa chọn và nút nghe chuông thiền. Batch random từng Reel, tránh lặp bài liền trước. Nhạc ngắn được lặp cho đủ Reel và fade đầu/cuối, âm thanh footage luôn tắt. Kho chưa có bài thì báo rõ chưa có nhạc, không phát chuông thay thế; bài chọn cố định bị mất sẽ yêu cầu chọn lại.


### Đánh dấu thủ công và sửa tiếng nháp — v11

Bấm **Đánh dấu đã tải** cho câu đang soạn: trạng thái được lưu ngay và có thời điểm đánh dấu. Có thể **Bỏ đánh dấu đã tải** để sửa lại; thao tác không dựng video, không tăng lượt footage hoặc số lần tải file thực tế. Dấu vẫn còn sau restart, dùng chung cho các bản trùng nội dung và ảnh hưởng lựa chọn câu chưa tải lúc khởi động. Đánh dấu không tự chuyển câu hoặc làm mất bản nháp đang sửa.

Nhạc nháp tự tiếp tục sau lúc tải clip, tạm dừng, tua hoặc đổi footage; không còn coi lần phát bị ngắt khi chờ dữ liệu là lỗi khóa âm thanh. Đồ thị âm thanh được kích hoạt từ thao tác bấm, dùng đúng âm lượng và fade của Reel. Khung preview có trạng thái và thanh tín hiệu nhạc; nếu trình duyệt thực sự chặn tiếng thì hiện **Bật tiếng nháp** để bật lại. Âm lượng 0 và Tắt nhạc vẫn được tôn trọng.

Chuông thiền đã bỏ khỏi giao diện, endpoint phát, fallback và EXE mới. Cài đặt cũ ở chế độ chuông được chuyển sang nhạc ngẫu nhiên. File nguồn chuông cũ và các EXE cũ được giữ trên đĩa để không phá dữ liệu/phiên cũ, không được ứng dụng v11 dùng để phát hoặc xuất. Kho 175 bài nhạc offline vẫn giữ nguyên.
