"""
Resilience, Circuit Breaker, and Self-Healing Engine for AEO Graph Engine.

Protects ingestion, AI gateway calls, crawler crawls, and third-party API dependencies
from network partitions, rate limits, hardware exhaustion, and abrupt vendor collapse.
Ensures graceful degradation to deterministic local heuristic synthesis and cached snapshots.
Zero external runtime dependencies (pure standard library).
"""

import time
import threading
from enum import Enum
from typing import Callable, Any, Optional, Dict, List, Tuple


class CircuitState(str, Enum):
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Failing / collapsed; fast fallback
    HALF_OPEN = "HALF_OPEN"  # Testing recovery


class CircuitBreaker:
    """
    Guards network/API operations against cascaded failure.
    Automatically trips when failure threshold is breached, and permits probing after cooldown.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
        half_open_max_trials: int = 2
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_trials = half_open_max_trials

        self.state: CircuitState = CircuitState.CLOSED
        self.failure_count: int = 0
        self.success_count: int = 0
        self.last_failure_time: float = 0.0
        self._lock = threading.Lock()

    def record_success(self) -> None:
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.half_open_max_trials:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0

    def record_failure(self) -> None:
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                self.success_count = 0

    def allow_execution(self) -> bool:
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            if self.state == CircuitState.OPEN:
                if (time.time() - self.last_failure_time) > self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    return True
                return False
            # HALF_OPEN
            return True

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "last_failure_time": self.last_failure_time,
            }


class SelfHealingEngine:
    """
    Manages circuit breakers, resilient retries with exponential backoff,
    and automatic degradation to local heuristic synthesis or cached ground truth.
    """

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._cache: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def get_or_create_breaker(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0
    ) -> CircuitBreaker:
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(
                    name=name,
                    failure_threshold=failure_threshold,
                    recovery_timeout=recovery_timeout
                )
            return self._breakers[name]

    def execute_resilient(
        self,
        breaker_name: str,
        primary_fn: Callable[[], Any],
        fallback_fn: Optional[Callable[[Exception], Any]] = None,
        retries: int = 2,
        base_backoff_sec: float = 0.5,
        cache_key: Optional[str] = None
    ) -> Tuple[Any, bool]:
        """
        Executes primary_fn behind breaker protection.
        If circuit is OPEN or retries exhaust due to collapse, falls back to fallback_fn
        or cached state, ensuring zero crash and uninterrupted operation.

        Returns:
            Tuple[Result, was_fallback (bool)]
        """
        breaker = self.get_or_create_breaker(breaker_name)

        if not breaker.allow_execution():
            # Circuit open - trigger immediate self-healing fallback
            return self._invoke_fallback(
                breaker_name=breaker_name,
                fallback_fn=fallback_fn,
                error=RuntimeError(f"Circuit '{breaker_name}' is OPEN due to upstream failure/collapse."),
                cache_key=cache_key
            )

        attempt = 0
        last_exception: Optional[Exception] = None

        while attempt <= retries:
            try:
                result = primary_fn()
                breaker.record_success()
                if cache_key:
                    with self._lock:
                        self._cache[cache_key] = result
                return result, False
            except Exception as e:
                breaker.record_failure()
                last_exception = e
                attempt += 1
                if attempt <= retries:
                    sleep_time = base_backoff_sec * (2 ** (attempt - 1))
                    time.sleep(sleep_time)

        # Retries exhausted - execute self-healing fallback
        return self._invoke_fallback(
            breaker_name=breaker_name,
            fallback_fn=fallback_fn,
            error=last_exception or RuntimeError(f"Operation on '{breaker_name}' failed after retries."),
            cache_key=cache_key
        )

    def _invoke_fallback(
        self,
        breaker_name: str,
        fallback_fn: Optional[Callable[[Exception], Any]],
        error: Exception,
        cache_key: Optional[str]
    ) -> Tuple[Any, bool]:
        if fallback_fn:
            try:
                return fallback_fn(error), True
            except Exception:
                pass

        if cache_key:
            with self._lock:
                if cache_key in self._cache:
                    return self._cache[cache_key], True

        raise error
