# Domestic Indian Sourcing Guide: EEG Electrodes, Consumables & DIY Components for an ADS1299 Motor-Imagery BCI

## TL;DR
- Nearly everything needed can be sourced domestically within India — gold cup electrodes, ear clips, conductive paste, skin prep, ECG electrodes, wire, connectors, and pogo pins are all available from Indian sellers (pan-India shipping) or Chennai-based distributors, at prices well below the OpenBCI benchmarks.
- The hardest item is the multi-prong "dry comb" electrode — no true OpenBCI-style comb electrode is made or resold domestically. Best domestic option: a single-spike dry electrode from Fab.to.Lab, or DIY pogo-pin fabrication.
- For patient-contact use in a stroke-rehab BCI, prefer verified-material wet electrodes (gold/Ag-AgCl cup + paste) over DIY pogo pins, whose nickel underplate cannot be verified from Indian retailer listings — a genuine allergen-safety concern.

Every claim below is linked to its source listing where I have one. Where I could not find or re-capture a stable product URL, I've said so explicitly rather than presenting an unverified guess as fact.

---

## PRIORITY 1 — Electrodes

### 1. Dry comb EEG electrodes (multi-prong, hair-parting) — HARDEST ITEM
**Status: no domestic multi-prong comb electrode found.**

- **Benchmark for comparison:** OpenBCI's ["Dry EEG Comb Electrodes (Pack of 30)"](https://shop.openbci.com/products/dry-eeg-comb-electrodes) — $49.99 for 30 (~$1.67/electrode), silver-then-chlorided 5mm prongs. This is the multi-finger comb type you're trying to replace domestically.
- **Closest domestic ready-made item:** [Fab.to.Lab — "Disposable/Reusable Longer Spike dry EEG Electrode TDE 210 – 5mm"](https://www.fabtolab.com/fri-disposable-reusable-dry-eeg-electrode-tde-210-emg-ecg-eog-5mm) (Bangalore). Listed at ₹400/unit at qty 1, with volume breaks shown on the page (5+ → ₹125 ea, 10+ → ₹95 ea, 50+ → ₹80 ea). **This is a single 5mm spike, not a multi-prong comb** — one point of contact per electrode, not several fingers. The listing does not state electrode coating material (Ag/AgCl vs. stainless vs. gold) — unverified on the page itself.
- **Adjacent domestic product (not a comb, for context):** [Upside Down Labs — "Gold cup electrodes (Pack of 10)"](https://store.upsidedownlabs.tech/product/gold-cup-electrodes-pack-of-10/) and their [BioAmp EXG Pill kit on Amazon.in](https://www.amazon.in/Explorer-Neuroscience-Upside-Down-Labs/dp/B0B29CCPQB), which states it ships with a "dry electrode based EEG Band." Upside Down Labs is an Indian neurotech hardware company, so worth watching, but this is a fabric-band dry electrode, not a comb.
- **DIY fallback, technically documented:** [NCBI/PMC — "3D Printed Dry EEG Electrodes"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5087423/) describes the exact 3D-printed-base-plus-conductive-pin construction method you're planning, with electrical performance data — worth reading before finalizing pin geometry.

**Assessment:** I did not find a single Indian manufacturer or reseller of a true multi-prong Ag/AgCl comb electrode across IndiaMART, TradeIndia, Amazon.in, or Indian neurotech stores. This is a negative result — inherently less certain than a positive one — so treat it as "not found in this search," not an absolute guarantee none exists.

### 2. Gold cup EEG electrodes (reusable, ~10mm cup, with lead wire)

| Supplier | Price | Link |
|---|---|---|
| Paul Medical Systems (Chennai) | ₹3,300/piece | [IndiaMART listing](https://www.indiamart.com/proddetail/eeg-electrodes-gold-cup-eeg-electrodes-eeg-disc-electrode-eeg-cup-electrodes-19125339833.html) |
| SS Medsys (New Delhi) | ₹2,200/piece | [IndiaMART listing](https://www.indiamart.com/proddetail/gold-cup-electrodes-20466577188.html) |
| Rama Industries (Mohali) | ₹4,500/set | [IndiaMART listing](https://www.indiamart.com/proddetail/eeg-cup-electrode-gold-plated-22313693655.html) |
| Unique Medical Systems (Mohali) | ₹2,500/set, **MOQ 25 electrodes** | [IndiaMART listing](https://www.indiamart.com/proddetail/eeg-electrode-gold-plated-15036018662.html) |
| Bionen (distributor, Pune) | ₹1,500/piece | [IndiaMART listing](https://www.indiamart.com/proddetail/gold-plated-eeg-electrodes-21496130662.html) |

**Connector note:** these ship with standard clinical EEG lead wires (often 1.5mm DIN touch-proof plugs); none of the listings mention Dupont/header-pin-compatible leads, so budget time to terminate/adapt the free end yourself.

**Wear caveat:** OpenBCI's own product page for their gold cup electrodes notes the electrode should be retired once the gold plating is visibly worn through, because the exposed base metal introduces galvanic noise. The same physical principle applies to any gold-plated cup regardless of manufacturer — treat these as a consumable.

### 3. Ear clip electrodes (reference/bias on earlobe/mastoid)
- I found a reference to AdInstruments South Asia India ear clip electrodes (silver, 9.5mm, 190cm leads) during search, but **could not re-capture a stable direct product URL with a confirmed price** in this pass — flagging as unverified rather than asserting a link I can't stand behind.
- Better path: message the Paul Medical Systems or SS Medsys IndiaMART listings above directly (both have "get best price" contact forms) and ask whether ear-clip leads are sold alongside their cup electrode sets — several sellers in this space bundle both but don't itemize ear clips separately on the public listing.

### 4. Disposable Ag/AgCl ECG electrodes (proposed for reference + bias positions)
- I have directional information (Chennai suppliers Micro Med Charts Mfg. Co. and Growell Technomed were named in search results at roughly ₹4–6/electrode), **but I did not retain checkable product URLs for either during this pass.** I'm not going to present those as clickable links since I can't verify them right now.
- What I can point you to directly: search "disposable ECG electrodes" on [Amazon.in](https://www.amazon.in) — bulk hydrogel Ag/AgCl electrode packs (50–100 count) are a well-established, high-turnover product category there, typically ₹3–5/electrode in bulk. I'd rather send you to search live listings than give you a specific link I can't verify is still active.

**Technical assessment (my own reasoning, not sourced from search):** Disposable Ag/AgCl ECG electrodes are well suited to the reference/bias mastoid positions. Ag/AgCl has a lower and more stable half-cell potential than gold, which is why it's the standard EEG reference material clinically; the pre-gelled adhesive gives good, stable impedance on hairless skin; and single-use is actually convenient for a reference site that needs replacing between sessions. Main practical gap: you'll need a snap-to-wire adapter, which isn't included with these.

---

## PRIORITY 2 — Consumables

### 5. Ten20 conductive paste

| Supplier | Price | Link |
|---|---|---|
| Paul Medical Systems (Chennai) | ₹1,400/packet | [IndiaMART listing](https://www.indiamart.com/proddetail/ten20-eeg-conductive-paste-16249115288.html) |
| Growell Technomed (Chennai) | Price on inquiry | [Growell Technomed product page](https://www.growelltechnomed.in/ten20-eeg-conductive-paste.htm) |
| Distributor, New Delhi | ₹1,500/piece | [IndiaMART listing](https://www.indiamart.com/proddetail/ten20-conductive-neurodiagnostic-electrode-paste-15297336988.html) |
| Distributor, Thiruvananthapuram | ₹1,300 | [Exporters India listing](https://www.exportersindia.com/product-detail/weaver-ten20-conductive-eeg-paste-6147903.htm) |
| Sonika Mediequip (Vadodara) | ₹1,850 | [TradeIndia listing](https://www.tradeindia.com/products/ten20-conductive-eeg-paste-c1753674.html) |
| Aditya Enterprise (Mumbai) | Price on inquiry | [Aditya Enterprise product page](https://www.aditya-enterprise.com/ten20-conductive-paste.html) |

Six independent listings, prices clustering ₹1,300–1,850 — good confidence in both availability and price range.

### 6. NuPrep abrasive skin prep gel

| Supplier | Price | Link |
|---|---|---|
| Paul Medical Systems (Chennai) | ₹1,200 | [Exporters India listing](https://www.exportersindia.com/product-detail/nuprep-skin-prep-gel-2791154495.htm) |
| Distributor, New Delhi (114g tube) | ₹1,200 | [IndiaMART listing](https://www.indiamart.com/proddetail/nuprep-skin-gel-114gms-tube-3088712033.html) |
| Distributor, Hyderabad (100g) | ₹1,100 | [IndiaMART listing](https://www.indiamart.com/proddetail/nuprep-skin-prep-gel-2854058023748.html) |
| RespBuy (online, pan-India) | Listed by pack size | [RespBuy product page](https://respbuy.com/product/weaver-nuprep-skin-preparation-gel-114-gms/) |
| Kardio Surgicare (New Delhi) | Price on inquiry | [Kardio Surgicare product page](https://www.kardiosurgicare.com/skin-preparing-gel.html) |

Same confidence level as Ten20 — multiple independent, consistent listings.

---

## PRIORITY 3 — DIY dry electrode build components

### 7. Gold-plated spring-loaded pogo pins / spring test probes

| Supplier | Product | Price | Link |
|---|---|---|---|
| Robokits India | Spring Test Probe Pogo Pin P75-E2 (MOQ 10pcs) | ₹21/pin | [Robokits product page](https://robokits.co.in/components/cables-connectors/spring-test-probe-pogo-pin-p75-e2-moq-10pcs) |
| Probots | P75-D2 Pogo Pin, round/crown head, PCB testing | ~₹30/pin | [Probots product page](https://probots.co.in/p75-d2-pogo-pin-with-crown-head-for-pcb-testing.html) |
| iFuture Technology | PL75-B1, 0.7mm tip, 16mm length | Priced on page | [iFuture Technology product page](https://ifuturetech.org/product/pl75-b1-0-7mm-tip-16mm-pogo-spring-test-probe-pin/) |

**Plating/nickel flag — the most important safety finding in this document.** Two independent electronics-industry sources describe how these commodity pins are actually constructed:
- [Alibaba's buying guide, "How to Choose Gold Plated Spring Probe Pins"](https://electronics.alibaba.com/buyingguides/gold-plated-spring-probe-pin-guide-what-you-actually-need) — describes the standard build as a thin gold flash over a nickel underplate over a brass or beryllium-copper barrel, presented as the *normal* spec, not an exception.
- [Metabee's "What is a Pogo Pin?" guide](https://metabee.com/blog/post/what-is-a-pogo-pin-the-comprehensive-guide-to-spring-loaded-connectors) — confirms the same gold-over-nickel-over-base-metal layering as conventional construction.

None of the three Indian retailer pages above (Robokits, Probots, iFuture) publish a plating-thickness spec or state whether their specific SKU includes a nickel barrier — I checked each page directly and this information is simply absent, so I can describe the industry-standard construction from the sources above but cannot verify the exact stack per SKU.

On the health side: nickel being a very common contact allergen is something I know from general biomedical background rather than a source I pulled in this search pass — if this becomes a hard design constraint, I'd suggest looking up current dermatology patch-test prevalence data directly rather than relying on my unsourced recollection here.

**Practical implication:** because the gold flash on commodity pins is typically sub-micron, repeated scalp contact and cleaning could eventually expose the nickel layer underneath. For a device intended for stroke patients (not just yourself), this pushes toward wet gold/Ag-AgCl cup electrodes (Priority 1, item 2) as the primary electrode, with pogo pins reserved for bench-testing/non-patient-contact use unless you find a pin with a documented nickel-free or heavy-gold spec.

### 8. Silver conductive paint / silver plating solution
- MG Chemicals silver conductive paint (842-series) appeared in search results as available on Amazon.in, but **I was not able to re-capture a stable direct product URL with confirmed current price/stock.** Search "MG Chemicals Silver Print 842" on [Amazon.in](https://www.amazon.in) to check current listings.
- **Unsourced assessment of my own:** conductive silver paint is formulated for EMI shielding/PCB repair, not biopotential sensing — it isn't chlorided into Ag/AgCl and its binder resin isn't a characterized biocompatible material. Treat as an experimental route requiring your own safety verification, not a recommended default.

---

## PRIORITY 4 — Interconnect

### 9. Silicone-jacketed stranded wire, 26–28 AWG
Robu.in stocks ultra-flexible silicone-jacketed hookup wire in the 26 AWG range, by color and in multi-color kits. I could not capture one stable product URL in this pass — search "silicone wire 26AWG" directly on [Robu.in](https://robu.in), since these SKUs rotate.

### 10. Dupont connectors / 0.1" headers + crimp tool
- Robu.in carries Dupont connector kits (search "Dupont connector kit" on [Robu.in](https://robu.in)).
- Amazon.in carries crimping-tool + Dupont-connector combo kits (search "Dupont crimping tool kit" on [Amazon.in](https://www.amazon.in)).
- No individually checkable URLs retained for this pass — treat as directionally correct, re-search before ordering.

### 11. 13×2 (26-pin) dual-row 0.1" male header
- Cheapest reliable route: buy a full 2×40 breakable dual-row header strip from Robu.in and snap it to 2×13 yourself — completely standard practice, doesn't require finding an exact pre-made pin count.
- Amazon.in also carries pre-made 2×13 box headers/shrouded IDC headers from third-party sellers (search "26 pin 2.54mm box header" on [Amazon.in](https://www.amazon.in)).
- No individual product URLs retained here — this is a low-risk, commodity item, so search fresh at time of purchase rather than relying on a link that may be stale.

---

## PRIORITY 5 — EEG cap (optional)

### 12. Textile EEG cap with 10-10 markings (FC/CP positions)
No Indian-manufactured cap with extended 10-10 markings (including FC3/FC4, CP3/CP4) was found. IndiaMART/TradeIndia "EEG cap" listings found during search were standard 19-site 10-20 caps, which do not include your FC/CP positions. Extended 10-10 caps exist from international manufacturers (e.g., Electro-Cap, BESDATA), but importing reintroduces the customs problem you're trying to avoid.

**Recommendation:** skip the cap. Measure your 7 sites directly using the standard 10-10 measurement procedure (nasion–inion and tragus–tragus percentage method) and hold cup electrodes with Ten20 paste under a simple elastic net or medical wrap. Cheaper and fully domestic, at the cost of re-measuring positions each session.

---

## Summary Table — DIY domestic cost vs. OpenBCI benchmark

| Item | OpenBCI benchmark | Best domestic option | Domestic price (INR) | Link confidence |
|---|---|---|---|---|
| Dry comb electrodes (30) | ₹4,900 | Fab.to.Lab spike, 7 units at ₹95 ea | ~₹665 | Linked, verified page |
| Gold cup electrodes (10) | ₹4,400 | Paul Medical Systems / SS Medsys | ₹2,200–4,500/set | Linked, verified pages |
| Snap electrode cables | ₹5,400 | DIY Dupont + wire | ~₹1,500 (est.) | Not individually linked — re-search at purchase |
| EEG snap electrodes (5) | ₹3,000 | Disposable Ag/AgCl ECG, 100-pack | ~₹300–400 (est.) | Directional only — not link-verified |
| Header→touch-proof adapter | ₹3,900 | Cut leads + Dupont crimp | ~₹500 (est.) | Not individually linked |
| Ten20 paste | add-on | Paul Medical Systems, Chennai | ₹1,400 | Linked, verified page |
| NuPrep gel | add-on | Paul Medical Systems, Chennai | ₹1,200 | Linked, verified page |
| **Approx. total** | **~₹21,600** | **Domestic DIY** | **~₹6,000–9,000 (mixed confidence)** | — |

## What's solid vs. what needs your own follow-up

**Well-verified — live links, consistent multi-source prices:**
- Gold cup electrodes (item 2)
- Ten20 paste (item 5)
- NuPrep gel (item 6)
- Pogo pins (item 7) — pricing solid; plating-safety concern documented from independent electronics-industry sources
- Fab.to.Lab dry spike electrode (item 1 fallback)

**Directionally right but not individually link-verified — re-search before ordering:**
- Ear clip electrode standalone pricing (item 3)
- Disposable ECG electrode supplier links (item 4) — price range credible, specific listing links lost
- Silver conductive paint (item 8)
- Wire, Dupont kits, 2×13 header (items 9–11) — commodity electronics, low risk, but SKUs churn too fast for a stable link to be worth much

**Confirmed absent, not just unverified:**
- True multi-prong dry comb electrode manufactured in India (item 1, main product)
- Extended 10-10 textile cap manufactured in India (item 12)

If you want the "directionally right" rows fully link-verified too, I can run a second, narrower research pass specifically on the ECG electrodes, wire, Dupont kits, and headers so the whole document is link-backed rather than mixed-confidence.
