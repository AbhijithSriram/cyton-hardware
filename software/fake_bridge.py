#!/usr/bin/env python3
"""
fake_bridge.py - Pretend to be the XIAO WiFi bridge.

Emits valid Cyton packets at 250 Hz over TCP so the web app, recorder, and
experiment runner can be developed and tested with no hardware attached.

    python fake_bridge.py                 # listens on 127.0.0.1:3000
    python cyton_server.py --host 127.0.0.1

Signal is a per-channel sine wave plus noise, so traces are recognisable and
each channel is visibly different.

Responds to the same commands as the real board:
    b = start streaming    s = stop    v = soft reset (prints the banner)
"""

import argparse
import math
import random
import socket
import struct
import threading
import time

START_BYTE = 0x41
STOP_BYTE = 0xC0
N_CHANNELS = 8
SAMPLE_RATE = 250

BANNER = (b"OpenBCI V3 8-16 channel\n"
          b"On Board ADS1299 Device ID: 0x3E\n"
          b"LIS3DH Device ID: 0x33\n"
          b"Firmware: v3.1.2\n$$$")


def encode_sample(counter, values):
    """values = 8 signed ints (24-bit range) -> a 33-byte Cyton packet."""
    out = bytearray([START_BYTE, counter & 0xFF])
    for v in values:
        v = max(-8388608, min(8388607, int(v)))
        out += struct.pack(">i", v & 0xFFFFFF)[1:]      # low 3 bytes, big-endian
    out += bytes(6)                                     # aux
    out.append(STOP_BYTE)
    return bytes(out)


def serve(conn, addr):
    print(f"client connected: {addr}")
    streaming = False
    counter = 0
    t = 0.0
    conn.setblocking(False)
    next_t = time.perf_counter()
    try:
        while True:
            # ---- read commands without blocking the sample clock ----
            try:
                data = conn.recv(64)
                if not data:
                    break
                for ch in data.decode(errors="ignore"):
                    if ch == "b":
                        streaming = True
                        print("  -> streaming")
                    elif ch == "s":
                        streaming = False
                        print("  -> stopped")
                    elif ch == "v":
                        streaming = False
                        conn.sendall(BANNER)
                        print("  -> reset, banner sent")
                    else:
                        print(f"  -> command {ch!r} (ignored)")
            except BlockingIOError:
                pass
            except (ConnectionError, OSError):
                break

            # ---- emit one sample per tick ----
            next_t += 1.0 / SAMPLE_RATE
            sleep = next_t - time.perf_counter()
            if sleep > 0:
                time.sleep(sleep)
            else:
                next_t = time.perf_counter()

            if not streaming:
                continue

            t += 1.0 / SAMPLE_RATE
            vals = []
            for i in range(N_CHANNELS):
                freq = 6 + i * 2                     # 6..20 Hz, one per channel
                amp = 40000 + i * 4000
                v = amp * math.sin(2 * math.pi * freq * t) + random.gauss(0, 3000)
                vals.append(v)
            try:
                conn.sendall(encode_sample(counter, vals))
            except (ConnectionError, OSError):
                break
            counter = (counter + 1) & 0xFF
    finally:
        conn.close()
        print(f"client gone: {addr}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=3000)
    args = ap.parse_args()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((args.host, args.port))
    srv.listen(1)
    print(f"fake bridge listening on {args.host}:{args.port}  (Ctrl-C to stop)")
    try:
        while True:
            conn, addr = srv.accept()
            threading.Thread(target=serve, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        pass
    finally:
        srv.close()


if __name__ == "__main__":
    main()
