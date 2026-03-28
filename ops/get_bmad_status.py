#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ops.bmad_operator import summarize_artifact_statuses


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact-root", default="_bmad-output/implementation-artifacts")
    ap.add_argument("--planning-root", action="append", default=["docs/mvp-mentoria"])
    args = ap.parse_args()

    artifact_root = Path(args.artifact_root)
    if not artifact_root.exists():
        raise SystemExit(f"Missing artifact root: {artifact_root}")

    planning_roots = [Path(root) for root in args.planning_root]
    summary = summarize_artifact_statuses(artifact_root, planning_roots=planning_roots)

    print("=== BMAD Artifact Status ===")
    print(f"artifact_root : {artifact_root.as_posix()}")

    current = summary["current"]
    if current is None:
        print("current       : none")
    else:
        print(f"current       : {current.path.name}")
        print(f"status        : {current.status}")
        print(f"updated_utc   : {current.last_modified_utc}")

    print("--- Status Counts ---")
    for status, count in sorted(summary["counts"].items()):
        print(f"{status}: {count}")

    print("--- Active Artifacts ---")
    for artifact in summary["artifacts"]:
        if artifact.status == "done":
            continue
        print(f"{artifact.status:14} {artifact.path.name}")

    if summary["planning_artifacts"]:
        print("--- Planning Inputs ---")
        for artifact in summary["planning_artifacts"]:
            print(f"{artifact.artifact_type:14} {artifact.path.as_posix()}")


if __name__ == "__main__":
    main()
