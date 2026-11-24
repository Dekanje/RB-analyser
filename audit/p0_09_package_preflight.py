"""Read-only P0-09 configuration receipt verification and Linux host preflight."""
import argparse
import json
import platform
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from p0_09_toolchain import ROOT, PIN, require, sha, verify_cache

LOCK_SHA = "b89f0fbb35b5b67a787959a89f613a8d2b01c6a59db40e2eafc94c86cac8ea4a"
SOURCE_SHA = "134d50f17378a07565c12f53180cb4e52cce85096c97ffd8428ecbce1412f8fc"
CORE = frozenset(("gcc-13", "g++-13", "gcc-13-x86-64-linux-gnu",
    "g++-13-x86-64-linux-gnu", "cpp-13", "cpp-13-x86-64-linux-gnu",
    "gcc-13-base", "libgcc-13-dev", "libstdc++-13-dev", "libstdc++6",
    "libgcc-s1", "libc6", "libc6-dev", "libc-bin", "libc-dev-bin",
    "binutils", "binutils-common", "binutils-x86-64-linux-gnu",
    "linux-libc-dev", "nlohmann-json3-dev", "cmake", "cmake-data",
    "ninja-build", "git", "git-man", "python3", "python3.12",
    "python3.12-minimal", "python3-minimal", "libgomp1", "libatomic1",
    "libmpc3", "libmpfr6", "libgmp10", "libzstd1", "zlib1g"))

def unique_pairs(pairs):
    out = {}
    for k,v in pairs:
        require(k not in out, "duplicate JSON key: " + k)
        out[k] = v
    return out

def read_lock(raw, root=ROOT):
    require(sha(raw)==LOCK_SHA, "wrong configuration receipt bytes")
    v=json.loads(raw, object_pairs_hook=unique_pairs)
    require(v["schema"]==1 and v["candidate"]==PIN["candidate"] and
            v["upstream"]==PIN["upstream"], "source identity mismatch")
    require(v["machine_arch"]=="x86_64" and 'VERSION_ID="24.04"' in v["os_release"],
            "unexpected baseline OS")
    require(v["compiler"]==PIN["compiler_version"], "compiler mismatch")
    require(v["dependencies"]==PIN["dependency_git"], "dependency Git drift")
    expected={p:sha((root/p).read_bytes()) for p in PIN["overlays"]}
    require(v["overlays"]==expected, "overlay receipt or current bytes differ")
    require(v["generated_source_count"]==2643 and v["generated_source_sha256"]==SOURCE_SHA,
            "generated source receipt mismatch")
    # This is an independent check of recorded flags, not a configure replay.
    flags=v["flags"]
    require(verify_cache({**flags,"CMAKE_CXX_COMPILER":"/usr/bin/g++-13"},3)==flags,
            "recorded flags mismatch")
    require(len(v["packages"])==180, "package receipt count mismatch")
    require(v["cmake"]=="cmake version 3.31.6" and v["ninja"]=="1.13.2" and
            v["python"]=="3.12.3" and v["git"]=="git version 2.56.1",
            "executable version mismatch")
    return v

def package_subset(packages):
    out={k:v for k,v in packages.items()
         if k.split(":")[0] in CORE or k.startswith("libboost")}
    require(CORE <= {k.split(":")[0] for k in out}, "missing core package")
    require(any(k.startswith("libboost-context1.83.0:") for k in out), "missing Boost runtime")
    for name,version in out.items():
        require(re.fullmatch(r"[a-z0-9][a-z0-9+.-]*(?::[a-z0-9-]+)?",name) and
                re.fullmatch(r"[0-9][a-zA-Z0-9+.:~\-]*",version), "unsafe package spec")
    return dict(sorted(out.items()))

def mismatches(expected, actual):
    return {k:{"expected":v,"observed":actual.get(k)}
            for k,v in expected.items() if actual.get(k)!=v}

def apt_command(packages):
    # Only a simulation, never sudo/install. Caller may run it explicitly.
    return ["apt-get","-s","install","--no-install-recommends"]+[
        k+"="+v for k,v in sorted(packages.items())]

def host_report(lock, selected):
    os_release=Path("/etc/os-release").read_text()
    expected_tools={"g++-13":lock["compiler"],"cmake":lock["cmake"],
                    "ninja":lock["ninja"],"git":lock["git"],
                    "python3":lock["python"]}
    args={"g++-13":["-dumpfullversion"],"cmake":["--version"],
          "ninja":["--version"],"git":["--version"],"python3":["--version"]}
    observed={}
    for tool in expected_tools:
        path=shutil.which(tool)
        if not path:
            observed[tool]={"path":None,"version":None}
            continue
        p=subprocess.run([path,*args[tool]],text=True,capture_output=True,timeout=15)
        version=p.stdout.splitlines()[0] if p.returncode==0 and p.stdout else None
        if tool=="python3" and version:
            version=version.removeprefix("Python ")
        observed[tool]={"path":str(Path(path).resolve()),"version":version}
    p=subprocess.run(["dpkg-query","-W","-f=${binary:Package}\t${Version}\t${db:Status-Status}\n"],
                     check=True,text=True,capture_output=True,timeout=30)
    installed={}
    for line in p.stdout.splitlines():
        name,version,status=line.split("\t")
        if status=="installed":
            installed[name]=version
    # APT/dpkg sometimes omits the :amd64 suffix for a non-multiarch package.
    # Only exact keys are accepted in this baseline comparison.
    package_diff=mismatches(selected,installed)
    tool_diff=mismatches(expected_tools,{k:v["version"] for k,v in observed.items()})
    full_package_diff=mismatches(lock["packages"],installed)
    arch_ok=platform.machine()==lock["machine_arch"]
    os_ok=os_release==lock["os_release"]
    return {"os_exact_match":os_ok,"architecture_match":arch_ok,
            "tools":observed,"tool_mismatches":tool_diff,
            "selected_package_mismatches":package_diff,
            "recorded_package_mismatches":full_package_diff,
            "selected_host_match":os_ok and arch_ok and not package_diff and not tool_diff,
            "full_configuration_certified":False}

def plan(raw, root=ROOT):
    lock=read_lock(raw,root)
    selected=package_subset(lock["packages"])
    return lock, {"status":"PASS_CONFIGURATION_RECEIPT_ONLY",
                  "reference_lock_sha256":sha(raw),"reference_run":45464883262,
                  "reference_artifact":14955535283,
                  "overlay_count":len(lock["overlays"]),"dependency_count":len(lock["dependencies"]),
                  "generated_source_count":lock["generated_source_count"],
                  "recorded_package_count":len(lock["packages"]),
                  "selected_package_count":len(selected),"selected_packages":selected,
                  "apt_simulation_argv":apt_command(selected),
                  "apt_simulation_shell":shlex.join(apt_command(selected)),
                  "actual_tool_versions":{k:lock[k] for k in ("compiler","cmake","ninja","git","python")},
                  "apt_versions_not_executable_versions":["cmake","ninja-build"],
                  "package_availability_verified":False,"native_build_certified":False,
                  "full_configuration_certified":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--lock",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--check-host",action="store_true")
    a=p.parse_args()
    lock,report=plan(a.lock.read_bytes())
    if a.check_host:
        report["host"]=host_report(lock,report["selected_packages"])
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("x") as f:
        json.dump(report,f,indent=2,sort_keys=True)
        f.write("\n")
    print(report["status"],report["selected_package_count"])
    if a.check_host and (not report["host"]["selected_host_match"] or report["host"]["recorded_package_mismatches"]):
        raise SystemExit(2)

if __name__=="__main__":
    main()
