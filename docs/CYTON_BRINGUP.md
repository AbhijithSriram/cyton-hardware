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
| **Status** | ✅ Streaming 8 channels at 250 Hz over WiFi, ±1 µV noise floor |
| **Date** | August 2026 |

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
13. [Appendix A — Full Source Listings](#appendix-a--full-source-listings)

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

Five git repositories under `NeuroRehab/`, all OpenBCI-related.

| Path | Upstream | HEAD | Role |
|---|---|---|---|
| `OpenBCI/` | `OpenBCI/V3_Hardware_Design_Files` | `6bce559` (2023-02-06) | **Working repo.** Schematic, PCB, Gerbers, BOM/CPL. Locally modified. |
| `OpenBCI/OpenBCI_Cyton_Library/` | `OpenBCI/OpenBCI_Cyton_Library` | `24e1c42` (2025-07-24) | Cyton firmware, **v3.1.5** |
| `OpenBCI/PIC32-avrdude-bootloader/` | `chipKIT32/PIC32-avrdude-bootloader` | `95cf5d9` (2024-02-08) | chipKIT bootloader source + prebuilt hex |
| `Ultracortex/` | `OpenBCI/Ultracortex` | `338b52b` (2022-09-29) | Headset mechanicals. **Broken clone** — empty index. |
| `Ultracortex2/` | `OpenBCI/Ultracortex` | `338b52b` (2022-09-29) | Duplicate. **Broken clone** — `.git` only. |

> The two nested repos under `OpenBCI/` are plain clones, **not submodules** — the parent sees them as untracked directories.

### 3.1 Local modifications to `OpenBCI/`

Tracked changes:

- `OpenBCI Cyton Designs/OpenBCI 32bit.pcb` — re-saved from DesignSpark (360 KB → 395 KB)
- `OBCI_V4_C (Component Positions CSV).csv` — header rewritten to JLCPCB CPL format:
  `Name,Component,Side,Centre X,Centre Y,Rotation` → `Designator,Val,Layer,Mid X,Mid Y,Rotation`

Untracked additions: full regenerated Gerber set, `gerber.zip`, `OBCI_BOM_JLCPCB.csv`, `Cyton_BOM_AutoMatch.csv`, `Cyton_PNP_Fixed_MM.csv`, and quote PDFs (JLCPCB / Robu / LionCircuits).

### 3.2 Key design files

| File | Notes |
|---|---|
| `OpenBCI Cyton Designs/OBCI_V3_32bit-Schematic.jpg` | **The schematic.** 5037×3237 px. Everything in §4 was read from here. |
| `OpenBCI Cyton Designs/OpenBCI 32bit.sch` | DesignSpark source |
| `OBCI_Cyton_Plots/OBCI_V4_C (Component Positions CSV).csv` | Pick-and-place / component locations |

### 3.3 Repairing the broken Ultracortex clones

Both have an empty index against a populated HEAD, so `git status` reports ~686 staged deletions and `git ls-files` returns nothing:

```bash
git -C "C:/Users/abhij/Desktop/NeuroRehab/Ultracortex2" reset --hard HEAD
```

Content currently in use came from zips instead: `Ultracortex/Ultracortex-master/`, `Ultracortex_Downloaded/Ultracortex-master/` (174 MB, no git), `Ultracortex_A1_Mini/` (STL/3MF, Cyton case and electrode mounts). Roughly 1.2 GB is duplicated across two `.git` stores at the same commit with no checkout, plus an 82 MB `Ultracortex.zip`.

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

`PIC32-avrdude-bootloader/BootloadersCurrent-hex/**UDB32_MX2_DIP.hex**` — the Cyton's bootloader. Config lives under `_BOARD_UDB32_MX2_DIP_` in `bootloaders/configs/openbci.h`.

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
3. **File → Save As** to your sketchbook (do not edit the library example in place — a library update silently wipes it).
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
powershell -File "C:\Users\abhij\Desktop\NeuroRehab\OpenBCI\merge-hex.ps1" -Bootloader "C:\Users\abhij\Desktop\NeuroRehab\OpenBCI\PIC32-avrdude-bootloader\BootloadersCurrent-hex\UDB32_MX2_DIP.hex" -App "C:\Users\abhij\Documents\Arduino\<sketch>\build\chipKIT.pic32.openbci\<sketch>.ino.hex" -Out "C:\Users\abhij\Desktop\NeuroRehab\CytonDebug-with-bootloader.hex"
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
powershell -File "C:\Users\abhij\Desktop\NeuroRehab\listen-cyton.ps1" -Port COM14 -Seconds 60
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

All files live under `C:\Users\abhij\Desktop\NeuroRehab\`.

| File | Lines | Purpose |
|---|---:|---|
| `CytonWiFiBridge/CytonWiFiBridge.ino` | 302 | XIAO firmware — UART ↔ WiFi TCP bridge, packet integrity counter |
| `cyton_client.py` | 335 | CLI: live view, ASCII scope, raw dump, matplotlib plot, LSL outlet |
| `cyton_server.py` | 296 | Flask backend — socket thread, ring buffer, CSV recording, REST API |
| `cyton_templates/index.html` | 295 | Web UI — 8-channel canvas plot, command buttons, recording, dark mode |
| `OpenBCI/merge-hex.ps1` | 85 | Intel HEX merger with overlap detection |
| `listen-cyton.ps1` | 88 | Bare serial listener with ADS1299 ID detection |
| `CytonDebug-with-bootloader.hex` | — | The working flashable image |

Full source in [Appendix A](#appendix-a--full-source-listings).

### 9.1 Running it

```bash
python C:\Users\abhij\Desktop\NeuroRehab\cyton_server.py
```

Then open <http://127.0.0.1:5000>. For station mode: `--host 192.168.1.15`.

CLI alternatives:

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
| `/api/status` | GET | `connected`, `streaming`, `rate`, `dropped`, `bad`, `total`, `railed[]`, recording state |
| `/api/data?since=N` | GET | New samples since index N (capped at 2000) |
| `/api/command` | POST | `{"cmd": "b"}` — chars sent one at a time with 0.35 s spacing |
| `/api/record` | POST | `{"action": "start"\|"stop", "label": "..."}` |

### 9.3 Recording format

CSV to `recordings/cyton-YYYYMMDD-HHMMSS-label.csv`:

```csv
timestamp_iso,sample_counter,ch1_uV,ch2_uV,...,ch8_uV
2026-08-28T09:14:22.331,131,-26.4213,-30.1044,...
```

The sample counter is written every row, so gaps are detectable in post-processing. **Recording happens server-side**, the moment data comes off the socket — closing the browser cannot lose samples.

### 9.4 Design notes

- **Rolling 1-second rate**, not an average since connect, so it falls to 0 when streaming stops.
- **Idle is not an error.** The Cyton sends nothing until `b`; a `recv()` timeout must not tear down the connection. `PacketReader(sock, yield_idle=True)` yields `None` and stays connected.
- **Counters survive reconnects** via `_dropped_base` / `_bad_base`.
- **Three-state status:** green = streaming, amber = connected but idle, red = disconnected.
- **Auto-reconnect** every 2 s.
- **Packet integrity** is tracked, not just throughput — `0x41` … 33 bytes … `0xCx`, counting good vs malformed, plus dropped-sample detection from the counter.

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

### 12.3 Not yet done

| Item | Notes |
|---|---|
| **Electrodes** | Never connected. All measurements are internal test signals and noise floor. |
| **Real EEG capture** | Blocked on electrodes. |
| **OpenBCI GUI** | Expects a serial dongle or the official WiFi Shield protocol. Workaround: **com0com** virtual COM pair, pump TCP → virtual port, GUI opens the other end. Same trick enables **BrainFlow** (filtering, band power). |
| **LSL integration** | `cyton_client.py --lsl` publishes an outlet; not yet wired into `test_lsl_sender.py` / the rehab app. |
| **Long-run drop statistics** | Needs a multi-minute run on AP mode with trustworthy counters. |
| **`Firmware: v3.1.2` vs `library.properties` 3.1.5** | The banner string is hardcoded and stale in the library; harmless. |
| **SW2** | Still bridged on the "PC" position rather than a real switch. |
| **PL1 / BLE1** | Still unpopulated. |

### 12.4 Disk hygiene

~1.2 GB duplicated across two Ultracortex `.git` stores at the same commit with no checkout, plus an 82 MB `Ultracortex.zip`. Restoring one (§3.3) and deleting the other reclaims roughly half a gigabyte.

---

## Appendix A — Full Source Listings

*(Continued in the sections below — every file, complete.)*

### A.1 — CytonWiFiBridge.ino

`CytonWiFiBridge/CytonWiFiBridge.ino` — 302 lines

XIAO ESP32C3 firmware. UART <-> WiFi TCP bridge with packet-integrity tracking. Also lives at `Documents\Arduino\CytonWiFiBridge\` for the IDE.

```cpp
/* ===========================================================================
 * CytonWiFiBridge
 *
 * Seeed XIAO ESP32C3 acting as the wireless link for an OpenBCI Cyton whose
 * RFD22301 radio (BLE1) was never populated.
 *
 *      Cyton  <--UART 115200-->  XIAO ESP32C3  <--WiFi TCP-->  PC
 *
 * ---------------------------------------------------------------------------
 * WIRING - 3.3V both sides, no level shifting required
 * ---------------------------------------------------------------------------
 *   Cyton D11  (J4 pin 4)   ->  XIAO D1 / GPIO3     Cyton transmits
 *   Cyton D12  (J3 pin 2)   <-  XIAO D2 / GPIO4     Cyton receives
 *   Cyton AGND (J3 pin 4)   <-> XIAO GND            required
 *
 * A USB-TTL adapter may share D11 (its RX only) as an independent monitor.
 * Two receivers on one transmit line is fine. Never put two transmitters on
 * D12 - only the XIAO drives that pin.
 *
 * ---------------------------------------------------------------------------
 * WHY D11/D12 AND NOT THE "RFTX"/"RFRX" PADS
 * ---------------------------------------------------------------------------
 * The pads silkscreened RFTX / RFRX / RFRESET are a breakout for the RFduino
 * module's OWN serial port (module GPIO0/GPIO1), provided so you can flash the
 * radio. They never connect to the PIC32. With BLE1 unpopulated they are dead
 * traces, and a UART attached to them decodes ambient noise into ~225 junk
 * bytes/sec.
 *
 * The PIC's Serial0 reaches only BLE1 pins 3/4, which are unreachable module
 * pads. But firmware built with board.beginDebug() mirrors every outgoing byte
 * to Serial1 as well - including the streaming EEG data - and processes
 * incoming commands from Serial1. Serial1 is D11/D12, on the accessible J3/J4
 * headers. So the debug port is a fully bidirectional substitute.
 *
 * REQUIRES Cyton firmware built with board.beginDebug() (not board.begin()).
 *
 * ---------------------------------------------------------------------------
 * ARDUINO IDE SETTINGS
 * ---------------------------------------------------------------------------
 *   Board:            XIAO_ESP32C3
 *   USB CDC On Boot:  ENABLED        <-- required
 *
 * With CDC disabled, `Serial` falls back to UART0 on GPIO20/21 (silkscreen
 * D6/D7) and collides with anything else placed there. GPIO2, GPIO8 and GPIO9
 * are strapping pins and are avoided.
 *
 * Close the Serial Monitor before every upload - the ESP32C3's USB port is
 * generated by the chip itself and re-enumerates on reset, so a monitor
 * holding the old handle blocks the upload.
 *
 * ---------------------------------------------------------------------------
 * NETWORK MODES  (set USE_SOFTAP below)
 * ---------------------------------------------------------------------------
 * USE_SOFTAP 1 - ACCESS POINT (default, recommended for a portable rig)
 *   The XIAO creates its own WiFi network. Your laptop joins it directly, so
 *   there is no router in the path: same address every boot, strongest
 *   possible signal, lowest latency, and it works in a clinic or lab with no
 *   WiFi at all. Cost: the laptop has no internet while connected.
 *
 *     join SSID "CytonBridge" / pass "neurorehab", then connect to
 *     192.168.4.1:3000
 *
 * USE_SOFTAP 0 - STATION
 *   The XIAO joins an existing network and gets an address from DHCP (or a
 *   fixed one via USE_STATIC_IP). Convenient at a desk, but signal strength
 *   is whatever the room gives you - below about -80 dBm this link starts
 *   losing samples, and at 8250 B/s that shows up as gaps in the EEG.
 *
 * ---------------------------------------------------------------------------
 * COMMANDS  (type into Serial Monitor, or send over the TCP socket)
 * ---------------------------------------------------------------------------
 *   b  start streaming EEG        s  stop streaming
 *   v  soft reset (re-sends the boot banner)
 *   ?  dump register settings
 *
 * Test signals - useful before you own electrodes. With open inputs every
 * channel rails at 0x800000; these drive known waveforms through the ADS1299
 * so you can prove the analog front end works:
 *   0  connect all channels to ground (measures noise floor)
 *   -  1x amplitude square wave, slow      =  1x fast
 *   [  2x amplitude square wave, slow      ]  2x fast
 *   p  connect to DC
 *
 * Healthy stream: 33 bytes x 250 Hz = ~8250 B/s and ~250 packets/sec.
 * =========================================================================== */

#include <WiFi.h>

// ---------------------------------------------------------------- settings --

// 1 = ACCESS POINT. The XIAO creates its own network and your laptop joins it
//     directly. No router involved: fixed address every time, best signal,
//     works anywhere. Your laptop loses internet while connected.
// 0 = STATION. The XIAO joins your existing WiFi.
#define USE_SOFTAP 1

// -- access point mode (USE_SOFTAP 1) --
const char *AP_SSID    = "CytonBridge";
const char *AP_PASS    = "neurorehab";     // must be >= 8 chars for WPA2
const uint8_t AP_CHAN  = 6;                // 1, 6 or 11 are non-overlapping
// The bridge is always at 192.168.4.1 in this mode.

// -- station mode (USE_SOFTAP 0) --
const char *WIFI_SSID  = "Abhijith-2.4";
const char *WIFI_PASS  = "YOUR_WIFI_PASSWORD";

// Optional fixed address in station mode, so the bridge lands on the same IP
// every boot. Pick something above your router's DHCP pool.
// #define USE_STATIC_IP
#ifdef USE_STATIC_IP
static IPAddress STATIC_IP (192, 168, 1, 200);
static IPAddress GATEWAY   (192, 168, 1, 1);
static IPAddress SUBNET    (255, 255, 255, 0);
static IPAddress DNS_SRV   (192, 168, 1, 1);
#endif

const uint16_t TCP_PORT = 3000;

#define CYTON_RX_PIN 3        // XIAO D1 <- Cyton D11
#define CYTON_TX_PIN 4        // XIAO D2 -> Cyton D12
#define CYTON_BAUD   115200

#define SHOW_PREVIEW 1        // 1 = print a hex/ASCII sample each second
// -----------------------------------------------------------------------------

WiFiServer server(TCP_PORT);
WiFiClient client;

static uint8_t  buf[1024];
static uint32_t rxBytes  = 0;      // bytes this second
static uint32_t lastTick = 0;

// OpenBCI packet framing, confirmed against library v3.1.5:
//   writeSerial(OPENBCI_BOP)                 -> 0x41 ('A'), NOT the 0xA0 the
//                                               older OpenBCI docs describe
//   sample counter                           -> 1 byte
//   8 channels x 3 bytes                     -> 24 bytes
//   aux                                      -> 6 bytes
//   writeSerial(PCKT_END | packetType)       -> 0xC0..0xCF
//                                            = 33 bytes total
// Tracking this turns "some bytes arrived" into a real integrity measure.
#define OPENBCI_START_BYTE 0x41

static int      pktPos  = -1;      // -1 = hunting for the start byte
static uint32_t pktGood = 0;
static uint32_t pktBad  = 0;

#if SHOW_PREVIEW
static uint8_t preview[24];
static int     previewLen = 0;
#endif

// -----------------------------------------------------------------------------

static void trackPacket(uint8_t b) {
  if (pktPos < 0) {
    if (b == OPENBCI_START_BYTE) pktPos = 0;   // possible start of packet
  } else {
    pktPos++;
    if (pktPos == 32) {                  // 33rd byte is the stop byte
      if ((b & 0xF0) == 0xC0) pktGood++; else pktBad++;
      pktPos = -1;
    }
  }
}

static void startNetwork() {
#if USE_SOFTAP
  WiFi.mode(WIFI_AP);
  WiFi.setSleep(false);                  // keep latency low for realtime use

  if (!WiFi.softAP(AP_SSID, AP_PASS, AP_CHAN)) {
    Serial.println("ERROR: could not start access point");
    return;
  }
  Serial.println("Access point up. On your laptop, join:");
  Serial.printf ("  SSID:     %s\n", AP_SSID);
  Serial.printf ("  Password: %s\n", AP_PASS);
  Serial.print  ("  Bridge:   ");
  Serial.print  (WiFi.softAPIP());       // always 192.168.4.1
  Serial.printf (":%u\n", TCP_PORT);
  Serial.printf ("  Channel:  %u\n", AP_CHAN);
#else
#ifdef USE_STATIC_IP
  if (!WiFi.config(STATIC_IP, GATEWAY, SUBNET, DNS_SRV)) {
    Serial.println("WARNING: static IP config failed, falling back to DHCP");
  }
#endif
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  Serial.printf("Joining \"%s\"", WIFI_SSID);
  while (WiFi.status() != WL_CONNECTED) {
    delay(250);
    Serial.print(".");
  }
  Serial.println();
  Serial.print  ("  IP:   ");
  Serial.print  (WiFi.localIP());
  Serial.printf (":%u\n", TCP_PORT);
  Serial.printf ("  RSSI: %d dBm   (weaker than -80 will drop samples)\n",
                 WiFi.RSSI());
#endif
}

static void printReport() {
  Serial.printf("[%5lu B/s | %3lu pkt/s", (unsigned long)rxBytes,
                (unsigned long)pktGood);
  if (pktBad) Serial.printf(" | %lu BAD", (unsigned long)pktBad);
  Serial.print(client && client.connected() ? " | client] " : " | no client] ");

#if SHOW_PREVIEW
  for (int i = 0; i < previewLen; i++) Serial.printf("%02X ", preview[i]);
  Serial.print("|");
  for (int i = 0; i < previewLen; i++) {
    char c = (char)preview[i];
    Serial.print((c >= 32 && c < 127) ? c : '.');
  }
  Serial.print("|");
#endif
  Serial.println();
}

// -----------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);                  // USB CDC console
  delay(300);

  // Enlarge the UART receive buffer BEFORE begin(). The 256-byte default is
  // only ~31 ms of headroom at 8250 B/s.
  Serial1.setRxBufferSize(4096);
  Serial1.begin(CYTON_BAUD, SERIAL_8N1, CYTON_RX_PIN, CYTON_TX_PIN);

  Serial.println("\n=== CytonWiFiBridge ===");
  Serial.printf("UART  RX=GPIO%d (<-Cyton D11)  TX=GPIO%d (->Cyton D12)  @%d\n",
                CYTON_RX_PIN, CYTON_TX_PIN, CYTON_BAUD);

  startNetwork();

  server.begin();
  server.setNoDelay(true);               // no Nagle buffering on a realtime link

  Serial.println("Ready. Commands: b=stream  s=stop  v=reset  ?=registers");
  Serial.println("Waiting for a TCP client...");
}

