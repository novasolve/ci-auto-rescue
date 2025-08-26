"""
File locking utilities for preventing concurrent Nova runs.
"""

import os
import time
import json
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from datetime import datetime


class NovaLock:
    """Simple file-based lock for preventing concurrent Nova runs."""
    
    def __init__(self, repo_path: Path, timeout: int = 3600):
        """
        Initialize lock manager.
        
        Args:
            repo_path: Repository path to lock
            timeout: Lock timeout in seconds (default: 1 hour)
        """
        self.repo_path = repo_path
        self.timeout = timeout
        self.lock_file = repo_path / ".nova" / "nova.lock"
        self.lock_file.parent.mkdir(exist_ok=True, parents=True)
    
    def _read_lock_info(self) -> Optional[dict]:
        """Read lock file information."""
        if not self.lock_file.exists():
            return None
        
        try:
            with open(self.lock_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # Corrupted lock file
            return None
    
    def _write_lock_info(self) -> None:
        """Write lock file with current process info."""
        lock_info = {
            'pid': os.getpid(),
            'timestamp': datetime.now().isoformat(),
            'hostname': os.environ.get('HOSTNAME', 'unknown')
        }
        
        with open(self.lock_file, 'w') as f:
            json.dump(lock_info, f)
    
    def _is_lock_stale(self, lock_info: dict) -> bool:
        """Check if a lock is stale based on timeout."""
        from nova.tools.datetime_utils import seconds_between, now_utc, to_datetime
        try:
            lock_time = to_datetime(lock_info['timestamp'])
            elapsed = seconds_between(now_utc(), lock_time)
            return elapsed > self.timeout
        except (KeyError, ValueError):
            # Invalid lock info, consider it stale
            return True
    
    def _is_process_alive(self, pid: int) -> bool:
        """Check if a process with given PID is still running."""
        try:
            # Send signal 0 to check if process exists
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    
    def acquire(self, wait: bool = False, wait_timeout: int = 300) -> bool:
        """
        Acquire the lock.
        
        Args:
            wait: Whether to wait for lock to be available
            wait_timeout: Maximum time to wait in seconds
            
        Returns:
            True if lock acquired, False otherwise
        """
        start_time = time.time()
        
        while True:
            lock_info = self._read_lock_info()
            
            if lock_info is None:
                # No lock exists, acquire it
                self._write_lock_info()
                return True
            
            # Check if existing lock is stale
            if self._is_lock_stale(lock_info):
                # Lock is stale, remove and acquire
                self.lock_file.unlink(missing_ok=True)
                self._write_lock_info()
                return True
            
            # Check if process is still alive (only works on same machine)
            pid = lock_info.get('pid', 0)
            if pid and not self._is_process_alive(pid):
                # Process is dead, remove and acquire
                self.lock_file.unlink(missing_ok=True)
                self._write_lock_info()
                return True
            
            # Lock is held by another process
            if not wait:
                return False
            
            # Check if we've exceeded wait timeout
            if time.time() - start_time > wait_timeout:
                return False
            
            # Wait a bit and retry
            time.sleep(5)
    
    def release(self) -> None:
        """Release the lock if we own it."""
        lock_info = self._read_lock_info()
        if lock_info and lock_info.get('pid') == os.getpid():
            self.lock_file.unlink(missing_ok=True)


@contextmanager
def nova_lock(repo_path: Path, timeout: int = 3600, wait: bool = False):
    """
    Context manager for Nova file locking.
    
    Args:
        repo_path: Repository path to lock
        timeout: Lock timeout in seconds
        wait: Whether to wait for lock availability
        
    Yields:
        None if lock acquired
        
    Raises:
        RuntimeError: If lock cannot be acquired
    """
    lock = NovaLock(repo_path, timeout)
    
    try:
        if not lock.acquire(wait=wait):
            lock_info = lock._read_lock_info()
            if lock_info:
                pid = lock_info.get('pid', 'unknown')
                timestamp = lock_info.get('timestamp', 'unknown')
                hostname = lock_info.get('hostname', 'unknown')
                raise RuntimeError(
                    f"Another Nova process is already running on this repository.\n"
                    f"Process ID: {pid} on {hostname}\n"
                    f"Started at: {timestamp}\n"
                    f"Lock file: {lock.lock_file}"
                )
            else:
                raise RuntimeError(f"Could not acquire lock: {lock.lock_file}")
        
        yield
    finally:
        lock.release()
