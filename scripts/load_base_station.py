#!/usr/bin/env python3
"""Resolve the RTK base station position for provisioning — READ ONLY.

Prefers config/base_station.local.yaml (your private, git-ignored file);
falls back to base_station.yaml.example. If only the placeholder example is
present, prints a loud reminder and exits 2 — it never touches hardware.

Usage:  python3 scripts/load_base_station.py
Exit:   0 = a real fixed position resolved (UBX values printed)
        2 = base position not set yet (edit base_station.local.yaml)
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL = os.path.join(HERE, 'config', 'base_station.local.yaml')
EXAMPLE = os.path.join(HERE, 'config', 'base_station.yaml.example')


def _tiny_yaml(path):
    """Minimal nested key: value reader — no PyYAML dependency."""
    stack = [(-1, {})]
    root = stack[0][1]
    for raw in open(path, encoding='utf-8'):
        line = raw.split('#', 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        key, _, val = line.strip().partition(':')
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        val = val.strip()
        if val == '':
            node = {}
            parent[key] = node
            stack.append((indent, node))
        else:
            parent[key] = val
    return root


def main():
    path = LOCAL if os.path.exists(LOCAL) else EXAMPLE
    data = _tiny_yaml(path)
    bs = data.get('base_station', {})
    lat = str(bs.get('latitude_deg', ''))
    if path == EXAMPLE or lat.startswith('FIXME') or not re.match(r'-?\d', lat):
        sys.stderr.write(
            'RTK base position is NOT set.\n'
            '  Copy config/base_station.yaml.example -> config/base_station.local.yaml\n'
            '  and enter your surveyed base position (see the file for how).\n')
        return 2
    lon = str(bs.get('longitude_deg'))
    hgt = str(bs.get('height_m'))
    print('RTK base (from %s):' % os.path.basename(path))
    print('  lat %s deg  lon %s deg  height %s m' % (lat, lon, hgt))
    print('  UBX: CFG_TMODE_LAT %d  CFG_TMODE_LON %d  CFG_TMODE_HEIGHT %d'
          % (round(float(lat) * 1e7), round(float(lon) * 1e7),
             round(float(hgt) * 100)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
