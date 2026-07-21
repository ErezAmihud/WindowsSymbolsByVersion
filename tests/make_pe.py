"""Build a minimal PE32+ file with an optional CodeView (RSDS) debug entry.

Used by the tests to generate deterministic inputs for pdb_finding.py without
shipping real Windows binaries in the repo.
"""

import struct
import uuid

SECTION_RVA = 0x1000
SECTION_FILE_OFFSET = 0x200
DEBUG_DIR_SIZE = 28


def make_pe(
    pdb_name: str | None = None, guid: uuid.UUID | None = None, age: int = 1
) -> bytes:
    cv_blob = b""
    debug_dir = b""
    if pdb_name is not None:
        guid = guid or uuid.uuid4()
        cv_blob = (
            b"RSDS"
            + guid.bytes_le
            + struct.pack("<I", age)
            + pdb_name.encode("ascii")
            + b"\x00"
        )
        debug_dir = struct.pack(
            "<IIHHIIII",
            0,  # Characteristics
            0,  # TimeDateStamp
            0,
            0,  # Major/MinorVersion
            2,  # Type = IMAGE_DEBUG_TYPE_CODEVIEW
            len(cv_blob),
            SECTION_RVA + DEBUG_DIR_SIZE,  # AddressOfRawData
            SECTION_FILE_OFFSET + DEBUG_DIR_SIZE,  # PointerToRawData
        )

    dos_header = b"MZ" + b"\x00" * 58 + struct.pack("<I", 64)
    coff = b"PE\x00\x00" + struct.pack(
        "<HHIIIHH",
        0x8664,  # Machine: amd64
        1,  # NumberOfSections
        0,  # TimeDateStamp
        0,
        0,  # symbols
        240,  # SizeOfOptionalHeader
        0x2022,  # EXECUTABLE | DLL | LARGE_ADDRESS_AWARE
    )
    optional_header = struct.pack(
        "<HBBIIIII",
        0x20B,  # PE32+
        14,
        0,  # linker version
        0,  # SizeOfCode
        0x200,  # SizeOfInitializedData
        0,  # SizeOfUninitializedData
        0,  # AddressOfEntryPoint
        SECTION_RVA,  # BaseOfCode
    ) + struct.pack(
        "<QIIHHHHHHIIIIHHQQQQII",
        0x180000000,  # ImageBase
        0x1000,  # SectionAlignment
        0x200,  # FileAlignment
        6,
        0,  # OS version
        0,
        0,  # image version
        6,
        0,  # subsystem version
        0,  # Win32VersionValue
        0x2000,  # SizeOfImage
        0x200,  # SizeOfHeaders
        0,  # CheckSum
        3,  # Subsystem: console
        0,  # DllCharacteristics
        0x100000,
        0x1000,
        0x100000,
        0x1000,  # stack/heap
        0,  # LoaderFlags
        16,  # NumberOfRvaAndSizes
    )
    data_directories = [(0, 0)] * 16
    if debug_dir:
        data_directories[6] = (SECTION_RVA, DEBUG_DIR_SIZE)
    optional_header += b"".join(
        struct.pack("<II", rva, size) for rva, size in data_directories
    )

    section_header = struct.pack(
        "<8sIIIIIIHHI",
        b".rdata",
        0x200,  # VirtualSize
        SECTION_RVA,
        0x200,  # SizeOfRawData
        SECTION_FILE_OFFSET,
        0,
        0,
        0,
        0,  # relocations/linenumbers
        0x40000040,  # INITIALIZED_DATA | READ
    )

    headers = dos_header + coff + optional_header + section_header
    headers += b"\x00" * (SECTION_FILE_OFFSET - len(headers))
    section = debug_dir + cv_blob
    section += b"\x00" * (0x200 - len(section))
    return headers + section


def expected_signature_string(guid: uuid.UUID, age: int) -> str:
    """The Signature_String pefile derives from an RSDS entry (symbol-server id)."""
    return f"{guid.hex.upper()}{age:X}"
