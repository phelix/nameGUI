import sys
sys.path.append("lib")

import traceback
import lineperdic
import mylogging

import shared

nameNewDbFilename = "nameNewDb.txt"

VALIDCHARS = "abcdefghijklmnopqrstuvwxyz1234567890-/"
POLLSECONDS = 3
POLLWAITSECONDS = 0.1
NAMENEWMATURATIONBLOCKS = 12

class NameDoesNotExistError(Exception):
    pass
class NameDoesAlreadyExistError(Exception):
    pass

import time
import sys
sys.path.append("../namerpc")
import namerpc

import time
import threading

nameTemplate = {
        "txid" : None,
        "known" : None,
        "confirmations" : None,
        "expires_in" : None,
        "expired" : None,
        "new" : None,  # only name_new done
        "transferred" : None,
        "queuedFirstUpdate" : None
    }

class Model(object):
    def __init__(self):
        self.names = {}
        self.connected = False
        self.blockchainUptodate = False
        self.inPoll = False
        self.stopped = False
        self.blockCount = None
        self.balance = -1
        self.firstUpdateQueue = []
        self.updateCount = 0
        self.blockHashPrev = None
        self.isLocked = None

        self.nameNewDb = lineperdic.LPD(nameNewDbFilename)

        self.log = mylogging.getMyLogger(name="model", levelConsole=shared.LOGLEVELCONSOLE,
                                         filename=shared.LOGFILE, levelFile=shared.LOGLEVELFILE)

        # rpc does currently not work asynchronously
        self._rpc = namerpc.CoinRpc(connectionType="client")  # poll
        self.rpc = namerpc.CoinRpc(connectionType="client")  # other functions

        self._doStop = False
        self._updateNow = False

        self._pollThread = threading.Thread(target=self._poll)
        self.log.info("model poll start ----------------------------------")
        self._pollThread.start()

    def callback_poll_start(self):
        """hook"""
        pass
    def callback_poll_end(self):
        """hook"""
        pass
    def callback_poll_stopped(self):
        """hook"""
        pass

    def _poll(self):
        while 1:
            try:
                self.inPoll = True
                self.callback_poll_start()
                #self.log.trace("poll start")
                self.isLocked = self._rpc.is_locked()
                self.blockchainUptodate = self._rpc.blockchain_is_uptodate()
                if not self.blockchainUptodate:
                    self.log.debug("waiting for blockchain, ", self._rpc.call("getblockcount"))
                else:
                    hPrev = None
                    self.blockCount = self._rpc.call("getblockcount")
                    blockHash = self._rpc.call("getblockhash", [self.blockCount])
                    if self._updateNow or blockHash != self.blockHashPrev:
                        self._update()
                    self.blockHashPrev = blockHash
                    self.balance = self._rpc.call("getbalance")
                self.connected = True
            except:
                self.log.exception("poll failed:")
                self.connected = False
            #self.log.debug("poll end. connected:", self.connected)
            self.inPoll = False
            self.callback_poll_end()
            time1 = time.time() + POLLSECONDS
            while time.time() < time1:
                if self.firstUpdateQueue:
                    try:
                        self.name_firstupdate_one()
                    except:
                        self.log.exception("poll: call to name_firstupdate_one failed:")
                else:
                    time.sleep(POLLWAITSECONDS)
                if self._updateNow:
                    break
                if self._doStop:
                    self.stopped = True
                    return
    def update(self, blocking=False):
        updateCount0 = self.updateCount
        self._updateNow = True
        if blocking:
            while updateCount0 == self.updateCount:
                time.sleep(0.001)
    def _update(self):
        self._updateNow = False
        self.log.info("_update: cycle: %s" % self.updateCount)
        R = self._rpc.call(method="name_list")
        nameListDic = {}
        for r in R:
            n = nameTemplate.copy()  # shallow
            n.update(r)
            n["new"] = False
            n["known"] = True
            nameListDic[r["name"]] = n
        nameNewDic = {}

        # previous name_new
        for name in self.nameNewDb:
            if not name in nameListDic:
                n = nameTemplate.copy()  # shallow
                n.update(self.nameNewDb[name])  # rand, txid
                n["new"] = True
                try:
                    r = self._rpc.call("gettransaction", [self.nameNewDb[name]["name_new"]["txid"]])
                    n["known"] = True
                    n["confirmations"] = r["confirmations"]
                    if (not "name_firstupdate" in self.nameNewDb[name] and
                        n["confirmations"] >= NAMENEWMATURATIONBLOCKS and
                        not name in self.firstUpdateQueue):
                        self.firstUpdateQueue.append(name)
                except namerpc.InvalidAddressOrKeyError:
                    n["known"] = False
                nameListDic[name] = n

        # merge
        for name in nameNewDic:
            self.log.debug(name, nameNewDic[name]["new"], "confirmations:", nameNewDic[n]["confirmations"])
        self.names = {}
        self.names.update(nameListDic)
        self.names.update(nameNewDic)

        # in firstupdate queue?
        for name in self.names:
            self.names[name]["queuedFirstUpdate"] = False
            if name in self.firstUpdateQueue:
                self.names[name]["queuedFirstUpdate"] = True

        self.updateCount += 1

    def stop(self):
        self._doStop = True
        for i in range(100):
            time.sleep(0.1)
            if self.stopped:
                self.log.info("model stopped")
                self.callback_poll_stopped()
                return

    def check_name_exists(self, name):
        try:
            self.rpc.nm_show(name)
            return True
        except namerpc.NameDoesNotExistError:
            return False

    def get_data(self, name):
        """comfort function for a single name name_list"""
        data = self.rpc.call("name_list", [name])[0]
        assert data["name"] == name
        return data

    def name_new(self, name, valuePostponed=None):
        """value is safed for a postponed name firstupdate"""
        self.log.info("name_new:", name, valuePostponed)
        if not set(name).issubset(set(VALIDCHARS)):
            raise Exception("Invalid character.")
        if self.check_name_exists(name):
            raise NameDoesAlreadyExistError()
        r = self.rpc.call("name_new", [name])
        self.nameNewDb[name] = {"name_new":{"txid":r[0], "rand":r[1],
                                            "valuePostponed":valuePostponed}}
        self.update()  # non blocking
        self.log.debug("name_new: %s" % r)
        return r

    def name_firstupdate(self, name, value, toAddress=None):
        self.log.info("name_firstupdate: %s %s %s" % (name, value, toAddress))
        nN = self.names[name]["name_new"]
        print "value: %s." % value
        params = [name, nN["rand"], nN["txid"], value]
        if toAddress:  # somehow None does not work properly
             params.append(toAddress)
        r = self.rpc.call("name_firstupdate", params)
        self.nameNewDb[name]["name_firstupdate"] = r
        self.log.debug("name_firstupdate: %s" % r)
        return r

    def name_firstupdate_one(self):
        while 1:
            if not self.firstUpdateQueue:
                return
            name = self.firstUpdateQueue.pop(0)
            data = self.nameNewDb[name]
            if (not "valuePostponed" in data["name_new"] or
                not data["name_new"]["valuePostponed"]):
                self.log.info("name_firstupdate_one: no postponed " +
                              'value for name "%s" - skipping' % name)
                continue
            value = self.nameNewDb[name]["name_new"]["valuePostponed"]
            r = self.name_firstupdate(name, value)
            return r

    def name_renew(self, name):
        self.log.info("name_renew: %s" % name)
        value = str(self.get_data(name)["value"])
        # dirty workaround for empty names
        if value == "":
            value = " "
        r = self.rpc.call("name_update", [name, value])
        self.log.debug("name_renew: %s" % r)
        return r

    def name_configure(self, name, value):
        self.log.info("name_configure: %s %s" % (name, value))
        r = self.rpc.call("name_update", [name, value])
        self.log.debug("name_configure: %s" % r)
        return r

    def name_transfer(self, name, value=None, address=None):
        self.log.info("name_transfer:",name, value, address)
        assert address
        if value == None:
            value = self.get_data(name)["value"]
        r = self.rpc.call("name_update", [name, value, address])
        self.log.debug("name_transfer: %s" % r)
        return r

    def validate_address(self, address):
        r = self.rpc.call("validateaddress", [address])
        return r["isvalid"]

    def is_locked(self):
        return self.isLocked

    def blockchain_is_uptodate(self):
        return self.blockchainUptodate

if __name__ == "__main__":
    model = Model()
    if 0:
        try:
            while 1:
                pass
        except:
            model.stop()
