import json
from pathlib import Path

def generate():
    arch_dir = Path(__file__).resolve().parents[2]
    live_p = arch_dir / "architecture" / "phase_1_data_foundation" / "output" / "phase1_live.jsonl"
    
    locations = set()
    cuisines = set()
    
    if not live_p.exists():
        print(f"Error: {live_p} not found.")
        return

    print(f"Processing {live_p}...")
    with open(live_p, "r", encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
                loc = r.get("location")
                if loc:
                    locations.add(loc.strip())
                c_list = r.get("cuisine", "")
                if isinstance(c_list, str):
                    for c in c_list.split(","):
                        c = c.strip()
                        if c:
                            cuisines.add(c)
            except:
                continue
                
    metadata = {
        "locations": sorted(list(locations)),
        "cuisines": sorted(list(cuisines))
    }
    
    out_p = Path(__file__).resolve().parent / "metadata.json"
    out_p.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Metadata generated with {len(locations)} locations and {len(cuisines)} cuisines at {out_p}")

if __name__ == "__main__":
    generate()
