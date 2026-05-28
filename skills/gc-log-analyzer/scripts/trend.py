"""Heap trend analysis with regression and leak detection.

Uses scipy for regression when available; gracefully degrades otherwise.
"""

import sys
from typing import Dict, List, Optional, Tuple


class HeapTrendAnalyzer:
    """Collects heap usage over time and performs regression analysis."""

    def __init__(self):
        # (timestamp_seconds, heap_after_mb, tenured_after_mb, is_full_gc)
        self.series: List[Tuple[float, float, float, bool]] = []
        self._has_scipy = self._check_scipy()

    @staticmethod
    def _check_scipy() -> bool:
        try:
            import numpy as np  # noqa: F401
            from scipy import stats  # noqa: F401
            return True
        except ImportError:
            return False

    def add_point(self, timestamp: float, heap_mb: float,
                  tenured_mb: float = 0.0, is_full_gc: bool = False):
        """Record a heap usage data point after a GC event."""
        self.series.append((timestamp, heap_mb, tenured_mb, is_full_gc))

    def regression_analysis(self, max_heap_mb: Optional[float] = None) -> Dict:
        """Perform regression analysis on heap usage trend.

        Returns dict with slope, R², leak risk, and optional OOM estimate.
        """
        if len(self.series) < 10:
            return {
                "confidence": "low",
                "samples": len(self.series),
                "trend": "insufficient_data",
            }

        if not self._has_scipy:
            return {
                "confidence": "low",
                "samples": len(self.series),
                "trend": "insufficient_data",
                "note": "numpy/scipy not available; install with: pip3 install numpy scipy",
            }

        import numpy as np
        from scipy import stats

        timestamps = np.array([s[0] for s in self.series])
        heaps = np.array([s[1] for s in self.series])

        slope, intercept, r_value, p_value, std_err = stats.linregress(timestamps, heaps)
        r_squared = r_value ** 2

        # Determine heap capacity for OOM estimation
        if max_heap_mb is None:
            max_heap_mb = max(heaps) * 1.5 if len(heaps) > 0 else 8192

        result = {
            "heap_slope_kbps": round(slope * 1000, 4),   # KB/second
            "r_squared": round(r_squared, 4),
            "p_value": round(p_value, 6),
            "trend": self._classify_trend(slope),
            "leak_risk": self._assess_leak_risk(slope, r_squared),
            "samples": len(self.series),
        }

        if slope > 0:
            oom_hours = self._estimate_oom_hours(slope, intercept, max_heap_mb)
            if oom_hours is not None:
                result["estimated_hours_to_oom"] = oom_hours

        # Full GC regression: evaluate if Full GCs are effectively reclaiming memory
        full_gc_points = [s for s in self.series if s[3]]
        if len(full_gc_points) >= 5:
            fg_timestamps = np.array([s[0] for s in full_gc_points])
            fg_heaps = np.array([s[1] for s in full_gc_points])
            fg_slope, _, fg_r, _, _ = stats.linregress(fg_timestamps, fg_heaps)
            result["post_full_gc_slope_kbps"] = round(fg_slope * 1000, 4)
            result["full_gc_effectiveness"] = (
                "poor" if fg_slope > 0.5 else
                "fair" if fg_slope > 0.1 else
                "good"
            )

        return result

    @staticmethod
    def _classify_trend(slope: float) -> str:
        if slope > 0.1:
            return "growing"
        if slope < -0.1:
            return "shrinking"
        return "stable"

    @staticmethod
    def _assess_leak_risk(slope: float, r_squared: float) -> str:
        if slope > 1.0 and r_squared > 0.7:
            return "high"
        if slope > 0.5 and r_squared > 0.5:
            return "medium"
        if slope > 0.1:
            return "low"
        return "none"

    def _estimate_oom_hours(self, slope: float, intercept: float,
                            max_heap_mb: float) -> Optional[float]:
        """Estimate hours until heap reaches max capacity at current growth rate."""
        if slope <= 0:
            return None
        current = self.series[-1][1] if self.series else intercept
        remaining = max_heap_mb - current
        if remaining <= 0:
            return 0.0
        seconds_to_oom = remaining / slope
        hours = seconds_to_oom / 3600
        return round(hours, 2)


if __name__ == "__main__":
    # Simple self-test
    hta = HeapTrendAnalyzer()
    for i in range(100):
        hta.add_point(i * 60, 100 + i * 0.5, is_full_gc=(i % 10 == 0))
    result = hta.regression_analysis(max_heap_mb=512)
    print(result)
