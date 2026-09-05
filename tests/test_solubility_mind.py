import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from solubility_mind.models import FrontierPayload, ExecutionStatus
from solubility_mind.engine import FrontierDomainEngine
from solubility_mind.agents import IntrinsicSolubilityAgent, BCSClassDeterminerAgent, DissolutionRatePredictorAgent, SolubilityCoordinator
from solubility_mind.cli import main, _resolve_safe_path


def test_sub_agents():
    a1 = IntrinsicSolubilityAgent()
    p1 = FrontierPayload("T1", "KEY-01", primary_metric=35.0, secondary_metric=4.0, status_descriptor="NOMINAL")
    alerts1 = a1.audit(p1)
    assert len(alerts1) == 1
    assert alerts1[0].status == ExecutionStatus.ELEVATED_RISK

    a2 = BCSClassDeterminerAgent()
    p2 = FrontierPayload("T2", "KEY-02", primary_metric=10.0, secondary_metric=15.0, status_descriptor="NOMINAL", is_critical_flag=True)
    alerts2 = a2.audit(p2)
    assert len(alerts2) == 1
    assert alerts2[0].status == ExecutionStatus.CRITICAL_INTERVENTION

    a3 = DissolutionRatePredictorAgent()
    p3 = FrontierPayload("T3", "KEY-03", primary_metric=10.0, secondary_metric=4.0, status_descriptor="DISCORDANT_ANOMALY")
    alerts3 = a3.audit(p3)
    assert len(alerts3) == 1


def test_coordinator():
    coord = SolubilityCoordinator()
    p_nominal = FrontierPayload("T4", "KEY-04", primary_metric=12.0, secondary_metric=4.0, status_descriptor="NOMINAL")
    dossier = coord.process(p_nominal)
    assert dossier["overall_status"] == ExecutionStatus.NOMINAL.value
    assert dossier["total_alerts"] == 0

    ans = coord.query_supervisory_chat("What standard is applied?")
    assert "FDA / WHO Biopharmaceutics Classification (BCS)" in ans or "specifications" in ans


def test_cli():
    assert main(["audit", "--task-id", "CLI-01"]) == 0
    assert main(["chat", "What", "is", "the", "system", "status?"]) == 0


def test_sm_path_traversal_protection():
    """Batch CLI must reject paths that escape the working directory."""
    with pytest.raises(ValueError, match="Path traversal blocked"):
        _resolve_safe_path("../../../etc/passwd")


def test_sm_batch_cli_with_valid_csv():
    """Batch CLI processes a valid CSV and produces output."""
    work_dir = Path(__file__).parent / "_test_sm_tmp"
    work_dir.mkdir(exist_ok=True)
    try:
        input_csv = work_dir / "input.csv"
        input_csv.write_text(
            "task_id,target_identifier,primary_metric,secondary_metric,is_critical_flag,status_descriptor\n"
            "TASK-SM1,TARGET-SM1,12.0,4.0,False,NOMINAL\n",
            encoding="utf-8",
        )
        output_csv = work_dir / "output.csv"
        result = main(["batch", "-i", str(input_csv), "-o", str(output_csv)])
        assert result == 0
        assert output_csv.exists()
        content = output_csv.read_text(encoding="utf-8")
        assert "overall_status" in content
    finally:
        if output_csv.exists():
            output_csv.unlink()
        if input_csv.exists():
            input_csv.unlink()
        if work_dir.exists():
            work_dir.rmdir()


def test_sm_batch_cli_missing_input():
    """Batch CLI returns non-zero exit code for missing input file."""
    result = main(["batch", "-i", "nonexistent_file_12345.csv"])
    assert result == 1
