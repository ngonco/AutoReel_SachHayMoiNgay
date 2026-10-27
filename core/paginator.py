"""Lossless Vietnamese segmentation and frame-aligned reading times."""
import math
import unicodedata


def split_into_slides(text, auto_paginate=True, max_words_per_slide=18):
    normalized = unicodedata.normalize('NFC', text or '')
    manual_lines = [' '.join(line.split()) for line in normalized.splitlines() if line.strip()]
    # Explicit Enter boundaries take priority over automatic pagination, including when disabled.
    if len(manual_lines) > 1:
        return manual_lines
    words = normalized.split()
    if not auto_paginate or len(words) <= max_words_per_slide:
        return [' '.join(words)]
    # Avoid breaking common Vietnamese phrases or leaving function words at a scene end.
    phrases = {'hạnh phúc', 'đạo đức', 'yêu thương', 'bình an', 'thành công', 'biết ơn', 'nhận lỗi', 'vô thường', 'con người', 'tràn ngập', 'phụng sự', 'kiên định', 'bản thân', 'tỉnh thức', 'gia hộ', 'nỗ lực', 'bình thản', 'phớt lờ', 'lăng mạ', 'chê bai', 'khinh bỉ', 'thù ghét', 'hiền lành', 'chịu đựng', 'đổi thay', 'nương tựa'}
    incomplete = {'và', 'là', 'của', 'đã', 'được', 'bị', 'những', 'các', 'một', 'về', 'với', 'cho', 'để', 'khi', 'mà', 'thì', 'sự', 'việc', 'ta'}
    costs, previous = [0.] + [float('inf')] * len(words), {}
    for end in range(1, len(words) + 1):
        for size in range(1, min(24, end) + 1):
            start = end - size
            boundary = words[end - 1].rstrip('”\"').endswith(('.', '!', '?', ';', ':', ','))
            cost = (size - 16) ** 2 / 8 + (0 if boundary or end == len(words) else 18)
            if end < len(words):
                pair = (words[end - 1] + ' ' + words[end]).lower()
                if pair in phrases or (not boundary and words[end - 1].lower() in incomplete):
                    cost += 80
            if size < 6:
                cost += 80
            if costs[start] + cost < costs[end]:
                costs[end], previous[end] = costs[start] + cost, start
    pieces, cursor = [], len(words)
    while cursor:
        start = previous[cursor]
        pieces.append(' '.join(words[start:cursor]))
        cursor = start
    return pieces[::-1]


def calculate_slide_timings(slides, total_duration=12.):
    if not slides or not any(s.strip() for s in slides):
        raise ValueError('Hãy nhập nội dung câu nói trước khi dựng reel.')
    frames = [math.ceil(max(4., len(s.split()) / 3 + .8) * 30) for s in slides]
    extra = max(0, math.ceil(float(total_duration) * 30) - sum(frames))
    weights = [max(1, len(s.split())) for s in slides]
    assigned = 0
    for i in range(len(frames)):
        addition = extra - assigned if i == len(frames) - 1 else int(extra * weights[i] / sum(weights))
        frames[i] += addition
        assigned += addition
    cursor, result = 0, []
    for i, (text, count) in enumerate(zip(slides, frames)):
        # Backgrounds overlap 12 frames, text switches at the midpoint.
        scene_start = cursor - (6 if i else 0)
        scene_end = cursor + count + (6 if i < len(slides) - 1 else 0)
        result.append(dict(slide_index=i, text=text, start=scene_start / 30,
                           end=scene_end / 30, text_start=cursor / 30,
                           text_end=(cursor + count) / 30, fade_in=.2, fade_out=.2))
        cursor += count
    return result
