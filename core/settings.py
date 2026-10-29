"""Canonical settings; accepts previous camelCase files and percent values."""
DEFAULTS = dict(credit='Thanh Vị Sách Hay Mỗi Ngày', credit_size=20, quote_size=68,
                theme_index=0, pos_mode='auto', vertical_offset=0, shade=.70,
                duration=12, auto_paginate=True, autofit=True, music_volume=.85,
                outline_enabled=True, outline_color='auto', outline_width=4,
                outline_blur=8, outline_opacity=.85,
                quote=None, quote_index=0, video_path='', safe_zone=False, last_save_directory='',
                background_video_directory='', scene_video_preferences={}, imported_video_paths=[],
                music_mode='random',music_path='',music_seed='',scroll_speed=1.)
ALIASES = dict(creditSize='credit_size', quoteSize='quote_size', themeIndex='theme_index',
               posMode='pos_mode', verticalOffset='vertical_offset', autoPaginate='auto_paginate',
               musicVolume='music_volume', outlineEnabled='outline_enabled', outlineColor='outline_color',
               outlineWidth='outline_width', outlineBlur='outline_blur', outlineOpacity='outline_opacity',
               quoteIndex='quote_index', videoPath='video_path', safeZone='safe_zone')


def normalize_settings(values=None):
    raw = dict(values or {})
    for old, new in ALIASES.items():
        if old in raw and new not in raw:
            raw[new] = raw[old]
    result = {**DEFAULTS, **{k: v for k, v in raw.items() if k in DEFAULTS}}
    for key, low, high in [('credit_size', 14, 48), ('quote_size', 40, 108), ('theme_index', 0, 5), ('vertical_offset', -1600, 1600), ('outline_width', 0, 16), ('outline_blur', 0, 24)]:
        result[key] = max(low, min(high, int(result[key])))
    result['duration'] = max(1., min(600., float(result['duration'])))
    import math
    speed = float(result['scroll_speed'])
    if not math.isfinite(speed):
        raise ValueError('Tốc độ chữ không hợp lệ.')
    result['scroll_speed'] = max(.65, min(1.5, speed))
    for key in ['shade', 'music_volume', 'outline_opacity']:
        value = float(result[key])
        result[key] = max(0., min(1., value / 100 if value > 1 else value))
    for key in ['auto_paginate', 'autofit', 'outline_enabled', 'safe_zone']:
        result[key] = result[key] if isinstance(result[key], bool) else str(result[key]).lower() in ('true', '1')
    result['credit'] = str(result['credit'] or '').strip()
    import unicodedata
    result['quote'] = None if result['quote'] is None else unicodedata.normalize('NFC', str(result['quote']))
    if result['quote'] is not None and len(result['quote']) > 20000:
        raise ValueError('Nội dung tối đa 20.000 ký tự.')
    result['quote_index'] = max(0, min(10000, int(result['quote_index'])))
    result['video_path'] = str(result['video_path'] or '')
    result['last_save_directory'] = str(result['last_save_directory'] or '')
    result['background_video_directory'] = str(result['background_video_directory'] or '').strip()
    result['music_mode']=str(result['music_mode'])
    if result['music_mode'] not in ('random','selected','none'):result['music_mode']='random'
    result['music_path']=str(result['music_path'] or '')
    result['music_seed']=str(result['music_seed'] or '')[:100]
    preferences = result['scene_video_preferences']
    if not isinstance(preferences, dict) or len(preferences) > 1000:
        raise ValueError('Gợi ý footage theo cảnh không hợp lệ.')
    result['scene_video_preferences'] = {}
    for index, value in preferences.items():
        if not str(index).isdigit() or int(index) > 999 or not isinstance(value, dict):
            raise ValueError('Gợi ý footage theo cảnh không hợp lệ.')
        result['scene_video_preferences'][str(int(index))] = {
            'path': str(value.get('path') or ''), 'text': str(value.get('text') or '')[:20000]}
    imports = result['imported_video_paths']
    if not isinstance(imports, list) or len(imports) > 1000:
        raise ValueError('Danh sách video thêm riêng không hợp lệ.')
    result['imported_video_paths'] = list(dict.fromkeys(str(p) for p in imports if isinstance(p, str) and p))
    import re
    color = str(result['outline_color']).lower()
    result['outline_color'] = color if color == 'auto' or re.fullmatch(r'#[0-9a-f]{6}', color) else DEFAULTS['outline_color']
    if result['pos_mode'] not in ('auto', 'bottom', 'top', 'center'):
        result['pos_mode'] = 'auto'
    return result


def load_settings(workspace):
    from pathlib import Path
    from core.persistence import read_json
    root=Path(workspace)
    path=root/'session_state.json'
    if not path.is_file():path=root/'settings.json'
    return normalize_settings(read_json(path,dict))


def save_settings_patch(workspace, patch):
    from pathlib import Path
    from core.persistence import file_mutex, read_json, atomic_json
    path=Path(workspace)/'session_state.json'
    import time
    client=str(patch.get('_client_id',''))[:80]
    sequence=int(patch.get('_sequence',0))
    canonical=dict(patch.get('_patch',patch))
    for old,new in ALIASES.items():
        if old in canonical and new not in canonical:canonical[new]=canonical[old]
    with file_mutex(path.with_suffix('.lock')):
        try:existing=read_json(path,lambda:read_json(Path(workspace)/'settings.json',dict))
        except (ValueError,OSError):
            raise ValueError('Không đọc được bản tự lưu. File cũ được giữ để khôi phục.')
        clients=existing.get('_save_clients',{})
        if not isinstance(clients,dict):clients={}
        if client and sequence<=clients.get(client,{}).get('sequence',0):return normalize_settings(existing)
        result=normalize_settings({**existing,**canonical})
        if client:
            clients[client]=dict(sequence=sequence,updated=time.time())
            clients=dict(sorted(clients.items(),key=lambda item:item[1].get('updated',0),reverse=True)[:50])
        atomic_json(path,{**result,'_save_clients':clients})
        return result
