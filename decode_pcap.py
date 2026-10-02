"""Decode (or shrink) a PCAPdroid capture of a Dwarf session.

PCAPdroid captures are mostly video/stream traffic; the Dwarf's commands
only travel on its WebSocket (TCP port 9900). This tool keeps just that.

Usage:
    python decode_pcap.py capture.pcap                 # text decode -> capture.txt
    python decode_pcap.py capture.pcap --filter        # smaller pcap -> capture_dwarf.pcap
    python decode_pcap.py capture.pcap --module 10     # only one module (e.g. 10 = panorama)
    python decode_pcap.py capture.pcap --port 9900 --out decode.txt

No dependency beyond this package's own protobuf modules (used only to
name commands/modules and to decode the WsPacket envelope). Reads classic
pcap and pcapng, raw-IP (PCAPdroid default), Ethernet and Linux SLL/SLL2.

Each line: time (s from first packet), direction (APP>DWARF / DWARF>APP),
module, command name, message type (request / response / notify) and the
payload decoded field by field as raw protobuf (nested messages expanded,
doubles/floats shown as numbers, strings shown as text).
"""
from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

def _load_protocol():
    """protocol_pb2 for command names, loaded straight from its file next to
    this script, so the package's __init__ (websockets, logging...) and the
    current directory don't matter. Needs only `protobuf`; without it the
    tool still works and prints numbers."""
    import importlib.util
    path = Path(__file__).resolve().parent / "dwarf_python_api" / "proto" / "protocol_pb2.py"
    try:
        spec = importlib.util.spec_from_file_location("dwarf_protocol_pb2", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"(command names unavailable: {e}; pip install protobuf)", file=sys.stderr)
        return None


protocol = _load_protocol()

TYPE_NAMES = {0: "request", 1: "reply", 2: "notify", 3: "response"}


# --- capture file readers ------------------------------------------------

def _read_pcap(data: bytes):
    magic = data[:4]
    endian = "<" if magic in (b"\xd4\xc3\xb2\xa1", b"\x4d\x3c\xb2\xa1") else ">"
    nano = magic in (b"\x4d\x3c\xb2\xa1", b"\xa1\xb2\x3c\x4d")
    linktype = struct.unpack(endian + "I", data[20:24])[0]
    i = 24
    while i + 16 <= len(data):
        sec, frac, incl, _ = struct.unpack(endian + "IIII", data[i:i + 16])
        i += 16
        yield sec + frac / (1e9 if nano else 1e6), linktype, data[i:i + incl], data[i:i + incl]
        i += incl


def _read_pcapng(data: bytes):
    i, endian, linktypes, tsres = 0, "<", [], []
    while i + 12 <= len(data):
        btype = struct.unpack(endian + "I", data[i:i + 4])[0]
        if btype == 0x0A0D0D0A:  # section header: re-read endianness
            endian = "<" if data[i + 8:i + 12] == b"\x4d\x3c\x2b\x1a" else ">"
            linktypes, tsres = [], []
        blen = struct.unpack(endian + "I", data[i + 4:i + 8])[0]
        body = data[i + 8:i + blen - 4]
        if btype == 1:  # interface description
            linktypes.append(struct.unpack(endian + "H", body[:2])[0])
            res = 1e-6
            j = 8
            while j + 4 <= len(body):
                code, olen = struct.unpack(endian + "HH", body[j:j + 4])
                if code == 0:
                    break
                if code == 9 and olen >= 1:
                    v = body[j + 4]
                    res = 2 ** -(v & 0x7F) if v & 0x80 else 10 ** -v
                j += 4 + ((olen + 3) & ~3)
            tsres.append(res)
        elif btype == 6:  # enhanced packet
            iface, hi, lo, cap = struct.unpack(endian + "IIII", body[:16])
            pkt = body[20:20 + cap]
            yield ((hi << 32) | lo) * tsres[iface], linktypes[iface], pkt, pkt
        elif btype == 3:  # simple packet
            pkt = body[4:]
            yield 0.0, linktypes[0] if linktypes else 101, pkt, pkt
        if blen < 12:
            break
        i += blen


def read_packets(path: Path):
    data = path.read_bytes()
    reader = _read_pcapng if data[:4] == b"\x0a\x0d\x0d\x0a" else _read_pcap
    yield from reader(data)


# --- link / IP / TCP -----------------------------------------------------

