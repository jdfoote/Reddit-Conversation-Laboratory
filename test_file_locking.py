#!/usr/bin/env python3
"""Test script to verify file locking functionality"""

import os
import sys
import subprocess
import tempfile
import fcntl

class FileLock:
    """Context manager for file-based locking to prevent concurrent executions."""
    
    def __init__(self, lockfile_path):
        self.lockfile_path = lockfile_path
        self.lockfile = None
    
    def __enter__(self):
        self.lockfile = open(self.lockfile_path, 'w')
        try:
            # Try to acquire an exclusive lock without blocking
            fcntl.flock(self.lockfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            print(f"Acquired lock: {self.lockfile_path}")
            return self
        except (BlockingIOError, OSError) as e:
            # Another instance is already running
            print(f"Another instance is already running. Lock file: {self.lockfile_path}")
            self.lockfile.close()
            sys.exit(0)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lockfile:
            try:
                fcntl.flock(self.lockfile.fileno(), fcntl.LOCK_UN)
            except (OSError, ValueError):
                # Lock may already be released or file closed
                pass
            finally:
                self.lockfile.close()
                print(f"Released lock: {self.lockfile_path}")


def test_file_lock():
    """Test that FileLock prevents concurrent execution"""
    
    # Create a temporary lock file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.lock') as f:
        lockfile_path = f.name
    
    try:
        print(f"Testing file locking with: {lockfile_path}")
        
        # First lock should succeed
        print("\nTest 1: Acquiring first lock...")
        with FileLock(lockfile_path):
            print("✓ First lock acquired successfully")
            
            # Try to acquire the same lock in a subprocess - should fail/exit
            print("\nTest 2: Trying to acquire lock from subprocess (should exit gracefully)...")
            test_script = f"""
import sys
import fcntl

class FileLock:
    def __init__(self, lockfile_path):
        self.lockfile_path = lockfile_path
        self.lockfile = None
    
    def __enter__(self):
        self.lockfile = open(self.lockfile_path, 'w')
        try:
            fcntl.flock(self.lockfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            print(f"ERROR: Second lock should not have been acquired!")
            return self
        except (BlockingIOError, OSError) as e:
            print("✓ Second lock correctly prevented (subprocess exiting with 0)")
            self.lockfile.close()
            sys.exit(0)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lockfile:
            try:
                fcntl.flock(self.lockfile.fileno(), fcntl.LOCK_UN)
            except (OSError, ValueError):
                pass
            finally:
                self.lockfile.close()

try:
    with FileLock('{lockfile_path}'):
        pass
except SystemExit:
    raise
"""
            result = subprocess.run(
                [sys.executable, '-c', test_script],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and "Second lock correctly prevented" in result.stdout:
                print("✓ Concurrent lock acquisition correctly prevented")
            else:
                print(f"✗ Test failed!")
                print(f"  Return code: {result.returncode}")
                print(f"  Stdout: {result.stdout}")
                print(f"  Stderr: {result.stderr}")
                return False
            
        print("✓ First lock released")
        
        # After releasing the first lock, second lock should succeed
        print("\nTest 3: Acquiring lock after release (should succeed)...")
        with FileLock(lockfile_path):
            print("✓ Lock acquired successfully after release")
        
        print("\n" + "="*60)
        print("✓ All file locking tests passed!")
        print("="*60)
        return True
        
    finally:
        # Clean up the lock file
        if os.path.exists(lockfile_path):
            os.remove(lockfile_path)
            print(f"\nCleaned up: {lockfile_path}")


# Run the test
if __name__ == '__main__':
    if test_file_lock():
        sys.exit(0)
    else:
        sys.exit(1)

