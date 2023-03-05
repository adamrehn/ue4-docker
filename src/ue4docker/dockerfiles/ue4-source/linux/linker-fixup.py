#!/usr/bin/env python3
import glob, os, shutil, sys

# Retrieve the Linux SDK root directory and system ld location from our command-line arguments
sdkRoot = sys.argv[1]
systemLd = sys.argv[2]

# Locate the bundled version(s) of ld and replace them with symlinks to the system ld
for bundled in glob.glob(
    os.path.join(
        sdkRoot, "*", "x86_64-unknown-linux-gnu", "bin", "x86_64-unknown-linux-gnu-ld"
    )
):
    os.unlink(bundled)
    os.symlink(systemLd, bundled)
    print("{} => {}".format(bundled, systemLd), file=sys.stderr)
