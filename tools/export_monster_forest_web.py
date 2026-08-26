#!/usr/bin/env python3
"""Export Pokémon data and sprite assets for the Monster Forest web client.

Run from the pokeemerald-expansion repository:
  python3 tools/export_monster_forest_web.py --out ../monster-forest-assets

The exporter deliberately emits an engine-neutral contract.  The PWA must never
read C headers directly; it only consumes the generated JSON and PNG/WebP paths.
"""
from __future__ import annotations
import argparse, json, re, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TYPE_RE = re.compile(r"TYPE_([A-Z_]+)")
FIELD_RE = re.compile(r"\.(baseHP|baseAttack|baseDefense|baseSpeed|baseSpAttack|baseSpDefense|type1|type2|catchRate|expYield|genderRatio|growthRate|abilities)\s*=\s*([^,\n}]+)")
ENTRY_RE = re.compile(r"\[SPECIES_([A-Z0-9_]+)\]\s*=\s*\{(.*?)\n\s*\},", re.S)

def clean(value: str):
    return value.strip().replace("TYPE_", "").lower().replace("ABILITY_", "").lower()

def species_records():
    src = (ROOT / "src/data/pokemon/species_info.h").read_text(encoding="utf-8")
    out = []
    for key, body in ENTRY_RE.findall(src):
        if key in {"NONE", "EGG"}: continue
        fields = {name: clean(value) for name, value in FIELD_RE.findall(body)}
        if not fields: continue
        stats = {
            "hp": int(fields.get("baseHP", 1)),
            "attack": int(fields.get("baseAttack", 1)),
            "defense": int(fields.get("baseDefense", 1)),
            "speed": int(fields.get("baseSpeed", 1)),
            "specialAttack": int(fields.get("baseSpAttack", 1)),
            "specialDefense": int(fields.get("baseSpDefense", 1)),
        }
        slug = key.lower().replace("_", "-")
        out.append({"id": key.lower(), "species": key, "slug": slug,
                    "types": [fields.get("type1", "normal")] + ([] if fields.get("type2") in (None, fields.get("type1")) else [fields["type2"]]),
                    "baseStats": stats, "catchRate": int(fields.get("catchRate", 0)),
                    "growthRate": fields.get("growthRate", "medium_fast"),
                    "sprites": {"front": f"sprites/{slug}/front.png", "back": f"sprites/{slug}/back.png", "icon": f"sprites/{slug}/icon.png"}})
    return out

def copy_sprites(records, out):
    for mon in records:
        src = ROOT / "graphics/pokemon" / mon["slug"]
        dst = out / "sprites" / mon["slug"]
        if not src.exists(): continue
        dst.mkdir(parents=True, exist_ok=True)
        for view, candidates in {"front": ("front.png","front.4bpp.png"), "back": ("back.png","back.4bpp.png"), "icon": ("icon.png","icon.4bpp.png")}.items():
            found = next((src / n for n in candidates if (src / n).exists()), None)
            if found: shutil.copy2(found, dst / f"{view}.png")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True, type=Path); args = ap.parse_args()
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=True)
    species = species_records()
    moves = json.loads((ROOT / "src/data/pokemon/all_learnables.json").read_text(encoding="utf-8"))
    (out / "pokemon-species.json").write_text(json.dumps({"schemaVersion":1,"species":species}, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "pokemon-learnsets.json").write_text(json.dumps({"schemaVersion":1,"learnsets":moves}, ensure_ascii=False), encoding="utf-8")
    copy_sprites(species, out)
    print(f"Exported {len(species)} species to {out}")

if __name__ == "__main__": main()
