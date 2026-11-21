#!/usr/bin/env python3
"""Reproducible, version-pinned engine *stability* patch for ISMCTS replay.

This touches only a disposable checkout at AlphaRune's pinned commit. It does
not skip matches, change decks, invent winners, or catch/discard rule failures.

The two observed failures motivating this patch were:
1. SIGSEGV in boost::context::jump_fcontext (Mordekaiser, 438 prior SIGSEGV
   series). Increase the protected fiber stack's reserved headroom and keep
   guard-page detection; validate the crashing seeds independently.
2. An otherwise affordable Convergent Mutation play chose an unaffordable
   second target when its finalize phase skipped the viability pass. Force
   the existing engine's *payable choice search* for this targeted spell.
   It must not convert an unpayable action into a game win.
"""
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
ENGINE = ROOT / "alpharune"
EXPECTED = "ec90f0fed002aed374d06249fa95e83e3cfbd386"
sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ENGINE, text=True).strip()
if sha != EXPECTED:
    raise SystemExit("Refusing stability patch on unverified engine commit " + sha)

def replace_once(path, old, new):
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected unique pinned-source anchor in {path}: {count} occurrences")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")

step = ENGINE / "src/engine/step_driver.cpp"
replace_once(
    step,
    "constexpr size_t kFiberStackBytes = 256 * 1024;",
    "// ISMCTS can explore much deeper stacked finalize/trigger paths than the\n"
    "// older engine's 256 KiB fiber. The guard page is retained: a remaining\n"
    "// overflow is still a hard failure, never silently a simulated win.\n"
    "constexpr size_t kFiberStackBytes = 2 * 1024 * 1024;"
)
engine = ENGINE / "src/engine/game_engine.cpp"
replace_once(
    engine,
    "done = too_dear ? choosePrePlayViable(pre, payable)\n"
    "                                : collectFinalizeChoices(std::move(pre));",
    "// Convergent Mutation chooses a second target before paying, and\n"
    "// its Deflect/target-dependent costs must stay payable after *all*\n"
    "// choices. The regular fast finalize path can pick an unaffordable\n"
    "// second target even when the original play was affordable. Retain\n"
    "// the existing exact viable-sequence filtering for this spell.\n"
    "const bool requires_complete_viability =\n"
    "    state_.objectExists(what) &&\n"
    "    state_.getObject(what).name.get() == \"Convergent Mutation\";\n"
    "done = (too_dear || requires_complete_viability)\n"
    "           ? choosePrePlayViable(pre, payable)\n"
    "           : collectFinalizeChoices(std::move(pre));"
)
print("PINNED_ISMCTS_STABILITY_PATCH_APPLIED", EXPECTED)
