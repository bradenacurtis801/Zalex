import platform

__all__ = ["_platform", "document_processor"]

class _platform:
    WINDOWS = platform.system() == "Windows"
    DARWIN = platform.system() == "Darwin"
    LINUX = platform.system() == "Linux"