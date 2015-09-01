import conf
import sys
sys.path.append("lib")
import platformdep
import logging

args = conf.get_args()  # configuration dictionary

appName = "nameGUI"
CONFFOLDER = args.datadir if args.datadir else platformdep.get_conf_dir(appName.lower())

LOGFILENAME = "logfile.txt"
LOGFILENAMEPATH = CONFFOLDER + "/" + LOGFILENAME
LOGLEVELCONSOLE = logging.DEBUG
LOGLEVELFILE = logging.DEBUG

NAMENEWDBFILENAME = "nameNewDb.txt"
NAMENEWDBFILENAMEPATH = CONFFOLDER + "/" + NAMENEWDBFILENAME
