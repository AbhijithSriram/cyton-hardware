#!/usr/bin/env python3
"""
cyton_server.py - Flask front end for the OpenBCI Cyton WiFi bridge.

    Cyton --UART--> XIAO ESP32C3 --WiFi TCP--> this server --HTTP--> browser

Run:
    python cyton_server.py
    then open http://127.0.0.1:5000

The bridge must be reachable first. In access-point mode, join the
"CytonBridge" WiFi network and the bridge is at 192.168.4.1:3000.

    python cyton_server.py --host 192.168.1.15      # station mode instead

Recordings are written as CSV to ./recordings/. Running an experiment writes two
files: the sample data (with a per-sample `phase` column) and a companion
`-events.csv` giving each cue's onset as both a wall clock time and an absolute
SAMPLE INDEX - the sample index is the authoritative one for epoching.
"""

import argparse
import csv
import os
import socket
import threading
import time
from collections import deque
from datetime import datetime

from flask import Flask, jsonify, render_template, request

from cyton_client import PacketReader, fmt_uv, is_railed, N_CHANNELS
from cyton_experiments import EXPERIMENTS, listing, total_seconds

# --------------------------------------------------------------------------- #
# configuration
# --------------------------------------------------------------------------- #
BRIDGE_HOST = "192.168.4.1"
BRIDGE_PORT = 3000
SAMPLE_RATE = 250
BUFFER_SECONDS = 30
MAX_PER_REQUEST = 2000          # cap so a slow browser can't ask for everything
RECORD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recordings")

app = Flask(__name__, template_folder="cyton_templates")


