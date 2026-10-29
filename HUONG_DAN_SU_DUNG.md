# Hướng dẫn Auto Reel Sách Hay Mỗi Ngày

Mở `Chay_Ung_Dung_Auto_Reel.bat` hoặc `AutoReelSachHay_v12.exe`.

1. Chọn hoặc nhập toàn bộ câu nói. Với mẫu 01–05, Enter tạo mỗi dòng có chữ thành một cảnh riêng (kể cả khi tắt tự chia cảnh); dòng trống được bỏ qua. Chọn clip cho cảnh đầu.
2. Với mẫu 01–05, bật **Tự chia cảnh theo dấu câu và từ nối** nếu muốn tự phân đoạn. Các phần sau dùng clip khác trong kho; clip ngắn được làm chậm. CHỮ CUỘN giữ chữ liên tục và tự chia riêng footage.
3. Dùng công tắc **CHỮ CUỘN** hoặc chọn một trong năm style chữ tĩnh ngay đầu giao diện. Mẫu 01–05 cho chỉnh cỡ chữ, credit và vị trí; CHỮ CUỘN dùng khung chữ nhỏ cố định như hướng dẫn bên dưới.
4. Xem **Kịch bản reel** để kiểm tra từng phần chữ, clip và thời lượng. Các nút 10/12/15 giây đặt thời lượng tối thiểu; câu dài được tăng thời gian để đọc hết.
5. Bấm **Phát toàn Reel** để xem nháp trực tiếp với chữ, chuyển cảnh và nhạc offline. Clip mới cần chuẩn bị bản nhẹ một lần. Dùng thanh tua hoặc bấm tên cảnh/footage để nhảy đến đoạn đó.
6. Bấm **Tải video** trên thanh đầu ứng dụng, cạnh nút thư mục, rồi chọn nơi lưu. Ứng dụng tự xuất Full HD nếu chưa có bản đúng thiết lập trong phiên này; nếu đã xuất thì lưu ngay.

## CHỮ CUỘN

Ngay đầu giao diện, phía trên mục nhập câu nói, công tắc **CHỮ CUỘN** nằm trong khung **Chọn style chữ**. Mặc định công tắc bật khi mở bản nâng cấp lần đầu, sau đó nhớ trạng thái bạn đã chọn. Tắt công tắc trở về style chữ tĩnh dùng trước đó; bấm một style tĩnh cũng tự tắt công tắc. Chữ trắng ngà nhỏ, nét vừa, có viền tối mảnh, nằm trong khung cố định khoảng 69–82% chiều cao video. Mẫu này không có bảng nền, hoa văn hoặc đường phân cách.

Nội dung vừa khung đứng yên; nội dung dài giữ phần đầu 2 giây, cuộn lên liên tục và dừng ở phần cuối ít nhất 2 giây. Chữ biến mất dần ở mép trên và hiện dần ở mép dưới. Nhấn Enter giữ ngắt dòng/đoạn, không tạo cảnh chữ mới. Tên trang trong ô Kênh/Nguồn nằm cuối cùng, cuộn cùng nội dung; để trống nếu không muốn hiện.

Thanh **Tốc độ chữ · Chậm–Nhanh** chỉnh từ 0,65× đến 1,50×. App tự tính thời lượng đủ đọc, các nút 10/12/15 giây vẫn là thời lượng tối thiểu. Footage chuyển khoảng 7 giây/clip; vẫn chọn và thay từng footage, chữ không bắt đầu lại khi chuyển clip. Vị trí, cỡ chữ và hiệu ứng của mẫu được cố định; chọn lại mẫu 01–05 để dùng các điều khiển thiết kế cũ, giá trị cũ được giữ nguyên.

Tên file gợi ý là 5 từ đầu câu nói, có dấu tiếng Việt và đuôi `.mp4`; có thể sửa tên. Hộp thoại nhớ thư mục sau khi xác nhận, kể cả khi mở lại ứng dụng. Hủy thì không dựng video. Tải lại bản vừa xuất không tính thêm lượt footage. Nếu lưu lỗi, bản Full HD vẫn còn trong ứng dụng để thử tải sang nơi khác. Thay đổi nội dung trong lúc dựng không đổi file đã yêu cầu tải.

Bản xem trước dùng lại khi chưa đổi thiết lập. Khi sửa chữ, clip hay template, bấm Play để dựng bản cập nhật. Xuất hàng loạt dùng thiết lập hiện tại cho toàn bộ câu trong danh sách.

Video hoàn tất: `output_videos`. Nhật ký lỗi: `logs/app.log`. Ảnh kiểm tra mẫu: `test_renders/verification`.

Chế độ tự động vị trí chữ chỉ là ước lượng theo ảnh mẫu; nếu mặt tượng di chuyển hoặc bị che, đổi sang vị trí thủ công và kiểm tra lại.

Nếu chạy từ mã nguồn hoặc build lại, xem `README.md`. Bản backup GitHub lưu mã nguồn và tài liệu; kho clip và video cá nhân được giữ cục bộ.

Điều chỉnh Y: kéo thanh trượt hoặc nhập số từ −1600 đến +1600 px. Toàn bộ chữ và nguồn vẫn được giữ trong vùng an toàn. Với nội dung có nhiều dòng, ranh giới dòng được ưu tiên; một dòng quá dài nên thêm Enter để dễ đọc.


### Viền chữ mềm

Trong mục vị trí chữ, bật **Viền chữ mềm** để chữ nổi rõ hơn trên nền. Chỉnh **Độ dày viền**, **Độ nhòe ra ngoài**, **Độ đậm viền** và **Màu viền**; viền nhạt dần ra ngoài, nét chữ vẫn sắc. Mặc định màu tự động theo mẫu; chọn màu riêng sẽ tắt chế độ màu tự động. Viền áp dụng cho câu nói và nguồn, được lưu lại và dùng giống nhau khi xem trước hoặc xuất Full HD. Bấm Play để dựng lại sau khi thay đổi.


### Tự lưu và footage không trùng

Mỗi lần sửa chữ (kể cả xuống dòng), chọn câu/clip hoặc chỉnh thiết kế/âm lượng, ứng dụng tự lưu và báo **Đã lưu tự động**. Khi mở lại sẽ khôi phục nội dung, clip và các cài đặt. V5 lưu trong `session_state.json`, nhập thiết lập cũ lần đầu và giữ riêng để các cửa sổ phiên bản cũ không ghi đè.

Footage được dùng luân phiên qua nhiều lần xuất, cả xuất hàng loạt; chỉ dùng lại khi đã đi hết kho. Các file sao chép giống hệt nội dung được tính là một footage. Xem trước không tính lượt; xuất lỗi trả lại lượt. Nếu clip đã chọn đã dùng trước các clip còn lại, ứng dụng tự chọn clip chưa dùng và hiển thị trong kịch bản. Lịch sử lưu ở `footage_usage.json`, không đưa lên GitHub; giữ file này nếu muốn tiếp tục vòng footage khi chuyển máy. Quy tắc có hiệu lực với các lần xuất từ v5.
