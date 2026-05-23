from pathlib import Path
import struct, zlib, gzip, io

# Minimal NBT writer helpers
TAG_End = 0
TAG_Byte = 1
TAG_Int = 3
TAG_Long = 4
TAG_String = 8
TAG_Compound = 10

def write_tag_header(buf, tag_type, name):
    buf.write(bytes([tag_type]))
    encoded = name.encode("utf-8")
    buf.write(struct.pack(">H", len(encoded)))
    buf.write(encoded)

def write_string_payload(buf, s):
    b = s.encode("utf-8")
    buf.write(struct.pack(">H", len(b)))
    buf.write(b)

def make_minimal_chunk_nbt():
    """
    Very small legacy-style chunk NBT.
    Not a full playable world, but a structurally valid MCA chunk payload.
    """
    buf = io.BytesIO()

    # Root compound ""
    write_tag_header(buf, TAG_Compound, "")

    # Compound "Level"
    write_tag_header(buf, TAG_Compound, "Level")

    # xPos
    write_tag_header(buf, TAG_Int, "xPos")
    buf.write(struct.pack(">i", 0))

    # zPos
    write_tag_header(buf, TAG_Int, "zPos")
    buf.write(struct.pack(">i", 0))

    # LastUpdate
    write_tag_header(buf, TAG_Long, "LastUpdate")
    buf.write(struct.pack(">q", 0))

    # TerrainPopulated
    write_tag_header(buf, TAG_Byte, "TerrainPopulated")
    buf.write(b"\x01")

    # End Level compound
    buf.write(bytes([TAG_End]))

    # End root compound
    buf.write(bytes([TAG_End]))

    return buf.getvalue()

# Create compressed chunk payload
nbt_data = make_minimal_chunk_nbt()
compressed = zlib.compress(nbt_data)

# Chunk format:
# length (4 bytes, includes compression byte)
# compression type (1 byte: 2 = zlib)
# compressed data
chunk_payload = struct.pack(">I", len(compressed) + 1) + b"\x02" + compressed

# Pad to sector size (4096)
sector_size = 4096
chunk_sectors = (len(chunk_payload) + sector_size - 1) // sector_size
chunk_payload_padded = chunk_payload.ljust(chunk_sectors * sector_size, b"\x00")

# Region file:
# 4096-byte location table
# 4096-byte timestamp table
# chunk data sectors

locations = bytearray(4096)
timestamps = bytearray(4096)

# Put chunk (0,0) at sector 2
sector_offset = 2
locations[0:4] = bytes([
    (sector_offset >> 16) & 0xFF,
    (sector_offset >> 8) & 0xFF,
    sector_offset & 0xFF,
    chunk_sectors
])

region_data = bytes(locations) + bytes(timestamps) + chunk_payload_padded

out_path = Path("/mnt/data/r.0.0.mca")
out_path.write_bytes(region_data)

print(f"Created minimal Minecraft region file: {out_path}")
print(f"Size: {out_path.stat().st_size} bytes")
