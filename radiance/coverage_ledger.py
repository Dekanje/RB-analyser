#!/usr/bin/env python3
"""Evidence-led Radiance coverage ledger. Never equate registration with correctness."""
import argparse
import json
from pathlib import Path

WAVE1 = {
    "RAD-077/167": ["WrathAlwaysEntersReadyAndHasShieldThree"],
    "RAD-088/167": ["StaunchSurvivorHasPrintedAssaultAndShieldTwo"],
    "RAD-059/167": ["SupernovaDealsTenToChosenUnitAndDrawsTwo"],
    "RAD-079/167": ["AvalancheHitsBothBasesButNotBattlefields"],
    "RAD-099/167": ["SuaveNegotiatorDrawsOneForEachPlayer"],
    "RAD-004/167": ["BrawlIsRegisteredAsChaosActionWithPrintedCost","BrawlGrantsAssaultEqualToChosenUnitMight","BrawlCanTargetEnemyUnit"],
    "RAD-008/167": ["WarScoutPrintedIdentityAndAccelerate","WarScoutBuffsChosenFriendlyUnitViaTriggeredChoice","WarScoutCanBuffEnemyUnitViaTriggeredChoice"],
    "RAD-049/167": ["PrintedCostDomainAndIdentity","IndustriousMechsmithCreatesThreeMightMechInBase","IndustriousMechsmithCreatesTokenAtSameBattlefield"],
    "RAD-003/167": ["PrintedCostDomainAndIdentity","BilgewaterTrackerCanDeclineEveryOptionalTarget","BilgewaterTrackerChoosesTwoUnitsAndNotThird","BilgewaterTrackerDamageIsLethalForOneMightUnits"],
    "RAD-009/167": ["NewCardsHaveExactPrintedIdentities","ApparatusAndItsMechEnterReadyInBase","ApparatusPlaysMechAtSameBattlefield"],
    "RAD-119/167": ["NewCardsHaveExactPrintedIdentities","HuntingDogDoesNotCreateBirdJustByBeingPlayed","HuntingDogDeathCreatesDeflectBirdInControllerBase"],
    "RAD-083/167": ["NewCardsHaveExactPrintedIdentities","GoatherdMayDeclineKillingAnyGear","GoatherdCanKillChosenAffordableGear","GoatherdDoesNothingWithoutLegalGearTarget"],
    "RAD-058/167": ["NineNewIdentitiesAndPreexistingOfferAreCorrect","RiptideMageDebuffsAnEnemyOnRealPlay"],
    "RAD-048/167": ["NineNewIdentitiesAndPreexistingOfferAreCorrect","HighNoteCountsOnlyFriendlyExhaustedUnits"],
    "RAD-071/167": ["NineNewIdentitiesAndPreexistingOfferAreCorrect","NazumanNtofoHasEnergyOnlyEquipCostAndShieldTwo"],
    "RAD-072/167": ["NineNewIdentitiesAndPreexistingOfferAreCorrect","OverloadedTravelerNeedsFriendlyDeployGearAtSameBattlefield"],
    "RAD-122/167": ["NineNewIdentitiesAndPreexistingOfferAreCorrect","PartyCrasherDiscountCountsOnlyExhaustedFriendlyUnits"],
    "RAD-128/167": ["NineNewIdentitiesAndPreexistingOfferAreCorrect","SteadfastOutriderRequiresTwoOtherAlliesAtSameBattlefield"],
    "RAD-037/167": ["NineNewIdentitiesAndPreexistingOfferAreCorrect","WatchfulCuratorGrantsDeflectOnlyToFriendlyGear"],
    "RAD-076/167": ["NineNewIdentitiesAndPreexistingOfferAreCorrect","SneakyZeeblesConquerAbilityAddsUnreactableUniversalPower"],
    "RAD-117/167": ["NineNewIdentitiesAndPreexistingOfferAreCorrect","ForDemaciaGrantsShieldAtChosenBattlefieldOnly"],
    "RAD-101/167": ["NineNewIdentitiesAndPreexistingOfferAreCorrect","AnOfferKillsChosenGearAndCreatesExhaustedGold"],
}
# Evidence gaps must remain explicit until deterministic gameplay interactions pass.
KNOWN_GAPS = {
    "RAD-077/167": ["Shield damage mitigation not exercised by dedicated test"],
    "RAD-088/167": ["Assault and Shield not exercised in engine combat; current test only checks printed values"],
    "RAD-059/167": ["Illegal-target and countered-spell scenarios not yet covered"],
    "RAD-079/167": ["Shield and replacement-effect interactions not yet covered"],
    "RAD-099/167": ["Trigger suppression, empty-deck and counter-interaction cases not yet covered"],
    "RAD-004/167": ["Assault expires at end of turn, actual attacker-only combat calculation, counter and illegal target cases not yet covered"],
    "RAD-008/167": ["Accelerate payment/ready-state, Might expiration, counter and invalid-target cases not yet covered"],
    "RAD-049/167": ["Source leaves board before triggered effect resolves; token replacement effects and token interactions not yet exercised"],
    "RAD-003/167": ["Deflect, mistargeted unit, damaged-before-trigger and death-replacement interactions not yet tested"],
    "RAD-009/167": ["Ready-state replacement effects, kill-source-before-trigger-resolution, and Mech interactions not yet tested"],
    "RAD-119/167": ["Death replacement, countered Deathknell, and Bird Deflect payment not yet tested"],
    "RAD-083/167": ["Shield 2 combat calculation, enemy Deflect costs, and gear death-replacement not yet tested"],
    "RAD-058/167": ["Accelerate payment and invalid/Deflect target interactions not yet tested"],
    "RAD-048/167": ["Reactive priority, zero exhausted count, invalid target, and Might expiration not yet tested"],
    "RAD-071/167": ["Actual paid Equip/attachment, Shield defender combat and death/re-equipping not yet tested"],
    "RAD-072/167": ["Deploy gear replacement, enemy gear condition and moving the source not yet covered"],
    "RAD-122/167": ["Real played-energy cost after discounts, Tank combat, and cost/payment interactions not yet covered"],
    "RAD-128/167": ["Friendly gear counted at battlefield, movement, Tank combat and replacement not yet tested"],
    "RAD-037/167": ["Deflect payment, preexisting Deflect stacking and counter-interactions not yet tested"],
    "RAD-076/167": ["Real conquer/point-resolution integration and resource timing not yet exercised"],
    "RAD-117/167": ["Shield defender combat bonus, duration, alternate battlefield and counter/reaction timing not yet tested"],
    "RAD-101/167": ["Opponent-owned gear and replacement/death-trigger/Deflect interaction not yet tested"],
}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("registry",type=Path)
    ap.add_argument("--catalog",type=Path,default=Path("radiance/data/radiance_catalog.json"))
    ap.add_argument("--output",type=Path,default=Path("results/radiance_coverage_ledger.json"))
    a=ap.parse_args()
    registry=json.loads(a.registry.read_text())["cards"]
    catalog=json.loads(a.catalog.read_text())["cards"]
    compiled={c["public_code"]:c for c in registry if c.get("public_code")}
    base={f"RAD-{i:03d}/167" for i in range(1,168)}
    records=[]
    for c in catalog:
        code=c["public_code"]
        row=compiled.get(code)
        tests=WAVE1.get(code,[])
        gaps=KNOWN_GAPS.get(code,[])
        if not row:
            status="not implemented"
        elif gaps:
            status="tests passing but known gap" if tests else "implementation pending tests"
        else:
            status="verified mechanics" if tests else "implementation pending tests"
        records.append({
            "code":code,"gallery_id":c["gallery_id"],"name":c["display_name"],
            "base_number":c.get("base_number"),"is_base_identity":code in base,
            "rules_text_sha256":c.get("rules_text_sha256"),
            "compiled":bool(row),"engine_id":row.get("card_id") if row else None,
            "status":status,"deterministic_test_names":tests,"known_gaps":gaps,
            "source_metadata_caveat":("Gallery domain for RAD-059 is incorrect: printed Mind" if code=="RAD-059/167" else None)
        })
    # Some alternate printings have no distinct mechanics: keep them separate
    # pending a verified print-to-rules fingerprint equivalence audit.
    statuses={s:sum(x["status"]==s for x in records) for s in
              ("not implemented","implementation pending tests","tests passing but known gap","verified mechanics")}
    output={
        "schema_version":1,"compiled_registry_count":len(registry),
        "catalog_printings":len(records),"base_identities":len(base),
        "compiled_base_identities":sum(x["compiled"] and x["is_base_identity"] for x in records),
        "statuses":statuses,"variant_equivalence_verified":False,
        "full_set_verified":False,"records":records
    }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(output,indent=2),encoding="utf8")
    print("RADIANCE_EVIDENCE_LEDGER",json.dumps({k:v for k,v in output.items() if k!="records"}))

if __name__=="__main__":main()
