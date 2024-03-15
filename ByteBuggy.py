#!/usr/bin/env python

# Note: This script runs byteBuggy from within a cloned git repo.
# The script `bin/byteBuggy` is designed to be run after installing (from /usr/sbin), not from the cwd.

from byteBuggy import __main__
__main__.entry_point()

