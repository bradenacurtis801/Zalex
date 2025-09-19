import sys
import os


def is_compiled() -> bool:
    """Check if the application is running as a compiled executable.

    Returns:
        bool: True if running as compiled executable, False if running as Python script
    """
    # Check multiple indicators of being in a compiled environment
    return (
        getattr(sys, "frozen", False)  # PyInstaller, cx_Freeze
        or hasattr(sys, "_MEIPASS")  # PyInstaller
        or "__compiled__" in globals()  # Nuitka
    )
