#!/usr/bin/env python3
"""
cyton_client.py - Receive OpenBCI Cyton data from the XIAO ESP32C3 WiFi bridge.

    Cyton --UART--> XIAO ESP32C3 --WiFi TCP--> this script

Packet format (confirmed against OpenBCI_32bit_Library v3.1.5):

    byte  0      0x41  ('A', OPENBCI_BOP) - NOT the 0xA0 in the older docs
    byte  1      sample counter, wraps 0..255
    bytes 2-25   8 channels x 3 bytes, signed 24-bit big-endian
    bytes 26-31  aux / accelerometer
    byte  32     stop byte, 0xC0..0xCF
                 = 33 bytes total, 250 packets/sec

Usage:
    python cyton_client.py                    # live view, all 8 channels
    python cyton_client.py --scope 1          # ASCII scope of channel 1
    python cyton_client.py --raw 20           # dump 20 consecutive samples
    python cyton_client.py --lsl              # also publish an LSL outlet

Commands can be sent while running (start/stop streaming, test signals):
    python cyton_client.py --send b           # start streaming, then view
    python cyton_client.py --send "["         # 2x square wave test signal
"""

import argparse
import socket
import sys
import time

# Default is the bridge in access-point mode: join the "CytonBridge" WiFi
# network first, then the XIAO is always at 192.168.4.1.
# If the bridge is in station mode instead, pass --host <its DHCP address>.
HOST = "192.168.4.1"
PORT = 3000

START_BYTE = 0x41
PACKET_LEN = 33
N_CHANNELS = 8

# ADS1299: 4.5 V reference, default gain 24, 24-bit.
#   volts per count = 4.5 / 24 / (2**23 - 1)
SCALE_UV = 4.5 / 24.0 / (2**23 - 1) * 1e6      # ~0.02235 uV per count


def parse_channels(payload):
    """payload = 24 bytes -> list of 8 signed ints."""
    return [
        int.from_bytes(payload[i * 3:i * 3 + 3], "big", signed=True)
        for i in range(N_CHANNELS)
    ]


class PacketReader:
    """Resyncing packet framer. Tolerates junk and mid-stream joins."""

    def __init__(self, sock, yield_idle=False):
        self.sock = sock
        self.buf = bytearray()
        self.good = 0
        self.bad = 0
        self.dropped = 0
        self.last_counter = None
        # An idle socket is NOT an error. The Cyton sends nothing at all until
        # you press 'b', so a recv() timeout just means "not streaming yet".
        # With yield_idle the caller gets None and can stay connected.
        self.yield_idle = yield_idle

    def _fill(self):
        """Return True if bytes were read, False on an idle timeout."""
        try:
            chunk = self.sock.recv(4096)
        except socket.timeout:
            return False
        if not chunk:
            raise ConnectionError("bridge closed the connection")
        self.buf.extend(chunk)
        return True

    def packets(self):
        """Yield (counter, [8 ints], stop_byte), or None while idle."""
        while True:
            while len(self.buf) < PACKET_LEN:
                if not self._fill():
                    if self.yield_idle:
                        yield None
                    # otherwise keep blocking until data shows up

            while len(self.buf) >= PACKET_LEN:
                if self.buf[0] != START_BYTE:
                    del self.buf[0]          # resync
                    continue

                pkt = bytes(self.buf[:PACKET_LEN])
                stop = pkt[32]
                if (stop & 0xF0) != 0xC0:
                    # Start byte was a coincidence inside the payload.
                    self.bad += 1
                    del self.buf[0]
                    continue

                del self.buf[:PACKET_LEN]
                self.good += 1

                counter = pkt[1]
                if self.last_counter is not None:
                    gap = (counter - self.last_counter) & 0xFF
                    if gap != 1:
                        self.dropped += gap - 1   # gap-1 samples never arrived
                self.last_counter = counter

                yield counter, parse_channels(pkt[2:26]), stop


def fmt_uv(counts):
    return counts * SCALE_UV


