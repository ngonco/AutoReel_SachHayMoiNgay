# Auto Reel Sách Hay Mỗi Ngày

Ứng dụng Windows dựng reel dọc với câu nói tiếng Việt, video tượng Phật, năm template và nhạc chuông thiền.

- Câu dài tự chia thành nhiều cảnh, giữ đủ nội dung và dấu câu.
- Mỗi cảnh dùng một clip khác; clip ngắn được làm chậm vừa đủ.
- Preview 360×640 được chuẩn bị ở nền, Play dùng lại bản đã sẵn sàng có đầy đủ chữ, nhạc và chuyển cảnh 0,4 giây.
- Xuất Full HD 1080×1920 từ chính kế hoạch đã xem trước.
- Tổng thời lượng tự tăng để đủ đọc, tối thiểu theo nút 10/12/15 giây đã chọn.

## Chạy

Bản đã đóng gói: mở `Chay_Ung_Dung_Auto_Reel.bat` hoặc `AutoReelSachHay_v9.exe` trong thư mục có dữ liệu. File EXE đi kèm FFmpeg, FFprobe, font và âm thanh bên trong. Có thể chọn folder clip ở vị trí khác; ứng dụng tự nhớ.

Chạy từ mã nguồn trên Windows, Python 3.11:

```powershell
python -m pip install -r requirements.txt
python -X utf8 app.py
```

Cần FFmpeg và FFprobe trên PATH khi chạy từ nguồn. Đặt clip trong `CLIP TƯỢNG PHẬT LQ/DỌC` hoặc `CLIP TƯỢNG PHẬT LQ/NGANG`, hoặc chọn **Folder video nền** (bao gồm thư mục con), hoặc bấm **Chọn video khác** để dùng file cục bộ.

Font dùng Times New Roman Bold và Segoe UI có sẵn trong `C:/Windows/Fonts`. Có thể đặt bản font được phép sử dụng trong `assets/fonts`. Repo không chứa các font Microsoft này. Nội dung câu nói đọc từ PMDX/TXT nếu có, nếu không dùng 16 câu có sẵn.

## Sử dụng

1. Chọn câu nói, clip cho cảnh đầu, template và vị trí chữ. Nhấn Enter trong câu nói để chia mỗi dòng thành một cảnh riêng; dòng trống được bỏ qua.
2. Kiểm tra **Kịch bản reel**: đầy đủ chữ, clip, thời gian nguồn và tốc độ từng cảnh.
3. Bấm **Phát toàn bộ reel**. Lần đầu chờ dựng; có thể tạm dừng, tua và phát lại.
4. Bấm **Tải video**, chọn nơi lưu và tên file. Ứng dụng tự xuất Full HD nếu cần; nếu đã xuất đúng thiết lập trong phiên này thì lưu ngay. Nút **Xuất nhiều Reel** trên thanh đầu xuất toàn bộ danh sách câu; nút Xuất Reel riêng đã bỏ.

Thay đổi thiết lập sẽ làm bản xem trước cũ hết hiệu lực. Cỡ chữ và credit được giới hạn trong vùng an toàn; nếu chủ thể di chuyển, hãy xem lại vị trí chữ trước khi xuất.

## Kiểm tra và build

```powershell
python -X utf8 -m unittest discover -s tests -v
python -X utf8 verify_samples.py
python -X utf8 build_onefile.py
```

`verify_samples.py` cần kho clip thật và xuất ba mẫu (một, hai, ba cảnh) ở cả bản nhẹ và Full HD. Kết quả ở `output_videos/verification`; ảnh kiểm tra và báo cáo ở `test_renders/verification`.

Build đọc `AutoReelSachHay.spec`, gom FFmpeg/FFprobe và DLL cạnh chúng, âm thanh và ba font cần thiết; ghi EXE mới vào thư mục gốc và `dist/AutoReelSachHay`. EXE trước đó được giữ ở `AutoReelSachHay_v9.previous.exe`.

Bắt buộc sau mỗi đợt sửa code, kể cả giao diện: đóng gói lại EXE từ code cuối cùng, mở qua launcher và kiểm tra chức năng vừa sửa trên bản đóng gói trước khi bàn giao. Không giao EXE cũ sau khi chỉ kiểm tra mã nguồn. Chỉ sửa tài liệu thì không cần build lại.

