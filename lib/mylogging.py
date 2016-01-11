# -*- coding: utf-8 -*-

# MIT license

from logging import *

def s(*args):
    args2 = []
    for a in args:
        if type(a) == str:
            try:
                a = a.decode("utf-8")
            except:
                a = a.decode("cp1252")
        if type(a) != unicode:
            a = unicode(a)
        args2.append(a)
    s = " ".join(args2)
    return s

# monkey patch to be able to use logging similar to print (plus unicode)
_logOriginal = Logger._log
def _logMy(self, level, msg, args, **kwargs):
    if args:
        msg = s(msg) + " " + s(*args)
        args = ()
    _logOriginal(self, level, msg, args, **kwargs)
Logger._log = _logMy  # instances should be updated, too

def get_logger(name=None, levelConsole=INFO, filename=None, levelFile=DEBUG):
    # create formatter
    formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger = getLogger(name)
    logger.setLevel(DEBUG)  # set max Level to output

    ch = StreamHandler()
    ch.setLevel(levelConsole)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if filename:
        fh = FileHandler(filename)
        fh.setLevel(levelFile)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger

if __name__ == "__main__":
    log = get_logger("test", levelConsole=DEBUG, filename="test.txt")
    log.info("test", 1)
    log.debug("teeeesüst2", u"teäst2b")
