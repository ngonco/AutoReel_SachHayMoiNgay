"""Canonical settings; accepts previous camelCase files and percent values."""
DEFAULTS = dict(credit='Thanh Vị Sách Hay Mỗi Ngày', credit_size=20, quote_size=68,
                theme_index=0, pos_mode='auto', vertical_offset=0, shade=.70,
                duration=12, auto_paginate=True, autofit=True, music_volume=.85)
ALIASES = dict(creditSize='credit_size', quoteSize='quote_size', themeIndex='theme_index',
               posMode='pos_mode', verticalOffset='vertical_offset', autoPaginate='auto_paginate',
               musicVolume='music_volume')


def normalize_settings(values=None):
    raw = dict(values or {})
    for old, new in ALIASES.items():
        if old in raw and new not in raw:
            raw[new] = raw[old]
    result = {**DEFAULTS, **{k: v for k, v in raw.items() if k in DEFAULTS}}
    for key, low, high in [('credit_size', 14, 48), ('quote_size', 40, 108), ('theme_index', 0, 4), ('vertical_offset', -350, 350)]:
        result[key] = max(low, min(high, int(result[key])))
    result['duration'] = max(1., min(600., float(result['duration'])))
    for key in ['shade', 'music_volume']:
        value = float(result[key])
        result[key] = max(0., min(1., value / 100 if value > 1 else value))
    for key in ['auto_paginate', 'autofit']:
        result[key] = result[key] if isinstance(result[key], bool) else str(result[key]).lower() in ('true', '1')
    result['credit'] = str(result['credit'] or '').strip()
    if result['pos_mode'] not in ('auto', 'bottom', 'top', 'center'):
        result['pos_mode'] = 'auto'
    return result
