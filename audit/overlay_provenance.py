"""Reconstruct and verify reviewed P0-04 test source against pinned historical XML.
This is source provenance, not a native execution or behavioral certification.
"""
import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

XML_SHA = "27a2b0fdf15dbde33b38b4a2af0438e9676101ab1e0ecd5f5d893938a3c11e53"
UPSTREAM = {
    "tests/cards/card_test_fixture.h": "46127edac7ef26b29478a9445536928cbf6f0222",
    "tests/cards/test_baron_nashor.cpp": "0a88addfae861a8b002f2e62fd1e86081bc559e3",
    "tests/test_review_fix_auras_costs.cpp": "2de935c242fa08d9d5a0187b0ddad321a232c831",
    "tests/test_review_fix_executor.cpp": "5c3717d8e61a79d579817e1be205df036e4cc679",
}
REVIEWED = {
    "wave1": "1bfa61da1b8ce51c13dcfb83c91362b0063d6b0b",
    "wave2": "fba7514a1405a91f33a8c828844e00eb7b25d15f",
    "wave3": "b5834494ab3e7396717cea617b832951bc41d884",
    "wave4": "45bbfc7bf4763b1220fea13cb682bd0a776ae6a0",
    "batch6": "60f908961068bb60c7add3710a9fbb170fee7e44",
    "batch7": "57a67975b0b7dedf8afd46e0953908f706772b57",
    "batch8": "81a1bd63e535cc2d67d6824c7eb7c0fd3b5003fa",
    "batch9": "e7209f63db14004399085ad7ac30821d5a050d0d",
}
FINAL64_SHA = "2c6bf1ad04fe1bbb9cd0624d94f148f3b946660a"
BARON = ("QABaronNashorAuraAffectsOtherFriendlyUnits",
         "QABaronNashorAuraStacksWithHeimerMechReplacement")
SHARED = (
    "AurasCostsTest.BaronNashor_OtherFriendlyUnitsPlusTwo",
    "AurasCostsTest.EquippedAssaultAndShield_AddMightInCombat",
    "AurasCostsTest.AuraKeywordHelper_AssaultCountedOnce",
    "AurasCostsTest.AuraKeywordHelper_ShieldCountedOnce",
    "ExecutorReviewFixTest.Predict_RecyclingFiresWhenYouRecycle",
    "ExecutorReviewFixTest.Predict_KeepingEveryCardRecyclesNothing",
)
DISABLED = "CardTestFixture.DISABLED_BaronNashor_AuraGivesFriendlyUnitsPlus2M"

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def xml_cases(raw):
    require(sha(raw) == XML_SHA, "historical XML hash mismatch")
    cases = {}
    for t in ET.fromstring(raw).iter("testcase"):
        name = t.attrib["classname"] + "." + t.attrib["name"]
        require(name not in cases, "duplicate XML case: " + name)
        if t.get("status") == "run" and t.get("result") == "completed" and not any(t.find(k) is not None for k in ("failure", "error", "skipped")):
            cases[name] = "pass"
        elif t.get("status") == "notrun" and t.get("result") == "suppressed":
            cases[name] = "disabled"
        else:
            cases[name] = "other"
    require(len(cases) == 3933 and list(cases.values()).count("pass") == 3932
            and cases.get(DISABLED) == "disabled", "unexpected historical outcome counts")
    return cases

def declarations(raw):
    pairs = re.findall(rb"(?m)^TEST_F\(\s*(\w+)\s*,\s*(\w+)\s*\)", raw)
    names = [a.decode() + "." + b.decode() for a, b in pairs]
    require(len(names) == len(set(names)) and bool(names), "invalid declarations")
    return set(names)

def baron_body(raw, name):
    # These exact pinned fixtures have a top-level closing brace in column zero.
    # Reject duplicate or missing matches, rather than accepting a prefix.
    pattern = rb"(?ms)^TEST_F\(RadianceFinal64Test,\s*" + name.encode() + rb"\)\s*\{.*?^\}[ \t]*$"
    matches = re.findall(pattern, raw)
    require(len(matches) == 1, "missing/duplicate Baron body: " + name)
    return matches[0]

def check_exact(raw, expected, label):
    require(blob(raw) == expected, "blob mismatch: " + label)
    return {"git_blob": blob(raw), "sha256": sha(raw)}

def audit(source, engine, xml):
    cases = xml_cases(xml)
    files = {}
    checked = set()
    for path, expected in UPSTREAM.items():
        files[path] = check_exact((engine / path).read_bytes(), expected, path)
    for suffix, expected in REVIEWED.items():
        path = "tests/cards/test_radiance_" + suffix + ".cpp"
        raw = (source / path).read_bytes()
        generated = (engine / path).read_bytes()
        files[path] = check_exact(raw, expected, path)
        require(raw == generated, "generated source changed: " + path)
        names = declarations(raw)
        suites = {n.split(".")[0] for n in names}
        actual = {n for n in cases if n.split(".")[0] in suites}
        require(names == actual, "XML suite declaration mismatch: " + path)
        require(all(cases[n] == "pass" for n in names), "reviewed test did not pass")
        files[path]["tests"] = sorted(names)
        checked.update(names)
    path = "tests/cards/test_radiance_final64.cpp"
    raw = (source / path).read_bytes()
    generated = (engine / path).read_bytes()
    files[path] = check_exact(raw, FINAL64_SHA, path)
    files[path]["generated_sha256"] = sha(generated)
    bodies = {}
    for name in BARON:
        body = baron_body(raw, name)
        require(body == baron_body(generated, name), "generated Baron body changed: " + name)
        full = "RadianceFinal64Test." + name
        require(cases.get(full) == "pass", "Baron evidence absent: " + full)
        bodies[full] = sha(body)
        checked.add(full)
    for name in SHARED:
        require(cases.get(name) == "pass", "shared evidence absent: " + name)
        checked.add(name)
    return {"status": "PASS_SOURCE_PROVENANCE_ONLY", "historical_xml_sha256": sha(xml),
            "files": files, "baron_body_sha256": bodies, "shared_tests": list(SHARED),
            "historical_pass_count": len(checked), "disabled_placeholder": DISABLED,
            "fresh_native_execution": False, "all_interactions_verified": False}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for k in ("source", "engine", "xml", "output"):
        p.add_argument("--" + k, type=Path, required=True)
    a = p.parse_args()
    result = audit(a.source, a.engine, a.xml.read_bytes())
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n")

if __name__ == "__main__":
    main()
