"""Monkey-patch undetected_chromedriver.patcher.Patcher.auto() to skip re-download.

The patcher tries to os.unlink + download fresh ChromeDriver on every import.
We override auto() with a no-op that returns True if a working binary exists,
preventing the version mismatch error when Chrome is pinned.
"""
import os


def _patch_auto():
    try:
        import undetected_chromedriver.patcher as p
    except ImportError:
        return  # undetected_chromedriver not installed yet

    original_auto = p.Patcher.auto

    def patched_auto(self, executable_path=None, force=False, version_main=None, _=None):
        # If binary already exists and is patched, skip download entirely
        if os.path.isfile(self.executable_path) and self.is_binary_patched(self.executable_path):
            return True
        return original_auto(self, executable_path, force, version_main, _)

    p.Patcher.auto = patched_auto


_patch_auto()
