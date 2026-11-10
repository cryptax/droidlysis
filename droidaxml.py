#!/usr/bin/env python3
#
# __author__ = "Axelle Apvrille"
# __license__ = "MIT License"
"""
Pure-Python decoder of Android binary XML (AXML) files to text XML.

This replaces the previous dependency on Androguard's ``androaxml.py``:
DroidLysis only ever needed to turn the binary AndroidManifest.xml into a
text manifest, and that can be done with a small AXML parser.

Usage (CLI):
    python3 droidaxml.py --input AndroidManifest.xml --output AndroidManifest.text.xml
"""
import argparse
import os
import struct
import sys

# ResChunk chunk types
RES_STRING_POOL_TYPE         = 0x0001
RES_XML_START_NAMESPACE_TYPE = 0x0100
RES_XML_END_NAMESPACE_TYPE   = 0x0101
RES_XML_START_ELEMENT_TYPE   = 0x0102
RES_XML_END_ELEMENT_TYPE     = 0x0103
RES_XML_TEXT_TYPE            = 0x0104
RES_XML_RESOURCE_MAP_TYPE    = 0x0180

# AXML file magic
AXML_MAGIC = 0x00080003

# String pool flag: strings are UTF-8 (otherwise UTF-16LE)
STRING_POOL_UTF8_FLAG = 0x00000100

# ResXML_tree_attr_value typed value data types
TYPE_NULL        = 0x00
TYPE_REFERENCE   = 0x01
TYPE_ATTRIBUTE   = 0x02
TYPE_STRING      = 0x03
TYPE_FLOAT       = 0x04
TYPE_DIMENSION   = 0x05
TYPE_FRACTION    = 0x06
TYPE_INT_DEC     = 0x10
TYPE_INT_HEX     = 0x11
TYPE_INT_BOOLEAN = 0x12


class AxmlError(Exception):
    """Raised when the file is not a valid AXML document."""


def _utf8_strlen(buf, off):
    """Decode the variable-length UTF-8 string length prefix.

    Returns (length, offset_of_first_string_byte)."""
    b0 = buf[off]
    if b0 < 0x80:
        return b0, off + 1
    length = ((b0 & 0x7F) << 8) | buf[off + 1]
    return length, off + 2


def _read_string_pool(data, pos):
    """Parse the string pool chunk located at ``pos``. Returns the list of strings."""
    string_count  = struct.unpack_from('<I', data, pos + 8)[0]
    flags         = struct.unpack_from('<I', data, pos + 16)[0]
    strings_start = struct.unpack_from('<I', data, pos + 20)[0]
    is_utf8 = bool(flags & STRING_POOL_UTF8_FLAG)

    base = pos + strings_start
    offsets = struct.unpack_from('<%dI' % string_count, data, pos + 28)

    strings = []
    for o in offsets:
        p = base + o
        if is_utf8:
            _, p2 = _utf8_strlen(data, p)
            length, p2 = _utf8_strlen(data, p2)
            strings.append(data[p2:p2 + length].decode('utf-8', 'replace'))
        else:
            length = struct.unpack_from('<H', data, p)[0]
            p += 2
            if length & 0x8000:
                length = ((length & 0x7fff) << 16) | struct.unpack_from('<H', data, p)[0]
                p += 2
            strings.append(data[p:p + length * 2].decode('utf-16-le', 'replace'))
    return strings


def _default_prefix(uri):
    if uri == 'http://schemas.android.com/apk/res/android':
        return 'android'
    if uri.endswith('/res-auto'):
        return 'app'
    return None


def decode(data):
    """Decode AXML, reporting malformed binary input as AxmlError."""
    try:
        return _decode(data)
    except (struct.error, IndexError) as error:
        raise AxmlError("malformed AXML: %s" % error) from error


