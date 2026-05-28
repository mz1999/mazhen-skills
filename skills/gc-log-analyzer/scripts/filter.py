"""Line filtering system for GC log parsing.

Handles verbose JVM flags that insert noise lines into GC logs.
Based on GCViewer's EXCLUDE_STRINGS approach.
"""


class LineFilter:
    """GCViewer-style line filtering for common -XX:+Print* options."""

    # Lines starting with these prefixes are skipped entirely
    EXCLUDE_STARTS = [
        '[Unloading class ',          # -XX:+TraceClassUnloading
        'Application time:',           # -XX:+PrintGCApplicationConcurrentTime
        'Desired survivor',            # -XX:+PrintTenuringDistribution
        '- age',                       # -XX:+PrintTenuringDistribution
        'AdaptiveSize',                # -XX:+PrintAdaptiveSizePolicy
        'Statistics',                  # -XX:+PrintFLSStatistics=1
        'Total Free Space:',           # -XX:+PrintFLSStatistics=1
        'Max   Chunk Size:',           # -XX:+PrintFLSStatistics=1
        'Number of Blocks:',           # -XX:+PrintFLSStatistics=1
        'GC locker: Trying a full collection because scavenge failed',
        'Uncommitted',                 # Shenandoah
        'Cancelling concurrent GC',    # Shenandoah
        'Cancelling GC',               # Shenandoah
        'Capacity',                    # Shenandoah
        'Periodic GC triggered',       # Shenandoah
        'Immediate Garbage',           # Shenandoah
        'Garbage to be collected',     # Shenandoah
        'Live',                        # Shenandoah
        'Concurrent marking triggered', # Shenandoah
        'Adjusting free threshold',    # Shenandoah
        'Predicted cset threshold',    # Shenandoah
        'Free',                        # Shenandoah
        'Evacuation Reserve',          # Shenandoah
        'Pacer for ',                  # Shenandoah
        '    Using',                   # Shenandoah
        '    Pacer for ',              # Shenandoah
        '    Adaptive CSet Selection', # Shenandoah
        '    Collectable Garbage',     # Shenandoah
        '    Immediate Garbage',       # Shenandoah
        '    Good progress for',       # Shenandoah
        '    Failed to',               # Shenandoah
        '    Cancelling GC',           # Shenandoah
        '/proc/meminfo',               # Apple JVM
        'Heap after GC invocations=',  # -XX:+PrintHeapAtGC
        '{Heap before GC',             # -XX:+PrintHeapAtGC
        '{Heap after GC',              # -XX:+PrintHeapAtGC
        ' class space',                # -XX:+PrintHeapAtGC
        ' Metaspace',                  # -XX:+PrintHeapAtGC
        ' par new generation',         # -XX:+PrintHeapAtGC
        'PSYoungGen',                  # -XX:+PrintHeapAtGC (Parallel)
        'eden space',                  # -XX:+PrintHeapAtGC
        'from space',                  # -XX:+PrintHeapAtGC
        'to   space',                  # -XX:+PrintHeapAtGC
        'the space',                   # -XX:+PrintHeapAtGC
        'PSOldGen',                    # -XX:+PrintHeapAtGC (Parallel)
        'object space',                # -XX:+PrintHeapAtGC
    ]

    # Lines containing these substrings are skipped entirely
    EXCLUDE_CONTAINS = [
        'LOG_FILE',   # log rotation markers
        ', start',    # Shenandoah start markers
    ]

    @classmethod
    def should_skip(cls, line: str) -> bool:
        """Return True if this line should be skipped during parsing."""
        stripped = line.lstrip()
        for prefix in cls.EXCLUDE_STARTS:
            if stripped.startswith(prefix):
                return True
        for contain in cls.EXCLUDE_CONTAINS:
            if contain in line:
                return True
        return False
