import struct
import unittest
import xml.etree.ElementTree as ET

import droidaxml


class AxmlTest(unittest.TestCase):
    def test_utf8_manifest_with_boolean_and_resource_map(self):
        strings = ['manifest', 'package', 'com.example.café', 'enabled']
        pool = bytearray()
        offsets = []
        for value in strings:
            offsets.append(len(pool))
            encoded = value.encode('utf-8')
            pool.extend(bytes([len(value), len(encoded)]) + encoded + b'\0')
        pool.extend(b'\0' * (-len(pool) % 4))
        start = 28 + 4 * len(strings)
        chunks = [struct.pack('<HHIIIIII', 1, 28, start + len(pool),
                              len(strings), 0, 0x100, start, 0)
                  + struct.pack('<4I', *offsets) + pool]
        chunks.append(struct.pack('<HHII', 0x180, 8, 12, 0x0101000e))
        attributes = (struct.pack('<iiiHBBI', -1, 1, -1, 8, 0, 3, 2)
                      + struct.pack('<iiiHBBI', -1, 3, -1, 8, 0, 0x12, 1))
        chunks.append(struct.pack('<HHIIIiiHHHHHH', 0x102, 16, 76,
                                  1, 0xffffffff, -1, 0, 20, 20, 2, 0, 0, 0)
                      + attributes)
        chunks.append(struct.pack('<HHIIIii', 0x103, 16, 24,
                                  1, 0xffffffff, -1, 0))
        body = b''.join(chunks)
        manifest = ET.fromstring(droidaxml.decode(
            struct.pack('<II', droidaxml.AXML_MAGIC, 8 + len(body)) + body))
        self.assertEqual(manifest.tag, 'manifest')
        self.assertEqual(manifest.get('package'), 'com.example.café')
        self.assertEqual(manifest.get('enabled'), 'true')

    def test_truncated_input(self):
        with self.assertRaises(droidaxml.AxmlError):
            droidaxml.decode(struct.pack('<II', droidaxml.AXML_MAGIC, 8))


if __name__ == '__main__':
    unittest.main()
