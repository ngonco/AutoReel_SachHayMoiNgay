# Auto Reel Sách Hay Mỗi Ngày

Ứng dụng Windows dựng reel dọc với câu nói tiếng Việt, video tượng Phật, năm template và nhạc chuông thiền.

- Câu dài tự chia thành nhiều cảnh, giữ đủ nội dung và dấu câu.
- Mỗi cảnh dùng một clip khác; clip ngắn được làm chậm vừa đủ.
- Play dựng bản nhẹ 540×960 có đầy đủ chữ, nhạc và chuyển cảnh 0,4 giây.
- Xuất Full HD 1080×1920 từ chính kế hoạch đã xem trước.
- Tổng thời lượng tự tăng để đủ đọc, tối thiểu theo nút 10/12/15 giây đã chọn.

## Chạy

Bản đã đóng gói: mở `Chay_Ung_Dung_Auto_Reel.bat` hoặc `AutoReelSachHay_v7.exe` trong thư mục có dữ liệu. File EXE đi kèm FFmpeg, FFprobe, font và âm thanh bên trong. Kho clip vẫn nằm cạnh ứng dụng.

Chạy từ mã nguồn trên Windows, Python 3.11:

```powershell
python -m pip install -r requirements.txt
python -X utf8 app.py
```

Cần FFmpeg và FFprobe trên PATH khi chạy từ nguồn. Đặt clip trong `CLIP TƯỢNG PHẬT LQ/DỌC` hoặc `CLIP TƯỢNG PHẬT LQ/NGANG`, hoặc bấm **Chọn video khác** để dùng file cục bộ.

Font dùng Times New Roman Bold và Segoe UI có sẵn trong `C:/Windows/Fonts`. Có thể đặt bản font được phép sử dụng trong `assets/fonts`. Repo không chứa các font Microsoft này. Nội dung câu nói đọc từ PMDX/TXT nếu có, nếu không dùng 16 câu có sẵn.

## Sử dụng

1. Chọn câu nói, clip cho cảnh đầu, template và vị trí chữ. Nhấn Enter trong câu nói để chia mỗi dòng thành một cảnh riêng; dòng trống được bỏ qua.
2. Kiểm tra **Kịch bản reel**: đầy đủ chữ, clip, thời gian nguồn và tốc độ từng cảnh.
3. Bấm **Phát toàn bộ reel**. Lần đầu chờ dựng; có thể tạm dừng, tua và phát lại.
4. Bấm **Tải video**, chọn nơi lưu và tên file. Ứng dụng tự xuất Full HD nếu cần; nếu đã xuất đúng thiết lập trong phiên này thì lưu ngay. Có thể dùng **Xuất reel** và **Xem lại video vừa render** như trước.

Thay đổi thiết lập sẽ làm bản xem trước cũ hết hiệu lực. Cỡ chữ và credit được giới hạn trong vùng an toàn; nếu chủ thể di chuyển, hãy xem lại vị trí chữ trước khi xuất.

## Kiểm tra và build

```powershell
python -X utf8 -m unittest discover -s tests -v
python -X utf8 verify_samples.py
python -X utf8 build_onefile.py
```

`verify_samples.py` cần kho clip thật và xuất ba mẫu (một, hai, ba cảnh) ở cả bản nhẹ và Full HD. Kết quả ở `output_videos/verification`; ảnh kiểm tra và báo cáo ở `test_renders/verification`.

Build đọc `AutoReelSachHay.spec`, gom FFmpeg/FFprobe và DLL cạnh chúng, âm thanh và ba font cần thiết; ghi EXE mới vào thư mục gốc và `dist/AutoReelSachHay`. EXE trước đó được giữ ở `AutoReelSachHay_v7.previous.exe`.

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

Footage được dùng luân phiên qua nhiều lần xuất, cả xuất hàng loạt; chỉ dùng lại khi đã đi hết kho. Các file sao chép giống hệt nội dung được tính là một footage. Xem trước không tính lượt; xuất lỗi trả lại lượt. Nếu clip đã chọn đã dùng trước các clip còn lại, ứng dụng tự chọn clip chưa dùng và hiển thị trong kịch bản. Lịch sử lưu ở `footage_usage.json`, không đưa lên GitHub; giữ file này nếu muốn tiếp tục vòng footage khi chuyển máy. Quy tắc có hiệu lực với các lần xuất từ v5.
