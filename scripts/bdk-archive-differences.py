#!/usr/bin/env python3
"""Locate differences in distributed vs rebuilt Mach-O sections and relocation records."""
from collections import Counter
import argparse
import importlib.util
import json
from pathlib import Path
import struct

spec = importlib.util.spec_from_file_location('archives', Path(__file__).with_name('compare-bdk-archives.py'))
archives = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archives)


def describe(obj):
    magic, cpu, _, kind, commands, command_bytes, _, _ = struct.unpack_from('<8I', obj)
    if (magic, cpu, kind) != (0xfeedfacf, 0x0100000c, 1):
        raise ValueError('Expected arm64 Mach-O object')
    def digest(offset, size):
        if offset + size > len(obj):
            raise ValueError('Object range overflows')
        return archives.sha(obj[offset:offset+size])
    at = 32
    pieces = {}
    for _ in range(commands):
        cmd, length = struct.unpack_from('<II', obj, at)
        if length < 8 or at + length > 32 + command_bytes or at + length > len(obj):
            raise ValueError('Invalid load command')
        if cmd == 0x19:
            count, = struct.unpack_from('<I', obj, at+64)
            if length != 72 + 80 * count:
                raise ValueError('Invalid segment')
            for j in range(count):
                sect, seg, _, size, off, _, reloc, nreloc, flags = struct.unpack_from('<16s16sQQIIIII', obj, at+72+j*80)
                label = ','.join(x.rstrip(b'\0').decode('ascii') for x in (seg, sect))
                if label in pieces:
                    raise ValueError('Duplicate section')
                # Zero-fill and thread-local zero-fill do not occupy object file bytes.
                zero_fill = (flags & 255) in (1, 12, 18)
                payload = None if zero_fill else digest(off, size)
                pieces[label] = {'size': size, 'flags': flags, 'data': payload, 'relocations': digest(reloc, 8*nreloc)}
        elif cmd == 2:
            symoff, count, stroff, size = struct.unpack_from('<4I', obj, at+8)
            pieces['symbol table'] = digest(symoff, count*16)
            pieces['string table'] = digest(stroff, size)
        at += length
    if at != 32 + command_bytes:
        raise ValueError('Incomplete load commands')
    pieces['header and load commands'] = digest(0, at)
    return pieces


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ('published', 'rebuilt', 'comparison', 'output'):
        parser.add_argument(arg, type=Path)
    a = parser.parse_args()
    trace = json.loads(a.comparison.read_bytes())
    views = []
    for field, path in [('published', a.published), ('rebuilt', a.rebuilt)]:
        data = path.read_bytes()
        if archives.sha(data) != trace[field]['sha256']:
            raise ValueError('Archive identity differs from member comparison')
        view = dict(archives.payloads(data))
        if len(view) != len(trace[field]['members']):
            raise ValueError('Duplicate or missing archive member')
        views.append(view)
    left, right = views
    # SDK or checkout changes may alter the cc crate's object-name prefixes.
    # Report unpaired names explicitly instead of matching by a common suffix.
    missing = sorted(left.keys() - right.keys())
    added = sorted(right.keys() - left.keys())
    rows = []
    categories = Counter()
    for name, obj in left.items():
        if name not in right:
            continue
        other = right[name]
        if obj == other:
            continue
        old, new = describe(obj), describe(other)
        changes = {}
        for key in sorted(old.keys() | new.keys()):
            if old.get(key) == new.get(key):
                continue
            if isinstance(old.get(key), dict) and isinstance(new.get(key), dict):
                for field in old[key]:
                    if old[key][field] != new[key][field]:
                        changes[key+'/'+field] = [old[key][field], new[key][field]]
            else:
                changes[key] = [old.get(key), new.get(key)]
        categories.update(changes.keys())
        rows.append({'member': name, 'differences': changes})
    a.output.write_text(json.dumps(dict(archives={k: trace[k]['sha256'] for k in ('published','rebuilt')},
        published_members=len(left), rebuilt_members=len(right), matching_names=len(left)-len(missing),
        published_only=missing, rebuilt_only=added, nonidentical_same_name_members=len(rows), same_member_order=list(left)==list(right),
        mismatching_members_by_component=dict(sorted(categories.items())), members=rows,
        scope='Raw section bytes and relocation records, symbols, strings, headers and load commands. Offsets, padding, archive headers and global symbol index are not normalized; equality of listed components alone does not establish archive equality.'), indent=2)+'\n')
    print(len(rows), 'non-identical members out of', len(left))

if __name__ == '__main__':
    main()
