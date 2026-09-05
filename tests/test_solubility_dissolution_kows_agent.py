"""
Automated Pytest Test Suite for Solubility Dissolution Kows Agent.
Domain: AI Drug Discovery, Structural Biology & Wet-Lab Robotics
Standard: wwPDB / IUPAC / OpenSMILES / ISAC Standards
"""
import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import PHIGuard, AuditLogger, AuditTrail, SecurityException
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from agents.supervisor import SystemSupervisor
from cli import main, _resolve_safe_path


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive for Staphylococcus")

    # Clean text passes
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_specialized_workers():
    # Worker 1: QC Invariant
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    alerts1 = InvariantQCWorker.evaluate(p1)
    assert len(alerts1) == 1
    assert alerts1[0].urgency == UrgencyLevel.ELEVATED

    # Worker 2: Safety
    p2 = SystemTaskPayload(task_id="T2", target_identifier="KEY-02", primary_metric=10.0, is_critical_flag=True)
    alerts2 = SafetyEscalationWorker.evaluate(p2)
    assert len(alerts2) == 1
    assert alerts2[0].urgency == UrgencyLevel.CRITICAL_STAT

    # Worker 3: Protocol Conformance
    p3 = SystemTaskPayload(task_id="T3", target_identifier="KEY-03", primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY")
    alerts3 = ProtocolConformanceWorker.evaluate(p3)
    assert len(alerts3) == 1


def test_supervisor_consensus_and_audit():
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-PROD-01",
        target_identifier="KEY-PROD-01",
        primary_metric=12.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL"
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash != ""

    # Verify cryptographic audit trail
    assert AuditLogger.verify_integrity() is True

    # CLI tests
    assert main(["audit", "--task-id", "CLI-TEST-01"]) == 0
    assert main(["chat", "Explain", "specifications"]) == 0
    assert main(["verify-audit"]) == 0


def test_path_traversal_protection():
    """Batch CLI must reject paths that escape the working directory."""
    with pytest.raises(ValueError, match="Path traversal blocked"):
        _resolve_safe_path("../../../etc/passwd")

    with pytest.raises(ValueError, match="Path traversal blocked"):
        _resolve_safe_path("/etc/passwd")


def test_batch_cli_with_valid_csv(tmp_path):
    """Batch CLI processes a valid CSV and produces output."""
    # Use a subdirectory of the working directory to satisfy path traversal guard
    work_dir = Path(__file__).parent / "_test_tmp"
    work_dir.mkdir(exist_ok=True)
    try:
        input_csv = work_dir / "input.csv"
        input_csv.write_text(
            "task_id,target_identifier,primary_metric,secondary_metric,is_critical_flag,status_descriptor\n"
            "TASK-B1,TARGET-B1,12.0,4.0,False,NOMINAL\n"
            "TASK-B2,TARGET-B2,35.0,15.0,True,DISCORDANT\n",
            encoding="utf-8",
        )
        output_csv = work_dir / "output.csv"

        result = main(["batch", "-i", str(input_csv), "-o", str(output_csv)])
        assert result == 0
        assert output_csv.exists()
        content = output_csv.read_text(encoding="utf-8")
        assert "overall_urgency" in content
        assert "TASK-B1" in content
        assert "TASK-B2" in content
    finally:
        # Clean up test artifacts
        if output_csv.exists():
            output_csv.unlink()
        if input_csv.exists():
            input_csv.unlink()
        if work_dir.exists():
            work_dir.rmdir()


def test_batch_cli_missing_input():
    """Batch CLI returns non-zero exit code for missing input file."""
    result = main(["batch", "-i", "nonexistent_file_12345.csv"])
    assert result == 1


def test_batch_cli_skips_malformed_rows():
    """Batch CLI skips rows with invalid numeric data and continues processing."""
    work_dir = Path(__file__).parent / "_test_tmp2"
    work_dir.mkdir(exist_ok=True)
    try:
        input_csv = work_dir / "input.csv"
        input_csv.write_text(
            "task_id,target_identifier,primary_metric,secondary_metric,is_critical_flag,status_descriptor\n"
            "TASK-GOOD,TARGET-GOOD,12.0,4.0,False,NOMINAL\n"
            "TASK-BAD,TARGET-BAD,not_a_number,4.0,False,NOMINAL\n",
            encoding="utf-8",
        )
        output_csv = work_dir / "output.csv"

        result = main(["batch", "-i", str(input_csv), "-o", str(output_csv)])
        assert result == 0
        content = output_csv.read_text(encoding="utf-8")
        assert "TASK-GOOD" in content
        # The bad row should be skipped, so only 1 data row in output
        lines = [line for line in content.strip().split("\n") if line]
        assert len(lines) == 2  # header + 1 valid row
    finally:
        if output_csv.exists():
            output_csv.unlink()
        if input_csv.exists():
            input_csv.unlink()
        if work_dir.exists():
            work_dir.rmdir()


def test_audit_trail_uses_env_key():
    """AuditTrail should use AUDIT_SECRET_KEY from environment when set."""
    os.environ["AUDIT_SECRET_KEY"] = "test-key-for-unit-test"
    trail = AuditTrail()
    assert trail.secret_key == b"test-key-for-unit-test"
    del os.environ["AUDIT_SECRET_KEY"]


def test_audit_trail_generates_random_key_without_env():
    """AuditTrail should generate a random key when no env var is set."""
    os.environ.pop("AUDIT_SECRET_KEY", None)
    trail = AuditTrail()
    assert len(trail.secret_key) == 64  # 32 bytes hex-encoded = 64 chars
