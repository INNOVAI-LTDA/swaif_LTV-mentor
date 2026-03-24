from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.storage.canonical_repositories import (
    CanonicalClientRepository,
    CanonicalEndUserRepository,
    CanonicalJourneyCheckpointRepository,
    CanonicalMetricMeasureRepository,
    CanonicalPillarMetricRepository,
    CanonicalProductAssignmentRepository,
    CanonicalProductPillarRepository,
    CanonicalProductRepository,
    CanonicalProviderRepository,
)


CANONICAL_EXPORT_FILES = {
    "clients.json": CanonicalClientRepository,
    "products.json": CanonicalProductRepository,
    "providers.json": CanonicalProviderRepository,
    "end_users.json": CanonicalEndUserRepository,
    "product_pillars.json": CanonicalProductPillarRepository,
    "pillar_metrics.json": CanonicalPillarMetricRepository,
    "product_assignments.json": CanonicalProductAssignmentRepository,
    "metric_measures.json": CanonicalMetricMeasureRepository,
    "journey_checkpoints.json": CanonicalJourneyCheckpointRepository,
}


def export_canonical_data(output_dir: str | Path) -> dict[str, Path]:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}
    for filename, repository_cls in CANONICAL_EXPORT_FILES.items():
        repository = repository_cls()
        items = [item.model_dump(mode="json") for item in repository.list_records()]
        payload = {"version": 1, "items": items}
        output_path = target_dir / filename
        output_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        written[filename] = output_path

    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Export legacy JSON stores into canonical client-agnostic store files.")
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parents[2] / "canonical-data"),
        help="Directory that will receive the canonical JSON store files.",
    )
    args = parser.parse_args()

    written = export_canonical_data(args.output_dir)
    for name, path in written.items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
