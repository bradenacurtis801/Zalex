"""
Constants for application data storage and configuration
"""
import os
import platform
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

def get_database_config() -> Dict[str, Any]:
    """Get database configuration for specified environment"""
    # Import here to avoid circular import
    
    return  {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_pre_ping": True,
            "pool_recycle": 300
        }

