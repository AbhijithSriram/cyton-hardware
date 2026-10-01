# OpenBCI Cyton — self-fabricated board, complete record

A self-fabricated **OpenBCI Cyton V3 (32-bit)** — ordered from JLCPCB from the open
hardware files, flashed over ICSP, and made wireless with a **Seeed XIAO ESP32C3** bridge
in place of the obsolete RFD22301 radio that was never populated.

This repo is the whole record: the order files, the firmware, the bring-up, every mistake
made getting there, the software stack that records from it, and the EEG it has recorded.

| | |
|---|---|
| **Board** | OpenBCI Cyton V3, PIC32MX250F128B + ADS1299IPAG, 8 channels @ 250 SPS |
| **Firmware** | OpenBCI_32bit_Library v3.1.5, built with `board.beginDebug()` |
| **Link** | Cyton `D11`/`D12` → XIAO ESP32C3 → WiFi TCP `192.168.4.1:3000` → Flask |
| **Proven** | ADS1299 ID `0x3E`, test signal ±3.74 mV (0.3 % error), noise floor ±1 µV, 250 pkt/s with 0 malformed |
| **Recorded** | Real EEG on 2 frontal channels — alpha blocks and motor execution |

**Start here:** [`docs/CYTON_BRINGUP.md`](docs/CYTON_BRINGUP.md) — the full technical
record, fabrication through live streaming. §11 is the troubleshooting catalogue: 13 traps,
each with the symptom that identifies it.

---

## Map

| Folder | Contents |
|---|---|
| `docs/` | The bring-up document. Wiring guides for the [frontal/Muse-comparison montage](docs/WIRING-cyton-muse-athena.md) and for [motor imagery](docs/WIRING-motor-imagery.md). Electrode [research](docs/Electrode_Research.md) and [decision](docs/ELECTRODE_DECISION.md). |
| `hardware/` | What the board was built from: `gerbers/` (the set actually sent out), `bom/` (BOM + JLCPCB CPL), `quotes/` (JLCPCB, Robu, LionCircuits), `component-selection/`, `reference/` (schematic, DesignSpark source, photos). |
| `firmware/cyton/` | The exact sketch flashed to the PIC32 — `DefaultBoard` with the one changed line, `board.beginDebug()` — plus the hex the IDE built. |
| `firmware/bridge/` | `CytonWiFiBridge.ino`, the XIAO ESP32C3 UART↔TCP bridge. Its header comment is the wiring reference. |
| `firmware/images/` | `CytonDebug-with-bootloader.hex` — the merged bootloader + application image on the board right now. |
| `firmware/tools/` | `merge-hex.ps1` (Intel HEX merger with overlap detection), `listen-cyton.ps1` (serial listener that recognises the ADS1299 ID). |
| `software/` | The Flask server and web UI, the CLI client, the cue protocols, a fake bridge for working with no hardware, and `recordings/`. |
| `logs/` | The first serial capture taken off the board. |
| `vendor/`, `mechanical/` | Upstream clones and headset STLs. On disk, **git-ignored**, pinned in [`VENDOR.md`](VENDOR.md). |

## Running it

Join the bridge's WiFi (`CytonBridge`, the XIAO is always `192.168.4.1`), then:

```bash
python software/cyton_server.py
```

Open <http://127.0.0.1:5000>, press **b** to start streaming, and pick a protocol from the
experiment list. Recordings land in `software/recordings/` as CSV with a `phase` column on
every row, plus an `-events.csv` giving each cue onset as an absolute **sample index**.

No hardware attached? Two terminals:

```bash
python software/fake_bridge.py
python software/cyton_server.py --host 127.0.0.1
```

## Electrodes, as currently wired

Two channels of 3M Ag/AgCl ECG gel patches. Electrodes go to the **N** pins — the P side is
already tied to SRB2 internally.

| Patch | Position | PL1 pin | Channel |
|---|---|---:|---|
| 1 | AF7, left forehead | 21 | ch1 (`1N`) |
| 2 | AF8, right forehead | 19 | ch2 (`2N`) |
| 3 | Fpz, centre forehead | 23 | `SRB2` — reference |
| 4 | Mastoid or earlobe | 5 | `BIAS` — not optional |

Channels 3–8 read ±187500 µV because nothing is wired to them. Full detail, skin prep and
test protocol: [`docs/WIRING-cyton-muse-athena.md`](docs/WIRING-cyton-muse-athena.md).

## What is not documented

Honest gaps, listed in `docs/CYTON_BRINGUP.md` §12.4: the **battery and power wiring**
(spec, connector, charging, how SW2's missing switch is bridged), the **physical assembly
record** for the hand-soldered PL1 header and the XIAO hookup, and the **alpha ratio
comparison against the Muse**, which has recordings but no written result.
