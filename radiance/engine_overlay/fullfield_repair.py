#!/usr/bin/env python3
"""Pinned AlphaRune rules repair for confirmed all-58 BO3 failures.

This runs after the accepted Radiance overlays and stability_patch.py in a
disposable pinned upstream checkout. It does not alter the original decks,
disable rules, suppress exceptions, or invent winners.
"""
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
ENGINE = ROOT / "alpharune"
PIN = "ec90f0fed002aed374d06249fa95e83e3cfbd386"
head = subprocess.check_output(["git", "-C", str(ENGINE), "rev-parse", "HEAD"],
                               text=True).strip()
if head != PIN:
    raise SystemExit("Refusing to patch unknown upstream version " + head)


def replace_once(path, before, after):
    text = path.read_text(encoding="utf-8")
    count = text.count(before)
    if count != 1:
        raise RuntimeError(f"Anchor mismatch {path} ({count}): {before[:120]!r}")
    path.write_text(text.replace(before, after, 1), encoding="utf-8")


# Primordial Roar's Show Off is optional, but if the player shows off a unit,
# the card requires another unit to take the damage. The prior implementation
# offered Show Off when the board had no possible damage target, then asked for
# a mandatory nonexistent target during the pre-play finalize phase.
# Preserve the legal "do not Show Off" option and make the damage requirement
# impossible to trigger without a unit. Clear a prior play's Show Off marker
# in case this card returned to hand and is replayed.
primordial = ENGINE / "src/cards/units/1084_radiance_final64_b.cpp"
replace_once(
    primordial,
    """ void asYouPlayChoices(CardContext& c)override{
   (void)f64ShowOff(c,[](const GameObject& o,const CardDef& d){
     return d.card_type==CardType::Unit||o.isUnit();
   },"Primordial Roar: Show Off a unit");
 }""",
    """ void asYouPlayChoices(CardContext& c)override{
   // The affirmative optional Show Off choice would create a mandatory
   // damage target. Do not offer that choice when no unit can be targeted.
   // The spell itself remains playable without showing off a unit.
   if(boardObjects(c.state,[](const GameObject& o){return o.isUnit();}).empty()){
     if(c.state.objectExists(c.source))
       c.state.getObject(c.source).card_counters["__final64_showoff"]=0;
     return;
   }
   (void)f64ShowOff(c,[](const GameObject& o,const CardDef& d){
     return d.card_type==CardType::Unit||o.isUnit();
   },"Primordial Roar: Show Off a unit");
 }"""
)

# One-Two Punch is checked by the complete pre-play target search in the
# previously applied stability_patch.py. Insist that the searched legality
# gate is actually present, rather than silently shipping an incomplete fix.
game = ENGINE / "src/engine/game_engine.cpp"
content = game.read_text(encoding="utf-8")
required = [
    'n == "One-Two Punch"',
    "payableThroughAFinalizeChoice(player, card_id, nullptr, true)",
    'name.get() == "Convergent Mutation"',
    "choosePrePlayViable(pre, payable)",
    "boost::context::detail::forced_unwind",
]
for expression in required:
    if expression not in content:
        raise RuntimeError(f"Missing required source-level rules repair: {expression}")

step = (ENGINE / "src/engine/step_driver.cpp").read_text(encoding="utf-8")
if "constexpr size_t kFiberStackBytes = 2 * 1024 * 1024;" not in step:
    raise RuntimeError("Missing guarded ISMCTS stack-headroom repair")

print("FULL_FIELD_CARD_TARGET_PAYMENT_AND_CONTEXT_REPAIR_APPLIED", PIN, flush=True)