void loop() {
  // -- accept a client, notice when one leaves --------------------------------
  if (!client || !client.connected()) {
    if (client) {
      client.stop();
      Serial.println("Client disconnected.");
    }
    WiFiClient incoming = server.available();
    if (incoming) {
      client = incoming;
      client.setNoDelay(true);
      Serial.print("Client connected: ");
      Serial.println(client.remoteIP());
    }
  }

  // -- Cyton -> network -------------------------------------------------------
  int avail = Serial1.available();
  if (avail > 0) {
    if (avail > (int)sizeof(buf)) avail = sizeof(buf);
    int got = Serial1.readBytes(buf, avail);
    rxBytes += got;

    for (int i = 0; i < got; i++) {
      trackPacket(buf[i]);
#if SHOW_PREVIEW
      if (previewLen < (int)sizeof(preview)) preview[previewLen++] = buf[i];
#endif
    }

    if (client && client.connected()) client.write(buf, got);
  }

  // -- network -> Cyton -------------------------------------------------------
  if (client && client.connected()) {
    while (client.available()) Serial1.write((uint8_t)client.read());
  }

  // -- USB console -> Cyton (type commands by hand) ---------------------------
  while (Serial.available()) Serial1.write((uint8_t)Serial.read());

  // -- once-per-second status -------------------------------------------------
  uint32_t now = millis();
  if (now - lastTick >= 1000) {
    if (rxBytes > 0) printReport();
    rxBytes = 0;
    pktGood = 0;
    pktBad  = 0;
#if SHOW_PREVIEW
    previewLen = 0;
#endif
    lastTick = now;
  }
}
```

### A.2 — cyton_client.py

`cyton_client.py` — 335 lines

Command-line client. Packet framing, uV conversion, live view, ASCII scope, raw dump, matplotlib plot, LSL outlet.

```python
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
```

### A.3 — cyton_server.py

`cyton_server.py` — 296 lines

Flask backend. Socket thread with auto-reconnect, ring buffer, CSV recording, REST API.

```python
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

