import platform

__all__ = ["_platform"]

class _platform:
    WINDOWS = platform.system() == "Windows"
    DARWIN = platform.system() == "Darwin"
    LINUX = platform.system() == "Linux"