# Upstream dependencies

Four upstream trees are used by this project. All are public, all are pinned to a known
commit, and none of them are tracked here — `vendor/` and `mechanical/` are git-ignored, so
a clone of this repo is small and contains only work that cannot be downloaded again.

Everything in those trees that was **not** upstream — the regenerated Gerbers, the JLCPCB
BOM and CPL, the quotes, the component-selection PDFs — was lifted out into `hardware/`
and **is** tracked here. Nothing irreplaceable sits behind a `.gitignore`.

| Path on disk | Upstream | Pinned at | Why it is kept |
|---|---|---|---|
| `vendor/openbci-v3-hardware/` | <https://github.com/OpenBCI/V3_Hardware_Design_Files> | `6bce559` (2023-02-06) | Schematic, PCB, upstream Gerbers and BOM/CPL. Two files locally modified — see below |
| `vendor/openbci-v3-hardware/OpenBCI_Cyton_Library/` | <https://github.com/OpenBCI/OpenBCI_Cyton_Library> | `24e1c42` (2025-07-24) | v3.1.5 — the firmware source that was compiled and flashed |
| `vendor/openbci-v3-hardware/PIC32-avrdude-bootloader/` | <https://github.com/chipKIT32/PIC32-avrdude-bootloader> | `95cf5d9` (2024-02-08) | `BootloadersCurrent-hex/UDB32_MX2_DIP.hex` is the bootloader half of the flashed image |
| `mechanical/ultracortex-upstream/` | <https://github.com/OpenBCI/Ultracortex> | `338b52b` (2022-09-29) | Headset mechanicals. Only `Mark_IV` is checked out; the clone's index is empty |

`vendor/PIC32-avrdude-bootloader-master/` plus its zip is an older, separate download of
the same bootloader. Kept because the flashing was actually done from that copy.

`mechanical/a1-mini-prints/` is **not** upstream — those are the Bambu A1 Mini plates and
the Cyton case that were printed. 2.6 MB. Git-ignored with the rest of `mechanical/`; to
track them instead, drop the `/mechanical/` line from `.gitignore` and re-add.

## Restoring any of them

```bash
# hardware design files (the parent tree)
git clone https://github.com/OpenBCI/V3_Hardware_Design_Files.git vendor/openbci-v3-hardware
git -C vendor/openbci-v3-hardware checkout 6bce559

# Cyton firmware library, nested inside it (and installed for the IDE at
# Documents/Arduino/libraries/OpenBCI_32bit_Library)
git clone https://github.com/OpenBCI/OpenBCI_Cyton_Library.git \
          vendor/openbci-v3-hardware/OpenBCI_Cyton_Library
git -C vendor/openbci-v3-hardware/OpenBCI_Cyton_Library checkout 24e1c42

# chipKIT bootloader
git clone https://github.com/chipKIT32/PIC32-avrdude-bootloader.git \
          vendor/openbci-v3-hardware/PIC32-avrdude-bootloader
git -C vendor/openbci-v3-hardware/PIC32-avrdude-bootloader checkout 95cf5d9

# headset mechanicals
git clone https://github.com/OpenBCI/Ultracortex.git mechanical/ultracortex-upstream
git -C mechanical/ultracortex-upstream checkout 338b52b
```

The existing Ultracortex clone has a populated HEAD against an empty index, so it looks
like 686 staged deletions and only `Mark_IV` is on disk. Its pack holds every revision —
`Mark_1`, `Mark_2`, `Mark_3`, `Mark_III_Nova`, `Mark_III_Nova_REVISED`, `Mark_IV` — and one
command brings them all back without the network:

```bash
git -C mechanical/ultracortex-upstream reset --hard HEAD
```

That is what made it safe to delete `Ultracortex2/` (502 MB, a duplicate `.git` at the same
commit), `Ultracortex_Downloaded/` (175 MB, `Mark_1`–`Mark_3`) and `Ultracortex.zip`
(79 MB) on 1 October 2026. 756 MB freed, nothing lost.

## Local modifications to the hardware design files

Two tracked files in `vendor/openbci-v3-hardware/` differ from upstream. Both are copied
into `hardware/`, so a fresh clone of upstream plus this repo reproduces what was ordered:

| File in the clone | Change | Tracked copy here |
|---|---|---|
| `OpenBCI Cyton Designs/OpenBCI 32bit.pcb` | Re-saved from DesignSpark (360 KB → 395 KB) | `hardware/reference/OpenBCI 32bit.pcb` |
| `OBCI_Cyton_Plots/OBCI_V4_C (Component Positions CSV).csv` | Header rewritten to JLCPCB CPL format: `Name,Component,Side,Centre X,Centre Y,Rotation` → `Designator,Val,Layer,Mid X,Mid Y,Rotation` | `hardware/bom/CPL-OBCI_V4_C-jlcpcb-format.csv` |

## Toolchain versions

Not vendored, but the versions that worked, for the record:

| Tool | Version | Note |
|---|---|---|
| Arduino IDE | 2.x | chipKIT core for the Cyton, ESP32 core for the XIAO |
| chipKIT core | 2.1.0 | Already ships `Board_Defs.h` with 11/12 — do **not** apply the library's stale edit instruction |
| Board (Cyton) | chipKIT → OpenBCI 32 | variant `chipKIT.pic32.openbci` |
| Board (bridge) | XIAO_ESP32C3 | **USB CDC On Boot: ENABLED** — not optional |
| MPLAB X IPE | v5.35 | Flashing the merged hex with a PICkit 3.5 |