def run_live(reader):
    print(f"{'sample':>7}  " + "  ".join(f"ch{i+1:>10}" for i in range(N_CHANNELS)))
    print(f"{'':>7}  " + "  ".join(f"{'(uV)':>12}" for _ in range(N_CHANNELS)))
    t0 = time.time()
    shown = 0
    for counter, chans, _ in reader.packets():
        shown += 1
        if shown % 25:                     # ~10 updates/sec at 250 Hz
            continue
        row = "  ".join(f"{fmt_uv(c):12.2f}" for c in chans)
        el = time.time() - t0
        rate = reader.good / el if el else 0
        sys.stdout.write(
            f"\r{counter:7d}  {row}   [{rate:6.1f} Hz  drop {reader.dropped}]"
        )
        sys.stdout.flush()


def run_raw(reader, n):
    print(f"{'#':>4} {'ctr':>4}  " + " ".join(f"ch{i+1:>9}" for i in range(N_CHANNELS)))
    for i, (counter, chans, _) in enumerate(reader.packets()):
        print(f"{i:4d} {counter:4d}  " + " ".join(f"{fmt_uv(c):10.1f}" for c in chans))
        if i + 1 >= n:
            break
    print(f"\ngood={reader.good} bad={reader.bad} dropped={reader.dropped}")


# A channel sitting at +/- full scale is not measuring anything - it is pinned
# against a rail, which is what an unconnected EEG input does.
RAIL_COUNTS = 2**23
RAIL_UV = RAIL_COUNTS * SCALE_UV          # ~187500 uV


def is_railed(counts):
    return abs(counts) >= RAIL_COUNTS - 16


def run_scope(reader, ch, width=70):
    """ASCII scope. A square wave is unmistakable here."""
    ch_idx = ch - 1
    lo, hi = None, None
    railed_run = 0
    print(f"ASCII scope, channel {ch}. Ctrl-C to stop.\n")
    for i, (_, chans, _) in enumerate(reader.packets()):
        if i % 10:                          # decimate 250 Hz -> 25 Hz
            continue
        raw = chans[ch_idx]
        v = fmt_uv(raw)

        if is_railed(raw):
            railed_run += 1
            if railed_run == 1:
                print(f"{v:11.1f}   RAILED at full scale - this channel is not")
                print(f"{'':11}   measuring. Open input, or no test signal set.")
                print(f"{'':11}   Try:  --send \"[b\"   (2x square wave + stream)")
            elif railed_run % 25 == 0:
                print(f"{v:11.1f}   still railed ({railed_run} samples)")
            continue
        railed_run = 0

        lo = v if lo is None else min(lo, v)
        hi = v if hi is None else max(hi, v)
        span = (hi - lo) or 1.0
        col = int((v - lo) / span * (width - 1))
        print(f"{v:11.1f} |" + " " * col + "*")


