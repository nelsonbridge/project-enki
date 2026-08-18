from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "releases" / "enki-hosted-1.0-rc2" / "evidence" / "sprint45"


def _fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> None:
    files = sorted(EVIDENCE_DIR.glob("*.json"))
    if len(files) != 7:
        _fail(f"expected 7 evidence files, found {len(files)}")

    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        scope = payload.get("validation_scope", {})
        if scope.get("external_services_budget_usd") != 0:
            _fail(f"{path.name}: external_services_budget_usd must be 0")

        attestation = payload.get("cost_attestation", {})
        if attestation.get("currency") != "USD":
            _fail(f"{path.name}: cost_attestation.currency must be USD")
        if float(attestation.get("total_observed_cost_usd", -1)) != 0.0:
            _fail(f"{path.name}: total_observed_cost_usd must be 0")

        checks = attestation.get("provider_checks", [])
        if not checks:
            _fail(f"{path.name}: provider_checks must not be empty")
        for item in checks:
            if float(item.get("observed_cost_usd", -1)) != 0.0:
                _fail(f"{path.name}: provider check {item.get('provider')}:{item.get('service')} observed_cost_usd must be 0")
            if not item.get("evidence_location"):
                _fail(f"{path.name}: provider check missing evidence_location")

    print(f"PASS: zero-cost checks validated for {len(files)} Sprint 45 evidence files")


if __name__ == "__main__":
    main()