# --------------------------------------------------------------------------- #
# shared state
# --------------------------------------------------------------------------- #
class Stream:
    """Owns the socket thread, the ring buffer, recording, and the cue runner."""

    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.lock = threading.Lock()
        self.samples = deque(maxlen=SAMPLE_RATE * BUFFER_SECONDS)
        self.total = 0                       # absolute count of samples ever seen

        self.connected = False
        self.streaming = False               # connected AND data actually arriving
        self.error = ""
        self.dropped = 0
        self.bad = 0
        self.rate = 0.0
        self.railed = [False] * N_CHANNELS

        # Counters survive reconnects instead of resetting to zero.
        self._dropped_base = 0
        self._bad_base = 0

        self._sock = None
        self._send_lock = threading.Lock()

        # recording
        self.recording = False
        self._rec_file = None
        self._rec_writer = None
        self.rec_name = ""
        self.rec_path = ""
        self.rec_count = 0

        # experiment / cue runner
        self.exp_running = False
        self.exp_id = ""
        self.exp_name = ""
        self.exp_steps = []
        self.exp_events = []
        self.exp_index = -1
        self.exp_cue = ""
        self.exp_sub = ""
        self.exp_style = "neutral"
        self.exp_step_end = 0.0
        self.exp_step_len = 0.0
        self.phase = ""                      # written into every CSV row
        self._exp_stop = threading.Event()

        threading.Thread(target=self._run, daemon=True).start()

    # -- socket thread ------------------------------------------------------ #
    def _run(self):
        while True:
            try:
                self.error = ""
                sock = socket.create_connection((self.host, self.port), timeout=10)
                sock.settimeout(1.0)          # short: idle is normal, not fatal
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self._sock = sock
                self.connected = True

                # yield_idle keeps the socket open when the Cyton is silent.
                # It sends nothing until 'b', so a quiet socket is the normal
                # resting state - tearing the connection down for it made the
                # server reconnect every second and never settle.
                reader = PacketReader(sock, yield_idle=True)

                win_n, win_t = 0, time.time()
                for item in reader.packets():
                    now = time.time()

                    if item is not None:
                        counter, chans, _ = item
                        uv = [fmt_uv(c) for c in chans]
                        win_n += 1
                        with self.lock:
                            self.samples.append(uv)
                            self.total += 1
                            self.dropped = self._dropped_base + reader.dropped
                            self.bad = self._bad_base + reader.bad
                            self.railed = [is_railed(c) for c in chans]
                        if self.recording:
                            self._write_row(counter, uv)

                    # Rolling one-second rate, so it falls to 0 when the board
                    # stops streaming instead of averaging since connect.
                    el = now - win_t
                    if el >= 1.0:
                        with self.lock:
                            self.rate = win_n / el
                            self.streaming = win_n > 0
                        win_n, win_t = 0, now

            except Exception as exc:                      # noqa: BLE001
                self.connected = False
                self.streaming = False
                self.error = str(exc)
                self.rate = 0.0
                self._dropped_base = self.dropped
                self._bad_base = self.bad
                try:
                    if self._sock:
                        self._sock.close()
                except Exception:                          # noqa: BLE001
                    pass
                self._sock = None
                time.sleep(2.0)                            # then retry

    # -- commands ----------------------------------------------------------- #
    def send(self, text):
        if not self._sock:
            return False, "not connected to bridge"
        try:
            with self._send_lock:
                for ch in text:
                    self._sock.sendall(ch.encode())
                    time.sleep(0.35)       # '[' and 'd' reconfigure all 8 channels
            return True, ""
        except Exception as exc:                           # noqa: BLE001
            return False, str(exc)

    # -- recording ---------------------------------------------------------- #
    def start_recording(self, label=""):
        if self.recording:
            return False, "already recording"
        os.makedirs(RECORD_DIR, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe = "".join(c for c in label if c.isalnum() or c in "-_")
        name = f"cyton-{stamp}{('-' + safe) if safe else ''}.csv"
        path = os.path.join(RECORD_DIR, name)

        self._rec_file = open(path, "w", newline="", encoding="utf-8")
        self._rec_writer = csv.writer(self._rec_file)
        self._rec_writer.writerow(
            ["timestamp_iso", "sample_index", "sample_counter", "phase"]
            + [f"ch{i+1}_uV" for i in range(N_CHANNELS)]
        )
        self.rec_name = name
        self.rec_path = path
        self.rec_count = 0
        self.recording = True
        return True, name

    def _write_row(self, counter, uv):
        try:
            self._rec_writer.writerow(
                [datetime.now().isoformat(timespec="milliseconds"),
                 self.total, counter, self.phase]
                + [f"{v:.4f}" for v in uv]
            )
            self.rec_count += 1
        except Exception:                                  # noqa: BLE001
            pass

    def stop_recording(self):
        if not self.recording:
            return False, "not recording"
        self.recording = False
        time.sleep(0.05)
        try:
            self._rec_file.flush()
            self._rec_file.close()
        except Exception:                                  # noqa: BLE001
            pass
        self._rec_file = None
        self._rec_writer = None
        return True, self.rec_name

    # -- experiment runner -------------------------------------------------- #
    def start_experiment(self, exp_id, label=""):
        if self.exp_running:
            return False, "an experiment is already running"
        exp = EXPERIMENTS.get(exp_id)
        if not exp:
            return False, f"unknown experiment '{exp_id}'"
        if not self.streaming:
            return False, "board is not streaming - press start (b) first"

        ok, msg = self.start_recording(label or exp_id)
        if not ok:
            return False, msg

        self.exp_id = exp_id
        self.exp_name = exp["name"]
        self.exp_steps = exp["steps"]
        self.exp_events = []
        self.exp_index = -1
        self.exp_running = True
        self._exp_stop.clear()
        threading.Thread(target=self._run_experiment, daemon=True).start()
        return True, msg

    def _run_experiment(self):
        # Deadlines are absolute offsets from the experiment start, not
        # "now + duration" per step, so scheduling jitter cannot accumulate
        # across the 80+ steps of the motor-imagery protocol.
        t0 = time.time()
        elapsed = 0.0
        for i, step in enumerate(self.exp_steps):
            if self._exp_stop.is_set():
                break

            # Stamp the transition against the DATA timeline, not just the clock.
            with self.lock:
                sample_idx = self.total

            self.exp_index = i
            self.phase = step["label"]
            self.exp_cue = step["cue"]
            self.exp_sub = step.get("sub", "")
            self.exp_style = step.get("style", "neutral")
            self.exp_step_len = float(step["seconds"])
            elapsed += self.exp_step_len
            self.exp_step_end = t0 + elapsed

            self.exp_events.append({
                "onset_iso": datetime.now().isoformat(timespec="milliseconds"),
                "onset_sample_index": sample_idx,
                "onset_seconds": round(sample_idx / SAMPLE_RATE, 4),
                "step_index": i,
                "phase": step["label"],
                "cue": step["cue"],
                "duration_s": step["seconds"],
            })

            if self._exp_stop.wait(max(0.0, self.exp_step_end - time.time())):
                break

        self._finish_experiment()

    def _finish_experiment(self):
        self.exp_running = False
        self.phase = ""
        self.exp_cue = ""
        self.exp_sub = ""
        self.exp_style = "neutral"
        self.exp_index = -1
        events_name = self._write_events()
        self.stop_recording()
        return events_name

    def _write_events(self):
        if not self.exp_events or not self.rec_path:
            return ""
        path = self.rec_path.replace(".csv", "-events.csv")
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=[
                    "onset_iso", "onset_sample_index", "onset_seconds",
                    "step_index", "phase", "cue", "duration_s",
                ])
                w.writeheader()
                w.writerows(self.exp_events)
            return os.path.basename(path)
        except Exception:                                  # noqa: BLE001
            return ""

    def stop_experiment(self):
        if not self.exp_running:
            return False, "no experiment running"
        self._exp_stop.set()
        for _ in range(40):                # wait for the runner to unwind
            if not self.exp_running:
                break
            time.sleep(0.05)
        return True, self.rec_name

    # -- reads -------------------------------------------------------------- #
    def since(self, index):
        """Return (next_index, [samples]) for everything after `index`."""
        with self.lock:
            oldest = self.total - len(self.samples)
            if index < oldest:
                index = oldest                  # client fell behind, skip ahead
            start = index - oldest
            out = list(self.samples)[start:]
            if len(out) > MAX_PER_REQUEST:
                out = out[-MAX_PER_REQUEST:]
                index = self.total - len(out)
            return self.total, out

    def status(self):
        with self.lock:
            st = {
                "connected": self.connected,
                "streaming": self.streaming,
                "error": self.error,
                "rate": round(self.rate, 1),
                "dropped": self.dropped,
                "bad": self.bad,
                "total": self.total,
                "railed": self.railed,
                "recording": self.recording,
                "rec_name": self.rec_name,
                "rec_count": self.rec_count,
                "bridge": f"{self.host}:{self.port}",
            }
        st["experiment"] = {
            "running": self.exp_running,
            "id": self.exp_id if self.exp_running else "",
            "name": self.exp_name if self.exp_running else "",
            "cue": self.exp_cue,
            "sub": self.exp_sub,
            "style": self.exp_style,
            "phase": self.phase,
            "step": self.exp_index + 1,
            "steps": len(self.exp_steps) if self.exp_running else 0,
            "remaining": round(max(0.0, self.exp_step_end - time.time()), 1)
                         if self.exp_running else 0.0,
            "step_len": self.exp_step_len if self.exp_running else 0.0,
        }
        return st


