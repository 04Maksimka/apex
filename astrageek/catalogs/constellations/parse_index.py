import argparse
import json
import sys
from pathlib import Path


def main():
    """
    Make a json file with constellations metadata: name, lines, center
    from two jsons: index.json and constellations_centers.json
    """

    ap = argparse.ArgumentParser(
        description="Build CONSTELLATIONS_DATA from constellation_centers.json"
        " + index.json (constellations only)"
    )
    ap.add_argument("--centers", default="constellation_centers.json")
    ap.add_argument("--index", default="index.json")
    ap.add_argument("--out", default="constellations_data.json")
    args = ap.parse_args()

    with open(args.centers, "r", encoding="utf-8") as f:
        centers = json.load(f)

    with open(args.index, "r", encoding="utf-8") as f:
        idx = json.load(f)

    constellations = idx.get("constellations")
    print(isinstance(constellations, dict), isinstance(constellations, list))
    if not isinstance(constellations, list):
        raise SystemExit(
            "ERROR: index.json: expected key 'constellations' as list"
        )

    out = {}
    used_codes = set()

    for c in constellations:
        if not isinstance(c, dict):
            continue

        cid = str(c.get("id", ""))
        if not cid.startswith("CON "):
            continue

        code = cid.split()[
            -1
        ].upper()  # "And"/"TrA"/"CVn" -> "AND"/"TRA"/"CVN"
        used_codes.add(code)

        if code not in centers:
            print(
                f"WARNING: no center/name for {code} (from id={cid})",
                file=sys.stderr,
            )
            continue

        lines = c.get("lines")
        if not isinstance(lines, list):
            print(
                f"WARNING: {code}: lines is not a list (from id={cid})",
                file=sys.stderr,
            )
            continue

        out[code] = {
            "name": centers[code].get("name"),
            "lines": lines,
            "center": centers[code].get("center"),
        }

    missing_in_index = sorted(set(centers.keys()) - used_codes)
    if missing_in_index:
        print(
            f"WARNING: centers present but not found in index.constellations: "
            f"{missing_in_index}",
            file=sys.stderr,
        )

    Path(args.out).write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
