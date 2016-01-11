import conf
import sys
sys.path.append("lib")
import platformdep
import mylogging

VERSION = "0.3"  # also in setup_script.iss

args = conf.get_args()  # configuration dictionary

appName = "nameGUI"
CONFFOLDER = args.datadir if args.datadir else platformdep.get_conf_dir(appName.lower())

LOGFILENAME = "logfile.txt"
LOGFILENAMEPATH = CONFFOLDER + "/" + LOGFILENAME
LOGLEVELCONSOLE = mylogging.DEBUG
LOGLEVELFILE = mylogging.DEBUG

NAMENEWDBFILENAME = "nameNewDb.txt"
NAMENEWDBFILENAMEPATH = CONFFOLDER + "/" + NAMENEWDBFILENAME

def get_my_logger(name):
    return mylogging.get_logger(name=name, levelConsole=LOGLEVELCONSOLE,
                                            filename=LOGFILENAMEPATH, levelFile=LOGLEVELFILE)
