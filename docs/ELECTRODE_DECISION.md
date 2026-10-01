# Electrode & Headset Decision — NeuroRehab

**Working document for the headset design. Two viable paths, laid out with costs, setup, and the reasoning behind each.**

Context: the Cyton is built and streaming (see `CYTON_BRINGUP.md`). The remaining hardware question is what touches the scalp. This is written as a decision aid, not a conclusion — the recommendation shifts depending on whether the target is a research rig or a patient-facing rehab product.

> 💰 All prices are **estimates in INR**, current as of writing. OpenBCI prices are from their store; "generic" prices assume AliExpress / IndiaMART sourcing. **Add shipping and customs for anything imported** — a real factor, and the same one that drove the decision to fabricate the Cyton at JLCPCB rather than buy it.

---

## 1. The montage is already fixed

This is not an open question. From `Neuro-Rehab-git/src/run_ablation.sh`:

```bash
# Simulates testing 8-channel consumer EEG hardware (e.g. ADS1299)
CHANNELS="C3 Cz C4 FC3 FC4 CP3 CP4"
```

The same seven appear in `cache_foundation.py` and `cache_openbmi.py`. A 5-channel subset (`C3, Cz, C4, CP3, CP4`) is used in `train_physionet_5ch.py` with weights at `Models/neurorehab_bci_5ch.pth`.

**Requirement: 7 scalp electrodes + 1 reference + 1 bias = 9 total.** The Cyton has 8 differential inputs, so 7 channels used, 1 spare.

Geometrically these form a **3×3 grid centred on Cz**, roughly 12 cm ear-to-ear and 8 cm front-to-back:

```
        FC3    ·    FC4
         C3   Cz    C4          all within the central third
        CP3    ·    CP4          of the scalp
```

This compactness matters later — see §5.

---

## 2. What the benchmark already tells us

From `Neuro-Rehab-git/README.md`:

| Dataset | Channels | Best model | Accuracy |
|---|---:|---|---:|
| **2B** | **3** (C3/Cz/C4) | Conformer (transfer) | **78.89%** |
| 2A | 22 | EEGNet | 78.86% |

**Three well-placed electrodes matched twenty-two.** Channel *count* is not the bottleneck, so no headset choice fails on coverage grounds. What the same table shows is where accuracy actually leaks:

- **FBCSP collapsed to 52.95%** at 3 channels — near chance. Classical methods need spatial redundancy.
- **EEGNet fell 78.86% → 70.91%** when channels were cut ("struggles when deprived of spatial electrodes").
- **Transfer learning recovered it** — Conformer, Deep4 and Inception each gained 4–6 points at low density.

> ⚠️ **Architecture note:** `Models/neurorehab_bci_5ch_eegnet.txt` exists. By this benchmark, EEGNet is the *weakest* architecture in exactly the low-channel regime the Cyton puts you in. Conformer-with-transfer is the strongest. Worth revisiting before deployment.

Since coverage is solved, the headset decision reduces to two variables: **placement repeatability** and **contact impedance**.

---

## 3. Option A — Wet: textile 10-20 cap + gold cup electrodes

The research-standard approach.

### 3.1 Bill of materials

| Item | Qty | OpenBCI | Generic | Notes |
|---|---:|---:|---:|---|
| Textile 10-20 EEG cap | 1 | — | ₹2,000–5,000 | **Must have 10-10 markings** — FC3/FC4/CP3/CP4 are not in the 19-site 10-20 set |
| Gold cup electrodes | 10 | ₹4,400 | ₹1,500–3,000 | ₹150–300 each generic vs ~₹440 from OpenBCI |
| Ten20 conductive paste (228 g) | 1 | — | ₹1,200–2,000 | The actual conductor |
| NuPrep abrasive gel (114 g) | 1 | — | ₹700–1,200 | Skin prep — matters more than people expect |
| Blunt-tip syringes | few | — | ₹300 | For getting paste under hair |
| Measuring tape + skin pencil | 1 | — | ₹200 | For nasion–inion measurement |
| Gauze, alcohol wipes | — | — | ₹500 | Consumable |
| **Total** | | | **₹6,400–12,200** | |

**Not needed:** OpenBCI's ₹3,900 *Header Pin to Touch Proof Adapter*. That's for DIN 1.5 mm electrodes; gold cups terminating in header pins plug into the Cyton directly.

### 3.2 Setup procedure (~15–20 min per session)

1. Measure **nasion → inion** and **left preauricular → right preauricular**. Cz is at 50% of both.
2. Select cap size by head circumference; seat it with the cap's Cz marker on the measured Cz.
3. For each of 9 sites: part the hair, abrade lightly with NuPrep on a cotton bud.
4. Fill the gold cup with Ten20, press onto the scalp through the cap hole, seat until the paste bridges.
5. Reference and bias go on the **mastoids or earlobes** (no hair, easy contact).
6. Verify impedance on every channel before starting.
7. Afterwards: patient washes their hair; cap is washed and dried.

