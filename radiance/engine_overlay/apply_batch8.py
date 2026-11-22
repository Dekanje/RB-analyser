#!/usr/bin/env python3
"""Apply Radiance Batch 8 after the fully validated Batch 7 overlay."""
from pathlib import Path
import shutil

root=Path(__file__).resolve().parents[2]
engine=root/"alpharune"
source=root/"radiance/engine_overlay/source"
files=[
 ("cards/units/1010_radiance_batch8.cpp","src/cards/units/1010_radiance_batch8.cpp"),
 ("tests/cards/test_radiance_batch8.cpp","tests/cards/test_radiance_batch8.cpp"),
 ("cards/units/1016_radiance_batch8_tranche2a.cpp","src/cards/units/1016_radiance_batch8_tranche2a.cpp"),
 ("cards/units/1019_radiance_batch8_tranche2b.cpp","src/cards/units/1019_radiance_batch8_tranche2b.cpp"),
 ("cards/units/1022_radiance_batch8_tranche2c.cpp","src/cards/units/1022_radiance_batch8_tranche2c.cpp"),
]
for src,dest in files:
    target=engine/dest
    if target.exists():raise SystemExit("Batch8 source collision: "+str(target))
    shutil.copyfile(source/src,target)
init=engine/"src/cards/cards_init.cpp"
s=init.read_text()
declaration="void register_card_1009(CardRegistry&);"
registration="    register_card_1009(registry);"
assert s.count(declaration)==1 and s.count(registration)==1, "Batch7 anchors changed"
s=s.replace(declaration,declaration+"\n"+"\n".join(
    f"void register_card_{i}(CardRegistry&);" for i in range(1010,1025)),1)
s=s.replace(registration,registration+"\n"+"\n".join(
    f"    register_card_{i}(registry);" for i in range(1010,1025)),1)
init.write_text(s)
# CR 323.6 has an "unless an effect would indicate otherwise" exception:
# [Deploy] is precisely the printed permission for an unattached Gear to
# remain at a battlefield. Ordinary unattached Gear still recalls to base.
game=engine/"src/engine/game_engine.cpp"
g=game.read_text()
before="if (obj.isGear() && !obj.attached_to.has_value() && obj.isAtBattlefield())"
after="if (obj.isGear() && !obj.attached_to.has_value() && obj.isAtBattlefield() &&\n            !obj.hasKeyword(Keyword::Deploy))"
assert g.count(before)==1, "Batch 8 Deploy cleanup anchor changed"
game.write_text(g.replace(before,after,1))

print("RADIANCE_BATCH8_TRANCHE1_APPLIED: engine IDs 1010..1015; Deploy recall exception")
