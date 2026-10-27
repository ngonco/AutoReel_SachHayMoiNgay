# -*- coding: utf-8 -*-
"""
pmdx_reader.py - Trình đọc danh sách câu nói từ New PlanMaker document.pmdx hoặc excel/txt.
"""

import os
import zipfile
import unicodedata
import xml.etree.ElementTree as ET

def _norm(s):
    return unicodedata.normalize('NFC', s.strip()) if s else ""

DEFAULT_QUOTES = [
    _norm(q) for q in [
        "Hạnh phúc không phải đến từ việc yêu thương bản thân, mà là kết quả của việc ta đã yêu thương con người rất nhiều và đã nỗ lực mang hạnh phúc đến cho con người.",
        "Hãy nhường phần tốt cho người khác và dành phần kém về mình. Hãy nhường danh dự, lời khen cho người khác và dành sự chỉ trích lại cho mình.",
        "Suốt cuộc đời tất bật lo toan phụng sự cho mọi người, đến một lúc nào đó, chúng ta sẽ thấy cuộc đời mình tràn ngập niềm vui.",
        "Nếu chúng ta càng được người khác bao bọc yêu thương. Thì chúng ta càng phải cố gắng sống cho thật xứng đáng với tình yêu thương đó.",
        "Cả một đời ta được học qua rất nhiều Thầy Cô giáo nên không thể nhớ hết, không thể đền ơn hết. Nhưng mong rằng trong trái tim ta, bất cứ Thầy Cô nào cũng tràn đầy ân nghĩa.",
        "Khi thấy người khác thành công thì hãy cứ vui mừng. Rồi sau này sự thành công đó sẽ trở lại nơi chính mình.",
        "Dù cho người khác có đối xử không tốt với ta, nhưng hãy đáp lại bằng tình thương chân thành. Chính tình thương này sẽ xoá tan những mầm mống hiềm hận nhỏ nhặt khác.",
        "Mọi chuyện trên đời đều là vô thường, mong manh, bất trắc, lòng người cũng dễ đổi thay, chỉ có Phước mới thật sự là chỗ nương tựa vững vàng",
        "Ít ai có thể phớt lờ khi bị người khác chửi mắng. Chỉ những người tu đến mức không thấy mình quan trọng nữa và luôn nhận lỗi về mình mới có thể bình thản trước sự lăng mạ của người khác.",
        "Đạo đức là nhân, tài năng là quả. Người có đạo đức rồi từ từ sẽ có tài năng. Còn người có tài năng mà đánh mất đạo đức rồi từ từ tài năng ấy sẽ tan vỡ.",
        "Tất cả sự lãng phí dù là nhỏ nhặt đều làm thành cái tội cho chúng ta",
        "Người biết nhặt rác là người biết giữ gìn đạo đức từng chút một.",
        "Hãy yêu việc mình đang làm, đừng trông ngóng chờ đợi để được làm việc mình yêu.",
        "Nếu có một ngày tất cả mọi người đều chê bai, khinh bỉ, thù ghét con, thì xin Phật gia hộ cho con đón nhận được tất cả sự chê bai, khinh bỉ, thù ghét ấy trong sự bình an, tha thứ, thương yêu.",
        "Người hiền lành có đạo đức sẽ là người kiên định giữa đúng và sai.",
        "Hoá ra bản lĩnh của người có đạo đức là chịu đựng được cái xấu của người khác. Ta chịu đựng được cái xấu của người khác đến đâu thì mức độ đạo đức của ta đến đấy."
    ]
]

def load_pmdx_quotes(file_path):
    """Đọc file PMDX dạng OpenXML zip và lấy danh sách chuỗi."""
    if not os.path.exists(file_path):
        return []
    try:
        with zipfile.ZipFile(file_path, 'r') as z:
            if 'xl/sharedStrings.xml' in z.namelist():
                content = z.read('xl/sharedStrings.xml')
                root = ET.fromstring(content)
                ns = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                strings = []
                for elem in root.findall('.//x:si', ns):
                    text_parts = [t.text for t in elem.findall('.//x:t', ns) if t.text]
                    full_text = "".join(text_parts).strip()
                    if full_text:
                        strings.append(_norm(full_text))
                if strings:
                    return strings
    except Exception as e:
        print(f"[PMDX Reader] Lỗi đọc file {file_path}: {e}")
    return []

def get_all_quotes(workspace_dir=None):
    """
    Trả về danh sách câu nói chuẩn bị cho Reels.
    Tìm kiếm file PMDX trong workspace_dir hoặc sử dụng danh sách chuẩn.
    """
    default_credit = "Thanh Vị Sách Hay Mỗi Ngày"
    if workspace_dir:
        candidates = [
            os.path.join(workspace_dir, "New PlanMaker document.pmdx"),
            os.path.join(workspace_dir, "quotes.txt"),
            os.path.join(workspace_dir, "quotes.xlsx"),
        ]
        for p in candidates:
            if os.path.exists(p) and p.endswith('.pmdx'):
                quotes = load_pmdx_quotes(p)
                if quotes:
                    return [
                        {"id": i + 1, "quote": _norm(q), "credit": default_credit}
                        for i, q in enumerate(quotes)
                    ]
            elif os.path.exists(p) and p.endswith('.txt'):
                try:
                    with open(p, 'r', encoding='utf-8') as f:
                        lines = [line.strip() for line in f if line.strip()]
                    if lines:
                        return [
                            {"id": i + 1, "quote": _norm(q), "credit": default_credit}
                            for i, q in enumerate(lines)
                        ]
                except Exception:
                    pass

    return [
        {"id": i + 1, "quote": q, "credit": default_credit}
        for i, q in enumerate(DEFAULT_QUOTES)
    ]
