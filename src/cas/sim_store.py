import json
import re
from datetime import date
from pathlib import Path

SIMS_DIR = Path(__file__).parent / "data" / "sims"


def _sim_path(name: str) -> Path:
    slug = re.sub(r"[^\w-]+", "_", name.strip().lower())
    return SIMS_DIR / f"{slug}.json"


def sim_exists(name: str) -> bool:
    return _sim_path(name).exists()


def save_sim(sim) -> None:
    """Write a sim to <name>.json, with its image alongside in <name>.image."""
    path = _sim_path(f"{sim.first_name} {sim.surname}")
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {key: value for key, value in vars(sim).items() if key != "image"}
    path.write_text(json.dumps(data, default=str, ensure_ascii=False, indent=2), encoding="utf-8")

    image_path = path.with_suffix(".image")
    if sim.image:
        image_path.write_bytes(sim.image)
    else:
        image_path.unlink(missing_ok=True)


def list_saved_sims() -> list[str]:
    sims = (json.loads(path.read_text(encoding="utf-8")) for path in SIMS_DIR.glob("*.json"))
    return sorted(f"{sim['first_name']} {sim['surname']}".strip() for sim in sims)


def load_sim(name: str) -> dict:
    path = _sim_path(name)
    sim = json.loads(path.read_text(encoding="utf-8"))
    sim["dob"] = date.fromisoformat(sim["dob"])

    image_path = path.with_suffix(".image")
    sim["image"] = image_path.read_bytes() if image_path.exists() else None
    return sim
