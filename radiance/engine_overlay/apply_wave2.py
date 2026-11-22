#!/usr/bin/env python3
"""Apply Wave 2 strictly after the validated Wave 1 overlay and regression fix."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[2]
engine=root/"alpharune"
source=root/"radiance/engine_overlay/source"
for src,dst in [
 ("cards/spells/0994_radiance_brawl.cpp","src/cards/spells/0994_radiance_brawl.cpp"),
 ("tests/cards/test_radiance_wave2.cpp","tests/cards/test_radiance_wave2.cpp")
]:
 target=engine/dst
 if target.exists(): raise SystemExit("Wave 2 collision: "+str(target))
 shutil.copyfile(source/src,target)
init=engine/"src/cards/cards_init.cpp"
s=init.read_text()
a="void register_card_993(CardRegistry&);"
b="    register_card_993(registry);"
assert s.count(a)==1 and s.count(b)==1,"Wave 1 registration anchors changed"
s=s.replace(a,a+"\nvoid register_card_994(CardRegistry&);",1)
s=s.replace(b,b+"\n    register_card_994(registry);",1)
init.write_text(s)
print("WAVE2_APPLIED: RAD-004 Brawl, engine ID 994, deterministic tests")
