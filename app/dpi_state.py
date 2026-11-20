"""Map sparse screen rows to compact firmware stages; no device I/O."""


def enabled_indices(dpi):
    values = dpi.get('values', [])
    indices = dpi.get('enabled_indices')
    if indices is None:
        indices = range(min(len(values), dpi.get('enabled_count', len(values))))
    valid = sorted({i for i in indices if isinstance(i, int) and 0 <= i < min(8, len(values))})
    return valid or ([0] if values else [])


def wire_config(dpi):
    indices = enabled_indices(dpi)
    values = dpi.get('values', [])
    colors = dpi.get('colors', [])
    selected = dpi.get('selected', 0)
    return ([values[i] for i in indices],
            [colors[i] if i < len(colors) else [255, 255, 255] for i in indices],
            indices.index(selected) if selected in indices else 0)