def _ip_payload(linktype: int, pkt: bytes):
    if linktype == 1:            # Ethernet
        etype, off = struct.unpack(">H", pkt[12:14])[0], 14
        while etype == 0x8100:   # VLAN
            etype, off = struct.unpack(">H", pkt[off + 2:off + 4])[0], off + 4
        pkt = pkt[off:]
    elif linktype == 113:        # Linux SLL
        pkt = pkt[16:]
    elif linktype == 276:        # Linux SLL2
        pkt = pkt[20:]
    elif linktype == 0:          # BSD loopback
        pkt = pkt[4:]
    # 101 / 12 / 14 / 228 / 229: raw IP
    if not pkt:
        return None
    ver = pkt[0] >> 4
    if ver == 4:
        ihl = (pkt[0] & 0x0F) * 4
        if pkt[9] != 6:
            return None
        total = struct.unpack(">H", pkt[2:4])[0] or len(pkt)
        src, dst = ".".join(map(str, pkt[12:16])), ".".join(map(str, pkt[16:20]))
        return src, dst, pkt[ihl:total]
    if ver == 6:
        if pkt[6] != 6:          # no extension-header support needed here
            return None
        src, dst = pkt[8:24].hex(), pkt[24:40].hex()
        return src, dst, pkt[40:40 + struct.unpack(">H", pkt[4:6])[0]]
    return None


def tcp_streams(path: Path, port: int):
    """{(src, sport, dst, dport): [(ts, seq, payload), ...]} for `port`."""
    streams: dict = {}
    raw_kept = []
    for ts, linktype, pkt, raw in read_packets(path):
        ip = _ip_payload(linktype, pkt)
        if ip is None:
            continue
        src, dst, tcp = ip
        if len(tcp) < 20:
            continue
        sport, dport, seq = struct.unpack(">HHI", tcp[:8])
        if port not in (sport, dport):
            continue
        raw_kept.append((ts, linktype, raw))
        payload = tcp[(tcp[12] >> 4) * 4:]
        if payload:
            streams.setdefault((src, sport, dst, dport), []).append((ts, seq, payload))
    return streams, raw_kept


def reassemble(segments):
    """Ordered, de-duplicated (retransmissions) byte stream + per-offset ts."""
    segments = sorted(segments, key=lambda s: s[1])
    out, times, seen, next_seq = bytearray(), [], set(), None
    for ts, seq, payload in segments:
        if seq in seen:
            continue
        seen.add(seq)
        if next_seq is not None and seq < next_seq:  # overlap
            payload = payload[next_seq - seq:]
            if not payload:
                continue
        times.append((len(out), ts))
        out += payload
        next_seq = seq + len(payload) if next_seq is None or seq >= next_seq else next_seq + len(payload)
    return bytes(out), times


def _ts_at(times, offset):
    ts = times[0][1] if times else 0.0
    for off, t in times:
        if off > offset:
            break
        ts = t
    return ts


# --- WebSocket + protobuf --------------------------------------------------

def ws_frames(stream: bytes):
    """Yields (offset, opcode, payload); joins fragmented messages."""
    i = stream.find(b"\r\n\r\n") + 4 if stream[:4] in (b"GET ", b"HTTP") else 0
    pending, pending_op, start = bytearray(), None, 0
    while i + 2 <= len(stream):
        off = i
        b0, b1 = stream[i], stream[i + 1]
        fin, op, masked, n = b0 & 0x80, b0 & 0x0F, b1 & 0x80, b1 & 0x7F
        i += 2
        if n == 126:
            n = struct.unpack(">H", stream[i:i + 2])[0]; i += 2
        elif n == 127:
            n = struct.unpack(">Q", stream[i:i + 8])[0]; i += 8
        mask = stream[i:i + 4] if masked else None
        i += 4 if masked else 0
        payload = stream[i:i + n]
        i += n
        if len(payload) < n:  # truncated capture
            break
        if mask:
            payload = bytes(c ^ mask[k % 4] for k, c in enumerate(payload))
        if op == 0:  # continuation
            pending += payload
        else:
            pending, pending_op, start = bytearray(payload), op, off
        if fin:
            yield start, pending_op, bytes(pending)
            pending = bytearray()


def _varint(buf, i):
    val = shift = 0
    while True:
        b = buf[i]; i += 1
        val |= (b & 0x7F) << shift; shift += 7
        if not b & 0x80:
            return val, i


def decode_raw(buf: bytes, depth=0):
    """Generic protobuf decode -> list of 'field: value' strings, or None."""
    out, i = [], 0
    try:
        while i < len(buf):
            key, i = _varint(buf, i)
            field, wire = key >> 3, key & 7
            if field == 0:
                return None
            if wire == 0:
                v, i = _varint(buf, i)
                out.append(f"{field}: {v - (1 << 64) if v >= 1 << 63 else v}")
            elif wire == 1:
                (d,) = struct.unpack("<d", buf[i:i + 8]); i += 8
                out.append(f"{field}: {d:.10g}")
            elif wire == 5:
                (f,) = struct.unpack("<f", buf[i:i + 4]); i += 4
                out.append(f"{field}: {f:.7g}")
            elif wire == 2:
                n, i = _varint(buf, i)
                chunk = buf[i:i + n]; i += n
                if len(chunk) < n:
                    return None
                nested = decode_raw(chunk, depth + 1) if chunk and depth < 6 else None
                text = None
                try:
                    text = chunk.decode("utf-8")
                    if not text.isprintable():
                        text = None
                except UnicodeDecodeError:
                    pass
                if text is not None and (nested is None or text.strip().startswith(("{", "["))):
                    out.append(f"{field}: {text!r}")
                elif nested is not None:
                    out.append(f"{field}: {{{', '.join(nested)}}}")
                else:
                    out.append(f"{field}: 0x{chunk.hex()}")
            else:
                return None
    except (IndexError, struct.error):
        return None
    return out


