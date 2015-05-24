# Copyright (C) 2014 by phelix / blockchained.com
# Copyright (C) 2013 by Daniel Kraft <d@domob.eu>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# todo: read NMControl config files

# todo: proper translation of error codes
# todo: setting an empty value does not work

import base64
import socket
import json
import sys
import os
import platform
import time
import traceback

import locale
encoding = locale.getpreferredencoding().lower()

COINAPP = "namecoin"
DEFAULTCLIENTPORT =  8332
DEFAULTNMCONTROLPORT =  9000
HOST = "127.0.0.1"

CONTYPECLIENT = "client"
CONTYPENMCONTROL = "nmcontrol"

class RpcError(Exception):
    """Server returned error."""
    pass

class RpcConnectionError(Exception):
    """Connection failed."""
    pass

# raised by comfort calls "nm_..."
class NameDoesNotExistError(Exception):
    pass

# create Exception classes for client errors from codes
# with results like this:
# class InvalidAddressError(Exception):
#    code = -4
##    // General application defined errors
##    RPC_MISC_ERROR                  = -1,  // std::exception thrown in command handling
##    RPC_FORBIDDEN_BY_SAFE_MODE      = -2,  // Server is in safe mode, and command is not allowed in safe mode
##    RPC_TYPE_ERROR                  = -3,  // Unexpected type was passed as parameter
##    RPC_INVALID_ADDRESS_OR_KEY      = -5,  // Invalid address or key
##    RPC_OUT_OF_MEMORY               = -7,  // Ran out of memory during operation
##    RPC_INVALID_PARAMETER           = -8,  // Invalid, missing or duplicate parameter
##    RPC_DATABASE_ERROR              = -20, // Database error
##    RPC_DESERIALIZATION_ERROR       = -22, // Error parsing or validating structure in raw format
##    RPC_TRANSACTION_ERROR           = -25, // General error during transaction submission
##    RPC_TRANSACTION_REJECTED        = -26, // Transaction was rejected by network rules
##    RPC_TRANSACTION_ALREADY_IN_CHAIN= -27, // Transaction already in chain
##    // P2P client errors
##    RPC_CLIENT_NOT_CONNECTED        = -9,  // Bitcoin is not connected
##    RPC_CLIENT_IN_INITIAL_DOWNLOAD  = -10, // Still downloading initial blocks
##    // Wallet errors
##    RPC_WALLET_ERROR                = -4,  // Unspecified problem with wallet (key not found etc.)
##    RPC_WALLET_INSUFFICIENT_FUNDS   = -6,  // Not enough funds in wallet or account
##    RPC_WALLET_INVALID_ACCOUNT_NAME = -11, // Invalid account name
##    RPC_WALLET_KEYPOOL_RAN_OUT      = -12, // Keypool ran out, call keypoolrefill first
##    RPC_WALLET_UNLOCK_NEEDED        = -13, // Enter the wallet passphrase with walletpassphrase first
##    RPC_WALLET_PASSPHRASE_INCORRECT = -14, // The wallet passphrase entered was incorrect
##    RPC_WALLET_WRONG_ENC_STATE      = -15, // Command given in wrong wallet encryption state (encrypting an encrypted wallet etc.)
##    RPC_WALLET_ENCRYPTION_FAILED    = -16, // Failed to encrypt the wallet
##    RPC_WALLET_ALREADY_UNLOCKED     = -17, // Wallet is already unlocked

clientErrorCodes = {
    "MiscError" : -1,  # e.g. "there are pending operations on that name"
    "WalletError" : -4,
    "InvalidAddressOrKeyError" : -5,  # also non wallet tx
    "WalletInsufficientFundsError" : -6,
    "InvalidParameterError" : -8,
    "ClientNotConnectedError" : -9,
    "ClientInInitialDownloadError" : -10,
    "WalletUnlockNeededError" : -13,
    "WalletPassphraseIncorrectError" : -14,
    "WalletAlreadyUnlockedError" : -17,
    }

clientErrorClasses = []
for e in clientErrorCodes:
    c = type(e, (Exception,), {"code":clientErrorCodes[e]})  # create class
    globals()[c.__name__] = c  # register in module
    clientErrorClasses.append(c)  # allow for easy access

