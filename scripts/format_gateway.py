#!/usr/bin/env python3
"""Explicit format preflight for new native jobs; historical tools are unchanged."""
from collections import defaultdict, Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import tempfile
import os

from optimize_58 import benchmark, stable_seed

ENGINE_SHA = "e49c0e4d97a86805b9d911175b686c53ff348736ee4406c50941fa0d7e88db6a"
HEADINGS = ("Legend", "Champion", "MainDeck", "Battlefields", "Runes", "Sideboard")
TYPES = {"Legend": {"legend"}, "Champion": {"unit"}, "MainDeck": {"unit","spell","gear"},
         "Battlefields": {"battlefield"}, "Runes": {"rune"}, "Sideboard": {"unit","spell","gear"}}


def digest(raw):
    return sha256(raw).hexdigest()


def norm(s):
    return s.replace("’", "'").strip().casefold()


def native_key(s):
    # Pinned native CardDB uses bytewise ASCII lowercasing.
    return s.translate(str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"))


class FormatRejected(ValueError):
    pass


class FormatGate:
    def __init__(self, profile, registry, allowed_sets, exempt_ids=()):
        if profile["schema_version"] != 1 or profile["format"] != "standard_constructed_1v1":
            raise FormatRejected("unsupported format profile")
        cards = registry["cards"]
        self.ids = {c["card_id"]: c for c in cards}
        if len(self.ids) != len(cards):
            raise FormatRejected("duplicate registry ID")
        codes = {c["public_code"]: c for c in cards if c.get("public_code")}
        if len(codes) != sum(bool(c.get("public_code")) for c in cards):
            raise FormatRejected("duplicate public code")
        self.sets = frozenset(allowed_sets)
        self.exempt = frozenset(exempt_ids)
        if not self.sets or not self.sets <= {c["set"] for c in cards}:
            raise FormatRejected("explicit known allowed sets required")
        if not self.exempt <= self.ids.keys() or any(
                self.ids[i]["card_type"] != "rune" for i in self.exempt):
            raise FormatRejected("only explicit registered rune IDs may be set-exempt")
        self.banned = set()
        self.banned_names = set()
        for row in profile["ban_entries"]:
            c = codes.get(row["code"])
            if not c or (c["card_id"],c["name"],c["card_type"]) != (
                    row["engine_id"],row["name"],row["type"]):
                raise FormatRejected("profile registry mismatch: " + row["code"])
            if c["card_id"] in self.banned:
                raise FormatRejected("duplicate profile ban")
            self.banned.add(c["card_id"])
            self.banned_names.update(norm(n) for n in [row["name"], *row["aliases"]])
        native_bans = {c["card_id"] for c in cards if c["banned"]}
        if not native_bans <= self.banned:
            raise FormatRejected("profile would unban a native-banned identity; requires new binary")
        self.names = defaultdict(set)
        # Conservative union of native aliases: collisions fail closed rather than
        # trusting registry insertion order or silently selecting a printing.
        for c in cards:
            names = [c["name"]]
            if c["card_type"] == "legend":
                titles = [c["name"]]
                if c["name"].endswith(" - Starter"):
                    titles.append(c["name"][:-10])
                names = titles + [tag + ", " + title for tag in c["tags"] for title in titles]
            for n in names:
                self.names[native_key(n)].add(c["card_id"])

    def resolve(self, entry):
        m = re.fullmatch(r"(.+?) #(\d+)", entry)
        name, explicit = (m[1], int(m[2])) if m else (entry, None)
        # Block a banned functional name even if a different printing ID is supplied.
        if norm(name) in self.banned_names:
            raise FormatRejected("profile banned name: " + name)
        candidates = self.names.get(native_key(name), set())
        if explicit is not None:
            if explicit not in candidates:
                raise FormatRejected("explicit ID/name mismatch: " + entry)
            i = explicit
        elif len(candidates) == 1:
            i = next(iter(candidates))
        else:
            raise FormatRejected("unknown or ambiguous identity: " + entry)
        c = self.ids[i]
        if i in self.banned or norm(c["name"]) in self.banned_names or c["banned"]:
            raise FormatRejected("banned identity: " + entry)
        if c["set"] not in self.sets and i not in self.exempt:
            raise FormatRejected("set excluded by selected profile: " + entry)
        if c.get("super_type") == "token":
            raise FormatRejected("token cannot be registered: " + entry)
        return c

    def validate(self, raw):
        text = raw.decode("utf-8")
        sections = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.endswith(":"):
                h = line[:-1]
                if len(sections) >= len(HEADINGS) or h != HEADINGS[len(sections)]:
                    raise FormatRejected("unexpected section: " + h)
                sections[h] = []
                continue
            m = re.fullmatch(r"([0-9]+)\s+(.+)", line)
            if not sections or not m or not 0 < int(m[1]) <= 39:
                raise FormatRejected("invalid card row")
            section = next(reversed(sections))
            c = self.resolve(m[2])
            if c["card_type"] not in TYPES[section]:
                raise FormatRejected("wrong card type in " + section)
            sections[section].extend([c["card_id"]] * int(m[1]))
            if len(sections[section]) > 39:
                raise FormatRejected("too many registered cards")
        if tuple(sections) != HEADINGS:
            raise FormatRejected("missing registration sections")
        for section, count in (("Legend",1),("Champion",1),("MainDeck",39),("Battlefields",3),("Runes",12)):
            if len(sections[section]) != count:
                raise FormatRejected("invalid count in " + section)
        if len(sections["Sideboard"]) > 10:
            raise FormatRejected("sideboard exceeds ten")
        # Other construction and champion/domain rules still require the native validator.
        return sections


class NativeGateway:
    """Only the pinned binary is accepted. No --wild or ambient profile defaults."""
    def __init__(self, engine, registry, profile, allowed_sets, exempt_ids=()):
        self.engine = Path(engine).resolve()
        self.profile = json.loads(Path(profile).read_bytes())
        raw = Path(registry).read_bytes()
        self.registry_sha = digest(raw)
        self.profile_sha = digest(Path(profile).read_bytes())
        if self.registry_sha != self.profile["registry_reference_sha256"]:
            raise FormatRejected("registry hash mismatch")
        if digest(self.engine.read_bytes()) != ENGINE_SHA:
            raise FormatRejected("engine hash mismatch")
        self.gate = FormatGate(self.profile, json.loads(raw), allowed_sets, exempt_ids)

    def provenance(self):
        return {"profile_id": self.profile["profile_id"], "profile_sha256": self.profile_sha,
                "registry_sha256": self.registry_sha, "engine_sha256": ENGINE_SHA,
                "allowed_sets": sorted(self.gate.sets), "rune_exempt_ids": sorted(self.gate.exempt),
                "full_official_legality_certified": False}

    def game(self, one, two, seed, agent="ismcts:sims=24", timeout=180, *, forced_start=None):
        if type(seed) is not int or seed <= 0 or timeout <= 0:
            raise FormatRejected("positive deterministic seed and timeout required")
        if not re.fullmatch(r"ismcts:sims=[1-9][0-9]*", agent):
            raise FormatRejected("only sampled ISMCTS agent accepted by this gateway")
        raws = [Path(p).read_bytes() for p in (one,two)]
        vectors = [self.gate.validate(raw) for raw in raws]
        if digest(self.engine.read_bytes()) != ENGINE_SHA:
            raise FormatRejected("engine changed")
        env = os.environ.copy()
        env.pop("RIFTBOUND_FORCE_STARTING_PLAYER", None)
        if forced_start is not None:
            if forced_start not in (1,2):
                raise FormatRejected("invalid first-player override")
            env["RIFTBOUND_FORCE_STARTING_PLAYER"] = str(forced_start)
        with tempfile.TemporaryDirectory(prefix="rb_format_") as tmp:
            paths = [Path(tmp)/f"p{i}.txt" for i in (1,2)]
            for p,raw in zip(paths,raws):
                p.write_bytes(raw)
            result = benchmark(self.engine,*paths,seed,agent,timeout,env)
        return {**result, **self.provenance(), "seed":seed, "agent":agent,
                "deck_sha256":[digest(raw) for raw in raws],
                "resolved_ids_sha256":[digest(json.dumps(v).encode()) for v in vectors]}

    def fixed_bo3(self, one, two, seed, agent="ismcts:sims=24", timeout=180):
        # Fixed-deck only. This is not a tournament-sideboard policy.
        wins = [0,0]
        games = []
        for i in range(3):
            flip = i == 1
            result = self.game(two if flip else one, one if flip else two,
                               stable_seed(seed,"format_fixed_bo3",i) or 1,agent,timeout)
            games.append(result)
            if result["status"] != "complete" or result["winner"] not in (1,2):
                return {**self.provenance(),"status":"incomplete","winner":None,"games":games}
            winner = 3-result["winner"] if flip else result["winner"]
            wins[winner-1] += 1
            if max(wins)==2:
                break
        return {**self.provenance(),"status":"complete_fixed_bo3","winner":wins.index(2)+1,
                "score":wins,"games":games,"sideboarding_applied":False}
