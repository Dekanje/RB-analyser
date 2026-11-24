#!/usr/bin/env python3
"""New guarded native match entry point; no implicit format selection."""
import argparse
import json
from pathlib import Path
from format_match_v2 import VerifiedGateway

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("engine","registry","profile","deck1","deck2","output"):
        p.add_argument("--"+n,type=Path,required=True)
    p.add_argument("--sets",nargs="+",required=True)
    p.add_argument("--rune-exempt-id",action="append",type=int,default=[])
    p.add_argument("--mode",choices=("single","declared-bo3"),required=True)
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--agent",default="ismcts:sims=24")
    p.add_argument("--timeout",type=float,default=180)
    p.add_argument("--policy",type=Path)
    a=p.parse_args()
    if a.mode=="single" and a.policy is not None:
        p.error("single game does not accept a sideboard policy")
    if a.mode=="declared-bo3" and a.policy is None:
        p.error("declared BO3 requires an explicit policy ({} is allowed)")
    if a.seed<=0 or a.timeout<=0:
        p.error("positive seed and timeout required")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    # Never overwrite an earlier experiment; fail before starting execution.
    with a.output.open("x",encoding="utf-8") as fp:
        try:
            g=VerifiedGateway(a.engine,a.registry,a.profile,a.sets,a.rune_exempt_id)
            if a.mode=="single":
                result=g.game(a.deck1.read_bytes(),a.deck2.read_bytes(),a.seed,a.agent,a.timeout)
            else:
                result=g.declared_bo3(a.deck1,a.deck2,json.loads(a.policy.read_bytes()),
                                     a.seed,a.agent,a.timeout)
        except Exception as exc:
            json.dump({"status":"error","winner":None,"error":str(exc)},fp,indent=2)
            raise
        json.dump(result,fp,indent=2)
    print(result["status"])

if __name__=="__main__":
    main()
