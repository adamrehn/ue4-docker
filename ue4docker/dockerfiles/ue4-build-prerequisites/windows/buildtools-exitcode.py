#!/usr/bin/env python3
import sys

# Propagate any exit codes from the VS Build Tools installer except for 3010
code = int(sys.argv[1])
code = 0 if code == 3010 else code
sys.exit(code)
