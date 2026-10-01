# Wiring — Motor Imagery Montage

**Purpose:** the production montage for left-vs-right hand motor imagery, matching the
channels the models were trained on.

For the frontal hardware-validation test with ECG patches, see
`WIRING-cyton-muse-athena.md`.

---

## The target montage

Fixed by the training pipeline — `Neuro-Rehab-git/src/run_ablation.sh`:

```bash
# Simulates testing 8-channel consumer EEG hardware (e.g. ADS1299)
CHANNELS="C3 Cz C4 FC3 FC4 CP3 CP4"
```

Same seven in `cache_foundation.py` and `cache_openbmi.py`. A 5-channel subset
(`C3, Cz, C4, CP3, CP4`) is used by `train_physionet_5ch.py` → `Models/neurorehab_bci_5ch.pth`.

**7 scalp + 1 reference + 1 bias = 9 electrodes.** Cyton has 8 inputs, so 7 used, 1 spare.

```
        FC3    ·    FC4
         C3   Cz    C4          3x3 grid centred on Cz
        CP3    ·    CP4          ~12 cm ear-to-ear, ~8 cm front-to-back
```

---

## PL1 pinout reference

PL1 is `26WDP` — **26 pins, 13 rows × 2**. Odd = left column (`PL1a`), even = right (`PL1b`).

`26WDP` = **26-Way Dual Pin** — 13 rows, two pins side by side per row. Odd numbers
run down one column, even down the other; pins 1 and 2 are adjacent.

```
        ODD COLUMN (PL1a)          EVEN COLUMN (PL1b)
        pin   signal               pin   signal
        ───   ──────               ───   ──────
  row A   1   AVDD                   2   AVDD
  row B   3   AGND                   4   AGND
  row C   5   BIAS  ★                6   BIAS
  row D   7   8N    ← ch8            8   8P
  row E   9   7N    ← ch7  ★        10   7P
  row F  11   6N    ← ch6  ★        12   6P
  row G  13   5N    ← ch5  ★        14   5P
  row H  15   4N    ← ch4  ★        16   4P
  row I  17   3N    ← ch3  ★        18   3P
  row J  19   2N    ← ch2  ★        20   2P
  row K  21   1N    ← ch1  ★        22   1P
  row L  23   SRB2  ★               24   SRB1
  row M  25   AVSS                  26   AVSS

  ★ = pins used by the 7-channel montage
```

### ⚠️ Electrodes go to the **N** pins, not the P pins

The default channel settings close an internal switch between each channel's
**P input and SRB2** — confirmed in `OpenBCI_32bit_Library.cpp`:

```cpp
defaultChannelSettings[SRB2_SET] = YES;   // connect this P side to SRB2
```

The P inputs are already taken by the shared reference, so **scalp electrodes connect
to the channel's N pin.**

Convenient consequence: for standard referential recording **everything you need is in
the odd column** — N pins, SRB2, and BIAS are all odd-numbered.

⚠️ **Channel order is reversed** — channel 8 near the top, channel 1 near the bottom.

### Polarity note

Because the reference sits on P and the electrode on N, the amplifier computes
`P − N` = `reference − electrode`, i.e. the signal is **inverted** relative to the usual
`electrode − reference` convention.

For band-power features (mu/beta ERD) this makes no difference — power is
sign-independent. For a model that consumes **raw time series** (EEGNet does), a global
sign flip is a real domain shift versus the training data. Check it empirically with the
blink test and negate in the client if needed.

---

## Option A — Full 7-channel (production montage)

| Electrode | → PL1 pin | Cyton channel | Used by 5ch model? |
|---|---:|---|---|
| **C3** | **21** | ch1 (**1N**) | ✅ |
| **Cz** | **19** | ch2 (**2N**) | ✅ |
| **C4** | **17** | ch3 (**3N**) | ✅ |
| **FC3** | **15** | ch4 (**4N**) | — |
| **FC4** | **13** | ch5 (**5N**) | — |
| **CP3** | **11** | ch6 (**6N**) | ✅ |
| **CP4** | **9** | ch7 (**7N**) | ✅ |
| **Reference** (mastoid or earlobe) | **23** | SRB2 | — |
| **BIAS** (other mastoid/earlobe) | **5** | BIAS | — |

Record all 7; feed whichever 5 the current model wants. Costs two extra electrodes and
gives you data to retrain an 8-channel model later without re-gelling anyone.

---

## Option B — 3-electrode minimum (Cz as reference)

For a first motor-imagery test with a case that only has C3/Cz/C4 provisions.

