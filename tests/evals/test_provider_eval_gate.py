from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _runner_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = ".:apps/api"
    env["LLM_PROVIDER"] = "fake"
    env.pop("OPENAI_API_KEY", None)
    return env


def test_phase9_provider_eval_gate_rejects_live_provider_mode_by_default() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/evals/run_eval_gate.py",
            "--suite",
            "phase9",
            "--mode",
            "live_provider",
        ],
        cwd=REPO_ROOT,
        env=_runner_env(),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 3
    error = json.loads(result.stderr)
    assert error["error"] == "unsupported mode: live_provider"
    assert error["supported_modes"] == ["fixture", "replay"]
    assert "OPENAI_API_KEY" not in result.stderr


def test_phase9_provider_eval_report_is_non_claim_and_ci_safe_without_credentials() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/evals/run_eval_gate.py",
            "--suite",
            "phase9",
            "--mode",
            "replay",
        ],
        cwd=REPO_ROOT,
        env=_runner_env(),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["provider_evidence_type"] == "replay"
    assert report["ci"]["default_requires_live_provider_credentials"] is False
    assert report["ci"]["mode_is_ci_safe"] is True
    assert report["ci"]["llm_provider_env_used"] is True
    assert "fake_visible_eval_is_not_production_provider_quality_evidence" in report["non_claims"]
    assert "replay_mode_is_not_real_provider_quality_evidence" in report["non_claims"]
    assert report["security_scan"]["raw_payload_stored"] is False


def test_phase12_provider_eval_contract_forbids_live_provider_in_default_static_gate() -> None:
    manifest = json.loads(
        (REPO_ROOT / "evals" / "suites" / "phase12.json").read_text(encoding="utf-8")
    )

    assert manifest["default_mode"] == "static_contract_review_no_live_provider"
    assert manifest["provider_evidence_policy"]["default_provider_mode"] == "none"
    assert manifest["provider_evidence_policy"]["live_provider_usage"] == "forbidden_in_p12_w1"
    assert manifest["provider_evidence_policy"]["real_provider_quality_certification"] == "not_claimed"
    assert (
        manifest["provider_evidence_policy"][
            "replay_fake_local_evidence_is_not_real_provider_quality_certification"
        ]
        is True
    )
    assert "p12_w1_does_not_certify_real_provider_quality" in manifest["non_claims"]
