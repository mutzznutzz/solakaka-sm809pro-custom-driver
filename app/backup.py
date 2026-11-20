"""Versioned data-only backups. Never execute code or take target paths from a file."""
import copy
import datetime
import json
import math
import pathlib
import uuid
from .persistence import atomic_bytes, atomic_json
from sm809pro import protocol as P

FORMAT = 'sm809pro-control-centre-backup'
MAX_BYTES = 8 * 1024 * 1024


class BackupError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise BackupError(message)


def integer(value, low, high):
    return type(value) is int and low <= value <= high


def rgb(value):
    return isinstance(value, (list, tuple)) and len(value) == 3 and all(integer(v, 0, 255) for v in value)


def validate_config(cfg):
    require(isinstance(cfg, dict), 'Invalid profile settings.')
    buttons = cfg.get('buttons')
    require(isinstance(buttons, list) and len(buttons) == 16, 'A profile must contain 16 button assignments.')
    for binding in buttons:
        if isinstance(binding, dict):
            require(('macro' in binding) != ('runapp' in binding), 'Invalid special button assignment.')
            if 'macro' in binding:
                require(isinstance(binding['macro'], str) and binding.get('playmode', 1) in (1, 2, 4)
                        and integer(binding.get('repeat', 0), 0, 255), 'Invalid macro assignment.')
            else:
                require(isinstance(binding['runapp'], str) and '\0' not in binding['runapp'], 'Invalid app launcher.')
        else:
            require(rgb(binding), 'Invalid button action bytes.')
    if 'wheel' in cfg:
        require(isinstance(cfg['wheel'], list) and len(cfg['wheel']) == 2 and all(rgb(c) for c in cfg['wheel']), 'Invalid wheel mappings.')
    dpi = cfg.get('dpi', {})
    require(isinstance(dpi, dict), 'Invalid DPI settings.')
    values = dpi.get('values', [])
    require(isinstance(values, list) and 1 <= len(values) <= 8 and all(integer(v, 100, 24000) for v in values), 'Invalid DPI stages.')
    colors = dpi.get('colors', [])
    require(isinstance(colors, list) and len(colors) == len(values) and all(rgb(c) for c in colors), 'Invalid DPI colours.')
    count = dpi.get('enabled_count', len(values))
    require(integer(count, 1, len(values)), 'Invalid DPI stage count.')
    indices = dpi.get('enabled_indices', list(range(count)))
    require(isinstance(indices, list) and 1 <= len(indices) <= len(values)
            and all(integer(i, 0, len(values)-1) for i in indices) and len(set(indices)) == len(indices), 'Invalid enabled DPI stages.')
    require(integer(dpi.get('selected', 0), 0, len(values)-1), 'Invalid active DPI stage.')
    require(cfg.get('polling_hz') in (125, 250, 500, 1000), 'Unsupported polling rate.')
    require(cfg.get('lod_mm') in (1, 2), 'Invalid lift-off distance.')
    light = cfg.get('lighting', {})
    require(isinstance(light, dict) and light.get('mode') in P.LIGHTING_MODES and rgb(light.get('color')), 'Invalid lighting preset.')
    power = cfg.get('power', {})
    require(isinstance(power, dict) and integer(power.get('sleep_min'), 0, 30)
            and all(type(power.get(k)) is bool for k in ('move_wakeup', 'move_lighting')), 'Invalid power settings.')
    sensor = cfg.get('sensor', {})
    require(isinstance(sensor, dict) and all(type(sensor.get(k)) is bool for k in ('angle_snap', 'motion_sync', 'ripple')), 'Invalid sensor settings.')


