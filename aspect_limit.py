"""Locate the aspect limit by its camera-code reference, rather than a fixed RVA."""
import math
import struct

# Cached screen width/height stores followed by a RIP-relative aspect multiply.
CAMERA_PATTERN = bytes.fromhex("4489b38400000089ab88000000f30f5905")


def find_aspect_offset(binary):
    if len(binary) < 64 or binary[:2] != b"MZ":
        raise RuntimeError("GameAssembly.dll is not a PE binary.")
    pe = struct.unpack_from("<I", binary, 60)[0]
    if pe + 24 > len(binary) or binary[pe:pe + 4] != b"PE\0\0":
        raise RuntimeError("Invalid PE header.")
    count = struct.unpack_from("<H", binary, pe + 6)[0]
    optional_size = struct.unpack_from("<H", binary, pe + 20)[0]
    headers = pe + 24 + optional_size
    if not count or headers + count * 40 > len(binary):
        raise RuntimeError("Invalid PE section table.")
    sections = [struct.unpack_from("<IIII", binary, headers + i * 40 + 8) for i in range(count)]

    def file_to_rva(offset):
        for size, address, raw_size, raw_address in sections:
            if raw_address <= offset < raw_address + min(size, raw_size):
                return address + offset - raw_address
        raise RuntimeError("Camera reference is outside a PE section.")

    def rva_to_file(rva):
        for size, address, raw_size, raw_address in sections:
            if address <= rva and rva + 4 <= address + min(size, raw_size):
                offset = raw_address + rva - address
                if offset + 4 <= len(binary):
                    return offset
        raise RuntimeError("Aspect constant is outside the binary's mapped data.")

    start = binary.find(CAMERA_PATTERN)
    if start < 0 or binary.find(CAMERA_PATTERN, start + 1) >= 0:
        raise RuntimeError("Expected one camera aspect-limit reference; this game build needs inspection.")
    displacement = start + len(CAMERA_PATTERN)
    if displacement + 4 > len(binary):
        raise RuntimeError("Truncated camera aspect reference.")
    maximum = rva_to_file(file_to_rva(displacement + 3) + 1 + struct.unpack_from("<i", binary, displacement)[0])

    # The same calculation also divides by the game's 1.6 minimum aspect ratio.
    divide = binary.find(bytes.fromhex("f30f5e05"), displacement + 4, start + 80)
    if divide < 0 or divide + 8 > len(binary):
        raise RuntimeError("Camera minimum-aspect calculation was not found.")
    minimum = rva_to_file(file_to_rva(divide + 7) + 1 + struct.unpack_from("<i", binary, divide + 4)[0])
    if not math.isclose(struct.unpack_from("<f", binary, minimum)[0], 1.6, rel_tol=1e-7):
        raise RuntimeError("Unexpected camera minimum aspect ratio; refusing to patch.")
    return maximum
