"""Preserve exact accepted configuration receipts and probe host availability, read-only."""
import argparse,json,os,shutil,subprocess,zipfile
from pathlib import Path
from p0_09_package_preflight import plan,host_report,LOCK_SHA,apt_command
from p0_09_toolchain import require,sha

PINS={
    14955535283:("83d0d56c68e4ee8a40fac99b9fc4befb686167ba302c5981c99c185871dbfe05","toolchain_lock.json",LOCK_SHA),
    14954388764:("3f69177e11ec43b8bfbc16dc7e7d315e6ddb755ead6e0a7089b34e7145463441","package_plan.json","dbbe7374c0f6862e6ad7d4a826ae91876d9bf727ce0d30bb21006a645a06e6f0")}
def verify_files(lock_raw,plan_raw):
    require(sha(plan_raw)==PINS[14954388764][2],"package plan hash mismatch")
    lock,expected=plan(lock_raw)
    require(json.loads(plan_raw)==expected,"package plan differs from regenerated plan")
    return lock,expected
def preserve(archives,dest):
    raw={}
    for i,(archive_sha,name,file_sha) in PINS.items():
        p=archives/f"{i}.zip"
        require(sha(p.read_bytes())==archive_sha,"archive drift")
        with zipfile.ZipFile(p) as z:
            require(z.namelist()==[name],"unexpected archive member")
            b=z.read(name)
        require(sha(b)==file_sha,"file drift")
        raw[name]=b
    verify_files(raw["toolchain_lock.json"],raw["package_plan.json"])
    require(not dest.exists(),"destination exists")
    dest.mkdir(parents=True)
    for name,b in raw.items():
        with (dest/name).open("xb") as f:f.write(b)
def execute(args,timeout=60):
    env={**os.environ,"LC_ALL":"C"}
    try:
        p=subprocess.run(args,capture_output=True,text=True,env=env,timeout=timeout)
        return p.returncode,p.stdout,p.stderr
    except subprocess.TimeoutExpired:return 124,"","timeout"
def madison_versions(text):
    out=set()
    for line in text.splitlines():
        parts=line.split("|")
        if len(parts)==3 and parts[2].strip() and parts[1].strip():
            out.add(parts[1].strip())
    return out
def probe(lock,selected):
    host=host_report(lock,selected)
    results={}
    for name,version in sorted(selected.items()):
        rc,out,err=execute(["apt-cache","madison",name],15)
        versions=madison_versions(out)
        results[name]={"expected":version,"apt_cache_exit":rc,"listed_versions":sorted(versions),
                       "exact_version_listed":rc==0 and version in versions}
    rc,out,err=execute(apt_command(selected),180)
    tools={}
    for name in ("gcc-13","g++-13","cmake","ninja","git","python3"):
        path=shutil.which(name)
        if path:
            actual=Path(path).resolve()
            dr,owner,_=execute(["dpkg-query","-S",str(actual)],15)
            tools[name]={"resolved_path":str(actual),"sha256":sha(actual.read_bytes()),
                         "dpkg_owner":owner.strip() if dr==0 else None}
        else:tools[name]={"resolved_path":None,"sha256":None,"dpkg_owner":None}
    return {"status":"HOST_AVAILABILITY_OBSERVATION_ONLY","host":host,"tools_observed_now":tools,
            "selected_package_count":len(selected),"exact_versions_listed_count":sum(x["exact_version_listed"] for x in results.values()),
            "packages":results,"apt_simulation_exit":rc,"apt_simulation_passed":rc==0,
            "apt_simulation_stdout_sha256":sha(out.encode()),"apt_simulation_stderr_sha256":sha(err.encode()),
            "apt_simulation_diagnostics":err[-4000:],"apt_simulation_install_actions":sum(s.startswith("Inst ") for s in out.splitlines()),
            "apt_simulation_remove_actions":sum(s.startswith("Remv ") for s in out.splitlines()),
            "historical_tool_binary_hashes_known":False,"package_downloads_verified":False,
            "physical_user_pc_verified":False,"native_build_certified":False,"production_authorized":False}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archives",type=Path);p.add_argument("--directory",type=Path,required=True)
    p.add_argument("--probe-output",type=Path);a=p.parse_args()
    if a.archives:preserve(a.archives,a.directory)
    lock,expected=verify_files((a.directory/"toolchain_lock.json").read_bytes(),(a.directory/"package_plan.json").read_bytes())
    if a.probe_output:
        report=probe(lock,expected["selected_packages"])
        a.probe_output.parent.mkdir(parents=True,exist_ok=True)
        with a.probe_output.open("x") as f:json.dump(report,f,indent=2,sort_keys=True);f.write("\n")
        print(report["status"],report["exact_versions_listed_count"],report["apt_simulation_exit"])
    else:print("PASS_DURABLE_LOCK_BYTES",len(lock["packages"]),len(expected["selected_packages"]))
if __name__=="__main__":main()
