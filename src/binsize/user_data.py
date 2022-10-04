"""
Setting up and creating user-specific directories
for storing configuration and cache files.
"""

from pathlib import Path

import platformdirs

app_name = "binsize"
app_author = "trezor"

config_dir = Path(platformdirs.user_config_dir(app_name, app_author))
cache_dir = Path(platformdirs.user_cache_dir(app_name, app_author))

if not config_dir.exists():
    config_dir.mkdir(parents=True, exist_ok=True)
if not cache_dir.exists():
    cache_dir.mkdir(parents=True, exist_ok=True)
