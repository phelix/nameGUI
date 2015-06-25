import sys
sys.path.append("lib")
import platformdep
import logging

appName = "nameGUI"
CONFFOLDER = platformdep.get_conf_dir(appName.lower())

LOGFILENAME = "logfile.txt"
LOGFILENAMEPATH = CONFFOLDER + "/" + LOGFILENAME
LOGLEVELCONSOLE = logging.DEBUG
LOGLEVELFILE = logging.DEBUG

NAMENEWDBFILENAME = "nameNewDb.txt"
NAMENEWDBFILENAMEPATH = CONFFOLDER + "/" + NAMENEWDBFILENAME