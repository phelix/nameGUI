import sys
sys.path.append("..")
sys.path.append("../lib")

import traceback
import lineperdic
import mylogging

import shared
import util

import time
import sys
sys.path.append("../namerpc")
import namerpc

import time
import threading

import json

# errors from namerpc for fine grained user info
NameDoesNotExistError = namerpc.NameDoesNotExistError
RpcError = namerpc.RpcError
RpcConnectionError = namerpc.RpcConnectionError
ClientError = namerpc.ClientError
clientErrorClasses = namerpc.clientErrorClasses

class NameDoesNotExistInWalletError(NameDoesNotExistError):
    pass
class NameDoesAlreadyExistError(Exception):
    pass
class WalletUnlockCancelledError(Exception):
    pass

VALIDCHARS = "abcdefghijklmnopqrstuvwxyz1234567890-/"
POLLSECONDS = 3
POLLWAITSECONDS = 0.1
NAMENEWMATURATIONBLOCKS = 12
UNLOCKTIME = 21
WAITFORBLOCKCHAIN = True
LISTNAMEUPDATE = "update: "

nameTemplate = {
        "txid" : None,
        "known" : None,
        "confirmations" : None,
        "expires_in" : None,
        "expired" : None,
        "new" : None,  # only name_new done
        "transferred" : None,
        "queuedFirstUpdate" : None,
        "update" : None,  # name_update pending
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
        self.listSinceBlockPrev = None
        self.isLocked = None

        self.passphrase = None

        self.unlocked = False  # did we unlock the wallet?

        self.unlockNeeded = None

        util.ensure_dirs(shared.CONFFOLDER)
        self.nameNewDb = lineperdic.LPD(shared.NAMENEWDBFILENAMEPATH)

        self.log = shared.get_my_logger(name=__file__)

        datadir = shared.args.namecoindatadir
        # rpc does currently not work asynchronously
        self._rpc = namerpc.CoinRpc(connectionType="client", datadir=datadir)  # poll
        self.rpc = namerpc.CoinRpc(connectionType="client", datadir=datadir)  # other functions

        self._doStop = False
        self._updateNow = False
        self._initialUpdate = True

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
                i = self._rpc.call("getinfo")
                if "unlocked_until" in i:
                    self.isLocked = False if i["unlocked_until"] else True
                else:
                    self.isLocked = False

                self.blockCount = i["blocks"]
                self.balance = i["balance"]
                self.blockchainUptodate = self._rpc.blockchain_is_uptodate()
                if (not self._initialUpdate and i["connections"] and
                    WAITFORBLOCKCHAIN and not self.blockchainUptodate):
                    self.log.debug("waiting for blockchain, ", self.blockCount)
                else:
                    hPrev = None
                    blockHash = self._rpc.call("getblockhash", [self.blockCount])
                    self.listSinceBlock = self._rpc.call("listsinceblock", [blockHash])
                    if (self._updateNow or blockHash != self.blockHashPrev or
                        self.listSinceBlock != self.listSinceBlockPrev):
                        self._update()
                    self.blockHashPrev = blockHash
                    self.listSinceBlockPrev = self.listSinceBlock
                self.connected = True
            except:
                self.log.exception("poll failed:")
                self.connected = False
            #self.log.debug("poll end. connected:", self.connected)
            self.inPoll = False
            self.callback_poll_end()
            time1 = time.time() + POLLSECONDS

            # work on name_firstupdate queue
            try:
                while time.time() < time1:
                    if self.firstUpdateQueue:
                        try:
                            self._name_firstupdate_one()
                        except (namerpc.WalletUnlockNeededError, WalletUnlockCancelledError):
                            self.unlockNeeded = True  # tkinter is not thread safe by default
                        except:
                            self.log.exception("poll: call to name_firstupdate_one failed:")
                    if self._updateNow:
                        break
                    if self._doStop:
                        self.stopped = True
                        return
                    time.sleep(POLLWAITSECONDS)
            except:
                self.log.exception("work on name_firstupdate queue failed:")
    def update(self, blocking=False):
        updateCount0 = self.updateCount
        self._updateNow = True
        if blocking:
            while updateCount0 == self.updateCount:
                time.sleep(0.001)
    def _update(self):
        self._updateNow = False
        self._initialUpdate = False
        self.log.info("_update: cycle: %s" % self.updateCount)
        R = self._rpc.call(method="name_list")
        nameListDic = {}
        for r in R:
            n = nameTemplate.copy()  # shallow
            n.update(r)
            n["new"] = False
            n["known"] = True
            nameListDic[r["name"]] = n

        # previous name_new
        nameNewDic = {}
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
                nameNewDic[name] = n

        # pending name_updates
        nameUpdateDic = {}
        for t in self.listSinceBlock["transactions"]:
            if "name" in t and t["name"].startswith(LISTNAMEUPDATE):  # secure?
                name = t["name"].replace(LISTNAMEUPDATE, "")
                n = nameTemplate.copy()
                n["update"] = True
                nameUpdateDic[name] = n

        # merge
        for name in nameUpdateDic:
            self.log.debug("nameUpdateDic:", name)
        for name in nameNewDic:
            self.log.debug("nameNewDic:", name, nameNewDic[name]["new"], "confirmations:", nameNewDic[name]["confirmations"])
        self.names = {}
        self.names.update(nameListDic)
        self.names.update(nameNewDic)
        self.names.update(nameUpdateDic)

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

                # allow coin to shut down ?
                self._rpc.authServiceProxy._AuthServiceProxy__conn.close()
                self.rpc.authServiceProxy._AuthServiceProxy__conn.close()

                self.log.info("model stopped")
                self.callback_poll_stopped()
                return

    def is_locked(self):
        return self.isLocked

    def check_name_exists(self, name):
        try:
            self.rpc.nm_show(name)
            return True
        except namerpc.NameDoesNotExistError:
            return False

    def name_history(self, name):
        try:
            data = self.rpc.call("name_history", [name])
        except namerpc.WalletError:
            raise NameDoesNotExistError
        assert data["name"] == name
        return data

    def name_show(self, name):
        try:
            data = self.rpc.call("name_show", [name])
        except namerpc.WalletError:
            raise NameDoesNotExistError
        assert data["name"] == name
        return data

    def get_data(self, name):
        """comfort function for a single name name_list"""
        try:
            data = self.call("name_list", [name])[0]
        except (namerpc.WalletError, IndexError):
            raise NameDoesNotExistInWalletError
        assert data["name"] == name
        return data

    def parse_json(self, s):
        v = {}
        try:
            v = json.loads(s)
        except ValueError:
            self.log.debug("parse_json: json decode failed: " + str(s))
            pass
        return v

    def get_value_dict(self, name):
        return self.parse_json(self.get_data(name)['value'])

    def name_new(self, name, valuePostponed=None, guiParent=None):
        """value is safed for a postponed name firstupdate"""
        self.log.info("name_new:", name, valuePostponed)
        if not set(name).issubset(set(VALIDCHARS)):
            raise Exception("Invalid character.")
        if self.check_name_exists(name):
            raise NameDoesAlreadyExistError()
        r = self.call("name_new", [name], guiParent=guiParent)
        self.nameNewDb[name] = {"name_new":{"txid":r[0], "rand":r[1],
                                            "valuePostponed":valuePostponed}}
        self.update()  # non blocking
        self.log.debug("name_new: %s" % r)
        return r

    def name_firstupdate(self, name, value, toAddress=None, guiParent=None, rpc=None):
        self.log.info("name_firstupdate: %s %s %s" % (name, value, toAddress))
        nN = self.names[name]["name_new"]
        params = [name, nN["rand"], nN["txid"], value]
        if toAddress:  # somehow None does not work properly
             params.append(toAddress)
        r = self.call("name_firstupdate", params, guiParent=guiParent, rpc=rpc)
        self.nameNewDb[name]["name_firstupdate"] = r
        self.log.debug("name_firstupdate: %s" % r)
        return r

    def _name_firstupdate_one(self):
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
            r = self.name_firstupdate(name, value, rpc=self._rpc)
            return r

    def name_renew(self, name, guiParent=None):
        self.log.info("name_renew: %s" % name)
        value = str(self.get_data(name)["value"])
        # dirty workaround for empty names
        if value == "":
            value = " "
        r = self.call("name_update", args=[name, value], guiParent=guiParent)
        self.log.debug("name_renew: %s" % r)
        return r

    def name_configure(self, name, value, guiParent=None):
        self.log.info("name_configure: %s %s" % (name, value))
        r = self.call("name_update", [name, value], guiParent=guiParent)
        self.log.debug("name_configure: %s" % r)
        return r

    def name_transfer(self, name, value=None, address=None, guiParent=None):
        self.log.info("name_transfer:",name, value, address)
        assert address
        if value == None:
            value = self.get_data(name)["value"]
        r = self.call("name_update", [name, value, address], guiParent=guiParent)
        self.log.debug("name_transfer: %s" % r)
        return r

    def validate_address(self, address):
        r = self.rpc.call("validateaddress", [address])
        return r["isvalid"]

    def blockchain_is_uptodate(self):
        return self.blockchainUptodate

    def call(self, method, args=[], guiParent=None, rpc=None):
        """will try to unlock the wallet if necessary"""
        if not rpc:
            rpc = self.rpc
        self.log.debug("call: method", method, "args:", args)
        try:
            return rpc.call(method, args)
        except (namerpc.WalletUnlockNeededError):
            self.log.debug("call: unlock necessary")
            self.unlock(rpc, guiParent=guiParent)
            return rpc.call(method, args)

    def unlock(self, rpc=None, passphrase=None, guiParent=None):
        if rpc == None:
            rpc = self.rpc
        if passphrase == None:
            passphrase = self.passphrase
        while 1:
            if passphrase == None and guiParent:
                self.log.info("unlock: about to get_passphrase...")
                passphrase = self.get_passphrase(guiParent)
            if not passphrase or not type(passphrase) in [str, unicode]:
                self.log.info("unlocking wallet... cancelled - no valid passphrase")
                raise WalletUnlockCancelledError
            try:
                self.log.info("unlocking wallet...")
                self.unlocked = True
                rpc.call("walletpassphrase", [passphrase, UNLOCKTIME])
                self.log.debug("unlock: passphrase is correct")
                self.passphrase = passphrase
                self.unlockNeeded = False
            except namerpc.WalletAlreadyUnlockedError:
                self.log.debug("unlock: wallet already unlocked")
                self.unlocked = False
            except namerpc.WalletPassphraseIncorrectError:
                passphrase = None
                self.passphrase = None
                self.unlocked = False
                self.log.info("unlock: wrong passphrase")
                continue
            break

    def lock(self):
        self.rpc.call("walletlock")  # throws no error if client already locked

    def get_passphrase(self, guiParent=None):
        self.log.info("get_passphrase: this function is a hook to be replaced. " +
                      "It should return the passphrase or None to cancel.")
        return None

class TestModel(object):
    @classmethod
    def setup_class(cls):
        cls.m = Model()
        import pytest
        cls.pytest = pytest
    @classmethod
    def teardown_class(cls):
        cls.m.stop()
    def test_model_call(self):
        assert self.m.call('getblockhash', [1984]) == '00000000003535a16c585a76c25ce9201edd6bf4d52fbf05efa30d5971f23c67'
        assert 'version' in self.m.call('getinfo')
    def test_model_validate_address(self):
        assert self.m.validate_address('MwLm9TPCmk8JxwX8ysGGAp2nc4D8T5cKpW')
        assert not self.m.validate_address('asdf')
    def test_name_new_exists(self):
        with self.pytest.raises(NameDoesAlreadyExistError):
            self.m.name_new('d/namecoin')
    def test_parse_json(self):
        assert self.m.parse_json('asdf') == {}
        assert self.m.parse_json('{"a":1}') == {"a":1}

if __name__ == "__main__":
    import utest
    utest.run(__file__)

    if 0:
        model = Model()
        try:
            while 1:
                pass
        except:
            model.stop()
