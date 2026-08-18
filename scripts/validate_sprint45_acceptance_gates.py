from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "releases" / "enki-hosted-1.0-rc2" / "evidence" / "sprint45"
GATES_PATH = ROOT / "releases" / "enki-hosted-1.0-rc2" / "sprint45-control-acceptance-gates.json"
LOCK_PATH = ROOT / "releases" / "enki-hosted-1.0-rc2" / "architecture-lock.json"


def _fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> None:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("architecture_id") != "CF-NEON-R2":
        _fail("architecture drift detected; expected CF-NEON-R2")

    gates = json.loads(GATES_PATH.read_text(encoding="utf-8"))
    required_controls = {item["control_id"] for item in gates["controls"]}

    evidence_by_control = {}
    for path in sorted(EVIDENCE_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        control_id = payload.get("control_id")
        if not control_id:
            _fail(f"{path.name}: missing control_id")
        evidence_by_control[control_id] = payload

    if required_controls != set(evidence_by_control):
        _fail("evidence control set does not match declared acceptance gates")

    blocking = []
    for control in gates["controls"]:
        control_id = control["control_id"]
        payload = evidence_by_control[control_id]
        status = payload["result"]["status"]
        reviewer = payload["participants"]["independent_reviewer"]
        if status not in {"PASS", "FAIL", "PARTIAL"}:
            _fail(f"{control_id}: invalid status {status}")
        if not reviewer:
            _fail(f"{control_id}: independent_reviewer missing")
        if reviewer == "@copilot-cli":
            _fail(f"{control_id}: independent reviewer cannot equal implementer")
        if reviewer.startswith("PENDING-") or status != "PASS":
            blocking.append(control_id)

    if not blocking:
        print("PASS: all Sprint 45 controls are independently attested PASS")
    else:
        print(
            "PASS: Sprint 45 remains fail-closed PARTIAL; blocking controls: "
            + ", ".join(sorted(blocking))
        )


if __name__ == "__main__":
    main()
