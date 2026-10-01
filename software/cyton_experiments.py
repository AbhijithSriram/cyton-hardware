#!/usr/bin/env python3
"""
cyton_experiments.py - Timed cue protocols for the Cyton web app.

Each experiment is a flat list of steps. A step is:

    {
      "label":   short machine-readable tag, written into every CSV row
      "cue":     the text shown to the participant
      "sub":     optional smaller line under the cue
      "seconds": how long the step lasts
      "style":   colour theme -> neutral | open | closed | cue | active | rest
    }

The runner stamps each step transition with the absolute SAMPLE INDEX, not just a
wall clock, so event onsets are locked to the 250 Hz data timeline and stay exact
regardless of browser lag or render delay.
"""

import random


def _alpha_block(repeats=3, open_s=20, closed_s=20):
    """Eyes-open / eyes-closed alternation - the classic alpha-blocking paradigm."""
    steps = [{
        "label": "settle", "cue": "RELAX",
        "sub": "Sit still, eyes open. Recording is starting.",
        "seconds": 10, "style": "neutral",
    }]
    for i in range(repeats):
        steps.append({
            "label": "eyes_open", "cue": "EYES OPEN",
            "sub": f"Block {i+1} of {repeats} - stay still, look ahead",
            "seconds": open_s, "style": "open",
        })
        steps.append({
            "label": "eyes_closed", "cue": "EYES CLOSED",
            "sub": f"Block {i+1} of {repeats} - keep them closed, stay still",
            "seconds": closed_s, "style": "closed",
        })
    steps.append({
        "label": "end", "cue": "DONE",
        "sub": "You can relax. Saving the recording.",
        "seconds": 5, "style": "neutral",
    })
    return steps


def _signal_check():
    """Fast hardware validation - each step produces an unmistakable artifact."""
    return [
        {"label": "rest_1", "cue": "RELAX",
         "sub": "Sit still. Establishing a baseline.", "seconds": 10, "style": "neutral"},
        {"label": "blink", "cue": "BLINK HARD",
         "sub": "One firm blink per second", "seconds": 10, "style": "active"},
        {"label": "rest_2", "cue": "RELAX",
         "sub": "Still again", "seconds": 8, "style": "rest"},
        {"label": "jaw_clench", "cue": "CLENCH JAW",
         "sub": "Hold it", "seconds": 5, "style": "active"},
        {"label": "rest_3", "cue": "RELAX",
         "sub": "Still again", "seconds": 8, "style": "rest"},
        {"label": "eyes_closed", "cue": "EYES CLOSED",
         "sub": "Keep still", "seconds": 15, "style": "closed"},
        {"label": "eyes_open", "cue": "EYES OPEN",
         "sub": "Look ahead", "seconds": 15, "style": "open"},
        {"label": "end", "cue": "DONE",
         "sub": "Saving the recording.", "seconds": 5, "style": "neutral"},
    ]


def _motor_imagery(n_trials=20, seed=42):
    """
    Left/right hand motor imagery, BCI-Competition-style trial structure:
        fixation 2 s -> cue 1.5 s -> imagery 4 s -> rest 3 s

    Trial order is shuffled with a fixed seed, so it is balanced and reproducible
    but not predictable to the participant.
    """
    rng = random.Random(seed)
    order = ["LEFT"] * (n_trials // 2) + ["RIGHT"] * (n_trials // 2)
    rng.shuffle(order)

    steps = [{
        "label": "settle", "cue": "RELAX",
        "sub": "Sit still. The task will start shortly.",
        "seconds": 10, "style": "neutral",
    }]
    for i, side in enumerate(order):
        low = side.lower()
        steps.append({
            "label": "fixation", "cue": "+",
            "sub": f"Trial {i+1} of {n_trials}", "seconds": 2, "style": "neutral",
        })
        steps.append({
            "label": f"cue_{low}", "cue": f"{side}",
            "sub": "Get ready", "seconds": 1.5, "style": "cue",
        })
        steps.append({
            "label": f"imagery_{low}", "cue": f"IMAGINE {side} HAND",
            "sub": "Imagine squeezing - do not actually move",
            "seconds": 4, "style": "active",
        })
        steps.append({
            "label": "rest", "cue": "REST",
            "sub": "", "seconds": 3, "style": "rest",
        })
    steps.append({
        "label": "end", "cue": "DONE",
        "sub": "Saving the recording.", "seconds": 5, "style": "neutral",
    })
    return steps


def _motor_execution(n_trials=20, seed=7):
    """
    Same structure as motor imagery but with ACTUAL movement. Produces a much
    stronger mu ERD, so run this first to confirm the effect exists at all
    before attempting imagery.
    """
    steps = _motor_imagery(n_trials=n_trials, seed=seed)
    for s in steps:
        if s["label"].startswith("imagery_"):
            side = s["label"].split("_")[1].upper()
            s["label"] = f"move_{side.lower()}"
            s["cue"] = f"SQUEEZE {side} HAND"
            s["sub"] = "Actually squeeze, open and close"
    return steps


EXPERIMENTS = {
    "signal_check": {
        "name": "Signal Check (1 min)",
        "description": "Blink, jaw clench, eyes open/closed. Fastest proof the "
                       "whole chain works. Run this first on any new setup.",
        "steps": _signal_check(),
    },
    "athena_alpha": {
        "name": "Athena / Alpha Test (2 min)",
        "description": "Eyes open vs closed, 3 blocks of 20 s each. Compare the "
                       "8-12 Hz alpha ratio against the Muse for validation.",
        "steps": _alpha_block(),
    },
    "athena_alpha_long": {
        "name": "Athena / Alpha Test - long (4 min)",
        "description": "Same as above with 5 blocks. More trials, tighter estimate.",
        "steps": _alpha_block(repeats=5),
    },
    "motor_execution": {
        "name": "Motor Execution L/R (4 min)",
        "description": "20 trials of ACTUAL left/right hand squeezing. Produces a "
                       "strong mu ERD - confirm this works before trying imagery.",
        "steps": _motor_execution(),
    },
    "motor_imagery": {
        "name": "Motor Imagery L/R (4 min)",
        "description": "20 trials of imagined left/right hand movement. The real "
                       "paradigm. Requires C3/C4 electrodes.",
        "steps": _motor_imagery(),
    },
}


def total_seconds(exp_id):
    exp = EXPERIMENTS.get(exp_id)
    return round(sum(s["seconds"] for s in exp["steps"]), 1) if exp else 0.0


def listing():
    """Metadata for the UI dropdown."""
    return [
        {
            "id": k,
            "name": v["name"],
            "description": v["description"],
            "steps": len(v["steps"]),
            "seconds": total_seconds(k),
        }
        for k, v in EXPERIMENTS.items()
    ]