### 3.3 Why it's the strongest signal

- **Impedance in single-digit kΩ** versus hundreds of kΩ dry. Mu (8–13 Hz) and beta (13–30 Hz) ERD are small effects, and the Cyton's ±1 µV noise floor is only meaningful if the electrode isn't the dominant noise source.
- **Precise, repeatable placement.** Positions are *measured* from anatomical landmarks, so they're the same today and next month. This is what makes a model trained once transfer across sessions.
- **Matches the training data.** PhysioNet and OpenBMI were recorded at exact 10-10 coordinates. Placement error is distribution shift.
- **Motion tolerance.** Paste maintains contact through small head movements.

### 3.4 Why it fails as a rehab product

| Problem | Consequence |
|---|---|
| 15–20 min setup, every session | A rehab programme is *many* sessions. This is a dropout cause, not an inconvenience. |
| Patient leaves with gel in their hair | Dignity issue. Requires a shower after every session. |
| Cap must be washed and dried between patients | Kills clinic turnaround; you'd need several caps in rotation. |
| Requires a trained operator | Not something a caregiver does at home. |
| Long static sitting during application | Hard for hemiparetic patients. |

**Verdict: correct for collecting training data and for validation. Wrong for the product.**

---

## 4. Option B — Dry: comb electrodes

### 4.1 Why this is right for neurorehab

The properties that make wet electrodes better in a lab are precisely what make them unusable in a clinic:

| | Wet | Dry |
|---|---|---|
| Setup per session | 15–20 min | **~2–3 min** |
| Patient leaves with | Gel in hair | **Nothing** |
| Between patients | Wash + dry cap | **Alcohol wipe** |
| Who can apply it | Trained operator | **A caregiver, after a demo** |
| Repeat sessions over weeks | High friction | **Low friction** |

For stroke rehabilitation — repeated sessions over weeks or months, patients with hemiparesis and possible cognitive load, applied by clinic staff or family — **ease of donning dominates absolute signal quality.**

### 4.2 What makes it actually work: per-session calibration

The usual objection to dry electrodes is that placement and impedance vary between sessions, so a model trained once doesn't transfer.

**The pipeline already doesn't assume that.** `benchmark_results_final.csv` contains `n_calib_trials` of 10/15/20/27 and a full `3_adaptation` phase. Per-subject calibration is already the architecture.

A short calibration at the start of each session absorbs that day's placement and contact quality into the model. Session-to-session variability stops being an engineering problem and becomes a two-minute step the patient does while getting settled.

> **Dry electrodes + per-session calibration is a legitimate product architecture.** It costs a few accuracy points and buys a device people will actually use.

### 4.3 Bill of materials

| Item | Qty | OpenBCI | Generic / DIY | Notes |
|---|---:|---:|---:|---|
| Dry comb electrodes | 9 + spares | ₹4,900 (30-pack) | — | ≈₹163 each — reasonable. Designed for the Ultracortex node holder |
| *or* EEG Snap Electrodes (metal comb) | 5-pack | ₹3,000 | — | Needs snap cables (₹5,400) — **more expensive overall** |
| Ear-clip electrodes (ref + bias) | 2 | — | ₹500–1,500 | Earlobes/mastoids have no hair — clips beat combs here |
| Octabolts + electrode holders | 9 | — | **3D printed** | STLs already in `Ultracortex/.../M4 Hardware/` |
| Compression springs | 9 | — | ₹300 | For the spring-loaded node assembly |
| M3 screws / nuts / heat inserts | — | — | ₹400 | |
| Filament (PETG or PLA) | ~150 g | — | ₹300 | Band + holders |
| Silicone-jacketed wire, 26–28 AWG | ~5 m | — | ₹500 | Electrode → Cyton |
| Dupont / header connectors | — | — | ₹300 | To PL1 |
| 13×2 header for PL1 | 1 | — | ₹100 | ⚠️ **Count the pads first** — README says 11×2, CPL says `26WDP` |
| **Total** | | | **≈₹7,300–9,000** | |

**Comparable up-front cost to wet.** The real difference is **per-session consumables (zero vs paste + prep gel) and time (2 min vs 20 min).** Over a rehab programme, that's the entire argument.

### 4.4 Setup procedure (~2–3 min per session)

1. Select band size / adjust the sliding mechanism.
2. Seat using ear-canal and nasion landmarks.
3. Tighten each Octabolt until the contact indicator (§6) goes green.
4. Run the calibration block.
5. Afterwards: wipe electrodes with alcohol.

---

## 5. The design insight: build a band, not a cage

The Ultracortex Mark IV is a full geodesic head frame reaching 35 positions from Fp to O. **You use none of the frontal, temporal, or occipital structure** — your 7 sites sit in a compact 3×3 grid over the vertex (§1).

