from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock


def percentile(values: list[float], percent: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((percent / 100) * (len(ordered) - 1))))
    return round(ordered[index], 2)


@dataclass
class MetricsRecorder:
    request_count: int = 0
    error_count: int = 0
    data_load_failure_count: int = 0
    request_latencies_ms: list[float] = field(default_factory=list)
    score_latencies_ms: list[float] = field(default_factory=list)
    _lock: Lock = field(default_factory=Lock)

    def record_request(self, latency_ms: float, status_code: int) -> None:
        with self._lock:
            self.request_count += 1
            if status_code >= 500:
                self.error_count += 1
            self.request_latencies_ms.append(round(latency_ms, 2))

    def record_exception(self, latency_ms: float) -> None:
        with self._lock:
            self.request_count += 1
            self.error_count += 1
            self.request_latencies_ms.append(round(latency_ms, 2))

    def record_score(self, latency_ms: float) -> None:
        with self._lock:
            self.score_latencies_ms.append(round(latency_ms, 2))

    def record_data_load_failure(self) -> None:
        with self._lock:
            self.data_load_failure_count += 1

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            request_latencies = list(self.request_latencies_ms)
            score_latencies = list(self.score_latencies_ms)
            return {
                "request_count": self.request_count,
                "error_count": self.error_count,
                "data_load_failure_count": self.data_load_failure_count,
                "request_latency_ms": {
                    "count": len(request_latencies),
                    "avg": round(sum(request_latencies) / len(request_latencies), 2) if request_latencies else 0.0,
                    "p95": percentile(request_latencies, 95),
                },
                "score_latency_ms": {
                    "count": len(score_latencies),
                    "avg": round(sum(score_latencies) / len(score_latencies), 2) if score_latencies else 0.0,
                    "p95": percentile(score_latencies, 95),
                },
            }

    def reset(self) -> None:
        with self._lock:
            self.request_count = 0
            self.error_count = 0
            self.data_load_failure_count = 0
            self.request_latencies_ms.clear()
            self.score_latencies_ms.clear()


metrics = MetricsRecorder()
