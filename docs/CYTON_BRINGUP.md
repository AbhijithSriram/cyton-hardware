# OpenBCI Cyton — Self-Fabricated Board Bring-Up

**Complete technical record: fabrication through live 8-channel wireless EEG streaming.**

| | |
|---|---|
| **Board** | OpenBCI Cyton V3 (32-bit), self-fabricated via JLCPCB |
| **MCU** | PIC32MX250F128B, SSOP-28, Rev B0 |
| **AFE** | ADS1299IPAG, TQFP-64, 8 channels @ 250 SPS |
| **Accelerometer** | LIS3DHTR, LGA-16 |
| **Firmware** | OpenBCI_32bit_Library v3.1.5, built with `board.beginDebug()` |
| **Radio** | RFD22301 **not populated** — replaced with a Seeed XIAO ESP32C3 WiFi bridge |
| **Status** | ✅ 8 channels streaming at 250 Hz over WiFi, ±1 µV noise floor. Real EEG recorded on 2 frontal channels — see §12.3 |
| **Date** | Bring-up August 2026. Reorganised into this repo 1 October 2026 |

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Hardware Inventory](#2-hardware-inventory)
3. [Source Repositories](#3-source-repositories)
4. [Schematic Reference](#4-schematic-reference)
5. [Firmware Reference](#5-firmware-reference)
6. [Serial Protocol Reference](#6-serial-protocol-reference)
7. [Bring-Up Procedure](#7-bring-up-procedure)
8. [The WiFi Bridge](#8-the-wifi-bridge)
9. [Software Stack](#9-software-stack)
10. [Results and Measurements](#10-results-and-measurements)
11. [Troubleshooting Catalogue](#11-troubleshooting-catalogue)
12. [Known Issues and Open Items](#12-known-issues-and-open-items)
13. [Appendix A — Source Files](#appendix-a--source-files)

---

## Where everything lives

This document is part of a repo that holds the entire record. Every path below is
relative to the repo root, `C:\Users\abhij\Desktop\NeuroRehab\cyton-hardware\`.

| Folder | What is in it |
|---|---|
| `docs/` | This document, the two wiring guides, the electrode research and the electrode decision |
| `hardware/` | What was sent to JLCPCB: `gerbers/`, `bom/` (BOM + CPL), `quotes/`, `component-selection/`, and `reference/` (schematic, board photos, DesignSpark source) |
| `firmware/cyton/` | The exact sketch flashed to the board — the one with `board.beginDebug()` — and the hex the IDE built from it |
| `firmware/bridge/` | The XIAO ESP32C3 bridge sketch |
| `firmware/images/` | `CytonDebug-with-bootloader.hex`, the merged image actually running on the PIC32 |
| `firmware/tools/` | `merge-hex.ps1` and `listen-cyton.ps1` |
| `software/` | Flask server, CLI client, cue protocols, fake bridge, web UI, and `recordings/` |
| `logs/` | The first serial capture taken off the board |
| `vendor/`, `mechanical/` | Upstream clones and headset STLs — on disk, git-ignored, pinned in `VENDOR.md` |

---

## 1. System Architecture

```
┌──────────────┐   UART 115200   ┌──────────────┐   WiFi TCP    ┌──────────────┐
│ OpenBCI      │  D11 ────────►  │ XIAO         │  192.168.4.1  │ Laptop       │
│ Cyton        │  D12 ◄────────  │ ESP32C3      │  :3000        │ Flask + web  │
│ PIC32MX250   │  GND ────────   │ (SoftAP)     │◄─────────────►│ UI / Python  │
│ + ADS1299    │                 │              │               │              │
└──────────────┘                 └──────────────┘               └──────────────┘
      │                                                                 │
      │ ICSP (PICkit 3.5) — programming only                            │
      │ D11/D12 also feed a USB-TTL adapter as an independent monitor   │
      └─────────────────────────────────────────────────────────────────┘
```

**Data path:** ADS1299 → SPI → PIC32 → UART2 (Serial1, D11/D12) → XIAO ESP32C3 → WiFi TCP → Python → browser.

**Why Serial1 and not Serial0:** the PIC's primary UART (Serial0) terminates at the unpopulated RFD22301 footprint with no accessible breakout. The debug UART (Serial1) lands on the ICSP header pins, which are exposed on J3/J4. Firmware built with `beginDebug()` mirrors all output to both ports and accepts commands on both. See §4.4.

---

## 2. Hardware Inventory

### 2.1 Fabrication

Board fabricated and assembled by JLCPCB from the OpenBCI V3 Hardware Design Files.

| Setting | Value | Rationale |
|---|---|---|
| Layers | 4 | Power/ground shielding planes for sensitive analog inputs |
| Material | FR-4, 1.6 mm | Standard |
| Surface finish | **ENIG** | **Mandatory.** HASL leaves uneven solder domes that cause the LGA-16 accelerometer to tombstone and risk bridges on the 0.5 mm-pitch ADS1299 TQFP-64 |
| Assembly | Both sides | |
| Confirm parts placement | Yes | CPL zero-degree conventions differ from JLCPCB tape-and-reel; an SMT engineer corrects centroids/rotations |
| Depanel | Yes | CNC removal of tooling rails |
| HS code | 847330 ("Development Board") | Classifying as medical/EEG triggers Indian customs holds demanding CDSCO/FDA import licences |

### 2.2 Deliberately unpopulated

| Ref | Part | Reason | Consequence |
|---|---|---|---|
| **BLE1** | RFD22301 BTLE module | Obsolete, not stocked by JLCPCB | **No radio.** Serial0 terminates at a dead footprint. Replaced by the XIAO bridge. |
| **SW2** | CUS-3B SP3T slide switch | Proprietary footprint | No power switch — pads bridged on the "PC" position |
| **PL1** | 26-way dual header | Through-hole, costly on an SMD board | EEG input connector must be hand-soldered |

### 2.3 Key components (BOM extract)

| Ref | Part | Package | JLCPCB |
|---|---|---|---|
| U1 | LIS3DHTR accelerometer | LGA-16 | C15134 |
| U2 | SN74LVC1G32DCKR OR gate | SOT-353 | C7840 |
| U3 | LM2664M6 voltage inverter | SOT-23-6 | C108573 |
| U4 | TLV70025QDDCRQ1 LDO | SOT-23-5 | C19619 |
| U5 | MCP1754T-3302E/OT LDO | SOT-23-5 | C295712 |
| **U6** | **ADS1299IPAG** | **TQFP-64** | C476817 |
| **U7** | **PIC32MX250F128B** | **SSOP-28** | C1337166 |
| VR1 | TPS72325DBVR −2.5 V reg | SOT-23-5 | C69932 |
| X1 | ABMM2-8.000MHZ crystal | SMT | C431529 |
| D1 | LTST-C193TBKT blue LED | 0603 | C2290 |
| CONN1 | MicroSD slot | SMT | C91145 |

### 2.4 Tools used

| Tool | Purpose |
|---|---|
| **PICkit 3.5** | ICSP programming (5 wires — see §7.1) |
| **MPLAB X IPE v5.35** | Flashing the merged hex |
| **Arduino IDE 2.x** | Compiling Cyton firmware (chipKIT core) and XIAO sketch (ESP32 core) |
| **CP2102 USB-TTL** (3.3 V) | Independent serial monitor on D11/D12, `VID_10C4&PID_EA64` |
| **Seeed XIAO ESP32C3** | WiFi bridge, `VID_303A&PID_1001` |
| Multimeter | Continuity checks |

---

## 3. Source Repositories

Three upstream repositories, all public, all pinned. They sit under `vendor/` (and
`mechanical/` for the headset) and are **git-ignored** — nothing tracked in this repo
depends on them being present, and each can be restored with one command. Everything in
those trees that was *not* upstream — the regenerated Gerbers, the JLCPCB BOM and CPL,
the quotes — was lifted out into `hardware/` and is tracked here. See `VENDOR.md`.

| Path in this repo | Upstream | Pinned at | Role |
|---|---|---|---|
| `vendor/openbci-v3-hardware/` | `OpenBCI/V3_Hardware_Design_Files` | `6bce559` (2023-02-06) | Schematic, PCB, upstream Gerbers, BOM/CPL. Two files locally modified — §3.1 |
| `vendor/openbci-v3-hardware/OpenBCI_Cyton_Library/` | `OpenBCI/OpenBCI_Cyton_Library` | `24e1c42` (2025-07-24) | Cyton firmware, **v3.1.5** — what was flashed |
| `vendor/openbci-v3-hardware/PIC32-avrdude-bootloader/` | `chipKIT32/PIC32-avrdude-bootloader` | `95cf5d9` (2024-02-08) | chipKIT bootloader source + prebuilt hex |
| `mechanical/ultracortex-upstream/` | `OpenBCI/Ultracortex` | `338b52b` (2022-09-29) | Headset mechanicals. Only `Mark_IV` is checked out — §3.3 |

`vendor/PIC32-avrdude-bootloader-master/` and its zip are an older separate download of
the same bootloader, kept because the flashing was done from that copy.

> The two repos nested inside `vendor/openbci-v3-hardware/` are plain clones, **not
> submodules** — the parent sees them as untracked directories.

### 3.1 Local modifications to the hardware repo

Two tracked files differ from upstream. Both are copied into `hardware/`, so they
survive even if the clone is deleted:

| File in the clone | Change | Copy tracked here |
|---|---|---|
| `OpenBCI Cyton Designs/OpenBCI 32bit.pcb` | Re-saved from DesignSpark (360 KB → 395 KB) | `hardware/reference/OpenBCI 32bit.pcb` |
| `OBCI_Cyton_Plots/OBCI_V4_C (Component Positions CSV).csv` | Header rewritten to JLCPCB CPL format: `Name,Component,Side,Centre X,Centre Y,Rotation` → `Designator,Val,Layer,Mid X,Mid Y,Rotation` | `hardware/bom/CPL-OBCI_V4_C-jlcpcb-format.csv` |

Everything that was merely *untracked* in that clone now lives here as tracked files:

| Now at | Contents |
|---|---|
| `hardware/gerbers/` | The regenerated Gerber set (`OpenBCI 32bit - *.gbr`), both NC drill files, `OpenBCI 32bit.mop`, the plot report, `gerber.zip` — **the files the board was actually built from** |
| `hardware/bom/` | `Cyton_BOM_AutoMatch.csv`, `Cyton_BOM_Turnkey.csv`, `Cyton_PNP_Fixed_MM.csv`, `OBCI_BOM_JLCPCB.csv`, and the CPL above |
| `hardware/quotes/` | JLCPCB, Robu and LionCircuits quotes, plus the initial and final quote |
| `hardware/component-selection/` | The five "Component selection" PDFs, in revision order |
| `hardware/reference/` | `OBCI_V3_32bit-Schematic.jpg`, board photos, DesignSpark `.sch` / `.pcb` |

### 3.2 Key design files

| File | Notes |
|---|---|
| `hardware/reference/OBCI_V3_32bit-Schematic.jpg` | **The schematic.** 5037×3237 px. Everything in §4 was read from here. |
| `hardware/reference/OpenBCI 32bit.sch` | DesignSpark source |
| `hardware/bom/CPL-OBCI_V4_C-jlcpcb-format.csv` | Pick-and-place / component locations, JLCPCB header |

### 3.3 The Ultracortex clone, and what was deleted

`mechanical/ultracortex-upstream/` has an empty index against a populated HEAD, so
`git status` reports ~686 staged deletions and `git ls-files` returns nothing. Only
`Mark_IV` is checked out. One command restores every revision in the pack — `Mark_1`,
`Mark_2`, `Mark_3`, `Mark_III_Nova`, `Mark_III_Nova_REVISED`, `Mark_IV`:

```bash
git -C "C:/Users/abhij/Desktop/NeuroRehab/cyton-hardware/mechanical/ultracortex-upstream" reset --hard HEAD
```

**Deleted 1 October 2026** as verified duplicates, freeing 756 MB:

| Deleted | Size | Why it was safe |
|---|---|---|
| `Ultracortex2/` | 502 MB | `.git` only, same remote at the same commit `338b52b` |
| `Ultracortex_Downloaded/` | 175 MB | `Mark_1`–`Mark_3`, all present in the kept clone's HEAD tree |
| `Ultracortex.zip` | 79 MB | Zip of the same upstream repo |

`mechanical/a1-mini-prints/` is **not** upstream — those are the Bambu A1 Mini plates and
the Cyton case that were actually printed.

---

## 4. Schematic Reference

> Everything here was read directly from `OBCI_V3_32bit-Schematic.jpg`. **This section is the single most valuable output of the whole exercise** — the pin mapping is what unblocked the bring-up.

### 4.1 PIC32MX250F128B (U7) — complete pinout

SSOP-28, **top side**, CPL position (1321, 780), rotation 90°.

| Pin | chipKIT | Net | Function |
|---:|---|---|---|
| 1 | — | MCLR | Reset. Pull-up **R7 470 K**; **SW3** pulls to GND |
| 2 | D9 | DRDY | ADS1299 data-ready interrupt |
| 3 | D10 | MOSI | SPI |
| 4 | **D11** | **PGD** | **ICSP data + BLUE LED D1 (via R8 1 K) + Serial1 TX** |
| 5 | **D12** | **PGC** | **ICSP clock + Serial1 RX** |
| 6 | D13 | D13 | Broken out on J3-1 |
| 7 | **D14** | **TXD** | **Serial0 TX** → BLE1 pin 4 |
| 8 | — | GND | |
| 9 | D15 | — | X1 8 MHz crystal (C23 18 pF) |
| 10 | D16 | — | X1 8 MHz crystal (C20 18 pF) |
| 11 | **D17** | **BOOT_EN** | Bootloader program-enable. Pull-**down** **R9 470 K**; **SW1** pulls to DVDD |
| 12 | D18 | D18 | Broken out on J4-3 |
| 13 | — | Vdd | |
| 14 | D0 | INT1 | |
| 15 | — | Vbus | |
| 16 | D1 | CS4 | |
| 17 | D2 | CS3 | |
| 18 | D3 | CS2 | |
| 19 | — | GND | |
| 20 | — | Vcap | C25 10 µF |
| 21 | D4 | RESET | ADS1299 reset |
| 22 | D5 | MISO | SPI |
| 23 | — | Vdd | |
| 24 | **D6** | **RXD** | **Serial0 RX** ← BLE1 pin 3 |
| 25 | D7 | SCLK | SPI |
| 26 | D8 | CS1 | |
| 27 | — | GND | |
| 28 | — | Vdd | |

### 4.2 J3 / J4 — "CHIPKIT PIN BREAKOUT"

Two 4-pin headers, top side. **These are the only accessible digital breakouts on the board.**

| J3 | Signal | | J4 | Signal |
|---:|---|---|---:|---|
| 1 | D13 | | 1 | **BOOT_EN** |
| 2 | **PGC (D12)** | | 2 | **MCLR** |
| 3 | **DVDD** | | 3 | D18 |
| 4 | **AGND** | | 4 | **PGD (D11)** |

### 4.3 BLE1 (RFD22301) footprint — bottom side

**This is the finding that cost the most time.** The pads silkscreened `RFTX` / `RFRX` / `RFRESET` are **not** the PIC's UART.

| BLE1 pin | Module signal | Net | Reaches the PIC? |
|---:|---|---|---|
| 1, 2, 8, 9, 10, 12, 18, 19 | GND | AGND | — |
| **3** | GPIO2 | **RXD** | ✅ **PIC pin 24 (D6)** |
| **4** | GPIO3 | **TXD** | ✅ **PIC pin 7 (D14)** |
| 5 | GPIO4 | BLE Enable | via R11 470 K, D10 3 V zener, R10 10 K |
| 6 | GPIO5 | PGC | |
| 7 | GPIO6 | — | not connected |
| 11 | EXT ANT | — | not connected |
| 13 | 3V | DVDD | |
| 14 | RESET | RF_RESET | ❌ module only |
| 15 | FACTORY | — | not connected |
| **16** | GPIO0/AREF | **RF_RXD** | ❌ **module only** |
| **17** | GPIO1 | **RF_TXD** | ❌ **module only** |

> **`RF_TXD` / `RF_RXD` are the RFduino module's own serial port (its GPIO0/GPIO1), broken out so you can flash the radio.** They never touch the PIC32. With BLE1 unpopulated they are **dead traces terminating at an empty footprint.**

Schematic annotation on this block (an errata applied to the design):

```
Change R10 to D10 3V Zener CZRQR52C3-HF
Change R11 to 470K
Add R10 10K to drain Zener
```

### 4.4 The two UARTs

| | Serial0 (UART1) | Serial1 (UART2) |
|---|---|---|
| TX pin | D14 (RB3), PIC pin 7 | **D11 (RB0/PGED1), PIC pin 4** |
| RX pin | D6 (RB13), PIC pin 24 | **D12 (RB1/PGEC1), PIC pin 5** |
| Goes to | BLE1 pins 4/3 (empty footprint) | **J4-4 / J3-2 (accessible)** |
| Purpose | Radio link | Debug / "sniff mode" |
| Usable on this board | ❌ not physically reachable | ✅ **this is the one to use** |

From `chipkit-core/pic32/2.1.0/variants/openbci/Board_Defs.h`:

```c
#define _SER0_TX_OUT   PPS_OUT_U1TX
#define _SER0_TX_PIN   14      // RB3
#define _SER0_RX_IN    PPS_IN_U1RX
#define _SER0_RX_PIN   6       // RB13
#define _SER1_TX_OUT   PPS_OUT_U2TX
#define _SER1_TX_PIN   11      // RB0  PGED1
#define _SER1_RX_IN    PPS_IN_U2RX
#define _SER1_RX_PIN   12      // RB1  PGEC1
```

> ⚠️ **The library's own comment is stale.** `OpenBCI_32bit_Library.cpp` instructs you to edit `Board_Defs.h` lines 311/313 from `7`/`10` to `11`/`12`. **chipKIT core 2.1.0 already ships 11/12.** Do not edit it.

### 4.5 Other schematic blocks

| Block | Contents |
|---|---|
| **Power supply** | Battery connect → SW2 (SP3T) → RAW. Voltage inverter (LM2664), +3 V reg (MCP1700T-2502E/TT per notes / MCP1754), +2.5 V reg, −2.5 V reg (TPS72325). Generates AVDD/AVSS **±2.5 V for the ADS1299** |
| **ADS1299** | U6, 8 differential inputs with CAY16-F4 resistor arrays and TPD4E1B06 TVS arrays. BIAS_DRV, BIAS_INV, SRB1/SRB2 |
| **Accelerometer** | LIS3DH on SPI (CS4) |
| **SD card** | CONN1, `SD_SS` = chipKIT pin 2 |
| **Input connector** | PL1, EEG inputs 1N/1P…8N/8P, SRB, BIAS, AVDD/AVSS |
| **Daisy bus** | DVDD, MISO, MOSI, SCLK, RESET, PGC/PGD, CS2/CS3 |

### 4.6 Connector/switch positions (from CPL)

| Ref | Value | Side |
|---|---|---|
| J1 | PINHEAD-8 | Top |
| J2 | 2WP | Top |
| J3, J4 | 4WP | Top |
| PL1 | **26WDP** (26-way dual = 13×2) | Top |
| PL2 | SMT_QUAD_04 | Bottom |
| B1 | BATT | Bottom |
| SW2 | **CUS-3B SP3T SLIDE SWITCH** | Bottom |
| SW1, SW3 | SW_TACT (PTS810) | Top |
| BLE1 | RFD22301 | Bottom |
| CONN1 | SEEEDmicroSD | Bottom |

---

## 5. Firmware Reference

`OpenBCI_32bit_Library` **v3.1.5**, installed at `Documents/Arduino/libraries/OpenBCI_32bit_Library`.

Required companion libraries (all present):

| Library | Version | Provides |
|---|---|---|
| OpenBCI_32bit_Library | 3.1.5 | Core |
| OpenBCI_32bit_SD | 2.0.0 | `OBCI32_SD.h` |
| OpenBCI_Wifi_Master | 1.0.1 | `OpenBCI_Wifi_Master.h` |
| DSPI, EEPROM | (chipKIT core) | SPI, EEPROM |

### 5.1 `begin()` vs `beginDebug()` — the critical distinction

```c
void OpenBCI_32bit_Library::begin(void)          { boardBegin(); }
void OpenBCI_32bit_Library::beginDebug(void)     { beginDebug(OPENBCI_BAUD_RATE); }

boolean OpenBCI_32bit_Library::boardBegin(void) {
  beginPinsDefault();
  beginSerial0();
  delay(10);
  boardBeginADSInterrupt();
  boardReset();
  return true;
}

boolean OpenBCI_32bit_Library::boardBeginDebug(int baudRate) {
  beginPinsDebug();
  beginSerial0();
  beginSerial1(baudRate);
  curBoardMode = BOARD_MODE_DEBUG;
  curDebugMode = DEBUG_MODE_ON;
  boardBeginADSInterrupt();
  boardReset();
  return true;
}
```

**Pin configuration differs, and this matters physically:**

```c
void OpenBCI_32bit_Library::beginPinsDefault(void) {
  pinMode(OPENBCI_PIN_LED, OUTPUT);        // pin 11
  digitalWrite(OPENBCI_PIN_LED, HIGH);     // <-- LED SOLID ON
  pinMode(OPENBCI_PIN_PGC, OUTPUT);        // pin 12 driven as OUTPUT
}

void OpenBCI_32bit_Library::beginPinsDebug(void) {
  pinMode(OPENBCI_PIN_SERIAL1_TX, OUTPUT); // pin 11
  pinMode(OPENBCI_PIN_SERIAL1_RX, INPUT);  // pin 12 becomes INPUT
}
```

> ⚠️ In **default** mode the PIC **drives D12 as an output**. Connecting a serial adapter's TX to D12 in that mode causes contention. `beginDebug()` makes it an input. **Never attach a transmitter to D12 unless the firmware was built with `beginDebug()`.**

> 💡 **`beginPinsDefault()` turning the LED solid on is a free diagnostic** — see §11.1.

Both functions **always return `true`**, so the `Board up` / `Board err` branch is decorative — `Board err` can never print. It is not an ADS1299 health check.

### 5.2 Output mirroring

```c
void OpenBCI_32bit_Library::writeSerial(uint8_t c) {
  if (iSerial0.tx) Serial0.write(c);
  if (iSerial1.tx) Serial1.write(c);
}
```

In debug mode **every outgoing byte goes to both ports** — banner *and* streaming EEG data. `DefaultBoard.ino` also processes incoming commands from both:

```c
if (board.hasDataSerial1()) {
    char newChar = board.getCharSerial1();
    sdProcessChar(newChar);
    board.processChar(newChar);
}
```

**Consequence:** Serial1 (D11/D12) is a fully bidirectional substitute for the radio link. This is what makes the whole project work.

### 5.3 The boot banner

`boardReset()` runs at the end of both begin paths and prints **unprompted**, ~500 ms after every power-up or `v`:

```c
void OpenBCI_32bit_Library::boardReset(void) {
  initialize();                    // ADS + accelerometer + daisy
  delay(500);
  configureLeadOffDetection(LOFF_MAG_6NA, LOFF_FREQ_31p2HZ);
  printlnAll("OpenBCI V3 8-16 channel");
  printAll("On Board ADS1299 Device ID: 0x");
  printlnHex(ADS_getDeviceID(ON_BOARD));      // must read 0x3E
  if (daisyPresent) { ... }
  printAll("LIS3DH Device ID: 0x");
  printlnHex(LIS3DH_getDeviceID());           // 0x33
  printlnAll("Firmware: v3.1.2");
  sendEOT();                                   // "$$$"
  delay(5);
  wifi.reset();
}
```

> 🔑 **The board announces itself. You never send a command to get the banner.** Open your terminal *before* powering on, or you miss it. Assuming otherwise wasted weeks.
>
> 🔑 **`ADS_getDeviceID(ON_BOARD)` reading `0x3E` is the definitive proof the ADS1299 was soldered correctly.** It is a real SPI transaction against the chip.

### 5.4 Constants

```c
#define OPENBCI_BAUD_RATE                 115200
#define OPENBCI_BAUD_RATE_BLE               9600
#define OPENBCI_BAUD_RATE_MIN_NO_AVG      200000
#define OPENBCI_BOP                          'A'   // 0x41 — packet start
#define PCKT_START                          0xA0   // defined, NOT used for serial
#define PCKT_END                            0xC0
#define OPENBCI_PACKET_SIZE                   33
#define OPENBCI_SAMPLE_RATE_250              250
#define OPENBCI_SAMPLE_RATE_125              125
#define OPENBCI_NUMBER_BYTES_PER_ADS_SAMPLE   24
#define OPENBCI_NUMBER_OF_BYTES_AUX            6
#define OPENBCI_ADS_BYTES_PER_CHAN             3
#define OPENBCI_NUMBER_OF_CHANNELS_DEFAULT     8
#define OPENBCI_NUMBER_OF_CHANNELS_DAISY      16
#define OPENBCI_PIN_LED                       11
#define OPENBCI_PIN_PGC                       12
#define OPENBCI_PIN_SERIAL1_TX                11
#define OPENBCI_PIN_SERIAL1_RX                12
#define SD_SS                                  2
#define BLE_BYTES_PER_PACKET                  20
#define BLE_BYTES_PER_SAMPLE                   6
#define BLE_SAMPLES_PER_PACKET                 3
#define BLE_TOTAL_DATA_BYTES                  18
```

### 5.5 The high-baud no-average path

```c
boolean downsample = true;
if (iSerial0.tx == false && iSerial1.baudRate > OPENBCI_BAUD_RATE_MIN_NO_AVG)
    downsample = false;
```

`ADS_writeChannelDataNoAvgDaisy()` runs only when Serial1 exceeds 200000 baud with Serial0 TX disabled. **Relevant only with a Daisy (16-channel) board** — for 8 channels both paths write the same 24 bytes. Not used here.

### 5.6 Bootloader

`vendor/openbci-v3-hardware/PIC32-avrdude-bootloader/BootloadersCurrent-hex/**UDB32_MX2_DIP.hex**` — the Cyton's bootloader. Config lives under `_BOARD_UDB32_MX2_DIP_` in `bootloaders/configs/openbci.h`.

```c
#define CAPABILITIES (blCapBootLED | blCapDownloadLED | blCapUARTInterface \
                    | blCapProgramButton | blCapVirtualProgramButton | CAPCOMMON)
#define BLedLat  B      // Boot LED on PORTB
#define BLedBit  0      // bit 0 = RB0 = D11 = the blue LED
#define LedOn    Low
#define BntOn    High
```

Config bits:

```c
#pragma config FNOSC    = PRIPLL      // primary oscillator with PLL
#pragma config POSCMOD  = XT          // 8 MHz crystal
#pragma config FPLLIDIV = DIV_2
#pragma config FPLLMUL  = MUL_20
#pragma config FPLLODIV = DIV_2       // -> 40 MHz core
#pragma config FPBDIV   = DIV_1
#pragma config UPLLEN   = ON
#pragma config FWDTEN   = OFF
#pragma config JTAGEN   = OFF
#pragma config ICESEL   = ICS_PGx1    // ICSP channel 1 = PGED1/PGEC1
#pragma config CP       = OFF
```

**Key facts:**
- `blCapUARTInterface` — the bootloader uploads over **UART only**, no USB. On a stock Cyton that UART runs through the RFduino to the dongle. With BLE1 unpopulated, **bootloader uploads are impossible** — you must use ICSP.
- `blCapProgramButton` — **BOOT_EN (D17)** held high at reset keeps it in upload mode. R9 470 K pulls it low; SW1 pulls it high.
- The Boot LED is **RB0 = D11 = the blue LED = PGD**. See §11.1.
- `ICESEL = ICS_PGx1` confirms programming happens on PGED1/PGEC1 = D11/D12.

### 5.7 Memory map

| Region | Address range | Contents |
|---|---|---|
| Program flash | `0x1D0000F8 … 0x1D016AF3` | Application (our `beginDebug` build, ~92 KB) |
| Program flash | `0x1D0000F8 … 0x1D016A53` | *(stock reference build, for comparison)* |
| Boot flash | `0x1FC00000 … 0x1FC00BFF` | Bootloader (3072 bytes) |

No overlap — this is why bootloader and application merge cleanly into one hex.

---

## 6. Serial Protocol Reference

### 6.1 Packet format

**33 bytes, 250 packets/sec = 8250 bytes/sec.**

| Offset | Bytes | Content |
|---:|---:|---|
| 0 | 1 | **`0x41`** (`'A'`, `OPENBCI_BOP`) |
| 1 | 1 | Sample counter, wraps 0–255, +1 per packet |
| 2–25 | 24 | 8 channels × 3 bytes, **signed 24-bit big-endian** |
| 26–31 | 6 | Aux / accelerometer |
| 32 | 1 | Stop byte: `PCKT_END \| packetType` = **`0xC0`–`0xCF`** |

```c
writeSerial(OPENBCI_BOP);                          // 0x41
...
writeSerial((uint8_t)(PCKT_END | packetType));     // 0xC0..0xCF
```

> ⚠️ **The start byte is `0x41`, not `0xA0`.** Older OpenBCI documentation says `0xA0`, and `PCKT_START 0xA0` *is* defined in the header — but `sendChannelData()` writes `OPENBCI_BOP` = `'A'` = `0x41`. Verified empirically and in source. A parser looking for `0xA0` will never sync.

### 6.2 Scale factor

```
volts per count = VREF / gain / (2^23 - 1)
                = 4.5 / 24 / 8388607
                = 2.23517e-8 V
                = 0.0223517 µV per count
```

| Raw | Signed | µV | Meaning |
|---|---:|---:|---|
| `0x800000` | −8,388,608 | **−187,500** | Negative full scale — **railed** |
| `0x7FFFFF` | +8,388,607 | +187,500 | Positive full scale |
| `0x0289A0` | +166,304 | +3,717 | 2× test signal, positive level |

Railed (`±187500 µV`) means the channel is **not measuring** — open input, or a detached electrode.

### 6.3 Command reference

All commands are single ASCII characters, sent on Serial0 or Serial1.

**Stream control**

| Char | Constant | Action |
|---|---|---|
| `b` | `OPENBCI_STREAM_START` | Start streaming |
| `s` | `OPENBCI_STREAM_STOP` | Stop streaming |
| `v` | `OPENBCI_MISC_SOFT_RESET` | Soft reset — re-sends the boot banner |
| `?` | `OPENBCI_MISC_QUERY_REGISTER_SETTINGS` | Dump all registers |

**Channel configuration**

| Char | Constant | Action |
|---|---|---|
| `d` | `OPENBCI_CHANNEL_DEFAULT_ALL_SET` | Reset all channels to default (undoes a test signal) |
| `D` | `OPENBCI_CHANNEL_DEFAULT_ALL_REPORT` | Report the default settings |
| `~` | `OPENBCI_SAMPLE_RATE_SET` | Set sample rate (multi-char) |

**Test signals** — invaluable before you own electrodes

| Char | Constant | Signal |
|---|---|---|
| `0` | `..._CONNECT_TO_GROUND` | All channels to internal ground → **noise floor** |
| `-` | `..._CONNECT_TO_PULSE_1X_SLOW` | ±1.875 mV square, ~1 Hz |
| `=` | `..._CONNECT_TO_PULSE_1X_FAST` | ±1.875 mV square, ~2 Hz |
| `[` | `..._CONNECT_TO_PULSE_2X_SLOW` | **±3.75 mV square, ~1 Hz** |
| `]` | `..._CONNECT_TO_PULSE_2X_FAST` | ±3.75 mV square, ~2 Hz |
| `p` | `..._CONNECT_TO_DC` | DC level |

Test-signal amplitude = `±(VREFP − VREFN) / 2.4 mV` per unit. With VREF = 4.5 V: **1× = ±1.875 mV, 2× = ±3.75 mV**. Frequency = fCLK/2²¹ ≈ 0.977 Hz (slow), fCLK/2²⁰ ≈ 1.95 Hz (fast).

> ⚠️ **Test signals do not survive a reset.** Any power-cycle, `v`, or reflash returns channels to normal input mode. Seeing `±187500 µV` again is expected, not a fault.

**SD card logging** (from `SD_Card_Stuff.ino`)

| Char | Duration | | Char | Duration |
|---|---|---|---|---|
| `A` | 5 min | | `J` | 4 hr |
| `S` | 15 min | | `K` | 12 hr |
| `F` | 30 min | | `L` | 24 hr |
| `G` | 1 hr | | `a` | 512 blocks |
| `H` | 2 hr | | `h` | 50 blocks (test) |
| `j` | close file | | | |

Autonomous SD logging with no host:

```c
void setup() {
  board.beginDebug();
  SDfileOpen = setupSDcard('A');   // 'A' = 5 minutes
  delay(1000);
  board.streamStart();             // no 'b' command needed
}
```

---

## 7. Bring-Up Procedure

The procedure that actually worked, in order.

### 7.1 ICSP wiring (PICkit 3.5 → Cyton)

| PICkit pin | Signal | Cyton pad |
|---:|---|---|
| 1 (arrow) | MCLR/VPP | **J4 pin 2** (MCLR) |
| 2 | VDD target | **J3 pin 3** (DVDD) |
| 3 | VSS/GND | **J3 pin 4** (AGND) |
| 4 | PGD / ICSPDAT | **J4 pin 4** (PGD / D11) |
| 5 | PGC / ICSPCLK | **J3 pin 2** (PGC / D12) |

Connect all five before powering the Cyton. The PICkit does **not** power the target — the board runs from its own supply.

> ICSP bypasses the bootloader entirely. **Do not** put the board into bootloader mode first (SW1+SW3); it is irrelevant and the merged image overwrites the bootloader anyway.

### 7.2 Build the firmware

1. Arduino IDE → **File → Examples → OpenBCI_32bit_Library → DefaultBoard**
2. Confirm **two tabs**: `DefaultBoard` and `SD_Card_Stuff`. Both are required.
3. **File → Save As** to your sketchbook (do not edit the library example in place — a library update silently wipes it). The sketch that was saved and flashed is preserved at `firmware/cyton/DefaultBoard-beginDebug/`; the Arduino IDE's working copy stays at `Documents\Arduino\DefaultBoard_copy_20260827202641\`.
4. Change **one line**:

```c
void setup() {
  board.beginDebug();      // was board.begin();
  wifi.begin(true, true);  // leave as-is
}
```

5. Board: **chipKIT → OpenBCI 32** (variant `chipKIT.pic32.openbci`)
6. **Sketch → Export Compiled Binary** → produces `build/chipKIT.pic32.openbci/<sketch>.ino.hex`

### 7.3 Merge bootloader + application

Intel HEX rules:
- Exactly **one** EOF record (`:00000001FF`), on the **last line**. A programmer stops at the first one it sees.
- The two files must **not overlap** in address space. (They don't — see §5.7.)
- The appended file must begin with its own type-04 extended-linear-address record, or its data inherits the previous segment.

```bash
powershell -File "C:\Users\abhij\Desktop\NeuroRehab\cyton-hardware\firmware\tools\merge-hex.ps1" -Bootloader "C:\Users\abhij\Desktop\NeuroRehab\cyton-hardware\vendor\openbci-v3-hardware\PIC32-avrdude-bootloader\BootloadersCurrent-hex\UDB32_MX2_DIP.hex" -App "C:\Users\abhij\Documents\Arduino\<sketch>\build\chipKIT.pic32.openbci\<sketch>.ino.hex" -Out "C:\Users\abhij\Desktop\NeuroRehab\cyton-hardware\firmware\images\CytonDebug-with-bootloader.hex"
```

The script strips EOF records, checks for address overlap and refuses to write a broken image, inserts a type-04 record if needed, and prints the resulting memory map.

Verified output:

```
Bootloader regions:  0x1FC00000 .. 0x1FC00BFF
Application regions: 0x1D0000F8 .. 0x1D01000B
                     0x1D01000C .. 0x1D016AF3
Wrote CytonDebug-with-bootloader.hex (6909 records, exactly 1 EOF at the end).
```

All 6909 records pass their checksums; structurally identical to OpenBCI's own combined image.

### 7.4 Flash with MPLAB IPE

Device **PIC32MX250F128B** → Connect → browse to the merged hex → **Erase** → **Program**.

A successful log:

```
Target voltage detected
Target device PIC32MX250F128B found.
Device ID Revision = B0
Hex file loaded successfully.
Device Erased...
Programming...
The following memory area(s) will be programmed:
program memory: start address = 0x1d000000, end address = 0x1d016fff
boot config memory
configuration memory
Programming/Verify complete
```

`boot config memory` appearing confirms the bootloader block landed. `Programming/Verify complete` means IPE read flash back and compared it.

### 7.5 Disconnect and monitor

1. **Power off. Unplug all five PICkit wires.** The PICkit holds MCLR and drives D11/D12 — the exact pins the debug UART uses.
2. Wire a **3.3 V** USB-TTL adapter, **receive-only**:

| Cyton | → | Adapter |
|---|---|---|
| **J4 pin 4** (D11) | → | **RX** |
| **J3 pin 4** (AGND) | → | **GND** |

   Leave the adapter's **TX, 5 V and 3V3 disconnected.** Receive-only sidesteps every level-shifting question — many CH340 modules drive 5 V TX, which can damage the 3.3 V PIC32.

3. **Open the terminal at 115200 first, then power the Cyton.** The banner appears once, ~500 ms after power-up, then silence forever.

```bash
powershell -File "C:\Users\abhij\Desktop\NeuroRehab\cyton-hardware\firmware\tools\listen-cyton.ps1" -Port COM14 -Seconds 60
```

### 7.6 Success criterion

```
OpenBCI V3 8-16 channel
On Board ADS1299 Device ID: 0x3E
LIS3DH Device ID: 0x33
Firmware: v3.1.2
$$$Board up
$$$
```

**`0x3E` is the whole ballgame** — the PIC read that ID over SPI from the ADS1299 itself. `0x33` confirms the LIS3DH. Two fine-pitch chips reporting correct identities means power rails, SPI bus, crystal, and assembly are all good.

---

## 8. The WiFi Bridge

### 8.1 Why a XIAO ESP32C3

| | |
|---|---|
| **Voltage** | 3.3 V both sides — no level shifting, and it can safely *send* commands (an Arduino Mega's 5 V TX cannot) |
| **Bandwidth** | 8250 B/s = 82.5 kbps at 8N1 = **72 % of a 115200 link.** Works, but with thin headroom — chunked reads and an enlarged RX buffer are mandatory |
| **Transport** | **WiFi TCP.** BLE cannot sustain 8.25 KB/s — ~410 notifications/sec at 20 bytes each. The firmware's own BLE mode downsamples hard (`BLE_BYTES_PER_SAMPLE 6`) for exactly this reason |

### 8.2 XIAO ESP32C3 pin map

| Silkscreen | GPIO | Note |
|---|---|---|
| D0 | GPIO2 | ⚠️ strapping pin |
| **D1** | **GPIO3** | ← Cyton D11 (RX) |
| **D2** | **GPIO4** | → Cyton D12 (TX) |
| D3 | GPIO5 | |
| D4 | GPIO6 | SDA |
| D5 | GPIO7 | SCL |
| D6 | GPIO21 | ⚠️ **U0TXD** |
| D7 | GPIO20 | ⚠️ **U0RXD** |
| D8 | GPIO8 | ⚠️ strapping |
| D9 | GPIO9 | ⚠️ strapping |
| D10 | GPIO10 | |

> ⚠️ **Never use D6/D7 (GPIO20/21) for `Serial1`.** They are the ESP32C3's own UART0. With **USB CDC On Boot** disabled, `Serial` also lands there and the two fight — producing complete silence. Additionally, the ROM bootloader prints a boot log on GPIO21 at every reset; wired to the Cyton's RX that injects random command characters (`b`, `s`, digits) and reconfigures the board unpredictably.

### 8.3 Wiring

| Cyton | → | XIAO | Direction |
|---|---|---|---|
| **D11** (J4 pin 4) | → | **D1** (GPIO3) | Cyton transmits |
| **D12** (J3 pin 2) | ← | **D2** (GPIO4) | XIAO transmits |
| **AGND** (J3 pin 4) | ↔ | **GND** | required |

A USB-TTL adapter may share **D11** (its RX only) as an independent monitor. **Two receivers on one transmit line is fine** — neither drives it. **Two transmitters is contention** — only the XIAO connects to D12.

### 8.4 Network modes

| | `USE_SOFTAP 1` (default) | `USE_SOFTAP 0` |
|---|---|---|
| Mode | XIAO creates its own network | XIAO joins existing WiFi |
| SSID | `CytonBridge` / `neurorehab` | your network |
| Address | **`192.168.4.1:3000`** — fixed, always | DHCP, or `USE_STATIC_IP` |
| Signal | Strongest possible, no router hop | Whatever the room gives |
| Works with no WiFi | ✅ | ❌ |
| Laptop keeps internet | ❌ | ✅ |

AP mode was adopted after station mode measured **−86 dBm** — marginal, and at 8250 B/s sustained that drops samples.

### 8.5 IDE settings

- Board: **XIAO_ESP32C3**
- **USB CDC On Boot: ENABLED** ← not optional
- Port: the one with hardware ID `VID_303A&PID_1001`

> **Close the Serial Monitor before every upload.** The ESP32C3's USB port is generated by the chip and re-enumerates on reset; a monitor holding the old handle blocks the upload with `Could not open COMx, the port is busy`. Manual bootloader entry: hold **BOOT**, tap **RESET**, release **BOOT**.

---

## 9. Software Stack

All of it is in this repo. Paths are relative to the repo root.

| File | Lines | Purpose |
|---|---:|---|
| `firmware/bridge/CytonWiFiBridge.ino` | 302 | XIAO firmware — UART ↔ WiFi TCP bridge, packet integrity counter |
| `firmware/cyton/DefaultBoard-beginDebug/` | — | The sketch flashed to the Cyton (`board.beginDebug()`) and the hex the IDE produced from it |
| `software/cyton_server.py` | 453 | Flask backend — socket thread, ring buffer, CSV recording, REST API, cue runner |
| `software/cyton_experiments.py` | 179 | Timed cue protocols — signal check, alpha blocks, motor execution, motor imagery |
| `software/cyton_templates/index.html` | 415 | Web UI — 8-channel canvas plot, command buttons, recording, experiment cues |
| `software/cyton_client.py` | 335 | CLI — live view, ASCII scope, raw dump, matplotlib plot, LSL outlet |
| `software/fake_bridge.py` | 130 | Fake bridge — valid 250 Hz packets with no hardware attached |
| `firmware/tools/merge-hex.ps1` | 85 | Intel HEX merger with overlap detection |
| `firmware/tools/listen-cyton.ps1` | 88 | Bare serial listener with ADS1299 ID detection |
| `firmware/images/CytonDebug-with-bootloader.hex` | — | The working flashable image |

Line counts are as of 1 October 2026. The files are authoritative — read them, not a
copy of them.

### 9.1 Running it

```bash
python C:\Users\abhij\Desktop\NeuroRehab\cyton-hardware\software\cyton_server.py
```

Then open <http://127.0.0.1:5000>. For station mode: `--host <bridge ip>`.

With no hardware at all — two terminals, from `software/`:

```bash
python fake_bridge.py                      # synthetic Cyton on 127.0.0.1:3000
python cyton_server.py --host 127.0.0.1
```

CLI alternatives, from `software/`:

```bash
python cyton_client.py --send "[b" --plot      # 8-channel live graph
python cyton_client.py --send "[b" --scope 1   # ASCII scope, one channel
python cyton_client.py --raw 300               # 300 consecutive samples
python cyton_client.py --send b --lsl          # publish to Lab Streaming Layer
```

### 9.2 REST API

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | The UI |
| `/api/status` | GET | `connected`, `streaming`, `rate`, `dropped`, `bad`, `total`, `railed[]`, recording state, and the live experiment block (`cue`, `phase`, `step`, `remaining`) |
| `/api/data?since=N` | GET | New samples since index N (capped at 2000 per request) |
| `/api/command` | POST | `{"cmd": "b"}` — chars sent one at a time with 0.35 s spacing |
| `/api/record` | POST | `{"action": "start"\|"stop", "label": "..."}` |
| `/api/experiments` | GET | The protocol catalogue for the dropdown — id, name, description, step count, duration |
| `/api/experiment` | POST | `{"action": "start"\|"stop", "id": "athena_alpha", "label": "..."}`. Refuses to start unless the board is actually streaming |

### 9.3 Recording format

CSV to `software/recordings/cyton-YYYYMMDD-HHMMSS-label.csv`:

```csv
timestamp_iso,sample_index,sample_counter,phase,ch1_uV,ch2_uV,ch3_uV,ch4_uV,ch5_uV,ch6_uV,ch7_uV,ch8_uV
2026-08-31T08:45:47.248,2733,9,settle,12595.0962,653.8109,-187500.0224,...
```

`sample_index` is the absolute count since the server connected; `sample_counter` is the
Cyton's own 8-bit counter, so gaps are detectable in post-processing. `phase` carries the
experiment step label on every row, which is what makes the file epochable on its own.

An experiment also writes a companion `-events.csv`:

| Column | Meaning |
|---|---|
| `onset_iso` | Wall clock at the cue transition |
| `onset_sample_index` | **The authoritative onset** — an index into the data file |
| `onset_seconds` | The same onset in seconds at 250 Hz |
| `step_index`, `phase`, `cue`, `duration_s` | Which step it was and how long it ran |

**Recording happens server-side**, the moment data comes off the socket — closing the
browser cannot lose samples.

### 9.4 Design notes

- **Rolling 1-second rate**, not an average since connect, so it falls to 0 when
  streaming stops.
- **Idle is not an error.** The Cyton sends nothing until `b`; a `recv()` timeout must not
  tear down the connection. `PacketReader(sock, yield_idle=True)` yields `None` and stays
  connected.
- **Counters survive reconnects** via `_dropped_base` / `_bad_base`.
- **Three-state status:** green = streaming, amber = connected but idle, red = disconnected.
- **Auto-reconnect** every 2 s.
- **Packet integrity** is tracked, not just throughput — `0x41` … 33 bytes … `0xCx`,
  counting good against malformed, plus dropped-sample detection from the counter.
- **Cue onsets are stamped against the data timeline.** The experiment runner records the
  absolute sample index at each step transition and computes step deadlines as absolute
  offsets from the start, so browser lag or scheduling jitter cannot accumulate across the
  80+ steps of the motor protocols.

---

## 10. Results and Measurements

### 10.1 Chip identification

| Measurement | Result | Spec | Verdict |
|---|---|---|---|
| ADS1299 Device ID | **`0x3E`** | `0x3E` | ✅ TQFP-64 soldered correctly |
| LIS3DH Device ID | **`0x33`** | `0x33` | ✅ LGA-16 soldered correctly |
| PIC32 Device ID Rev | `B0` | — | ✅ |

### 10.2 Analog front end (2× test signal)

| Measurement | Result | Spec | Error |
|---|---|---|---|
| Amplitude | **±3.74 mV** | ±3.75 mV | **0.3 %** |
| Frequency | **0.96 Hz** | 0.977 Hz | **2 %** |
| Channel-to-channel spread | 208 counts ≈ **4.6 µV** on 3.7 mV | — | **0.13 %** |
| Noise on plateau | **±0.4 µV** | — | — |

Raw capture (channel 1, decimated to 25 Hz):

```
+3717.3 µV ×13   →   -3762.8 µV ×13   →   +3717.3 µV ×13   ...
```

Intermediate values (`-2509.9`, `+2464.3`) are single samples caught mid-edge — expected at 250 Hz against a ~1 Hz square.

### 10.3 Noise floor (all channels grounded, `0`)

| Measurement | Result |
|---|---|
| Noise, all 8 channels | **±1 µV** |
| DC offsets | −21 to −30 µV, tightly clustered |
| Channel uniformity | No outliers |

**Alpha waves are 10–50 µV**, giving **20–50× SNR headroom**. This is the measurement that predicts real EEG is achievable.

### 10.4 Link performance

| Measurement | Result |
|---|---|
| Throughput | **8250 B/s** (= 33 × 250, exactly) |
| Packet rate | **250 pkt/s**, 0 malformed |
| Sample counter | −6 per second in an 8-bit counter = +250 wrapping at 256 ✅ |

Three independent measurements of 250 Hz agreeing: byte throughput, packet count, and counter arithmetic.

> The `8250` / `8217` alternation in the bridge's report is a **counting artifact** — the 1-second window doesn't align with packet boundaries, so 249 or 250 packets land inside it. The difference is exactly 33 bytes. `0 BAD` is what proves integrity.

---

## 11. Troubleshooting Catalogue

Every trap encountered, with its signature. **Most produce the identical symptom — silence — which is why they were so expensive.**

### 11.1 The blue LED lies

`OPENBCI_PIN_LED` is **11**, and D11 is also **PGD** *and* the bootloader's Boot LED (`BLedLat B, BLedBit 0` = RB0). It lights in three different situations:

| LED behaviour | Meaning |
|---|---|
| Flickers randomly | PICkit is toggling PGD during ICSP |
| **Blinks** in a pattern | **Bootloader** running, waiting on UART |
| **Solid, bright, no blinking** | **Application running** (`beginPinsDefault()` sets it HIGH) |
| Flickers during transmission | Serial1 TX activity (idle UART sits high) |

> "I flashed it and got lights" is **not** evidence the application runs. Distinguishing *solid* from *blinking* is the whole diagnostic — and solid-on was what finally proved the firmware had been running correctly for days.

### 11.2 The board self-announces

No command produces the banner. It fires ~500 ms after power-up, then silence. **Open the terminal before switching on.** Sending `b` to "get output" tests nothing about the receive path.

### 11.3 RFTX / RFRX are dead pads

They are the RFduino's own GPIO0/GPIO1, exposed for flashing the radio module. With BLE1 unpopulated they terminate at an empty footprint. **The PIC's UART is at BLE1 pins 3/4** — module pads, effectively unreachable. Use D11/D12 instead.

### 11.4 A floating UART input manufactures data

A disconnected input isn't "nothing" — it's an antenna whose voltage drifts across the logic threshold. The UART interprets each wobble as a start bit and fabricates a byte.

Signature observed: **a steady ~225 B/s** of bytes dominated by `44`, `04`, `33`, `66`, `CC`, `FC` — regular alternating bit patterns.

> ⚠️ **This looks like structured data and is easy to misread as a baud-rate mismatch.** It isn't random because the board's own 250 Hz ADS1299/SPI activity couples capacitively into the floating trace — which also explains why the rate parks suspiciously near 250/sec.
>
> **How to tell:** a *driven, idle* UART line sits cleanly high and produces **zero** bytes. Real output is readable ASCII (`|OpenBCI V3 8-16 c...|`). Continuous unreadable bytes = floating wire.
>
> Confirming test: swapping the two pins changed nothing (30–390 B/s before, 220–390 after). If either pad had been live, swapping would have been dramatic.

### 11.5 XIAO GPIO20/21 collision

`Serial1.begin(115200, SERIAL_8N1, 20, 21)` puts Serial1 on the ESP32C3's own UART0. With **USB CDC On Boot** disabled, `Serial` is *also* there — the passthrough fights itself and outputs nothing. Use GPIO3/GPIO4 and enable USB CDC On Boot.

### 11.6 Windows serial ports are exclusive

Only one process may hold a COM port.

| Symptom | Cause | Fix |
|---|---|---|
| Port opens but shows nothing | Another Arduino IDE **window** has Serial Monitor open | Quit **all** IDE instances; check Task Manager for stragglers |
| `Access is denied` on upload | `serial-monitor.exe` holding the port | Close the Serial Monitor **tab** (✕) before every upload |
| Dropdown lists boards on impossible ports | Arduino IDE remembers manual board↔port pairings forever | Ignore, or clear with the pencil icon |

Diagnosing which port is real — Bluetooth phantoms clutter the list:

```powershell
Get-PnpDevice -Class Ports | Select-Object Status, FriendlyName, InstanceId
```

`USB\VID_303A&PID_1001` = Espressif (XIAO). `USB\VID_10C4&PID_EA64` = Silicon Labs CP2102. `BTHENUM\...` = Bluetooth phantom, never real.

### 11.7 Packet start byte is `0x41`, not `0xA0`

Documentation and the `PCKT_START` constant both say `0xA0`. Firmware v3.1.5 writes `OPENBCI_BOP` = `'A'` = `0x41`. A parser hunting `0xA0` reports `0 pkt/s` forever while data flows perfectly.

### 11.8 Test signals don't survive a reset

Power-cycle, `v`, or reflash → channels revert to normal input → open inputs → **`±187500 µV`**. Re-send `[`. Later, with electrodes attached, railing means a lead detached.

### 11.9 Windows abandons no-internet networks

Joined to `CytonBridge`, Windows silently reconnects to a network with internet. Symptom: server can't reach `192.168.4.1`.

```powershell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' }
Test-NetConnection -ComputerName 192.168.4.1 -Port 3000
```

On `CytonBridge` your adapter must show **192.168.4.x**. Tick "Connect automatically" on it; untick on your usual network.

### 11.10 An idle socket is not a dead socket

The Cyton sends nothing until `b`. A `recv()` timeout treated as fatal makes the server reconnect endlessly. Because the bridge accepts **one client at a time** and takes a while to notice a dead peer, this can wedge the link entirely — presenting as "connected, rate 0.0 Hz". Handle timeouts by staying connected.

### 11.11 Contention rules

- **Two receivers on one transmit line:** fine. Both just read the voltage.
- **Two transmitters on one line:** direct short through the output drivers. Both chips current-limit so nothing died, but don't leave it.
- **The PICkit must be fully disconnected** before the firmware runs — it holds MCLR and drives D11/D12.
- **In default (non-debug) firmware, D12 is driven as an output.** Don't attach a transmitter to it.

### 11.12 Intel HEX merging

- Exactly one `:00000001FF`, on the last line.
- No address overlap — otherwise one region silently erases the other with **no warning**.
- The appended file needs its own type-04 record.

### 11.13 BOOT_EN

D17, pulled low by R9 470 K, pulled high by SW1. **High at reset keeps the bootloader in upload mode and the application never runs.** R9 is a weak pull-down on an exposed header pin (J4-1) — a stray wire there is enough. Verify J4-1 reads ~0 V.

---

## 12. Known Issues and Open Items

### 12.1 BOM discrepancies

The project README and the design's own CPL file disagree. **The CPL is authoritative.**

| Ref | README says | CPL says | Impact |
|---|---|---|---|
| **PL1** | "Dual 11×2 Header" (22 pins) | **`26WDP`** = 26-way dual = **13×2** | Ordering off the README leaves you two positions short per row |
| **SW2** | source `CUS-13TB` | **`CUS-3B SP3T SLIDE SWITCH`** (3-position) | An SPDT part won't drop into an SP3T footprint |

### 12.2 Power topology caveat

The XIAO is wired in parallel with the Cyton's 3.3 V rail, so USB power to the XIAO **backfeeds** the Cyton. It's non-damaging at these currents, but:

> ⚠️ **Don't trust EEG taken in that state.** The Cyton needs more than 3.3 V — the LM2664 inverter and TPS72325 generate the **−2.5 V analog rail** the ADS1299 requires. Backfeeding DVDD does not reliably bring those up. The board will look alive and may talk to you while the analog front end sits half-powered. **For real signals, power from the Cyton's own battery switch.**

### 12.3 Done since the bring-up

| Item | Status |
|---|---|
| **Electrodes** | ✅ 3M Ag/AgCl ECG gel patches, 2 channels: AF7→`1N`, AF8→`2N`, Fpz→`SRB2`, mastoid→`BIAS`. See `docs/WIRING-cyton-muse-athena.md`. |
| **Real EEG capture** | ✅ In `software/recordings/`: an eyes-open/closed alpha block (31 Aug) and two motor-execution sessions (23 Sep). ch1/ch2 carry signal; ch3–ch8 sit at ±187500 µV because nothing is wired to them. |
| **Cue protocols** | ✅ `cyton_experiments.py` — signal check, alpha blocks (2 and 4 min), motor execution and motor imagery, with sample-indexed event files. |

### 12.4 Still open

| Item | Notes |
|---|---|
| **Full 8-channel montage** | Only 2 inputs are wired. Motor imagery wants C3/C4 — see `docs/WIRING-motor-imagery.md`. |
| **Alpha ratio vs the Muse** | Recordings exist on the Cyton side; the eyes-closed/open 8–12 Hz ratio comparison is not written down anywhere yet. |
| **Battery and power wiring** | Undocumented. The rail topology is in §4.5 and the backfeed warning in §12.2, but the battery itself, its connector, charging, and how SW2's missing switch is bridged are not recorded. |
| **Assembly record** | JLCPCB did the SMT. Hand-soldering PL1 and the XIAO hookup are described as wiring tables but never recorded as a procedure — no photos, no inspection notes. |
| **OpenBCI GUI** | Expects a serial dongle or the official WiFi Shield protocol. Workaround: **com0com** virtual COM pair, pump TCP → virtual port, GUI opens the other end. The same trick enables **BrainFlow** (filtering, band power). |
| **LSL integration** | `cyton_client.py --lsl` publishes an outlet; not yet wired into the rehab app. |
| **Long-run drop statistics** | Needs a multi-minute run on AP mode with trustworthy counters. |
| **Live plot has no filter** | The UI plots raw counts, so 50 Hz mains dominates. The training pipeline bandpasses 4–40 Hz; the plot does not. |
| **`Firmware: v3.1.2` vs `library.properties` 3.1.5** | The banner string is hardcoded and stale in the library; harmless. |
| **SW2 / PL1** | SW2 still bridged on the "PC" position. PL1 populated only on the pins the 2-channel montage uses. |

### 12.5 Disk hygiene — resolved

The 1.2 GB of duplicated Ultracortex `.git` stores and the 82 MB zip are gone as of
1 October 2026: 756 MB freed, with every deleted revision still restorable from the kept
clone (§3.3).

---

## Appendix A — Source Files

This appendix used to inline every source file. Those listings went stale almost
immediately — `cyton_server.py` was 296 lines when they were written and is 453 now, and
two files that did not exist yet (`cyton_experiments.py`, `fake_bridge.py`) were never in
it at all. The code lives in this repo, under git, so the repo is the listing.

| Was | Read it at | Lines |
|---|---|---:|
| A.1 `CytonWiFiBridge.ino` | `firmware/bridge/CytonWiFiBridge.ino` | 302 |
| A.2 `cyton_client.py` | `software/cyton_client.py` | 335 |
| A.3 `cyton_server.py` | `software/cyton_server.py` | 453 |
| A.4 `cyton_templates/index.html` | `software/cyton_templates/index.html` | 415 |
| A.5 `merge-hex.ps1` | `firmware/tools/merge-hex.ps1` | 85 |
| A.6 `listen-cyton.ps1` | `firmware/tools/listen-cyton.ps1` | 88 |
| — | `software/cyton_experiments.py` — the cue protocols | 179 |
| — | `software/fake_bridge.py` — the hardware-free bridge | 130 |
| — | `firmware/cyton/DefaultBoard-beginDebug/` — the flashed Cyton sketch | — |

Every one of those files opens with a header comment covering its own wiring, usage and
packet format; the bridge sketch's header is the authoritative wiring reference for §8.3.

> The August snapshots are not lost — they are in the **first commit** of this repo,
> before this rewrite. `git log -p --follow docs/CYTON_BRINGUP.md` will show them.