def run_plot(reader, seconds=5.0, fs=250.0, spacing=None):
    """Live scrolling plot of all 8 channels, stacked like a real EEG trace."""
    import threading
    from collections import deque
    try:
        import matplotlib.pyplot as plt
        from matplotlib.animation import FuncAnimation
    except ImportError:
        print("matplotlib is required for --plot.  pip install matplotlib",
              file=sys.stderr)
        return

    n = int(seconds * fs)
    bufs = [deque([0.0] * n, maxlen=n) for _ in range(N_CHANNELS)]
    lock = threading.Lock()
    state = {"rate": 0.0, "t0": time.time(), "alive": True}

    def worker():
        try:
            for _, chans, _ in reader.packets():
                with lock:
                    for i, c in enumerate(chans):
                        bufs[i].append(fmt_uv(c))
                el = time.time() - state["t0"]
                if el:
                    state["rate"] = reader.good / el
        except Exception:
            state["alive"] = False

    threading.Thread(target=worker, daemon=True).start()

    fig, ax = plt.subplots(figsize=(12, 8))
    fig.canvas.manager.set_window_title("OpenBCI Cyton - live")
    t = [-(n - i) / fs for i in range(n)]

    lines = []
    for i in range(N_CHANNELS):
        (ln,) = ax.plot(t, [0] * n, lw=0.8)
        lines.append(ln)

    ax.set_xlim(t[0], 0)
    ax.set_xlabel("seconds (0 = now)")
    ax.set_yticks([])
    ax.grid(alpha=0.25, axis="x")

    labels = [ax.text(t[0], 0, f" ch{i+1}", va="center", fontsize=9)
              for i in range(N_CHANNELS)]

    def update(_):
        with lock:
            data = [list(b) for b in bufs]

        # Centre each channel on its own mean so DC offset never hides the shape.
        centred, peaks = [], []
        for d in data:
            m = sum(d) / len(d)
            c = [v - m for v in d]
            centred.append(c)
            peaks.append(max(abs(min(c)), abs(max(c)), 1e-6))

        step = spacing if spacing else max(peaks) * 2.2
        for i, (ln, c) in enumerate(zip(lines, centred)):
            off = (N_CHANNELS - 1 - i) * step
            ln.set_ydata([v + off for v in c])
            labels[i].set_position((t[0], off))

        ax.set_ylim(-step, N_CHANNELS * step)
        ax.set_title(
            f"{state['rate']:.1f} Hz   dropped {reader.dropped}   "
            f"bad {reader.bad}   scale +/-{step/2.2:,.0f} uV/ch"
        )
        return lines + labels

    FuncAnimation(fig, update, interval=50, blit=False, cache_frame_data=False)
    print("Close the plot window to stop.")
    plt.tight_layout()
    plt.show()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default=HOST)
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--send", metavar="CMD",
                    help="command to send on connect, e.g. b, s, v, [, 0")
    ap.add_argument("--raw", type=int, metavar="N",
                    help="print N consecutive samples and exit")
    ap.add_argument("--scope", type=int, metavar="CH",
                    help="ASCII scope of one channel (1-8)")
    ap.add_argument("--plot", action="store_true",
                    help="live scrolling graph of all 8 channels (needs matplotlib)")
    ap.add_argument("--window", type=float, default=5.0, metavar="SEC",
                    help="seconds visible in --plot (default 5)")
    ap.add_argument("--spacing", type=float, default=None, metavar="UV",
                    help="fixed uV between channels in --plot (default auto)")
    ap.add_argument("--lsl", action="store_true",
                    help="publish an LSL outlet (needs pylsl)")
    args = ap.parse_args()

    outlet = None
    if args.lsl:
        try:
            from pylsl import StreamInfo, StreamOutlet
            info = StreamInfo("OpenBCI_Cyton", "EEG", N_CHANNELS, 250, "float32",
                              "cyton-wifi-bridge")
            outlet = StreamOutlet(info)
            print("LSL outlet 'OpenBCI_Cyton' created.")
        except ImportError:
            print("pylsl not installed - continuing without LSL.", file=sys.stderr)

    print(f"Connecting to {args.host}:{args.port} ...")
    with socket.create_connection((args.host, args.port), timeout=10) as sock:
        sock.settimeout(5.0)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        print("Connected.")

        if args.send:
            # Send one character at a time. Commands like '[' reconfigure all
            # eight ADS1299 channels and need a moment before the next one.
            for ch in args.send:
                sock.sendall(ch.encode())
                print(f"  sent {ch!r}")
                time.sleep(0.4)
            time.sleep(0.4)

        reader = PacketReader(sock)

        if outlet:
            for _, chans, _ in reader.packets():
                outlet.push_sample([fmt_uv(c) for c in chans])
        elif args.plot:
            run_plot(reader, seconds=args.window, spacing=args.spacing)
        elif args.raw:
            run_raw(reader, args.raw)
        elif args.scope:
            run_scope(reader, args.scope)
        else:
            run_live(reader)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
    except (ConnectionError, socket.timeout, OSError) as e:
        print(f"\nConnection problem: {e}", file=sys.stderr)
        sys.exit(1)
