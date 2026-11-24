#!/usr/bin/env bash
# Run only from a dedicated clean checkout of the P0-09 candidate branch.
set -euo pipefail
cd "$(dirname "$0")/.."
jobs="${RB_BUILD_JOBS:-3}"
[[ "$jobs" =~ ^[1-9][0-9]*$ ]] || { echo "Invalid RB_BUILD_JOBS" >&2; exit 2; }
case "${1:-}" in
  configure)
    [[ ! -e alpharune && ! -e results/p0_09 ]] || { echo "Use a fresh dedicated checkout; existing files are not deleted." >&2; exit 2; }
    git diff --exit-code e1123124e0d20164a3a063d73363d200c59cb5fb -- radiance/engine_overlay rulesets/standard-global-2026-11-23.json
    git clone --quiet https://github.com/chorlick/alpharune.git alpharune
    git -C alpharune checkout --quiet --detach ec90f0fed002aed374d06249fa95e83e3cfbd386
    python3 radiance/engine_overlay/apply.py
    python3 radiance/engine_overlay/wave1_regression_fix.py
    python3 radiance/engine_overlay/apply_wave2.py
    python3 radiance/engine_overlay/apply_wave3.py
    python3 radiance/engine_overlay/apply_wave4.py
    python3 radiance/engine_overlay/apply_batch6.py
    python3 radiance/engine_overlay/apply_batch7.py
    python3 radiance/engine_overlay/apply_batch8.py
    python3 radiance/engine_overlay/apply_batch9.py
    python3 radiance/engine_overlay/apply_batch9_battlefields.py
    python3 radiance/engine_overlay/apply_batch9_disarm_chain.py
    python3 radiance/engine_overlay/apply_batch10.py
    python3 radiance/engine_overlay/apply_final64.py
    python3 radiance/engine_overlay/stability_patch.py
    python3 radiance/engine_overlay/fullfield_repair.py
    python3 radiance/engine_overlay/tournament_starting_player.py
    python3 radiance/engine_overlay/apply_elnuk_errata.py
    python3 radiance/engine_overlay/apply_elnuk_interaction_tests.py
    python3 radiance/engine_overlay/apply_neeko_errata.py
    python3 radiance/engine_overlay/apply_neeko_receipt.py
    python3 radiance/engine_overlay/apply_neeko_privacy.py
    python3 radiance/engine_overlay/apply_neeko_controlled_agent_tests.py
    python3 radiance/engine_overlay/apply_format_aware_prior.py
    cmake -S alpharune -B alpharune/build -G Ninja \
      -DCMAKE_CXX_COMPILER=/usr/bin/g++-13 -DCMAKE_C_COMPILER=/usr/bin/gcc-13 \
      -DCMAKE_BUILD_TYPE=Release -DRIFTBOUND_BUILD_JOBS="$jobs" \
      -DRIFTBOUND_BUILD_LIBTORCH=OFF -DRIFTBOUND_USE_PCH=ON -DRIFTBOUND_UNITY_CARDS=ON \
      -DRIFTBOUND_CARD_UNITY_BATCH=16 -DRIFTBOUND_CHECK_BOARD_INDEX=OFF -DRIFTBOUND_OPT_LEVEL=
    args=(--jobs "$jobs" --output results/p0_09/toolchain_lock.json)
    if [[ -n "${RB_EXPECTED_LOCK:-}" ]]; then args+=(--expected-lock "$RB_EXPECTED_LOCK"); fi
    python3 audit/p0_09_toolchain.py "${args[@]}"
    ;;
  build)
    [[ -f results/p0_09/toolchain_lock.json && ! -e engine_build && ! -e results/p0_09/prebuild_lock.json ]] || { echo "Missing configure receipt or build already attempted" >&2; exit 2; }
    python3 audit/p0_09_toolchain.py --jobs "$jobs" --expected-lock results/p0_09/toolchain_lock.json --output results/p0_09/prebuild_lock.json
    cmake --build alpharune/build --target riftbound riftbound_tests riftbound_openspiel_tests -j "$jobs"
    mkdir engine_build
    cp alpharune/build/riftbound engine_build/riftbound
    ldd engine_build/riftbound | tee results/p0_09/ldd.txt
    if grep -q 'not found' results/p0_09/ldd.txt; then exit 1; fi
    engine_build/riftbound --dump-registry engine_build/registry.json
    echo '0d6165c2ce08b3d60e423a9216150dc15c9527656f9358a6e119d94c6c189e0a  engine_build/registry.json' | sha256sum -c -
    RIFTBOUND_ROOT="$PWD/alpharune" alpharune/build/riftbound_tests --gtest_brief=1 --gtest_output=xml:results/p0_09/all_tests.xml
    python3 radiance/verify_final64_registry.py engine_build/registry.json --mechanics-xml results/p0_09/all_tests.xml
    sha256sum engine_build/riftbound engine_build/registry.json > results/p0_09/build_sha256.txt
    ;;
  *) echo "Usage: bash audit/p0_09_local.sh configure|build" >&2; exit 2;;
esac
