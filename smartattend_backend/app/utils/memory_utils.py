import os
import gc
import sys

def log_memory_usage(stage: str):
    """
    Logs current RSS memory usage. Forces garbage collection first for accuracy.
    Uses /proc/self/status on Linux (extremely lightweight) and ctypes on Windows.
    """
    gc.collect()
    
    # 1. Try Linux /proc filesystem (Render environment)
    try:
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    mem_kb = float(line.split()[1])
                    print(f"[MEMORY LOG] {stage} -> RSS Memory: {mem_kb / 1024:.2f} MB", flush=True)
                    return
    except Exception:
        pass

    # 2. Try Windows ctypes (Local development)
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            GetProcessMemoryInfo = ctypes.windll.psapi.GetProcessMemoryInfo
            GetCurrentProcess = ctypes.windll.kernel32.GetCurrentProcess
            
            GetCurrentProcess.restype = wintypes.HANDLE
            GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS), wintypes.DWORD]
            GetProcessMemoryInfo.restype = wintypes.BOOL

            counters = PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
            if GetProcessMemoryInfo(GetCurrentProcess(), ctypes.byref(counters), counters.cb):
                mem_mb = counters.WorkingSetSize / 1024 / 1024
                print(f"[MEMORY LOG] {stage} -> RSS Memory: {mem_mb:.2f} MB", flush=True)
                return
        except Exception:
            pass

    # 3. Last resort fallback to psutil if installed
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_mb = process.memory_info().rss / 1024 / 1024
        print(f"[MEMORY LOG] {stage} -> RSS Memory: {mem_mb:.2f} MB", flush=True)
    except Exception:
        print(f"[MEMORY LOG] {stage} -> RSS Memory: [Unable to retrieve]", flush=True)
