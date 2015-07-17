# from Nmcontrol

import os
import platform

def get_namecoin_dir():
    if platform.system() == "Darwin":
        return os.path.expanduser("~/Library/Application Support/Namecoin")
    elif platform.system() == "Windows":
        return os.path.join(os.environ['APPDATA'], "Namecoin")
    return os.path.expanduser("~/.namecoin")

def get_conf_dir(appName):
    if platform.system() == "Darwin":  # Mac OS X
        return os.path.expanduser("~/Library/Application Support/" + appName)
    elif platform.system() == "Windows":  # MS Windows
        return os.path.join(os.environ['APPDATA'], appName)

    # Linux
    try:
        s = '/var/lib/' + appName
        st = os.stat(s)
        haspermission = bool(st.st_mode & stat.S_IRGRP)
    except OSError:
        haspermission = False
    if haspermission:
        return s
    else:
        return os.path.expanduser("~/.config/" + appName)
