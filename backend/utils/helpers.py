"""
Utility Helper Functions
"""
import os
from typing import Optional


def ensure_directory(directory: str) -> None:
    """Ensure directory exists, create if not"""
    os.makedirs(directory, exist_ok=True)


def get_file_size(file_path: str) -> Optional[int]:
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except:
        return None


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"