| Electrode | → PL1 pin | Cyton channel |
|---|---:|---|
| **C3** | **21** | ch1 (**1N**) |
| **C4** | **19** | ch2 (**2N**) |
| **Cz** | **23** | SRB2 — **reference** |
| **BIAS** (forehead / mastoid / earlobe) | **5** | BIAS |

### Why Cz-as-reference is legitimate here

```
ch1 = C3 − Cz
ch2 = C4 − Cz
ch1 − ch2 = C3 − C4        ← Cz cancels completely
```

Left-vs-right MI is classified on the **lateralisation** between C3 and C4. A common
reference subtracted from both leaves that difference untouched, so the discriminative
information survives intact.

**Cost:** Cz sits on the motor strip and carries its own mu rhythm, so absolute
amplitudes shrink. The left/right asymmetry — the thing that matters — does not.

**This gives 2 channels**, so it will not run the 5ch or 7ch models. It is a hardware
and physiology test, not a model test.

---

## Electrode material rules

| Electrode | Matching required? | Why |
|---|---|---|
| **Signal** (C3, C4, …) | ✅ all same material | — |
| **Reference (SRB2)** | ✅ **must match the signal electrodes** | It is subtracted from every channel, so its half-cell potential appears as a DC offset on all of them |
| **BIAS** | ❌ anything conductive | Driven output, never subtracted from the signal |

> Mixing metals between signal and reference can produce a DC offset large enough to
> exceed the ADS1299's **±187.5 mV** input range (gain 24) and rail every channel.
>
> Once digitised in range, the pipeline's **4 Hz high-pass**
> (`raw.filter(4.0, 40.0)`) removes offset and drift entirely — so matched metals matter
> for *staying in range*, not for the filtered signal.

---

## Finding the positions

Use the standard 10-20 measurement rather than eyeballing — placement repeatability is
what makes per-session calibration work.

1. **Nasion → inion** over the top of the head. **Cz is at 50%.**
2. **Left preauricular → right preauricular** through Cz. Confirm Cz at 50% of this too.
3. **C3** is 20% of the ear-to-ear distance left of Cz; **C4** is 20% right.
4. **FC3 / FC4** sit halfway between C3/C4 and F3/F4 — roughly 2 cm forward of C3/C4.
5. **CP3 / CP4** sit halfway between C3/C4 and P3/P4 — roughly 2 cm behind.

FC and CP are **10-10 positions**, not part of the 19-site 10-20 set. A cap marked only
for 10-20 will not have them.

---

## Test protocol

| # | Action | Expected |
|---:|---|---|
| 1 | Send `[` | Clean square wave — proves the board independent of electrodes |
| 2 | Send `d`, then `b` | Normal inputs, streaming |
| 3 | **Blink ×5** | Visible but *smaller* than frontal — these are central sites |
| 4 | **Clench jaw** | EMG burst |
| 5 | **Eyes closed / open, 20 s blocks** | Alpha/mu change in 8–13 Hz |
| 6 | **Squeeze RIGHT hand, 5 s on / 5 s off ×10** | **Mu suppression at C3** (contralateral) |
| 7 | **Squeeze LEFT hand, same pattern** | **Mu suppression at C4** |
| 8 | **Imagine the same squeezes** | Same effect, weaker |

**Steps 6–7 are the real milestone.** Contralateral mu ERD with actual movement is the
physiological basis of motor imagery — if it appears, imagery is within reach and
everything after is signal processing.

---

## What to expect on screen

The live web UI plots **raw, unfiltered** data.

- **50 Hz mains** will be prominent. The training pipeline bandpasses **4–40 Hz**, which
  removes mains entirely — the live view has no filter yet.
- **Mu is 8–13 Hz** and will be buried under mains in the raw view. A 4–40 Hz bandpass
  plus a 50 Hz notch on the live plot makes steps 5–8 visible.
- `±187500 µV` on a channel means **railed** — electrode lifted, or BIAS not connected.

---

## Open items

- [ ] Solder header pins / wires into PL1 (unpopulated). **Count the pads — it is 13×2,
      not the 11×2 the project README claims.**
- [ ] Confirm gold cup pricing is per *set*, not per *piece* (IndiaMART listings are
      ambiguous — see `electrode_research.md`)
- [ ] FRI TDE 210 combs from Fab.to.Lab (₹95 ea at 10+) + printed `FRI_electrode_mount.stl`
- [ ] Add 4–40 Hz bandpass + 50 Hz notch to the live view
- [ ] Add per-channel contact/impedance indicator to the UI
