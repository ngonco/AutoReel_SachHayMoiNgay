# Hướng dẫn Auto Reel Sách Hay Mỗi Ngày

Mở `Chay_Ung_Dung_Auto_Reel.bat` hoặc `AutoReelSachHay_v3.exe`.

1. Chọn hoặc nhập toàn bộ câu nói. Nhấn Enter để mỗi dòng có chữ thành một cảnh riêng (kể cả khi tắt tự chia cảnh); dòng trống được bỏ qua. Chọn clip cho cảnh đầu.
2. Bật **Tự chia câu dài thành nhiều cảnh**. Các phần sau tự dùng clip khác trong kho; clip ngắn được làm chậm.
3. Chọn một trong năm template, cỡ chữ, credit và vị trí chữ.
4. Xem **Kịch bản reel** để kiểm tra từng phần chữ, clip và thời lượng. Các nút 10/12/15 giây đặt thời lượng tối thiểu; câu dài được tăng thời gian để đọc hết.
5. Bấm **Phát toàn bộ reel**, chờ dựng bản nhẹ lần đầu. Có đầy đủ cảnh, chữ, chuông thiền và chuyển cảnh giống video xuất. Dùng thanh video để tua; bấm tên cảnh để nhảy đến cảnh đó.
6. Bấm **Xuất reel** để xuất Full HD. Mở thư mục kết quả hoặc xem lại ngay trong ứng dụng.

Bản xem trước dùng lại khi chưa đổi thiết lập. Khi sửa chữ, clip hay template, bấm Play để dựng bản cập nhật. Xuất hàng loạt dùng thiết lập hiện tại cho toàn bộ câu trong danh sách.

Video hoàn tất: `output_videos`. Nhật ký lỗi: `logs/app.log`. Ảnh kiểm tra mẫu: `test_renders/verification`.

Chế độ tự động vị trí chữ chỉ là ước lượng theo ảnh mẫu; nếu mặt tượng di chuyển hoặc bị che, đổi sang vị trí thủ công và kiểm tra lại.

Nếu chạy từ mã nguồn hoặc build lại, xem `README.md`. Bản backup GitHub lưu mã nguồn và tài liệu; kho clip và video cá nhân được giữ cục bộ.

Điều chỉnh Y: kéo thanh trượt hoặc nhập số từ −1600 đến +1600 px. Toàn bộ chữ và nguồn vẫn được giữ trong vùng an toàn. Với nội dung có nhiều dòng, ranh giới dòng được ưu tiên; một dòng quá dài nên thêm Enter để dễ đọc.
