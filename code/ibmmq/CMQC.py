import sys
import os
import platform

sys.path.insert(0,os.path.dirname(__file__))

_plat=platform.system()
_mach=platform.machine()

# Load a different variant of CMQC for each platform
# The other definition files do not vary by platform.
# If the OS and/or hardware are unrecognised, we end up
# loading the Linux X64 definitions.
if _plat == "Linux":
    if _mach == "x86_64":
        from _CMQC_linux_x64 import *
    elif _mach == "aarch64":
        from _CMQC_linux_arm64 import *
    elif _mach == "s390x":
        from _CMQC_linux_s390x import *
    elif _mach == "ppc64le" or _mach == "ppcle":
        from _CMQC_linux_ppcle import *
    else:
        from _CMQC_linux_x64 import *
elif _plat == "AIX":
    from _CMQC_aix import *
elif _plat == "Darwin":
    from _CMQC_macos import *
elif _plat == "Windows":
    from _CMQC_windows import *
else:
    from _CMQC_linux_x64 import *