Xem [system_map.md](system_map.md) trước khi nâng cấp hoặc sửa lỗi. Đọc [VERIFICATION.md](VERIFICATION.md) để xem kết quả kiểm tra đợt nâng cấp.

## Backup

Repo nguồn: https://github.com/ngonco/AutoReel_SachHayMoiNgay

Sau mỗi đợt sửa hoàn tất: cập nhật tài liệu, chạy kiểm tra liên quan, commit và push; xác nhận commit trên GitHub trùng commit cục bộ. Không force-push. Clip, file xuất, cache, font Microsoft, EXE và cài đặt cá nhân được giữ cục bộ theo `.gitignore`; phục hồi đầy đủ cần sao lưu riêng các dữ liệu này.

Điều chỉnh Y: kéo thanh trượt hoặc nhập số từ −1600 đến +1600 px. Toàn bộ chữ và nguồn vẫn được giữ trong vùng an toàn. Với nội dung có nhiều dòng, ranh giới dòng được ưu tiên; một dòng quá dài nên thêm Enter để dễ đọc.


### Viền chữ mềm

Trong mục vị trí chữ, bật **Viền chữ mềm** để chữ nổi rõ hơn trên nền. Chỉnh **Độ dày viền**, **Độ nhòe ra ngoài**, **Độ đậm viền** và **Màu viền**; viền nhạt dần ra ngoài, nét chữ vẫn sắc. Mặc định màu tự động theo mẫu; chọn màu riêng sẽ tắt chế độ màu tự động. Viền áp dụng cho câu nói và nguồn, được lưu lại và dùng giống nhau khi xem trước hoặc xuất Full HD. Bấm Play để dựng lại sau khi thay đổi.

### Tải video về nơi đã chọn

Nút **Tải video** nằm trên thanh đầu ứng dụng, cạnh nút thư mục video đã xuất, luôn nhìn thấy khi cuộn. Nút mở hộp thoại Lưu video của Windows trước khi dựng. Tên gợi ý lấy 5 từ đầu câu nói (Enter tính như khoảng trắng), giữ dấu tiếng Việt và bỏ ký tự không hợp lệ; bạn có thể sửa tên. Thư mục được nhớ sau khi xác nhận, kể cả khi mở lại ứng dụng. Hủy thì không dựng và không tính lượt footage. File trùng tên được hỏi ghi đè.

Video tải là MP4 Full HD 1080×1920. Tải lại bản vừa xuất không dựng lại và không tăng lượt footage. Nếu chỉnh nội dung trong lúc chờ, file tải vẫn dùng nội dung lúc bấm nút. Lưu lỗi không làm mất bản xuất nội bộ; chọn nơi khác rồi tải lại. Bản xuất nội bộ vẫn nằm trong `output_videos`; xuất hàng loạt giữ nguyên.


### Tự lưu và footage không trùng

Mỗi lần sửa chữ (kể cả xuống dòng), chọn câu/clip hoặc chỉnh thiết kế/âm lượng, ứng dụng tự lưu và báo **Đã lưu tự động**. Khi mở lại sẽ khôi phục nội dung, clip và các cài đặt. V5 lưu trong `session_state.json`, nhập thiết lập cũ lần đầu và giữ riêng để các cửa sổ phiên bản cũ không ghi đè.

V8 tránh toàn bộ footage của câu trước khi đổi câu (kể cả chỉ xem trước trong phiên), ưu tiên clip có ít lượt dùng nhất trong nhóm phù hợp. Khi hết clip mới mới quay lại footage của câu trước; chỉ lặp trong cùng reel sau khi đi hết kho. Cảnh phải quay vòng được ghi rõ trong kịch bản. Kho chọn mới thay kho cũ, nhưng lịch sử số lượt mọi clip vẫn giữ nguyên. Các file sao chép giống hệt nội dung được tính là một footage. Xem trước không tính lượt; xuất lỗi trả lại lượt. Nếu clip đã chọn đã dùng trước các clip còn lại, ứng dụng tự chọn clip chưa dùng và hiển thị trong kịch bản. Lịch sử lưu ở `footage_usage.json`, không đưa lên GitHub; giữ file này nếu muốn tiếp tục vòng footage khi chuyển máy. Quy tắc có hiệu lực với các lần xuất từ v5.


