"""Audit-chain modifications must be detected, not merely linked."""
from agents.base import AuditTrail


def test_audit_chain_verifies_hmac():
    trail = AuditTrail(secret_key="local-test-key")
    a = trail.log("worker", "tier", "event", {"status": "ok"})
    trail.log("worker", "tier", "event2", {"status": "ok"})
    assert trail.verify_integrity()
    # Caller mutation of returned entry must not mutate internal state.
    a["event_type"] = "changed"
    assert trail.verify_integrity()
    trail.logs[0]["actor"] = "impostor"
    assert not trail.verify_integrity()


def test_audit_chain_detects_digest_tampering():
    trail = AuditTrail(secret_key="local-test-key")
    trail.log("w", "t", "e", {"ok": 1})
    trail.logs[0]["current_hash"] = "0" * 64
    assert not trail.verify_integrity()


def test_audit_chain_snapshot_isolation():
    trail = AuditTrail(secret_key="local-test-key")
    trail.log("w", "t", "e", {"ok": 1})
    snapshot = trail.get_trail()
    snapshot[0]["actor"] = "tampered"
    assert trail.verify_integrity()
