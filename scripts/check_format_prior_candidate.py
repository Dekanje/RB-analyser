"""Execute two public format configurations with native receipt and samples."""
import json,os,subprocess
from pathlib import Path
from format_prior_gateway import FormatPriorGateway,ENV
from format_match_v2 import digest
def main():
    root=Path("results");out=root/"rule407"
    decks=root/"controlled_decks"
    results=[]
    for label,sets in (("standard",("OGN","OGS","SFD","UNL","VEN","RAD")),
                       ("exclude_ogs",("OGN","SFD","UNL","VEN","RAD"))):
        g=FormatPriorGateway("engine_build/riftbound","engine_build/registry.json",
                            "rulesets/standard-global-2026-11-23.json",sets)
        env=os.environ.copy();env[ENV]=g.prior_text
        env["RB_NEEKO_CONTROLLED_DECKS"]=str(decks.resolve())
        env["RIFTBOUND_ROOT"]="alpharune"
        xml=out/(label+"_prior.xml")
        subprocess.run(["alpharune/build/src/openspiel/riftbound_openspiel_tests",
                        "--gtest_filter=NeekoFormatPriorTest.*:NeekoControlledAgentTest.*",
                        "--gtest_output=xml:"+str(xml)],check=True,env=env,timeout=180)
        games=[]
        for flip in (False,True):
            a,b=decks/"neeko_b.txt",decks/"observer.txt"
            if flip:a,b=b,a
            games.append(g.game(a.read_bytes(),b.read_bytes(),2026112450+int(flip)))
        results.append({"label":label,**g.provenance(),"prior_ids":list(map(int,g.prior_text.split(","))),
                        "xml_sha256":digest(xml.read_bytes()),"games":games})
    assert len(results[0]["prior_ids"])-len(results[1]["prior_ids"])==24
    assert set(results[0]["prior_ids"])-set(results[1]["prior_ids"])==set(range(299,323))
    (out/"format_prior.json").write_text(json.dumps({"formats":results,"adopted":0,"fitness_evaluated":False},indent=2))
if __name__=="__main__":main()
