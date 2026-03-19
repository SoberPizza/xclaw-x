"""Platform detection and capability probing."""

import platform
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformInfo:
    system: str           # "Windows" | "Darwin" | "Linux"
    arch: str             # "arm64" | "x86_64" | "AMD64"
    is_apple_silicon: bool
    memory_gb: int
    gpu_backend: str      # "cuda" | "mps" | "cpu"

    @property
    def supported(self) -> bool:
        if self.system == "Darwin" and self.memory_gb < 16:
            return False
        return True

    @property
    def support_reason(self) -> str:
        if self.system == "Darwin" and self.memory_gb < 16:
            return (
                f"macOS with {self.memory_gb}GB RAM is not supported. "
                f"X-Claw requires at least 16GB on macOS."
            )
        return "OK"


def detect_platform() -> PlatformInfo:
    system = platform.system()
    arch = platform.machine()

    is_apple_silicon = system == "Darwin" and arch == "arm64"
    memory_gb = _get_memory_gb()
    gpu_backend = _detect_gpu_backend(system, is_apple_silicon)

    return PlatformInfo(
        system=system,
        arch=arch,
        is_apple_silicon=is_apple_silicon,
        memory_gb=memory_gb,
        gpu_backend=gpu_backend,
    )


def _get_memory_gb() -> int:
    system = platform.system()
    try:
        if system == "Darwin":
            out = subprocess.check_output(
                ["sysctl", "-n", "hw.memsize"]
            ).decode().strip()
            return int(out) // (1024 ** 3)
        elif system == "Windows":
            import ctypes

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
        pass
    return 16  # conservative default


def _detect_gpu_backend(system: str, is_apple_silicon: bool) -> str:
    if system == "Windows":
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass
    elif system == "Darwin" and is_apple_silicon:
        try:
            import torch
            if torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass
    return "cpu"
