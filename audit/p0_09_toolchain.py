"""P0-09 native build configuration lock, no compilation in this module."""
import argparse
import hashlib
import json
import platform
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN = json.loads((ROOT / "audit/p0_09_source_pins.json").read_text())

def require(ok, message):
    if not ok:
        raise ValueError(message)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def run(*cmd, cwd=ROOT):
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()

def cache_values(raw):
    values = {}
    for line in raw.splitlines():
        m = re.fullmatch(r"([^#/:][^:]*):[^=]+=(.*)", line)
        if m:
            require(m[1] not in values, "duplicate cache key: " + m[1])
            values[m[1]] = m[2]
    return values

def verify_cache(v, jobs):
    expected = {"CMAKE_BUILD_TYPE": "Release", "CMAKE_GENERATOR": "Ninja",
                "RIFTBOUND_BUILD_JOBS": str(jobs), "RIFTBOUND_BUILD_OPENSPIEL": "ON",
                "RIFTBOUND_BUILD_LIBTORCH": "OFF", "RIFTBOUND_USE_PCH": "ON",
                "RIFTBOUND_UNITY_CARDS": "ON", "RIFTBOUND_CARD_UNITY_BATCH": "16",
                "RIFTBOUND_OPT_LEVEL": "", "RIFTBOUND_CHECK_BOARD_INDEX": "OFF"}
    for k, val in expected.items():
        require(v.get(k) == val, "configuration mismatch: " + k)
    require(not v.get("CMAKE_CXX_COMPILER_LAUNCHER"), "compiler cache forbidden for clean build")
    require(v.get("CMAKE_CXX_COMPILER", "").endswith("/g++-13"), "unexpected compiler path")
    require("-O3" in v.get("CMAKE_CXX_FLAGS_RELEASE", "").split(), "missing Release optimization")
    require(not v.get("CMAKE_CXX_FLAGS"), "unexpected extra CXX flags")
    return {**expected, "CMAKE_CXX_FLAGS_RELEASE": v["CMAKE_CXX_FLAGS_RELEASE"]}

def verify_lock(expected, actual):
    require(expected == actual, "toolchain lock drift; inspect differences before rebuilding")

def packages(raw):
    result = {}
    # Capture the build toolchain and native runtime packages rather than the
    # entire GitHub image. Transitive dependencies outside this scope remain open.
    pat = re.compile(r"^(?:gcc(?:-|$)|g\+\+(?:-|$)|cpp(?:-|$)|libgcc|libstdc\+\+|libc6|libc-bin|libboost|libgomp|libatomic|libasan|libubsan|binutils|cmake|ninja-build|git(?:-|$)|python3(?:[.-]|$)|nlohmann-json|linux-libc-dev|libc-dev-bin|libmpc|libmpfr|libgmp|libzstd|zlib1g)")
    for line in raw.splitlines():
        name, version, status = line.split("\t")
        if status == "installed" and pat.match(name):
            require(name not in result, "duplicate package: " + name)
            result[name] = version
    require(any(k.startswith("libboost-context1.83") for k in result), "Boost.Context missing")
    require("g++-13" in result, "GCC 13 missing")
    return result

def capture(jobs):
    e = ROOT / "alpharune"
    b = e / "build"
    require(run("git", "rev-parse", "HEAD", cwd=e) == PIN["upstream"], "wrong upstream")
    # Check tracked candidate engine input files and all overlay script bytes
    # against the exact historical candidate commit, before trusting the lock.
    paths = ["radiance/engine_overlay", "rulesets/standard-global-2026-11-23.json"]
    require(not run("git", "diff", PIN["candidate"], "--", *paths), "candidate source drift")
    require(not run("git", "ls-files", "--others", "--exclude-standard", "--", *paths), "untracked candidate input")
    deps = {}
    for path, expected in PIN["dependency_git"].items():
        d = b / "_deps" / path
        actual = run("git", "rev-parse", "HEAD", cwd=d)
        require(actual == expected, "dependency revision mismatch: " + path)
        # Nested dependency clones may be untracked in OpenSpiel; tracked
        # edits are never permitted.
        require(not run("git", "status", "--porcelain", "--untracked-files=no", cwd=d),
                "tracked dependency changes: " + path)
        deps[path] = actual
    flags = verify_cache(cache_values((b / "CMakeCache.txt").read_text()), jobs)
    compiler = run("g++-13", "-dumpfullversion")
    require(compiler == PIN["compiler_version"], "GCC version mismatch")
    pkg = packages(run("dpkg-query", "-W", "-f=${binary:Package}\t${Version}\t${db:Status-Status}\n"))
    overlay = {p: sha((ROOT / p).read_bytes()) for p in PIN["overlays"]}
    # Hash generated tracked + nonignored untracked source file bytes. Build
    # directory is explicitly excluded, even if upstream ignores change.
    files = sorted(set(run("git", "ls-files", "--cached", "--others", "--exclude-standard", cwd=e).splitlines()))
    source = {}
    for p in files:
        if p.startswith("build/"):
            continue
        f = e / p
        if f.is_file() and not f.is_symlink():
            source[p] = sha(f.read_bytes())
    require(len(source) > 1000, "unexpectedly small generated source tree")
    lock = {"schema": 1, "candidate": PIN["candidate"], "upstream": PIN["upstream"],
            "machine_arch": platform.machine(), "os_release": Path("/etc/os-release").read_text(),
            "compiler": compiler, "cmake": run("cmake", "--version").splitlines()[0],
            "ninja": run("ninja", "--version"), "git": run("git", "--version"),
            "python": platform.python_version(), "packages": pkg, "dependencies": deps,
            "flags": flags, "overlays": overlay,
            "generated_source_count": len(source),
            "generated_source_sha256": sha(json.dumps(source, sort_keys=True).encode())}
    require(lock["machine_arch"] == "x86_64", "only x86_64 baseline supported")
    return lock

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--jobs", required=True, type=int)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--expected-lock", type=Path)
    a = p.parse_args()
    lock = capture(a.jobs)
    if a.expected_lock:
        verify_lock(json.loads(a.expected_lock.read_text()), lock)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open("x") as f:
        json.dump(lock, f, indent=2, sort_keys=True)
        f.write("\n")
    print("PASS_CONFIGURATION_LOCK", lock["generated_source_count"])

if __name__ == "__main__":
    main()
