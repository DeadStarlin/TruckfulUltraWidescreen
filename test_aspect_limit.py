import struct
import unittest

from aspect_limit import CAMERA_PATTERN, find_aspect_offset


def fixture(data_rva=0x3000):
    binary = bytearray(0x600)
    binary[:2] = b"MZ"
    struct.pack_into("<I", binary, 60, 0x80)
    binary[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<H", binary, 0x86, 2)
    struct.pack_into("<IIII", binary, 0x98 + 8, 0x200, 0x1000, 0x200, 0x200)
    struct.pack_into("<IIII", binary, 0xC0 + 8, 0x200, data_rva, 0x200, 0x400)
    binary[0x220:0x220 + len(CAMERA_PATTERN)] = CAMERA_PATTERN
    displacement = 0x220 + len(CAMERA_PATTERN)
    struct.pack_into("<i", binary, displacement, data_rva + 0x40 - (0x1000 + displacement - 0x200 + 4))
    binary[0x248:0x24C] = bytes.fromhex("f30f5e05")
    struct.pack_into("<i", binary, 0x24C, data_rva + 0x44 - 0x1050)
    struct.pack_into("<ff", binary, 0x440, 16 / 9, 1.6)
    return binary


class AspectLimitTests(unittest.TestCase):
    def test_relocated_data(self):
        for address in (0x3000, 0x9000):
            self.assertEqual(find_aspect_offset(fixture(address)), 0x440)

    def test_missing_or_duplicate_reference(self):
        binary = fixture()
        binary[0x220] = 0
        with self.assertRaises(RuntimeError):
            find_aspect_offset(binary)
        with self.assertRaises(RuntimeError):
            find_aspect_offset(fixture() + CAMERA_PATTERN)

    def test_wrong_minimum(self):
        binary = fixture()
        struct.pack_into("<f", binary, 0x444, 2)
        with self.assertRaises(RuntimeError):
            find_aspect_offset(binary)

    def test_bad_binary(self):
        with self.assertRaises(RuntimeError):
            find_aspect_offset(b"not a game binary")


if __name__ == "__main__":
    unittest.main()