def _decode(data):
    """Decode an AXML byte string into a text XML string."""
    if len(data) < 8 or struct.unpack_from('<I', data, 0)[0] != AXML_MAGIC:
        raise AxmlError("not an AXML file")

    n = len(data)
    pos = 8  # skip the 8-byte root ResChunk header

    # First chunk must be the string pool.
    strings = _read_string_pool(data, pos)
    pos += struct.unpack_from('<I', data, pos + 4)[0]

    ns_prefix = {}      # uri -> prefix (from START_NAMESPACE chunks)
    ns_ordered = []     # ordered (prefix, uri) for xmlns declarations
    resmap = {}         # resource id -> string index

    def s(idx):
        return strings[idx] if 0 <= idx < len(strings) else ''

    lines = []
    stack = []          # open element local names, for indentation

    while pos + 8 <= n:
        ctype, header_size, chunk_len = struct.unpack_from('<HHI', data, pos)
        if chunk_len < 8 or pos + chunk_len > n or header_size > chunk_len:
            raise AxmlError("invalid XML chunk size")

        if ctype == RES_XML_RESOURCE_MAP_TYPE:
            count = (chunk_len - 8) // 4
            p = pos + 8
            for i in range(count):
                resmap[struct.unpack_from('<I', data, p)[0]] = i
                p += 4

        elif ctype == RES_XML_START_NAMESPACE_TYPE:
            prefix_idx = struct.unpack_from('<i', data, pos + 16)[0]
            uri_idx    = struct.unpack_from('<i', data, pos + 20)[0]
            if prefix_idx >= 0 and uri_idx >= 0:
                prefix, uri = s(prefix_idx), s(uri_idx)
                if uri not in ns_prefix:
                    ns_prefix[uri] = prefix
                    ns_ordered.append((prefix, uri))

        elif ctype == RES_XML_START_ELEMENT_TYPE:
            name_idx   = struct.unpack_from('<i', data, pos + 20)[0]
            ns_idx     = struct.unpack_from('<i', data, pos + 16)[0]
            attr_count = struct.unpack_from('<H', data, pos + 28)[0]
            attr_size  = struct.unpack_from('<H', data, pos + 26)[0]
            if attr_size < 20:
                attr_size = 20

            depth = len(stack)
            prefix = '  ' * depth

            parts = [prefix + '<%s' % s(name_idx)]
            if depth == 0:
                # attach xmlns declarations on the root element
                for pref, uri in ns_ordered:
                    if pref:
                        parts.append(' xmlns:%s="%s"' % (pref, uri))

            attr_base = pos + 16 + struct.unpack_from('<H', data, pos + 24)[0]
            for j in range(attr_count):
                b = attr_base + j * attr_size
                a_ns       = struct.unpack_from('<i', data, b)[0]
                a_name     = struct.unpack_from('<i', data, b + 4)[0]
                data_type  = struct.unpack_from('<B', data, b + 15)[0]
                data_val   = struct.unpack_from('<i', data, b + 16)[0]
                if a_name < 0:
                    continue
                local = s(a_name)
                if a_ns >= 0:
                    uri = s(a_ns)
                    pref = ns_prefix.get(uri) or _default_prefix(uri)
                    if pref:
                        local = '%s:%s' % (pref, local)
                if data_type == TYPE_STRING:
                    value = _escape(s(data_val))
                else:
                    value = _value(data_type, data_val)
                parts.append(' %s="%s"' % (local, value))

            if attr_count == 0 and depth == 0:
                parts.append('>')
            else:
                parts.append('>')
            lines.append(''.join(parts))
            stack.append(s(name_idx))

        elif ctype == RES_XML_END_ELEMENT_TYPE:
            name_idx = struct.unpack_from('<i', data, pos + 20)[0]
            depth = max(len(stack) - 1, 0)
            lines.append('  ' * depth + '</%s>' % s(name_idx))
            if stack:
                stack.pop()

        elif ctype == RES_XML_TEXT_TYPE:
            text_idx = struct.unpack_from('<i', data, pos + 16)[0]
            text = s(text_idx).strip()
            if text:
                depth = len(stack)
                lines.append('  ' * depth + _escape(text))

        pos += chunk_len

    return '<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n' + '\n'.join(lines) + '\n'


def _value(data_type, data_val):
    if data_type == TYPE_REFERENCE:
        return '@0x%08x' % (data_val & 0xffffffff)
    if data_type == TYPE_ATTRIBUTE:
        return '?0x%08x' % (data_val & 0xffffffff)
    if data_type == TYPE_INT_DEC:
        return str(data_val)
    if data_type == TYPE_INT_HEX:
        return '0x%08x' % (data_val & 0xffffffff)
    if data_type == TYPE_INT_BOOLEAN:
        return 'true' if data_val else 'false'
    if data_type == TYPE_FLOAT:
        return repr(struct.unpack('<f', struct.pack('<I', data_val & 0xffffffff))[0])
    # TYPE_DIMENSION, TYPE_FRACTION, and anything else: emit the raw value.
    return str(data_val)


def _escape(v):
    if isinstance(v, int):
        return str(v)
    return (str(v).replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))


def axml_to_text(input_path, output_path=None):
    """Decode the AXML file at ``input_path`` to text XML.

    Writes to ``output_path`` if given. Returns the text XML string.
    """
    with open(input_path, 'rb') as f:
        data = f.read()
    text = decode(data)
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
    return text


def main():
    parser = argparse.ArgumentParser(description='Decode an Android binary XML (AXML) file to text.')
    parser.add_argument('--input', required=True, help='binary AXML file to decode')
    parser.add_argument('--output', help='where to write the text XML (default: stdout)')
    args = parser.parse_args()
    text = axml_to_text(args.input, args.output)
    if not args.output:
        sys.stdout.write(text)


if __name__ == '__main__':
    main()