### Folder nền và chia cảnh v8

Ở phần video nền, bấm **Chọn folder** để thay kho và tự nhớ; **Quét lại** khi thêm clip; **Dùng kho mặc định** để trở về kho đi kèm. Folder bị xóa/mất kết nối hoặc không có clip hợp lệ sẽ báo lỗi và cho chọn lại, không âm thầm đổi nguồn. Folder nền độc lập với thư mục lưu video tải xuống.

Với nội dung một dòng, tự chia theo dấu kết câu và ưu tiên dấu phẩy/từ nối khi hai vế đủ dài, từ nối nằm ở cảnh sau. Nhấn Enter vẫn chủ động đặt mỗi dòng thành một cảnh. Chữ hiển thị tự cân dòng, tránh đuôi một từ hoặc hai từ ngắn và giữ các cụm như “hạnh phúc”, “biết ơn”, “yêu thương” khi khung cho phép. Tắt tự chia để giữ nguyên một cảnh cho nội dung một dòng.

Kiểm tra riêng bản đóng gói: `python -X utf8 verify_v8.py --hold`. Script tạo profile dưới `.cache`, dùng clip màu riêng và không sửa bản nháp/lịch sử/video thật.


### Tự cập nhật câu nói từ Google Sheet — v9

Ứng dụng tự đọc tab **Đạo lý hay mỗi ngày** trong [Sheet nguồn](https://docs.google.com/spreadsheets/d/1Ku40G9gH89W7eRpN6u6NAYnxj2hGf8Gv-QL_34a2teI/edit) khi mở app và **mỗi 30 phút khi app đang chạy**. Lấy toàn bộ cột A, kể cả dòng đã đánh dấu done ở cột B; thêm/sửa/xóa câu trong app theo Sheet. Bấm **Cập nhật ngay** nếu cần kiểm tra sớm hơn. Chỉ đọc công khai, không đăng nhập, không khóa API, không xin quyền hoặc ghi lên Google Sheet.

Danh sách cập nhật ở nền, giữ nguyên câu đang soạn và các Reel đang xuất. Nếu câu đang chọn bị sửa/xóa trên Sheet, phần đang soạn được giữ làm bản nháp để bạn chủ động chọn lại. Mất mạng hoặc Sheet không còn công khai: app giữ danh sách đã tải gần nhất và báo lỗi, tiếp tục thử lại sau 30 phút. Chưa từng tải thành công thì tạm dùng câu trong PMDX/TXT/có sẵn. Bản lưu Sheet nằm trong `.cache/quotes/google_sheet.json`; không phải bản nháp và không đưa lên GitHub.

Nút Xuất nhiều Reel dùng danh sách tại lúc bắt đầu, nên bài mới xuất hiện giữa chừng sẽ dành cho lần xuất tiếp theo. Nếu Sheet rỗng, vẫn có thể nhập và tải một Reel riêng. Khi tiến trình ứng dụng dừng, việc kiểm tra cũng dừng; lần mở tiếp theo kiểm tra ngay.

Kiểm tra bản đóng gói riêng: `python -X utf8 verify_v9.py --hold`. Với bài thử cục bộ không muốn đọc Sheet, thêm `--no-sheet-sync` khi chạy ứng dụng. Không thay đổi thiết lập chia sẻ của Sheet qua app.


### Xem trước nhanh và giãn dòng đều — v9

Sau khi bạn ngừng sửa khoảng một giây, app chuẩn bị bản xem trước ở nền. Khi hiện **Sẵn sàng xem**, bấm Phát sẽ mở bản đã chuẩn bị; không tự phát tiếng/video. Bản xem nhanh 360×640 dùng cùng kịch bản, chữ, chuyển cảnh và nhạc; video tải xuống vẫn Full HD 1080×1920. Lần đầu hoặc vừa đổi câu có thể cần chờ ngắn để chuẩn bị. Preview có hàng đợi riêng, không phải đợi xuất nhiều Reel xong, và không tính lượt footage.

Giãn dòng câu nói và nguồn được căn theo đường chân chữ chung, giữ đều bước dòng dù các dòng có dấu tiếng Việt cao/thấp khác nhau. App tạo lại cache kế hoạch/preview để áp dụng bản sửa; bản video đã xuất trước đây cần xuất lại nếu muốn bố cục mới.
