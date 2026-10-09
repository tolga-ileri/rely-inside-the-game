"""Export JSON Schemas for the synthetic event/match format to synthetic-data/schemas."""
from __future__ import annotations

import json
from pathlib import Path

from rely_brain.schemas import Event, Match

OUT = Path(__file__).resolve().parents[3] / "synthetic-data" / "schemas"


def schemas() -> dict[str, dict]:
    ev = Event.model_json_schema()
    ev["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    ev["$id"] = "https://github.com/rely/rely-inside-the-game/synthetic-data/schemas/event.schema.json"
    ev["description"] = ("Rely Match Brain synthetic football event. Coordinates 0-100 in the acting team's attacking frame "
                         "(x=100 opponent goal; y<33.3 left, 33.3-66.7 centre, >66.7 right). SYNTHETIC DATA ONLY.")
    m = Match.model_json_schema()
    m["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    return {"event.schema.json": ev, "match.schema.json": m}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, sch in schemas().items():
        (OUT / name).write_text(json.dumps(sch, indent=2) + "\n", encoding="utf-8")
        print("wrote", OUT / name)


if __name__ == "__main__":
    main()
