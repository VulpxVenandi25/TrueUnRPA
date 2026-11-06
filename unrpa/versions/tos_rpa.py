import struct
import zlib
from typing import BinaryIO, Optional, Tuple, Type

from unrpa.view import ArchiveView
from unrpa.versions.version import HeaderBasedVersion, Version


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    """Repeat a byte-wise XOR mask over the data."""
    n = len(key)
    return bytes(b ^ key[i % n] for i, b in enumerate(data))


class TOSBase(HeaderBasedVersion):
    """Common machinery for the custom "TOS-*" archives shipped with some
    Ren'Py based games (e.g. Tavern of Spear).

    Layout of an archive::

        "TOS-B1\\r\\n" <u32LE size> <obfuscated blob B>
        "TOS-M1\\r\\n" <u32LE size> <obfuscated blob M>

    Both blobs are zlib streams once deobfuscated; which one holds the RPA
    index pickle and which one holds the file data is decided after parsing
    the first successful decompression.
    """

    block_terminators = (b"TOS-B1\r\n", b"TOS-M1\r\n")

    def find_offset_and_key(self, archive: BinaryIO) -> Tuple[int, Optional[int]]:
        # Not used directly; this version overrides get_index() instead.
        raise NotImplementedError(
            f"{self.name} archives must be read through UnRPA.get_index()."
        )

    @staticmethod
    def _read_blocks(archive: BinaryIO):
        archive.seek(0)
        blocks = []
        while True:
            header_line = archive.readline()
            if not header_line:
                break
            magic = header_line.rstrip(b"\r\n")
            if not magic.startswith(b"TOS-"):
                break
            raw_size = archive.read(4)
            if len(raw_size) != 4:
                break
            (size,) = struct.unpack("<I", raw_size)
            payload = archive.read(size)
            blocks.append((magic, payload))
        return blocks

    @staticmethod
    def _try_decompress(payload: bytes) -> Optional[bytes]:
        """Attempt to recover the zlib stream from an obfuscated payload.

        The payloads are stored as ``<u32LE compressed-size><zlib stream>``,
        wrapped in a repeating XOR mask derived from the game's obfuscation
        key. Because the outer u32LE size field is small (< 2**24), its most
        significant byte is always zero, which leaks part of the keystream.
        Combined with the known zlib CMF byte (0x78) at offset 4, candidate
        masks can be reconstructed and verified by attempting decompression.
        """
        # Known plaintext structure: [S0 S1 S2 0x00 0x78 FLG ...]
        candidates = []

        def make_key(length: int) -> Optional[bytearray]:
            if length < 6:
                return None
            key = bytearray(length)
            # Position of leaked keystream bytes within one period.
            pos_hi = 3 % length
            pos_cmf = 4 % length
            pos_flg = 5 % length
            if len({pos_hi, pos_cmf, pos_flg}) != 3:
                return None
            key[pos_hi] = payload[3]
            key[pos_cmf] = payload[4] ^ 0x78
            for flg in (0x01, 0x5E, 0x9C, 0xDA):
                k = bytearray(key)
                k[pos_flg] = payload[5] ^ flg
                candidates.append(bytes(k))
            return None

        for length in range(6, 65):
            make_key(length)

        # Also try masks taken verbatim from the beginning of other blocks
        # (some builds chain the keystream between blocks).
        for cand in candidates:
            plain = _xor_bytes(payload, cand)
            (comp_size,) = struct.unpack("<I", plain[:4])
            if comp_size + 4 > len(plain):
                continue
            try:
                return zlib.decompress(plain[4 : 4 + comp_size])
            except zlib.error:
                continue
        return None


class TOSB1(TOSBase):
    """The "TOS-B1/TOS-M1" variant used by Tavern of Spear archives."""

    name = "TOS-B1"
    header = b"TOS-B1"

    def detect(self, extension: str, first_line: bytes) -> bool:
        return first_line.startswith(b"TOS-B1") or first_line.startswith(b"TOS-M1")

    def get_index(self, archive: BinaryIO):
        """Parse the archive's own block structure and return the index.

        Returns a dict mapping path -> list of (offset, length, prefix)
        tuples relative to the concatenated data section, mirroring the
        normalised index format used by unrpa.
        """
        blocks = self._read_blocks(archive)
        datas = {}
        for magic, payload in blocks:
            plain = self._try_decompress(payload)
            if plain is None:
                raise ValueError(
                    f"Unable to deobfuscate {magic.decode(errors='replace')} block; "
                    "the archive may use an unknown key rotation."
                )
            datas[magic] = plain

        import pickle

        index_blob = datas.get(b"TOS-B1", b"")
        data_blob = datas.get(b"TOS-M1", b"")
        index = pickle.loads(index_blob, encoding="bytes")
        normalised = {}
        for path, entry in index.items():
            parts = []
            for part in entry:
                if len(part) == 2:
                    offset, length = part
                    parts.append((offset, length, b""))
                else:
                    parts.append(tuple(part))
            normalised[path] = parts
        self._data_blob = data_blob
        return normalised

    def extract_file_view(self, offset: int, length: int, start: bytes) -> ArchiveView:
        """Build an in-memory view over the decrypted data section."""
        import io

        source = io.BytesIO(self._data_blob)
        return ArchiveView(source, offset, length, start)


versions: Tuple[Type[Version], ...] = (TOSB1,)
