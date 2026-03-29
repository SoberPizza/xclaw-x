"""Platform detection — Windows CUDA only."""

import ctypes
from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformInfo:
    system: str           # "Windows"
    arch: str             # "AMD64"
    memory_gb: int
    gpu_backend: str      # "cuda" | "cpu"


def detect_platform() -> PlatformInfo:
    memory_gb = _get_memory_gb()
    gpu_backend = _detect_gpu_backend()

    return PlatformInfo(
        system="Windows",
        arch="AMD64",
        memory_gb=memory_gb,
        gpu_backend=gpu_backend,
    )


def _get_memory_gb() -> int:
    try:
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        mem = MEMORYSTATUSEX()
        mem.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
        return int(mem.ullTotalPhys // (1024 ** 3))
    except Exception:
        return 16


def _detect_gpu_backend() -> str:
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"