def ws_packet(payload: bytes):
    """WsPacket fields (base.proto): 4 module, 5 cmd, 6 type, 7 data."""
    fields, i = {}, 0
    try:
        while i < len(payload):
            key, i = _varint(payload, i)
            field, wire = key >> 3, key & 7
            if wire == 0:
                fields[field], i = _varint(payload, i)
            elif wire == 2:
                n, i = _varint(payload, i)
                fields[field] = payload[i:i + n]; i += n
            else:
                return None
    except IndexError:
        return None
    return fields if 5 in fields else None


# Seen in captures but missing from protocol.proto (names are ours).
EXTRA_CMD_NAMES = {
    15509: "PANORAMA_START_FRAMING", 15510: "PANORAMA_STOP_FRAMING",
    15512: "PANORAMA_UPDATE_FRAMING_RECT", 15513: "PANORAMA_STOP_FRAMING_AND_START_GRID",
    15277: "NOTIFY_PANORAMA_STATE", 15297: "NOTIFY_PANORAMA_FRAMING_RECT",
    15298: "NOTIFY_PANORAMA_FRAMING_PREVIEW (WebP)", 15299: "NOTIFY_PANORAMA_FRAMING_STATE",
}


def _name(enum, value):
    if enum == "DwarfCMD" and value in EXTRA_CMD_NAMES:
        return EXTRA_CMD_NAMES[value]
    if protocol is None:
        return str(value)
    try:
        return getattr(protocol, enum).Name(value)
    except (ValueError, AttributeError):
        return str(value)


# --- main ----------------------------------------------------------------

def _default_out(capture: Path, tail: str) -> Path:
    """<capture name without .pcap/.pcapng> + tail, next to the capture.
    Not Path.with_suffix(): PCAPdroid names contain dots
    ("PCAPdroid_02_oct._10_35_14") that it would treat as an extension."""
    base = capture.stem if capture.suffix.lower() in (".pcap", ".pcapng", ".cap") else capture.name
    return capture.with_name(base + tail)


def write_filtered_pcap(raw_kept, path: Path):
    linktype = raw_kept[0][1] if raw_kept else 101
    with path.open("wb") as f:
        f.write(struct.pack("<IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 262144, linktype))
        for ts, lt, raw in raw_kept:
            if lt != linktype:
                continue
            sec = int(ts)
            f.write(struct.pack("<IIII", sec, int((ts - sec) * 1e6), len(raw), len(raw)))
            f.write(raw)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("capture", type=Path)
    ap.add_argument("--port", type=int, default=9900, help="Dwarf WebSocket port (default 9900)")
    ap.add_argument("--filter", action="store_true", help="write a pcap with only that port's traffic")
    ap.add_argument("--module", type=int, action="append", help="only these module ids (repeatable)")
    ap.add_argument("--out", type=Path, help="output file (default: next to the capture)")
    args = ap.parse_args()

    streams, raw_kept = tcp_streams(args.capture, args.port)
    if args.filter:
        out = args.out or _default_out(args.capture, "_dwarf.pcap")
        write_filtered_pcap(raw_kept, out)
        print(f"{len(raw_kept)} packets on port {args.port} -> {out.resolve()} ({out.stat().st_size // 1024} KB)")
        return

    events = []
    for (src, sport, dst, dport), segs in streams.items():
        direction = "APP>DWARF" if dport == args.port else "DWARF>APP"
        data, times = reassemble(segs)
        for off, op, payload in ws_frames(data):
            if op != 2:  # binary frames only
                continue
            pkt = ws_packet(payload)
            if pkt is None:
                continue
            module = pkt.get(4, 0)
            if args.module and module not in args.module:
                continue
            events.append((_ts_at(times, off), direction, module, pkt.get(5, 0), pkt.get(6, 0), pkt.get(7, b"")))

    events.sort(key=lambda e: e[0])
    t0 = events[0][0] if events else 0.0
    lines = []
    for ts, direction, module, cmd, typ, data in events:
        decoded = decode_raw(data) if data else []
        body = ", ".join(decoded) if decoded is not None else f"0x{data.hex()}"
        lines.append(
            f"{ts - t0:9.3f}  {direction}  m{module:<2} {cmd:<5} {_name('DwarfCMD', cmd):<45} "
            f"{TYPE_NAMES.get(typ, typ):<8} {{{body}}}"
        )

    out = args.out or _default_out(args.capture, ".txt")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(events)} Dwarf messages decoded -> {out.resolve()}")
    if not events:
        print(f"No Dwarf WebSocket traffic found on port {args.port} - wrong port, "
              "or the capture started after the app had connected (try --port).")


if __name__ == "__main__":
    sys.exit(main())