You are carrying a whole-head exoskeleton to instrument a strip.

**Proposal: a sensorimotor band.** An arc over the vertex from ear to ear, with short forward and rearward arms reaching the FC and CP rows — roughly an "H" or cross shape.

| Benefit | Why |
|---|---|
| **Faster donning** | One axis to align, not a cage to seat |
| **Better repeatability** | Anchor on **ear canals** (coronal line through Cz) and **nasion–inion** (A–P). Those are the same landmarks a 10-20 measurement uses — arguably *more* repeatable than a lattice hole that happens to land near FC3 |
| **Lighter, less clinical** | A band reads as a headset; a cage reads as an experiment. Matters for patient acceptance |
| **Fewer sizes to stock** | The DevKit ships five frames (`08mm_Small` → `28mm_Large`). A shorter arc tolerates far more head-size variation with one adjustment mechanism |
| **Reuses existing parts** | `M4_Hardware_09_Octabolt.STL`, `M4_Hardware_09_Eholder.STL`, `M4_Hardware_07d_Node_4d.STL` are already in the Ultracortex checkout. Keep the spring-loaded comb assembly, drop the cage |

### 5.1 Caveat on Ultracortex placement accuracy

The Mark IV is a **lattice, not a 10-20 map**. The README says the frame is *"based on an average of many heads"*; you screw nodes into whichever holes land near your target. So a Mark IV position is *approximately* FC3, varying with head size and re-seating.

For C3/C4 mu-ERD that's survivable — motor cortex is a broad strip. But it isn't repeatable between sessions, which is exactly what per-session calibration exists to absorb. A landmark-referenced band reduces the problem at source rather than relying on software to fix it.

---

## 6. Contact quality becomes a product requirement

With dry electrodes, **bad contact is the failure mode**, and the clinician must see it *before* the session, not after.

Both halves already exist:

- **Firmware:** `configureLeadOffDetection(LOFF_MAG_6NA, LOFF_FREQ_31p2HZ)` runs inside `boardReset()` at every boot. The ADS1299 impedance measurement is already configured.
- **Client:** `is_railed()` in `cyton_client.py` flags `±187500 µV` — exactly what a detached or badly-seated electrode looks like.

**To build:** a per-electrode contact indicator in the web UI — green / amber / red per channel, live during donning. The clinician adjusts each Octabolt until all seven go green, then starts.

That single feature is what separates "dry electrodes work in the lab" from "dry electrodes work in a clinic."

---

## 7. Residual risks

| Risk | Notes | How to retire it |
|---|---|---|
| **Thick or dense hair** | Where dry combs genuinely struggle. No software fix. | Test early with hair types representative of actual patients — not just yours. Fallback is a little saline on the comb tips (towels off, no shower) |
| **Comfort over 30–60 min** | Spring-loaded combs press into the scalp. Fine for 10 min, potentially sore for an hour | Measure with real session lengths before finalising the mechanical design |
| **Hemiparetic patients** | May not tolerate certain head positions or be able to assist | Design for one-handed application by a caregiver |
| **Accuracy delta vs wet** | Unquantified for this hardware | Run the same subject through both — that comparison is publishable and directly answers the question |

---

## 8. Summary

| | Wet cap | Dry band |
|---|---|---|
| Up-front cost | ₹6,400–12,200 | ₹7,300–9,000 |
| Per-session consumables | Paste + prep gel | **None** |
| Setup time | 15–20 min | **2–3 min** |
| Placement repeatability | **Excellent** (measured) | Good (landmark-referenced band) |
| Impedance | **Single-digit kΩ** | Hundreds of kΩ |
| Clinic turnaround | Poor | **Excellent** |
| Patient acceptance | Poor | **Good** |
| Best for | Training data, validation, the wet-vs-dry comparison | **The product** |

**Recommendation: build the dry band for the product; keep a wet cap for collecting ground-truth training data and for measuring what dry costs you.** They are not competing options — the wet setup is the instrument you use to validate the dry one.

---

## 9. Open questions for brainstorming

1. Is the reference on **mastoid, earlobe, or Cz**? Affects both the band geometry and how the montage compares to the training data.
2. Does calibration happen **every session**, or only when contact quality degrades? Changes the patient experience meaningfully.
3. **One band size with a wide adjustment range, or two?** Affects moulding cost later.
4. Does the Cyton mount **on the band** (weight on the head) or **clip to clothing** (cable strain)?
5. Should the contact indicator be **on the device** (an LED strip the clinician can see while adjusting) rather than only in the browser?
6. Is the target **clinic-only**, or eventually **home use**? Home use raises the bar on donning simplicity considerably.
7. Retrain on **Conformer + transfer** rather than EEGNet before deployment? §2 suggests ~8 recoverable points.