class CoinRpc(object):
    """connectionType: auto, nmcontrol or client"""
    def __init__(self, connectionType="auto", options=None, datadir=None, timeout=5):
        self.bufsize = 4096
        self.queryid = 1
        self.host = HOST

        self.timeout = timeout  # If set to None the global default will be used.

        self.connectionType = connectionType
        self.datadir = datadir
        if datadir:
            self.datadir = datadir + "/"
        self.options = options
        if options == None:
            self.options = self.get_options()

        if not connectionType in [CONTYPECLIENT, CONTYPENMCONTROL]:
            self._detect_connection()

    def _detect_connection(self):
        options = self.options

        self.connectionType = CONTYPENMCONTROL
        if options == None:
            self.options = self.get_options()
        errorString = ""
        try:
            self.call("help")
            return
        except:
            errorString = traceback.format_exc()

        self.connectionType = CONTYPECLIENT
        if options == None:
            self.options = self.get_options()
        try:
            self.call("help")
        except:
            errorString += "\n\n" + traceback.format_exc()
            raise RpcConnectionError("Auto detect connection failed: " + errorString)

    def call(self, method="getinfo", params=[]):
        data = {"method": method, "params": params, "id": self.queryid}
        if self.connectionType == CONTYPECLIENT:
          resp = self.query_http(json.dumps(data))
        elif self.connectionType == CONTYPENMCONTROL:
          resp = self.query_server(json.dumps(data))
        else:
          assert False
        resp = resp.decode(encoding)
        val = json.loads(resp)

        if self.connectionType != CONTYPENMCONTROL and val["id"] != self.queryid:
            raise Exception("ID mismatch in JSON RPC answer.")
        self.queryid = self.queryid + 1

        if val["error"] is not None:
            if self.connectionType == CONTYPECLIENT:
                for e in clientErrorClasses:
                    if e.code == val["error"]["code"]:
                        #print e.code
                        raise e
            raise RpcError(val)  # attn: different format for client and nmcontrol

        return val["result"]

    def query_http(self, data):
        """Query the server via HTTP. (client)"""
        header = "POST / HTTP/1.1\n"
        header += "User-Agent: coinrpc\n"
        header += "Host: %s\n" % self.host
        header += "Content-Type: application/json\n"
        header += "Content-Length: %d\n" % len (data)
        header += "Accept: application/json\n"
        authstr = "%s:%s" % (self.options["rpcuser"], self.options["rpcpassword"])
        header += "Authorization: Basic %s\n" % base64.b64encode (authstr)

        resp = self.query_server("%s\n%s" % (header, data))
        lines = resp.split("\r\n")
        result = None
        body = False
        for line in lines:
            if line == "" and not body:
                body = True
            elif body:
                if result is not None:
                    raise Exception("Expected a single line in HTTP response.")
                result = line
        return result

    def query_server(self, data):
        """Helper routine sending data to the RPC server and returning the result."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if self.timeout:
                s.settimeout(self.timeout)
            s.connect((self.host, int(self.options["rpcport"])))
            s.sendall(data)
            result = ""
            while True:
                tmp = s.recv(self.bufsize)
                if not tmp:
                  break
                result += tmp
            s.close()
            return result
        except socket.error as exc:
            raise RpcConnectionError("Socket error in RPC connection to " +
                                     "%s: %s" % (str(self.connectionType), str(exc)))

    # after nmcontrol platformDep.py
    def get_conf_folder(self, coin=COINAPP):
        coin = coin.lower()
        if platform.system() == "Darwin":
            return os.path.expanduser("~/Library/Application Support/" + coin.capitalize())
        elif platform.system() == "Windows":
            return os.path.join(os.environ['APPDATA'], coin.capitalize())
        return os.path.expanduser("~/." + coin)

    def get_options(self):
        if self.connectionType == CONTYPECLIENT:
            return self.get_options_client()
        if self.connectionType == CONTYPENMCONTROL:
            return {"rpcport":DEFAULTNMCONTROLPORT}
        return None

    def get_options_client(self):
        """Read options (rpcuser/rpcpassword/rpcport) from .conf file."""
        options = {}
        options["rpcport"] = DEFAULTCLIENTPORT
        if not self.datadir:
            self.datadir = self.get_conf_folder()
        with open(self.datadir + "/" + COINAPP + ".conf") as f:
            while True:
                line = f.readline()
                if line == "":
                    break
                parts = line.split ("=")
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip()
                    options[key] = val
        return options


    # comfort functions
    def is_locked(self):
        try:
            self.call("sendtoaddress", ["", 0.00000001])  # Certainly there is a more elegant way to check for a locked wallet?
        except WalletUnlockNeededError:
            return True
        except (WalletError, InvalidAddressOrKeyError):
            return False

    def chainage(self):
        c = self.call("getblockcount")
        T = 0
        for i in [0, 1, 2]:
            h = self.call("getblockhash", [c - i])
            t = self.call("getblock", [h])["time"]
            T += t + i * 60 * 9  # conservative
        t = T / 3
        return int(round(time.time() - t))

    def blockchain_is_uptodate(self, period=60 * 10 * 10):
        if self.chainage() <= period:
            return True
        else:
            return False

    def nm_show(self, name):
        if self.connectionType == CONTYPENMCONTROL:
            data = self.call("data", ["getData", name])["reply"]
            if data == False:
                raise NameDoesNotExistError()
        else:
            try:
                data = self.call("name_show", [name])
            except WalletError:
                raise NameDoesNotExistError()
        return data

if __name__ == "__main__":

    if len(sys.argv) == 1:
        print "========auto detect"
        rpc = CoinRpc()  # default: connectionType="auto"
        print "detected:", rpc.connectionType

        print "\n\n========NMControl"
        try:
            rpc = CoinRpc(connectionType=CONTYPENMCONTROL)
            print rpc.call("help")["reply"]
            print rpc.nm_show("d/nx")
        except:
            traceback.print_exc()

        print "\n\n========Namecoind"
        rpc = CoinRpc(connectionType=CONTYPECLIENT)
        print rpc.call("getinfo")
        print rpc.nm_show("d/nx")

        print '\n\n========Command line usage examples'
        print 'namerpc.py getinfo'
        print 'namerpc.py name_show d/nx'

    else:
        import pprint
        rpc = CoinRpc()
        if sys.argv[1] == "nm_show":
            pprint.pprint(rpc.nm_show(sys.argv[2]))
        else:
            pprint.pprint(rpc.call(sys.argv[1], sys.argv[2:]))
