# todo
# modify select to use decimal
# move to antpy class
# address reuse is evil
# clipboard stuffing / monitoring

import sys
sys.path.append("../lib")

import namerpc
import decimal

TXFEENMC = decimal.Decimal('0.001')

NAMENEWFEENMC = decimal.Decimal('0.01')
NMCSATOSHIS = 100000000

def to_satoshis(v):
    return int(round(decimal.Decimal(v) * NMCSATOSHIS, 0))
def from_satoshis(v):
    return round(decimal.Decimal(v) / NMCSATOSHIS, 8)

TXFEESATOSHIS = to_satoshis(TXFEENMC)

NameDoesNotExistError = namerpc.NameDoesNotExistError
ClientInInitialDownloadError = namerpc.ClientInInitialDownloadError
WalletInsufficientFundsError = namerpc.WalletInsufficientFundsError

# from pybitcointools
def select(unspent, value):
    value = int(value)
    high = [u for u in unspent if u["satoshis"] >= value]
    high.sort(key=lambda u:u["satoshis"])
    low = [u for u in unspent if u["satoshis"] < value]
    low.sort(key=lambda u:-u["satoshis"])
    if len(high): return [high[0]]
    i, tv = 0, 0
    while tv < value and i < len(low):
        tv += low[i]["satoshis"]
        i += 1
    if tv < value: raise WalletInsufficientFundsError
    return low[:i]

def get_name(vouts):
    names = []    
    for v in vouts:
        try:
            names.append(v["scriptPubKey"]["nameOp"]["name"])
        except KeyError:
            pass
    if len(names) != 1:
        raise IndexError()
    return names[0]

def sum_inputs(tx, rpc_call):
    missing = []
    sumInputs = decimal.Decimal(0)
    for vin in tx["vin"]:
        try:
            pTx = rpc_call("getrawtransaction", [vin["txid"], 1])
            sumInputs += pTx["vout"][vin["vout"]]["value"]            
        except namerpc.InvalidAddressOrKeyError:
            missing.append(vin["txid"])
    return sumInputs, missing

def sum_outputs(tx):
    sumOutputs = decimal.Decimal(0)
    for vout in tx["vout"]:
        sumOutputs += vout["value"]
    return sumOutputs

def calc_fee(tx, rpc_call):
    sumInputs, missingInputs = sum_inputs(tx, rpc_call)
    return (sumInputs - sum_outputs(tx), missingInputs)

def analyze_tx(tx, rpc_call, seller=True):
    D = {"warning":""}
    try:
        D["name"] = get_name(tx["vout"])
    except IndexError:
        raise Exception("Multiple names in offer. Currently not supported.")

    if seller:
        nameData = rpc_call("name_list", [D["name"]])
        if nameData == []:
            raise Exception("Name not in wallet: " + str(D["name"]))

    nameData = rpc_call("name_show", [D["name"]])
    if nameData == []:
        raise Exception("Name is not currently registered.")
    sellerAddress = nameData["address"]
    nameTxid = nameData["txid"]

    # make sure the seller is not tricked into transfering NMC from name address
    if seller:
        nameBalance = rpc_call("getreceivedbyaddress", [nameData["address"], 0])
        if (type(nameBalance) != decimal.Decimal):
            raise Exception("Balance on name address unkown.")
        if nameBalance != decimal.Decimal(0):
            raise Exception("Error: There is a balance on the address holding " +
                            "the name. Currently not supported. The offer creator " +
                            "may not be able to see this.")
    
    fee, missingInputs = calc_fee(tx, rpc_call)
    if not missingInputs or (len(missingInputs) == 1 and nameTxid in missingInputs):
        # no balance on name input (checked by seller)
        if fee < 0:
            raise Exception("Tx fee is negative. !?")
        if fee > NAMENEWFEENMC:  # arbitrary value
            raise Exception("Transaction fee seems to high.")
        if fee < TXFEENMC:
            D["warning"] += "Tx fee is lower than current setting.\n"
    else:
        if seller:
            D["warning"] += "Tx fee unknown. (Not necessarily a problem.)\n"
        else:
            raise Exception("Missing inputs: %d" % len(missingInputs))
    

    D["compensation"] = decimal.Decimal(0)
    i = 0
    for v in tx["vout"]:
        if (len(v["scriptPubKey"]["addresses"]) == 1 and
            v["scriptPubKey"]["addresses"][0] == sellerAddress):
            D["compensation"] += v["value"]
            i += 1
    if i != 1:
        raise Exception("Compensation divided over multiple outputs. Currently not supported.")

    #sumInputs, missing = sum_inputs(tx, rpc)
    #print "(Sum of input values: " + repr(float(sumInputs)) + "NMC)"
    #for m in missing:
        #print "(Missing input: %s)" % m
    return D

if __name__ == "__main__":
    import namerpc
    rpc = namerpc.CoinRpc(connectionType="client")

    txid = rpc.call("name_show", ["d/nx"])["txid"]
    tx = rpc.call("getrawtransaction", [txid, 1])

    analyze_tx(tx, rpc.call, seller=False)
