#!/usr/bin/env python3
"""Build the JSON + sprite package consumed by 100days/mons.html."""
from __future__ import annotations
import argparse,json,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ENTRY=re.compile(r"\[SPECIES_([A-Z0-9_]+)\]\s*=\s*\{(.*?)\n\s*\},",re.S)
FIELD=re.compile(r"\.(baseHP|baseAttack|baseDefense|baseSpeed|baseSpAttack|baseSpDefense|type1|type2|catchRate|growthRate)\s*=\s*([^,\n}]+)")
def val(x): return x.strip().replace("TYPE_","").lower()
def num(x): 
 try:return int(x)
 except ValueError:return 0
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--out",required=True,type=Path);a=ap.parse_args();out=a.out;out.mkdir(parents=True,exist_ok=True)
 # species_info.h is only an include dispatcher in this expansion. Read each
 # generation family file, so the exported catalogue is real data, not a stub.
 text="\n".join(p.read_text(encoding="utf8") for p in sorted((ROOT/"src/data/pokemon/species_info").glob("gen_*_families.h")))
 species=[]
 for key,body in ENTRY.findall(text):
  f={k:val(v) for k,v in FIELD.findall(body)}
  if not f:continue
  slug=key.lower().replace("_","-"); types=[f.get("type1","normal")]
  if f.get("type2") and f["type2"]!=types[0]:types.append(f["type2"])
  species.append({"id":key.lower(),"slug":slug,"name":key.replace("_"," ").title(),"types":types,"baseStats":{"hp":num(f.get("baseHP","0")),"attack":num(f.get("baseAttack","0")),"defense":num(f.get("baseDefense","0")),"speed":num(f.get("baseSpeed","0")),"specialAttack":num(f.get("baseSpAttack","0")),"specialDefense":num(f.get("baseSpDefense","0"))},"catchRate":num(f.get("catchRate","0")),"growthRate":f.get("growthRate","medium_fast"),"sprites":{"front":f"sprites/{slug}/front.png","back":f"sprites/{slug}/back.png","icon":f"sprites/{slug}/icon.png"}})
  src=ROOT/"graphics/pokemon"/slug;dst=out/"sprites"/slug
  for view,names in {"front":["front.png","front.4bpp.png"],"back":["back.png","back.4bpp.png"],"icon":["icon.png","icon.4bpp.png"]}.items():
   p=next((src/n for n in names if (src/n).exists()),None)
   if p:dst.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst/f"{view}.png")
 (out/"pokemon-species.json").write_text(json.dumps({"schemaVersion":1,"species":species},ensure_ascii=False,separators=(",",":")),encoding="utf8")
 # Kept separate: expansion's all_learnables is already structured and large.
 shutil.copy2(ROOT/"src/data/pokemon/all_learnables.json",out/"pokemon-learnsets.json")
 print("exported",len(species),"species")
if __name__=="__main__":main()
