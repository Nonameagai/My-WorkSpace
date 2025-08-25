#!/usr/bin/env python3
import re
import struct
from typing import List, Tuple, Set, Union


def extract_encoded_payload(lua_source: str) -> str:
    """Extract the big encoded string passed to return v23("...")."""
    # Match the first string literal passed to v23("...")
    m = re.search(r'return\s+v23\("(.*?)"\s*,\s*v17\(\)\s*,?', lua_source, re.S)
    if not m:
        raise ValueError("Could not find encoded payload string in the Lua source")
    return m.group(1)


def decode_pairs_rle_hex(encoded: str) -> bytes:
    """Replicate the Lua gsub RLE + hex decoding used by the obfuscator.

    The Lua code does:
      s = gsub(s[5:], pattern="..", repl=function(pair)
          if byte(pair, 2) == 81 -- 'Q' then
              repeat_count = tonumber(sub(pair,1,1))
              return ""
          else
              ch = char(tonumber(pair, 16))
              if repeat_count then return rep(ch, repeat_count) else return ch end
          end
      end)
    """
    s = encoded[4:]  # drop the 'LOL!' prefix
    out = bytearray()
    repeat_count: Union[int, None] = None
    i = 0
    n = len(s)
    while i + 1 < n:
        pair = s[i : i + 2]
        i += 2
        if pair[1] == 'Q':
            # Decimal digit followed by 'Q'
            try:
                repeat_count = int(pair[0])
            except ValueError:
                # If it's not a digit, treat it as no-op (robustness)
                repeat_count = None
            continue
        # Otherwise interpret as hex byte
        try:
            value = int(pair, 16)
        except ValueError:
            # In case of invalid hex (should not happen), skip safely
            continue
        if repeat_count is not None:
            out.extend([value] * repeat_count)
            repeat_count = None
        else:
            out.append(value)
    return bytes(out)


class Reader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0

    def tell(self) -> int:
        return self.pos

    def read_bytes(self, n: int) -> bytes:
        if self.pos + n > len(self.data):
            raise EOFError("Unexpected end of data")
        b = self.data[self.pos : self.pos + n]
        self.pos += n
        return b

    def read_u8(self) -> int:
        return self.read_bytes(1)[0]

    def read_u16(self) -> int:
        b = self.read_bytes(2)
        return b[0] | (b[1] << 8)

    def read_u32(self) -> int:
        b = self.read_bytes(4)
        return b[0] | (b[1] << 8) | (b[2] << 16) | (b[3] << 24)

    def read_double(self) -> float:
        # Little-endian IEEE 754 double
        b = self.read_bytes(8)
        return struct.unpack('<d', b)[0]

    def read_lstring(self) -> bytes:
        length = self.read_u32()
        if length == 0:
            return b""
        return self.read_bytes(length)


def get_bits_1_indexed(value: int, start: int, end: int) -> int:
    """Replicate v31 bit-slicing (1-indexed, inclusive)."""
    # Convert to 0-indexed bit positions
    start0 = start - 1
    end0 = end - 1
    width = end0 - start0 + 1
    mask = (1 << width) - 1
    return (value >> start0) & mask


def parse_proto(reader: Reader, strings: List[bytes]) -> None:
    # Constants
    const_count = reader.read_u32()
    for _ in range(const_count):
        t = reader.read_u8()
        if t == 1:
            _bool = reader.read_u8() != 0
            # We do not record booleans/numbers
        elif t == 2:
            _num = reader.read_double()
        elif t == 3:
            s = reader.read_lstring()
            strings.append(s)
        else:
            # Unknown type; try to continue safely
            pass

    # num params or flags
    _ = reader.read_u8()

    # Instructions
    insn_count = reader.read_u32()
    for _ in range(insn_count):
        v86 = reader.read_u8()
        # Base two fields (u16 each)
        _a = reader.read_u16()
        _b = reader.read_u16()
        mode = get_bits_1_indexed(v86, 2, 3)
        if mode == 0:
            _c = reader.read_u16()
            _d = reader.read_u16()
        elif mode == 1:
            _c = reader.read_u32()
        elif mode == 2:
            _c = reader.read_u32()
        elif mode == 3:
            _c = reader.read_u32()
            _d = reader.read_u16()
        else:
            # Should not happen, but keep parser robust
            pass

    # Nested protos
    nested_count = reader.read_u32()
    for _ in range(nested_count):
        parse_proto(reader, strings)


def dump_strings_pretty(strings: List[bytes]) -> str:
    unique: List[bytes] = []
    seen: Set[bytes] = set()
    for s in strings:
        if s not in seen:
            unique.append(s)
            seen.add(s)
    lines: List[str] = []
    for s in unique:
        try:
            text = s.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text = s.decode('latin-1')
            except UnicodeDecodeError:
                text = repr(s)
        lines.append(text)
    return "\n".join(lines)


def main() -> None:
    with open('/workspace/underground war', 'r', encoding='utf-8', errors='ignore') as f:
        src = f.read()
    payload = extract_encoded_payload(src)
    decoded = decode_pairs_rle_hex(payload)
    reader = Reader(decoded)
    strings: List[bytes] = []
    parse_proto(reader, strings)
    out = dump_strings_pretty(strings)
    with open('/workspace/underground_war_strings.txt', 'w', encoding='utf-8') as f:
        f.write(out)
    # Best-effort guess for URLs
    urls: List[str] = []
    for line in out.splitlines():
        ls = line.strip()
        if ls.startswith(('http://', 'https://')) or 'pastebin' in ls or 'github' in ls or 'gist' in ls or 'rbxcdn' in ls or 'raw' in ls:
            urls.append(ls)
    if urls:
        with open('/workspace/underground_war_urls.txt', 'w', encoding='utf-8') as f:
            f.write("\n".join(urls))


if __name__ == '__main__':
    main()