Recordings are written as CSV to ./recordings/.
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
    """Owns the socket thread, the ring buffer, and the recording file."""

    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.lock = threading.Lock()
        self.samples = deque(maxlen=SAMPLE_RATE * BUFFER_SECONDS)
        self.total = 0                       # absolute count of samples ever seen

        self.connected = False
        self.streaming = False           # connected AND data actually arriving
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

        self.recording = False
        self._rec_file = None
        self._rec_writer = None
        self.rec_name = ""
        self.rec_count = 0

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
            ["timestamp_iso", "sample_counter"]
            + [f"ch{i+1}_uV" for i in range(N_CHANNELS)]
        )
        self.rec_name = name
        self.rec_count = 0
        self.recording = True
        return True, name

    def _write_row(self, counter, uv):
        try:
            self._rec_writer.writerow(
                [datetime.now().isoformat(timespec="milliseconds"), counter]
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
            return {
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
    app.run(host="127.0.0.1", port=args.web_port, threaded=True, debug=False)


if __name__ == "__main__":
    main()
```

### A.4 — cyton_templates/index.html

`cyton_templates/index.html` — 295 lines

Web UI. Canvas plot of 8 colour-coded channels, command buttons, recording controls, light/dark theme.

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cyton Live</title>
<style>
  :root {
    --bg:      #ffffff;
    --fg:      #111111;
    --muted:   #666666;
    --line:    #d8d8d8;
    --panel:   #f6f6f6;
    --grid:    #e8e8e8;
    --ok:      #17803d;
    --bad:     #c02626;
  }
  html[data-theme="dark"] {
    --bg:      #101216;
    --fg:      #e8e8e8;
    --muted:   #9099a6;
    --line:    #2a2f38;
    --panel:   #181b21;
    --grid:    #23272f;
    --ok:      #3ecf6a;
    --bad:     #ff6b6b;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--fg);
    font: 14px/1.45 ui-monospace, "Cascadia Mono", Consolas, monospace;
  }
  header {
    display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
    padding: 10px 14px; border-bottom: 1px solid var(--line); background: var(--panel);
  }
  h1 { font-size: 15px; margin: 0 12px 0 0; font-weight: 700; letter-spacing: .02em; }
  .spacer { flex: 1; }
  button {
    font: inherit; padding: 5px 11px; cursor: pointer;
    background: var(--bg); color: var(--fg);
    border: 1px solid var(--line); border-radius: 4px;
  }
  button:hover { border-color: var(--muted); }
  button:active { transform: translateY(1px); }
  button.rec    { border-color: var(--bad); color: var(--bad); font-weight: 700; }
  button.recing { background: var(--bad); color: #fff; border-color: var(--bad); }
  .bar {
    display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
    padding: 8px 14px; border-bottom: 1px solid var(--line);
  }
  .grp { display: flex; align-items: center; gap: 5px; }
  .grp > span.lbl { color: var(--muted); margin-right: 3px; }
  .stat { color: var(--muted); }
  .stat b { color: var(--fg); font-weight: 700; }
  .dot { display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:5px; }
  .up { background: var(--ok); } .down { background: var(--bad); }
  .idle { background: #d99400; }
  #wrap { padding: 10px 14px; }
  canvas { width: 100%; height: 72vh; display: block; border: 1px solid var(--line); border-radius: 4px; }
  input[type=text], input[type=number] {
    font: inherit; background: var(--bg); color: var(--fg);
    border: 1px solid var(--line); border-radius: 4px; padding: 4px 7px;
  }
  input[type=text] { width: 130px; } input[type=number] { width: 78px; }
  .note { color: var(--muted); padding: 0 14px 12px; font-size: 12px; }
</style>
</head>
<body>

<header>
  <h1>CYTON LIVE</h1>
  <span class="stat"><span id="dot" class="dot down"></span><span id="conn">connecting</span></span>
  <span class="stat">rate <b id="rate">0</b> Hz</span>
  <span class="stat">dropped <b id="drop">0</b></span>
  <span class="stat">samples <b id="tot">0</b></span>
  <span class="spacer"></span>
  <button id="theme">dark</button>
</header>

<div class="bar">
  <div class="grp">
    <span class="lbl">stream</span>
    <button data-cmd="b">start (b)</button>
    <button data-cmd="s">stop (s)</button>
    <button data-cmd="v">reset (v)</button>
  </div>
  <div class="grp">
    <span class="lbl">test signal</span>
    <button data-cmd="[">square 2x</button>
    <button data-cmd="-">square 1x</button>
    <button data-cmd="0">ground</button>
    <button data-cmd="d">normal (d)</button>
  </div>
  <div class="grp">
    <span class="lbl">scale</span>
    <input type="number" id="scale" value="0" min="0" step="10">
    <span class="stat">ÂµV/ch (0 = auto)</span>
  </div>
  <div class="grp">
    <span class="lbl">window</span>
    <input type="number" id="win" value="5" min="1" max="30" step="1">
    <span class="stat">s</span>
  </div>
</div>

<div class="bar">
  <div class="grp">
    <span class="lbl">record</span>
    <input type="text" id="label" placeholder="label (optional)">
    <button id="rec" class="rec">â— start recording</button>
    <span class="stat" id="recinfo"></span>
  </div>
</div>

<div id="wrap"><canvas id="plot"></canvas></div>
<div class="note" id="msg"></div>

<script>
const NCH = {{ channels }};
const FS  = {{ fs }};

const COLORS = ["#d62728","#2ca02c","#1f77b4","#ff7f0e",
                "#9467bd","#00a0a0","#8c564b","#e377c2"];

// ---- theme ---------------------------------------------------------------
const root = document.documentElement;
function setTheme(t) {
  root.setAttribute("data-theme", t);
  document.getElementById("theme").textContent = t === "dark" ? "light" : "dark";
  try { localStorage.setItem("cyton-theme", t); } catch (e) {}
}
try { setTheme(localStorage.getItem("cyton-theme") || "light"); } catch (e) { setTheme("light"); }
document.getElementById("theme").onclick = () =>
  setTheme(root.getAttribute("data-theme") === "dark" ? "light" : "dark");

// ---- data ----------------------------------------------------------------
let nextIdx = 0;
let buf = Array.from({length: NCH}, () => []);
let maxLen = FS * 5;

function trim() {
  for (let i = 0; i < NCH; i++)
    if (buf[i].length > maxLen) buf[i].splice(0, buf[i].length - maxLen);
}

async function poll() {
  try {
    const r = await fetch("/api/data?since=" + nextIdx);
    const j = await r.json();
    nextIdx = j.next;
    for (const s of j.samples)
      for (let i = 0; i < NCH; i++) buf[i].push(s[i]);
    trim();
  } catch (e) {}
  setTimeout(poll, 50);
}

async function pollStatus() {
  try {
    const s = await (await fetch("/api/status")).json();
    document.getElementById("dot").className =
      "dot " + (s.streaming ? "up" : (s.connected ? "idle" : "down"));
    document.getElementById("conn").textContent =
      !s.connected ? ("disconnected â€” " + (s.error || "retrying"))
      : s.streaming ? ("streaming â€” " + s.bridge)
                    : ("connected, idle â€” press start (b)");
    document.getElementById("rate").textContent = s.rate.toFixed(1);
    document.getElementById("drop").textContent = s.dropped;
    document.getElementById("tot").textContent  = s.total;

    const btn = document.getElementById("rec");
    btn.classList.toggle("recing", s.recording);
    btn.textContent = s.recording ? "â–  stop recording" : "â— start recording";
    document.getElementById("recinfo").textContent =
      s.recording ? `${s.rec_name} â€” ${s.rec_count} samples`
                  : (s.rec_name ? `last: ${s.rec_name}` : "");
  } catch (e) {}
  setTimeout(pollStatus, 500);
}

// ---- drawing -------------------------------------------------------------
const cv = document.getElementById("plot");
const cx = cv.getContext("2d");

function css(v) { return getComputedStyle(root).getPropertyValue(v).trim(); }

function draw() {
  const dpr = window.devicePixelRatio || 1;
  const w = cv.clientWidth, h = cv.clientHeight;
  if (cv.width !== w * dpr || cv.height !== h * dpr) {
    cv.width = w * dpr; cv.height = h * dpr;
  }
  cx.setTransform(dpr, 0, 0, dpr, 0, 0);
  cx.clearRect(0, 0, w, h);
  cx.fillStyle = css("--bg"); cx.fillRect(0, 0, w, h);

  const winSec = Math.max(1, +document.getElementById("win").value || 5);
  maxLen = Math.round(FS * winSec);

  const padL = 52, padR = 8, padT = 8, padB = 20;
  const pw = w - padL - padR, ph = h - padT - padB;
  const band = ph / NCH;

  // vertical second markers
  cx.strokeStyle = css("--grid"); cx.lineWidth = 1;
  cx.fillStyle = css("--muted"); cx.font = "11px monospace";
  for (let s = 0; s <= winSec; s++) {
    const x = padL + pw * (1 - s / winSec);
    cx.beginPath(); cx.moveTo(x, padT); cx.lineTo(x, padT + ph); cx.stroke();
    if (s) cx.fillText("-" + s + "s", x - 10, h - 6);
  }

  // shared scale
  let manual = +document.getElementById("scale").value || 0;
  let peak = 1e-6;
  const means = [];
  for (let i = 0; i < NCH; i++) {
    const d = buf[i];
    if (!d.length) { means.push(0); continue; }
    let m = 0; for (const v of d) m += v; m /= d.length;
    means.push(m);
    for (const v of d) { const a = Math.abs(v - m); if (a > peak) peak = a; }
  }
  const half = manual > 0 ? manual / 2 : peak * 1.15;

  for (let i = 0; i < NCH; i++) {
    const yMid = padT + band * i + band / 2;
    const d = buf[i];

    cx.strokeStyle = css("--grid");
    cx.beginPath(); cx.moveTo(padL, yMid); cx.lineTo(padL + pw, yMid); cx.stroke();

    cx.fillStyle = COLORS[i % COLORS.length];
    cx.font = "bold 11px monospace";
    cx.fillText("ch" + (i + 1), 6, yMid - 3);
    if (d.length) {
      cx.fillStyle = css("--muted"); cx.font = "10px monospace";
      cx.fillText(Math.round(d[d.length - 1]) + "ÂµV", 6, yMid + 10);
    }
    if (!d.length) continue;

    cx.strokeStyle = COLORS[i % COLORS.length];
    cx.lineWidth = 1.1; cx.beginPath();
    const n = d.length, step = Math.max(1, Math.floor(n / pw));
    let first = true;
    for (let k = 0; k < n; k += step) {
      const x = padL + pw * (1 - (n - k) / maxLen);
      let y = yMid - ((d[k] - means[i]) / half) * (band / 2 - 3);
      y = Math.max(padT + band * i + 1, Math.min(padT + band * (i + 1) - 1, y));
      if (first) { cx.moveTo(x, y); first = false; } else cx.lineTo(x, y);
    }
    cx.stroke();
  }

  cx.fillStyle = css("--muted"); cx.font = "10px monospace";
  cx.fillText("Â±" + Math.round(half) + "ÂµV", w - 78, padT + 11);

  requestAnimationFrame(draw);
}

// ---- controls ------------------------------------------------------------
const msg = document.getElementById("msg");
async function send(cmd) {
  msg.textContent = "sending " + JSON.stringify(cmd) + " ...";
  try {
    const r = await (await fetch("/api/command", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({cmd})
    })).json();
    msg.textContent = r.ok ? "sent " + JSON.stringify(cmd)
                           : "failed: " + r.error;
  } catch (e) { msg.textContent = "failed: " + e; }
}
document.querySelectorAll("button[data-cmd]").forEach(b =>
  b.onclick = () => send(b.dataset.cmd));

document.getElementById("rec").onclick = async () => {
  const recing = document.getElementById("rec").classList.contains("recing");
  const body = recing ? {action: "stop"}
                      : {action: "start", label: document.getElementById("label").value};
  try {
    const r = await (await fetch("/api/record", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body)
    })).json();
    msg.textContent = r.ok ? (recing ? "saved " + r.message : "recording to " + r.message)
                           : "failed: " + r.error;
  } catch (e) { msg.textContent = "failed: " + e; }
};

poll(); pollStatus(); draw();
</script>
</body>
</html>
```

### A.5 — merge-hex.ps1

`OpenBCI/merge-hex.ps1` — 85 lines

Intel HEX merger. Strips EOF records, detects address overlap and refuses to write a broken image, prints the memory map.

```powershell
# merge-hex.ps1 - Combine a chipKIT bootloader .hex with a compiled sketch .hex
# into one file that MPLAB IPE can flash in a single shot.
#
# Usage:
#   .\merge-hex.ps1 -Bootloader "UDB32_MX2_DIP.hex" -App "DefaultBoard.ino.hex" -Out "combined.hex"

param(
    [Parameter(Mandatory=$true)][string]$Bootloader,
    [Parameter(Mandatory=$true)][string]$App,
    [Parameter(Mandatory=$true)][string]$Out
)

function Get-Records($path) {
    if (-not (Test-Path $path)) { throw "File not found: $path" }
    # Keep every record except End-Of-File (type 01). We add exactly one back at the end.
    Get-Content $path | ForEach-Object { $_.Trim() } |
        Where-Object { $_.Length -ge 11 -and $_[0] -eq ':' -and $_.Substring(7,2) -ne '01' }
}

function Get-Ranges($records) {
    $upper = 0
    $seen = @{}
    foreach ($l in $records) {
        $tt = $l.Substring(7,2)
        if ($tt -eq '04') { $upper = [Convert]::ToUInt32($l.Substring(9,4),16) }
        elseif ($tt -eq '00') {
            $addr = ($upper -shl 16) -bor [Convert]::ToUInt32($l.Substring(3,4),16)
            $len  = [Convert]::ToUInt32($l.Substring(1,2),16)
            $key  = '0x{0:X4}0000' -f $upper
            if (-not $seen.ContainsKey($key)) { $seen[$key] = @($addr, ($addr+$len-1)) }
            else {
                $r = $seen[$key]
                if ($addr -lt $r[0]) { $r[0] = $addr }
                if (($addr+$len-1) -gt $r[1]) { $r[1] = $addr+$len-1 }
                $seen[$key] = $r
            }
        }
    }
    return $seen
}

$blRecs  = @(Get-Records $Bootloader)
$appRecs = @(Get-Records $App)

if ($blRecs.Count  -eq 0) { throw "No usable records in bootloader file." }
if ($appRecs.Count -eq 0) { throw "No usable records in app file." }

$blRange  = Get-Ranges $blRecs
$appRange = Get-Ranges $appRecs

Write-Host "Bootloader regions:" -ForegroundColor Cyan
foreach ($k in ($blRange.Keys | Sort-Object)) {
    Write-Host ("  {0}: 0x{1:X8} .. 0x{2:X8}" -f $k, $blRange[$k][0], $blRange[$k][1])
}
Write-Host "Application regions:" -ForegroundColor Cyan
foreach ($k in ($appRange.Keys | Sort-Object)) {
    Write-Host ("  {0}: 0x{1:X8} .. 0x{2:X8}" -f $k, $appRange[$k][0], $appRange[$k][1])
}

# Overlap check - if these collide, one will silently overwrite the other.
$overlap = $false
foreach ($k in $blRange.Keys) {
    if ($appRange.ContainsKey($k)) {
        $b = $blRange[$k]; $a = $appRange[$k]
        if ($b[0] -le $a[1] -and $a[0] -le $b[1]) {
            Write-Host ("  !! OVERLAP in {0}: bootloader 0x{1:X8}-0x{2:X8} vs app 0x{3:X8}-0x{4:X8}" -f $k,$b[0],$b[1],$a[0],$a[1]) -ForegroundColor Red
            $overlap = $true
        }
    }
}
if ($overlap) { throw "Address overlap detected - refusing to write a broken image." }

# The app's records must not inherit the bootloader's segment. Force a fresh
# extended-linear-address record if the app file doesn't open with one.
$prefix = @()
if ($appRecs[0].Substring(7,2) -ne '04') {
    Write-Host "  (app has no leading type-04 record; inserting :020000040000FA)" -ForegroundColor Yellow
    $prefix = @(':020000040000FA')
}

$all = @($blRecs) + $prefix + @($appRecs) + @(':00000001FF')
Set-Content -Path $Out -Value $all -Encoding ascii

Write-Host ""
Write-Host ("Wrote {0} ({1} records, exactly 1 EOF at the end)." -f $Out, $all.Count) -ForegroundColor Green
```

### A.6 — listen-cyton.ps1

`listen-cyton.ps1` — 88 lines

Bare serial listener. Receive-only, logs to file, auto-detects the ADS1299 device ID, dumps hex on a suspected baud mismatch.

```powershell
# listen-cyton.ps1 - Dumb serial listener. Opens a COM port, prints everything
# that arrives, and tees it to a log file. Receive-only; never transmits.
#
#   .\listen-cyton.ps1 -Port COM14 -Seconds 40

param(
    [string]$Port    = "COM14",
    [int]$Baud       = 115200,
    [int]$Seconds    = 40,
    [string]$LogFile = "$PSScriptRoot\cyton-serial-log.txt"
)

$sp = New-Object System.IO.Ports.SerialPort $Port, $Baud, 'None', 8, 'One'
$sp.ReadTimeout  = 250
$sp.DtrEnable    = $true
$sp.RtsEnable    = $true

try { $sp.Open() }
catch {
    Write-Host "COULD NOT OPEN $Port" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Almost always this means another program is holding the port." -ForegroundColor Yellow
    Write-Host "Close every Arduino IDE window, then try again." -ForegroundColor Yellow
    exit 1
}

Write-Host "Listening on $Port at $Baud for $Seconds seconds." -ForegroundColor Green
Write-Host "POWER ON THE CYTON NOW." -ForegroundColor Cyan
Write-Host "----------------------------------------------------" -ForegroundColor DarkGray

$deadline = (Get-Date).AddSeconds($Seconds)
$buf      = New-Object System.Text.StringBuilder
$total    = 0

while ((Get-Date) -lt $deadline) {
    try {
        $chunk = $sp.ReadExisting()
        if ($chunk.Length -gt 0) {
            $total += $chunk.Length
            [void]$buf.Append($chunk)
            Write-Host $chunk -NoNewline
        }
        Start-Sleep -Milliseconds 50
    }
    catch [TimeoutException] { }
    catch { break }
}

$sp.Close()
$text = $buf.ToString()

Write-Host ""
Write-Host "----------------------------------------------------" -ForegroundColor DarkGray
Write-Host ("Received $total bytes.") -ForegroundColor Green

if ($total -gt 0) {
    Set-Content -Path $LogFile -Value $text -Encoding utf8
    Write-Host "Saved to $LogFile" -ForegroundColor Green
    Write-Host ""
    # Pull out the one number that matters.
    $m = [regex]::Match($text, 'On Board ADS1299 Device ID:\s*0x([0-9A-Fa-f]+)')
    if ($m.Success) {
        $id = $m.Groups[1].Value.ToUpper()
        if ($id -eq '3E') {
            Write-Host ">>> ADS1299 Device ID = 0x$id  -- CORRECT. The EEG chip is alive. <<<" -ForegroundColor Green
        } else {
            Write-Host ">>> ADS1299 Device ID = 0x$id  -- expected 0x3E. <<<" -ForegroundColor Yellow
        }
    }
    # Show non-printable bytes as hex if the text looks like garbage (wrong baud).
    $printable = ($text.ToCharArray() | Where-Object { [int]$_ -ge 32 -and [int]$_ -lt 127 }).Count
    if ($total -gt 8 -and ($printable / $total) -lt 0.6) {
        Write-Host ""
        Write-Host "Output looks like garbage - probably a baud rate mismatch." -ForegroundColor Yellow
        Write-Host "Raw hex of first 64 bytes:" -ForegroundColor Yellow
        $bytes = [System.Text.Encoding]::GetEncoding(28591).GetBytes($text)
        ($bytes | Select-Object -First 64 | ForEach-Object { '{0:X2}' -f $_ }) -join ' '
    }
} else {
    Write-Host ""
    Write-Host "Nothing received. Check, in this order:" -ForegroundColor Yellow
    Write-Host "  1. Was the Cyton powered on during the listening window?"
    Write-Host "  2. Is Cyton J4 pin 4 (D11) wired to the adapter's RX hole?"
    Write-Host "  3. Is Cyton J3 pin 4 (AGND) wired to the adapter's GND hole?"
    Write-Host "  4. Are ALL five PICkit wires unplugged?"
    Write-Host "  5. Loopback test: jumper the adapter's own TX to its own RX and rerun."
}
```