def validate(bundle):
    require(isinstance(bundle, dict) and bundle.get('format') == FORMAT, 'This is not a Control Centre backup.')
    require(type(bundle.get('version')) is int and bundle['version'] == 1, 'Unsupported backup version.')
    data, macros = bundle.get('profiles'), bundle.get('macros')
    require(isinstance(data, dict) and isinstance(macros, list) and len(macros) <= 1000, 'Invalid backup contents.')
    profiles = data.get('profiles')
    require(isinstance(profiles, list) and 1 <= len(profiles) <= 500, 'Invalid profile list.')
    ids = set()
    for profile in profiles:
        require(isinstance(profile, dict) and isinstance(profile.get('id'), str) and bool(profile['id']) and profile['id'] not in ids, 'Invalid or duplicate profile ID.')
        ids.add(profile['id'])
        require(isinstance(profile.get('name'), str), 'Invalid profile name.')
        created = profile.get('created')
        require(created is None or (type(created) in (int, float) and abs(created) <= 2**53 and math.isfinite(created)), 'Invalid profile ordering.')
        rules = profile.get('match_rules', [])
        require(isinstance(rules, list) and len(rules) <= 1000, 'Invalid auto-switch rules.')
        for rule in rules:
            require(isinstance(rule, dict) and all(v is None or isinstance(v, str) for v in rule.values()), 'Invalid auto-switch rule.')
        validate_config(profile.get('config'))
    require(data.get('active') in ids, 'The selected profile is missing.')
    settings = data.get('settings', {})
    require(isinstance(settings, dict), 'Invalid app preferences.')
    for key in ('auto_switch', 'overlay', 'overlay_follow_cursor'):
        require(key not in settings or type(settings[key]) is bool, 'Invalid toggle preference.')
    for key, low, high in [('overlay_opacity', 0, 100), ('overlay_scale', 60, 200), ('overlay_hold', 300, 60000), ('overlay_monitor', 0, 100)]:
        require(key not in settings or integer(settings[key], low, high), 'Invalid overlay preference.')
    require('overlay_show' not in settings or (isinstance(settings['overlay_show'], dict) and all(type(v) is bool for v in settings['overlay_show'].values())), 'Invalid overlay fields.')
    require('overlay_pos' not in settings or isinstance(settings['overlay_pos'], str), 'Invalid overlay position.')
    require('profile_sort' not in settings or isinstance(settings['profile_sort'], str), 'Invalid profile sorting.')
    ids = set()
    for macro in macros:
        require(isinstance(macro, dict) and isinstance(macro.get('id'), str) and bool(macro['id']) and macro['id'] not in ids and isinstance(macro.get('name'), str), 'Invalid macro or duplicate ID.')
        ids.add(macro['id'])
        events = macro.get('events')
        require(isinstance(events, list) and len(events) <= 4096, 'Invalid macro events.')
        for event in events:
            require(isinstance(event, dict) and event.get('type') in ('key', 'mouse', 'consumer', 'delay'), 'Invalid macro event.')
            require(integer(event.get('next_delay', 0), 0, 4095) and integer(event.get('ms', 0), 0, 4095), 'Invalid macro timing.')
            kind = event['type']
            if kind != 'delay':
                require(type(event.get('down', True)) is bool, 'Invalid key state.')
            if kind == 'key':
                require(integer(event.get('keycode'), 0, 255), 'Invalid key usage.')
            if kind == 'mouse':
                require(integer(event.get('button'), 1, 5), 'Invalid mouse action.')
            if kind == 'consumer':
                require(integer(event.get('code', 0), 0, 255), 'Invalid media action.')
    return bundle


def snapshot(profiles, macros):
    return copy.deepcopy(dict(format=FORMAT, version=1,
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        profiles=dict(active=profiles.active_id, profiles=profiles.all(), settings=profiles._settings),
        macros=macros.all()))


def write(path, bundle):
    validate(bundle)
    content = json.dumps(bundle, ensure_ascii=False, allow_nan=False, indent=2).encode('utf-8')
    require(len(content) <= MAX_BYTES, 'Backup is larger than the 8 MB limit.')
    atomic_bytes(path, content)


def read(path):
    try:
        with open(path, 'rb') as stream:
            content = stream.read(MAX_BYTES + 1)
        require(len(content) <= MAX_BYTES, 'Backup is larger than the 8 MB limit.')
        bundle = json.loads(content, parse_constant=lambda value: (_ for _ in ()).throw(BackupError('Invalid numeric value.')))
        return validate(bundle)
    except (UnicodeError, json.JSONDecodeError, TypeError, KeyError, RecursionError) as error:
        raise BackupError('The backup is malformed or incomplete.') from error


def restore(bundle, profiles, macros):
    """Validate first, keep recovery data, roll back disk changes on write failure."""
    validate(bundle)
    targets = [pathlib.Path(profiles.path), pathlib.Path(macros.path)]
    recovery = targets[0].parent / 'backups' / ('before-restore-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6] + '.sm809backup')
    write(recovery, snapshot(profiles, macros))
    originals = [p.read_bytes() if p.exists() else None for p in targets]
    replaced = []
    try:
        for target, payload in zip(targets, [bundle['profiles'], bundle['macros']]):
            atomic_json(target, payload)
            replaced.append(target)
    except Exception:
        for target, original in zip(targets, originals):
            if target in replaced:
                if original is None:
                    target.unlink(missing_ok=True)
                else:
                    atomic_bytes(target, original)
        raise
    profiles.load()
    macros.load()
    return recovery
