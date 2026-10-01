# Wiring — Cyton ↔ Muse Athena Comparison Montage

**Purpose:** validate the self-fabricated Cyton against a commercial headset (Muse) using
frontal/temporal positions, with 3M Ag/AgCl ECG gel patches. No hair, no dry-electrode
problems, no custom mount required.

This is a **hardware validation test**, not a motor-imagery test. For MI see
`WIRING-motor-imagery.md`.

---

## Why this test

| | |
|---|---|
| **No hair** | ECG patches stick straight to skin. Removes the entire hair-penetration problem. |
| **Better electrodes than the bolts** | 3M patches are Ag/AgCl with wet gel — non-polarizable, low drift, low impedance. Materially better than SS 304. |
| **All electrodes matched** | Every contact is the same 3M Ag/AgCl. No dissimilar-metal DC offset. |
| **Ground truth available** | You own a Muse. Same positions → direct comparison against a commercial device. |
| **Strong, obvious signals** | Frontal sites give the largest blink and EOG artifacts on the head. Easy to confirm life. |

---

## PL1 pinout reference

PL1 is `26WDP` — **26 pins, 13 rows × 2**. Odd pins are the left column (`PL1a`),
even pins the right (`PL1b`).

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
  row E   9   7N    ← ch7           10   7P
  row F  11   6N    ← ch6           12   6P
  row G  13   5N    ← ch5           14   5P
  row H  15   4N    ← ch4           16   4P
  row I  17   3N    ← ch3           18   3P
  row J  19   2N    ← ch2  ★        20   2P
  row K  21   1N    ← ch1  ★        22   1P
  row L  23   SRB2  ★               24   SRB1
  row M  25   AVSS                  26   AVSS

  ★ = pins used in this test
```

### ⚠️ Electrodes go to the **N** pins, not the P pins

The default channel settings close an internal switch between each channel's
**P input and SRB2** — confirmed in `OpenBCI_32bit_Library.cpp`:

```cpp
defaultChannelSettings[SRB2_SET] = YES;   // connect this P side to SRB2
```

So the P inputs are already taken by the shared reference. **Your scalp electrode
connects to the channel's N pin.**

Convenient consequence: for standard referential recording **everything you need is
in the odd column** — N pins, SRB2, and BIAS are all odd-numbered.

⚠️ **Channel order is reversed** — channel 8 is near the top, channel 1 near the bottom.

---

## Muse electrode positions

The classic Muse layout is **TP9, AF7, AF8, TP10**, referenced to **Fpz**.

> ⚠️ **Verify this against the Athena's own documentation before relying on it for a
> like-for-like comparison.** The Athena is a newer model and may differ from the
> Muse 2 / Muse S layout. The positions below are the standard Muse montage.

| Muse site | Where it sits |
|---|---|
| **Fpz** | Centre of forehead, above the bridge of the nose (reference) |
| **AF7** | Left forehead, above the outer third of the left eyebrow |
| **AF8** | Mirror image on the right |
| **TP9** | Behind the left ear, on the mastoid bone |
| **TP10** | Behind the right ear, on the mastoid bone |

---

## Option A — Minimal 2-channel test (start here)

Four patches. Fastest path to "is my board reading a real brain".

| Electrode | Position | → PL1 pin | Cyton channel |
|---|---|---:|---|
| Patch 1 | **AF7** (left forehead) | **21** | ch1 (**1N**) |
| Patch 2 | **AF8** (right forehead) | **19** | ch2 (**2N**) |
| Patch 3 | **Fpz** (centre forehead) | **23** | SRB2 — reference |
| Patch 4 | **Mastoid or earlobe** | **5** | BIAS |

## Option B — Full 4-channel Muse-equivalent

Six patches. Gives you all four Muse sites for a proper comparison.

| Electrode | Position | → PL1 pin | Cyton channel |
|---|---|---:|---|
| Patch 1 | **AF7** | **21** | ch1 (**1N**) |
| Patch 2 | **AF8** | **19** | ch2 (**2N**) |
| Patch 3 | **TP9** (behind left ear) | **17** | ch3 (**3N**) |
| Patch 4 | **TP10** (behind right ear) | **15** | ch4 (**4N**) |
| Patch 5 | **Fpz** | **23** | SRB2 — reference |
| Patch 6 | **Earlobe or neck** | **5** | BIAS |

> **BIAS is not optional.** It is a *driven* electrode — the amplifier pushes current
> into it to hold your body's common-mode voltage inside the input range. Without it,
> 50 Hz mains swamps everything and channels may rail.
>
> Unlike the reference, **BIAS material does not need to match** — it is never
> subtracted from the signal.

---

## Connecting to the board

PL1 is unpopulated, so:

1. **Solder single male header pins** into only the holes you need (snap them off a
   breakaway strip). That's 4 pins for Option A, 6 for Option B.
2. Your **alligator-clip-to-Dupont-female** leads then plug straight onto those pins.
3. Clip the alligator jaw onto the **snap stud** of each ECG patch — it grips the metal
   post fine, no snap adapter needed.

Keep the leads loose. ECG patch adhesive is not strong enough to survive a taut wire.

---

## Skin prep

Forehead skin is oily and this matters more than people expect.

1. Wipe each site with an **alcohol swab**, let it dry fully.
2. Press the patch down firmly for a few seconds; make sure the gel contacts skin
   across the whole disc, not just the rim.
3. Leave 2–3 minutes before recording — freshly applied gel electrodes drift while the
   gel settles into the skin.

---

## Test protocol

Run in order. Each step proves more than the last.

| # | Action | Expected |
|---:|---|---|
| 1 | Send `[` (2× square wave) | Clean square wave. Confirms the **board** is fine independent of electrodes. |
| 2 | Send `d` then `b` | Back to normal inputs, streaming |
| 3 | **Blink hard ×5** | Huge deflections (hundreds of µV) on AF7/AF8. **This is your proof of life.** |
| 4 | **Look hard left, then right** | EOG step artifacts, opposite polarity on AF7 vs AF8 |
| 5 | **Clench jaw 2 s** | Dense high-frequency EMG burst |
| 6 | **Eyes closed 20 s / open 20 s ×3** | Alpha (8–12 Hz) rises with eyes closed. Weaker frontally than occipitally but usually visible. |

If step 3 works, you have real biopotentials and the whole chain is proven.

---

## Comparing against the Muse

You can't easily sync timestamps between the two devices, so compare **event-locked
effects** rather than raw traces:

1. Run the **eyes-closed / eyes-open** block (step 6) on the Muse, note the alpha change
   its app reports.
2. Repeat the identical block on the Cyton.
3. Compare the **ratio** of alpha power (8–12 Hz) between eyes-closed and eyes-open on
   each device.

The absolute µV values will differ — different reference, different gain, different
electrode contact. **The eyes-closed/open alpha ratio is the comparable number**, and it
should be in the same ballpark on both if your board is working correctly.

Blink amplitude is a useful second check — it should be large and obvious on both.

---

## What to expect on screen

The live web UI plots **raw, unfiltered** data.

- **50 Hz mains will be prominent.** Your training pipeline bandpasses 4–40 Hz, which
  removes mains entirely, but the live plot has no filter yet.
- **Slow drift** in the first minute or two as gel settles.
- **Blinks will be unmistakable** — they are far larger than anything else here.

If a channel sits at `±187500 µV` it is **railed** — the patch has lifted, or BIAS is
not connected.
