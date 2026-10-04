import pytest
import time
from aeo_graph_engine.resilience import CircuitBreaker, CircuitState, SelfHealingEngine


def test_circuit_breaker_transitions():
    cb = CircuitBreaker(name="test_api", failure_threshold=2, recovery_timeout=0.2)
    assert cb.state == CircuitState.CLOSED
    assert cb.allow_execution() is True

    cb.record_failure()
    assert cb.state == CircuitState.CLOSED

    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.allow_execution() is False

    time.sleep(0.25)
    assert cb.allow_execution() is True
    assert cb.state == CircuitState.HALF_OPEN

    cb.record_success()
    cb.record_success()
    assert cb.state == CircuitState.CLOSED


def test_self_healing_fallback_and_cache():
    engine = SelfHealingEngine()
    call_count = 0

    def flaky_api():
        nonlocal call_count
        call_count += 1
        if call_count > 1:
            raise ConnectionResetError("Third-party API collapse")
        return {"data": "live_telemetry"}

    def deterministic_fallback(err):
        return {"data": "heuristic_offline_model", "error": str(err)}

    # First call succeeds and caches
    res1, fallback1 = engine.execute_resilient(
        breaker_name="external_provider",
        primary_fn=flaky_api,
        fallback_fn=deterministic_fallback,
        retries=1,
        base_backoff_sec=0.01,
        cache_key="telemetry"
    )
    assert fallback1 is False
    assert res1["data"] == "live_telemetry"

    # Second call fails and falls back to deterministic fallback
    res2, fallback2 = engine.execute_resilient(
        breaker_name="external_provider",
        primary_fn=flaky_api,
        fallback_fn=deterministic_fallback,
        retries=1,
        base_backoff_sec=0.01,
        cache_key="telemetry"
    )
    assert fallback2 is True
    assert res2["data"] == "heuristic_offline_model"

    # Subsequent call without explicit fallback uses cached ground truth
    res3, fallback3 = engine.execute_resilient(
        breaker_name="external_provider",
        primary_fn=flaky_api,
        fallback_fn=None,
        retries=0,
        base_backoff_sec=0.01,
        cache_key="telemetry"
    )
    assert fallback3 is True
    assert res3["data"] == "live_telemetry"