stream = None          # set in main()


# --------------------------------------------------------------------------- #
# routes
# --------------------------------------------------------------------------- #
@app.route("/")
def index():
    return render_template("index.html", channels=N_CHANNELS, fs=SAMPLE_RATE)


@app.route("/api/status")
def api_status():
    return jsonify(stream.status())


@app.route("/api/data")
def api_data():
    try:
        since = int(request.args.get("since", 0))
    except ValueError:
        since = 0
    nxt, rows = stream.since(since)
    return jsonify({"next": nxt, "samples": rows})


@app.route("/api/command", methods=["POST"])
def api_command():
    cmd = (request.json or {}).get("cmd", "")
    if not cmd or len(cmd) > 8:
        return jsonify({"ok": False, "error": "bad command"}), 400
    ok, err = stream.send(cmd)
    return jsonify({"ok": ok, "error": err, "sent": cmd})


@app.route("/api/record", methods=["POST"])
def api_record():
    body = request.json or {}
    action = body.get("action")
    if action == "start":
        ok, msg = stream.start_recording(body.get("label", ""))
    elif action == "stop":
        ok, msg = stream.stop_recording()
    else:
        return jsonify({"ok": False, "error": "action must be start or stop"}), 400
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/experiments")
def api_experiments():
    return jsonify({"experiments": listing()})


@app.route("/api/experiment", methods=["POST"])
def api_experiment():
    body = request.json or {}
    action = body.get("action")
    if action == "start":
        ok, msg = stream.start_experiment(body.get("id", ""), body.get("label", ""))
    elif action == "stop":
        ok, msg = stream.stop_experiment()
    else:
        return jsonify({"ok": False, "error": "action must be start or stop"}), 400
    return jsonify({"ok": ok, "message": msg})


# --------------------------------------------------------------------------- #
def main():
    global stream
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default=BRIDGE_HOST, help="bridge IP")
    ap.add_argument("--port", type=int, default=BRIDGE_PORT)
    ap.add_argument("--web-port", type=int, default=5000)
    args = ap.parse_args()

    stream = Stream(args.host, args.port)

    print(f"Bridge:  {args.host}:{args.port}")
    print(f"Open:    http://127.0.0.1:{args.web_port}")
    print(f"Records: {RECORD_DIR}")
    print("Experiments: " + ", ".join(f"{e['id']} ({e['seconds']:.0f}s)"
                                      for e in listing()))
    app.run(host="127.0.0.1", port=args.web_port, threaded=True, debug=False)


if __name__ == "__main__":
    main()
