"""Lossless Vietnamese segmentation and frame-aligned reading times."""
import math
import unicodedata
import re


PHRASES = {'hạnh phúc', 'đạo đức', 'yêu thương', 'bình an', 'thành công', 'biết ơn',
           'nhận lỗi', 'vô thường', 'con người', 'tràn ngập', 'phụng sự', 'kiên định',
           'bản thân', 'tỉnh thức', 'gia hộ', 'nỗ lực', 'bình thản', 'phớt lờ',
           'lăng mạ', 'chê bai', 'khinh bỉ', 'thù ghét', 'hiền lành', 'chịu đựng',
           'đổi thay', 'nương tựa', 'tuy nhiên', 'vì vậy', 'do đó', 'mặc dù'}
INCOMPLETE = {'và', 'là', 'của', 'đã', 'được', 'bị', 'những', 'các', 'một', 'về',
              'với', 'cho', 'để', 'khi', 'mà', 'thì', 'sự', 'việc', 'ta', 'nhưng'}
CONNECTORS = [('tuy', 'nhiên'), ('vì', 'vậy'), ('do', 'đó'), ('mặc', 'dù'),
              ('bởi', 'vì'), ('cho', 'nên'), ('vì', 'thế'), ('nhưng',), ('mà',),
              ('và',), ('nên',), ('để',), ('khi',)]
ABBREVIATIONS = {'ts.', 'ths.', 'pgs.', 'gs.', 'tp.', 'q.', 'p.', 'v.v.', 'v.d.', 'mr.', 'mrs.', 'dr.'}


def clean_word(word):
    return word.strip('.,;:!?…“”"\'()[]{}').casefold()


def boundary_penalty(words, end):
    if end >= len(words):
        return 0
    pair = clean_word(words[end - 1]) + ' ' + clean_word(words[end])
    return (120 if pair in PHRASES else 0) + (60 if clean_word(words[end - 1]) in INCOMPLETE else 0)


def sentence_end(word):
    token = word.rstrip('”"\'»)]}')
    if token.casefold() in ABBREVIATIONS or re.fullmatch(r'(?:[A-Za-zĐđ]\.)+', token):
        return False
    return token.endswith(('.', '!', '?', '…'))


def soft_boundaries(words):
    marks = set()
    lowered = [clean_word(w) for w in words]
    for index in range(1, len(words)):
        punct = words[index - 1].rstrip('”"\')]}').endswith((',', ';', ':'))
        matched = next((c for c in CONNECTORS if tuple(lowered[index:index + len(c)]) == c), None)
        # A single connective without punctuation needs a plausible following clause.
        clause = matched and (len(matched) > 1 or matched[0] in {'nhưng', 'mà'} or
                              (index + 1 < len(words) and lowered[index + 1] in
                               {'ta', 'tôi', 'bạn', 'chúng', 'con', 'người', 'hãy', 'đừng', 'mỗi', 'đã', 'biết'}))
        if punct or clause:
            marks.add(index)
    return marks


def split_sentence(words, target):
    """DP chooses meaningful clauses, with a hard 24-token ceiling for long text."""
    n = len(words)
    marks = soft_boundaries(words)
    costs, previous = [0.] + [float('inf')] * n, {}
    for end in range(1, n + 1):
        for size in range(1, min(24, end) + 1):
            start = end - size
            if start and (size < 6 or start < 6):
                continue
            # Leave at least six tokens on each side of a soft split.
            if end < n and n - end < 6:
                continue
            meaningful = end in marks
            cost = 6 + (size - target) ** 2 / 12
            if end < n:
                cost += (-16 if meaningful else 30) + boundary_penalty(words, end)
            if costs[start] + cost < costs[end]:
                costs[end], previous[end] = costs[start] + cost, start
    pieces, cursor = [], n
    while cursor:
        start = previous[cursor]
        pieces.append(' '.join(words[start:cursor]))
        cursor = start
    return pieces[::-1]


def split_into_slides(text, auto_paginate=True, max_words_per_slide=18):
    normalized = unicodedata.normalize('NFC', text or '')
    manual_lines = [' '.join(line.split()) for line in normalized.splitlines() if line.strip()]
    # Explicit Enter boundaries take priority over automatic pagination, including when disabled.
    if len(manual_lines) > 1:
        return manual_lines
    words = normalized.split()
    if not auto_paginate or not words:
        return [' '.join(words)]
    result, start = [], 0
    for end, word in enumerate(words, 1):
        if sentence_end(word) or end == len(words):
            result.extend(split_sentence(words[start:end], min(18, max(6, max_words_per_slide))))
            start = end
    return result


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
