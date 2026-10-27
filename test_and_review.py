# -*- coding: utf-8 -*-
"""
test_and_review.py - Tự động kết xuất 4 video mẫu khác nhau theo 4 phong cách và trích xuất ảnh để tự xem lại và đánh giá.
"""

import os
import sys
import subprocess
import time

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from core.pmdx_reader import get_all_quotes
from core.video_detector import VideoDetector
from core.renderer import render_reel_video

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    quotes = get_all_quotes(base_dir)
    detector = VideoDetector(base_dir)
    videos = detector.scan_all_videos()

    v_map = {v['name']: v['path'] for v in videos}

    test_cases = [
        {
            "id": "Test_01_ThienVang",
            "quote": quotes[0]['quote'], # Hạnh phúc không phải đến từ việc yêu thương bản thân...
            "video_name": "IMG_3381.MOV",
            "theme": 0, # Thiền Vàng
            "duration": 12.0
        },
        {
            "id": "Test_02_TinhKhoi",
            "quote": quotes[1]['quote'], # Hãy nhường phần tốt cho người khác...
            "video_name": "IMG_4037.MOV",
            "theme": 1, # Tinh Khôi
            "duration": 12.0
        },
        {
            "id": "Test_03_KinhDien",
            "quote": quotes[6]['quote'], # Dù cho người khác có đối xử không tốt với ta...
            "video_name": "IMG_4087.MOV",
            "theme": 2, # Kinh Điển
            "duration": 12.0
        },
        {
            "id": "Test_04_DienAnh",
            "quote": quotes[9]['quote'], # Đạo đức là nhân, tài năng là quả...
            "video_name": "IMG_4089.MOV",
            "theme": 3, # Điện Ảnh
            "duration": 12.0
        }
    ]

    out_dir = os.path.join(base_dir, "output_videos")
    review_dir = os.path.join(base_dir, "test_renders")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(review_dir, exist_ok=True)

    print("=" * 65)
    print("✦ BẮT ĐẦU KẾT XUẤT 4 VIDEO MẪU ĐỂ TỰ XEM LẠI VÀ ĐÁNH GIÁ MỸ THUẬT")
    print("=" * 65)

    for tc in test_cases:
        v_name = tc["video_name"]
        v_path = v_map.get(v_name)
        if not v_path or not os.path.exists(v_path):
            print(f"[Bỏ qua] Không tìm thấy video {v_name}")
            continue

        out_mp4 = os.path.join(out_dir, f"{tc['id']}.mp4")
        print(f"\n▶ Đang render {tc['id']}: Theme {tc['theme']} trên video {v_name}...")
        t0 = time.time()
        res = render_reel_video(
            background_video_path=v_path,
            quote_text=tc["quote"],
            theme_index=tc["theme"],
            pos_mode="auto",
            duration=tc["duration"],
            auto_paginate=True,
            output_path=out_mp4,
            workspace_dir=base_dir
        )
        print(f"   -> Kết quả: {res['success']} ({res['elapsed']}s). Vị trí chữ AI chọn: {res['resolved_pos']}")

        if res['success']:
            # Trích xuất 2 frame tại 3.0s và 8.5s để tự xem lại
            f1 = os.path.join(review_dir, f"{tc['id']}_slide1.jpg")
            f2 = os.path.join(review_dir, f"{tc['id']}_slide2.jpg")
            subprocess.run(["ffmpeg", "-y", "-ss", "3.0", "-i", out_mp4, "-vframes", "1", f1], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["ffmpeg", "-y", "-ss", "8.5", "-i", out_mp4, "-vframes", "1", f2], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"   -> Đã trích xuất ảnh đánh giá: {os.path.basename(f1)} & {os.path.basename(f2)}")

    print("\n" + "=" * 65)
    print("✦ HOÀN TẤT KẾT XUẤT TẤT CẢ VIDEO MẪU!")
    print("=" * 65)

if __name__ == '__main__':
    main()
