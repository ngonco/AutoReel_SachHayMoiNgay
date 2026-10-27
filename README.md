# Auto Reel Sách Hay Mỗi Ngày

Ứng dụng Windows dựng reel dọc với câu nói tiếng Việt, video tượng Phật, năm template và nhạc chuông thiền.

- Câu dài tự chia thành nhiều cảnh, giữ đủ nội dung và dấu câu.
- Mỗi cảnh dùng một clip khác; clip ngắn được làm chậm vừa đủ.
- Play dựng bản nhẹ 540×960 có đầy đủ chữ, nhạc và chuyển cảnh 0,4 giây.
- Xuất Full HD 1080×1920 từ chính kế hoạch đã xem trước.
- Tổng thời lượng tự tăng để đủ đọc, tối thiểu theo nút 10/12/15 giây đã chọn.

## Chạy

Bản đã đóng gói: mở `Chay_Ung_Dung_Auto_Reel.bat` hoặc `AutoReelSachHay_v3.exe` trong thư mục có dữ liệu. File EXE đi kèm FFmpeg, FFprobe, font và âm thanh bên trong. Kho clip vẫn nằm cạnh ứng dụng.

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
4. Bấm **Xuất reel**, rồi **Xem lại video vừa render** hoặc mở thư mục kết quả.

Thay đổi thiết lập sẽ làm bản xem trước cũ hết hiệu lực. Cỡ chữ và credit được giới hạn trong vùng an toàn; nếu chủ thể di chuyển, hãy xem lại vị trí chữ trước khi xuất.

## Kiểm tra và build

```powershell
python -X utf8 -m unittest discover -s tests -v
python -X utf8 verify_samples.py
python -X utf8 build_onefile.py
```

`verify_samples.py` cần kho clip thật và xuất ba mẫu (một, hai, ba cảnh) ở cả bản nhẹ và Full HD. Kết quả ở `output_videos/verification`; ảnh kiểm tra và báo cáo ở `test_renders/verification`.

Build đọc `AutoReelSachHay.spec`, gom FFmpeg/FFprobe và DLL cạnh chúng, âm thanh và ba font cần thiết; ghi EXE mới vào thư mục gốc và `dist/AutoReelSachHay`. EXE trước đó được giữ ở `AutoReelSachHay_v3.previous.exe`.

Bắt buộc sau mỗi đợt sửa code, kể cả giao diện: đóng gói lại EXE từ code cuối cùng, mở qua launcher và kiểm tra chức năng vừa sửa trên bản đóng gói trước khi bàn giao. Không giao EXE cũ sau khi chỉ kiểm tra mã nguồn. Chỉ sửa tài liệu thì không cần build lại.

Xem [system_map.md](system_map.md) trước khi nâng cấp hoặc sửa lỗi. Đọc [VERIFICATION.md](VERIFICATION.md) để xem kết quả kiểm tra đợt nâng cấp.

## Backup

Repo nguồn: https://github.com/ngonco/AutoReel_SachHayMoiNgay

Sau mỗi đợt sửa hoàn tất: cập nhật tài liệu, chạy kiểm tra liên quan, commit và push; xác nhận commit trên GitHub trùng commit cục bộ. Không force-push. Clip, file xuất, cache, font Microsoft, EXE và cài đặt cá nhân được giữ cục bộ theo `.gitignore`; phục hồi đầy đủ cần sao lưu riêng các dữ liệu này.

Điều chỉnh Y: kéo thanh trượt hoặc nhập số từ −1600 đến +1600 px. Toàn bộ chữ và nguồn vẫn được giữ trong vùng an toàn. Với nội dung có nhiều dòng, ranh giới dòng được ưu tiên; một dòng quá dài nên thêm Enter để dễ đọc.
