#!/usr/bin/env python3
"""Promote Disarm from immediate prompt to a reactable, stackable keyword trigger.

In AlphaRune a keyword ability is a Card supplied by keywordAbilityCard;
the actual attack event queues it on the chain. Choices/Deflect are paid at
finalization, the debuff is dealt at resolution, with normal priority.
"""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
engine=root/"alpharune"
tm=engine/"src/engine/trigger_manager.cpp"
s=tm.read_text()
start=s.index("    // Radiance Disarm (2026-10-16): stack printed and aura-granted values.")
end=s.index("    if (is_attacker &&\n        cardFiresOn(card_registry_",start)
assert end>start, "Could not identify old immediate-disarm block"
s=s[:start]+"""    // Radiance Disarm: one reactable triggered keyword ability per attacker
    // per combat. Printed and aura-granted magnitudes stack into ONE trigger.
    if (is_attacker)
        queueKeywordAbilities(id, obj.controller, Keyword::Disarm, false);

"""+s[end:]
old="            item.keyword_ability = keyword;\n            stampBatch(state_.chain, item);"
new="""            item.keyword_ability = keyword;
            // Snapshot the stacked Disarm value as the attack triggers.
            // A response that removes an aura or kills its source must not
            // retroactively change the amount of this pending trigger.
            if (keyword == Keyword::Disarm) {
                const auto& src = state_.getObject(object);
                int strength = 0;
                if (src.keywords.has(Keyword::Disarm)) {
                    strength = 1;
                    if (src.card_def_id != kInvalidId) {
                        if (const Card* def = card_registry_.get(src.card_def_id))
                            if (def->def().ability_text.find("[Disarm 2]") !=
                                std::string::npos)
                                strength = 2;
                    }
                }
                for (const auto& aura : src.aura_effects)
                    if (aura.keyword == Keyword::Disarm)
                        strength += std::max(1, aura.keyword_value);
                item.triggering_spell_energy_spent = strength;
            }
            stampBatch(state_.chain, item);"""
assert s.count(old)==1, "Keyword queue's ChainItem hook changed"
s=s.replace(old,new,1)
tm.write_text(s)

keyword=engine/"src/engine/keyword_abilities.cpp"
s=keyword.read_text()
anchor="/// [Temporary] — CR 816.1.b:"
disarm=r'''/// [Disarm] — 2026-10-16 Radiance Core Rules update:
/// stacks like Shield/Assault but triggers only ONCE with the combined value.
/// The player chooses an enemy unit at the attacker's battlefield when this
/// ability is finalized (Deflect included), and it resolves on the chain.
class DisarmAbility : public Card {
public:
    const CardDef& def() const override { return def_; }
    TriggerType triggerType() const override { return TriggerType::WhenIAttack; }
    unsigned choicesAtFinalization() const override { return kFinalizeTrigger; }
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&) override {
        if (!ctx.state.objectExists(ctx.source)) return;
        const auto& attacker=ctx.state.getObject(ctx.source);
        auto here=attacker.battlefieldId();
        if (!here && attacker.last_location)
            if (auto* was=std::get_if<BattlefieldLocation>(&*attacker.last_location))
                here=was->id;
        if (!here) return;
        const auto enemies=chooseableUnits(ctx.state,ctx.controller,
            [&](const GameObject& u){
                return u.isUnit() && u.isAtBattlefield() &&
                       u.controller!=ctx.controller && u.battlefieldId()==here;
            });
        const auto picked=pickTarget(ctx,"Disarm: choose an enemy unit here",enemies);
        if (finalizingChoices(ctx)) return;
        if (picked==kInvalidId || !ctx.state.chain.resuming.has_value())return;
        const int value=ctx.state.chain.resuming->triggering_spell_energy_spent;
        if (value>0)ctx.executor.giveTemporaryMight(picked,-value);
    }
private:
    const CardDef def_=keywordDef("Disarm");
};

'''
assert s.count(anchor)==1
s=s.replace(anchor,disarm+anchor,1)
old="    static QuickDrawAbility quick_draw;"
assert s.count(old)==1
s=s.replace(old,old+"\n    static DisarmAbility disarm;",1)
old="        case Keyword::QuickDraw:    return &quick_draw;"
assert s.count(old)==1
s=s.replace(old,old+"\n        case Keyword::Disarm:       return &disarm;",1)
old="    if (keyword == Keyword::QuickDraw) n = std::min(n, 1);"
assert s.count(old)==1
s=s.replace(old,old+"\n    if (keyword == Keyword::Disarm) n = std::min(n, 1);",1)
keyword.write_text(s)
print("BATCH9_DISARM_CHAIN_APPLIED: reactable keyword trigger, locked choice/Deflect, stacked magnitude")
