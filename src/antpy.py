"""
# todo
buyer: not enough coins
buyer/seller: blockchain up to date?
remove code/text widget alltogether?

"""

import sys
sys.path.append("..")
sys.path.append("../lib")

import ttkinter as tk
import tkMessageBox

import namedialog
import tkentryplus


import antpycore
import antpyshared
import decimal

import tkSimpleDialog
# workaround to ttk style tkSimpleDialog
# todo: make this more general (list of widget names from tk?)
for s in ["Toplevel", "Button", "Label"]:
    tkSimpleDialog.__dict__[s] = tk.__dict__[s]

import json

class TradeDialog(namedialog.NameDialog):
    def callback_unlock(self):
        pass
    def __init__(self, model, parent, name=None):
        self.model = model
        self.apc = antpycore.AntpyCore(self.rpc_call)
        namedialog.NameDialog.__init__(self, model, parent, name)
    def apply(self):
        pass
    def rpc_call(self, *args, **kwargs):
        kwargs["guiParent"] = self
        return self.model.call(*args, **kwargs)
class CreateOfferDialog(TradeDialog):
    dialogTitle = "Create Offer"
    def body(self, master):
        frame = tk.Frame(master).grd(row=10, column=10, columnspan=100)

        # display name
        tk.Label(frame, justify="left", text="Name:").grd(row=10, column=10)
        tk.Label(frame, justify="left", text=self.name).grd(row=10, column=20)

        # display available NMC        
        tk.Label(frame, justify="left", text="Available balance after fee:").grd(row=20, column=10)
        tk.Label(frame, justify="left", text="%.3f" % self.apc.get_available_balance()
                 ).grd(row=20, column=20)

        # display fee
        tk.Label(frame, justify="left", text="Transaction fee (fixed):").grd(row=25, column=10)
        tk.Label(frame, justify="left", text="%.3f" % antpyshared.TXFEENMC
                 ).grd(row=25, column=20)

        # get bid
        tk.Label(frame, justify="left", text="Offer amount [NMC]:").grd(row=30, column=10)
        self.entryAmount = tkentryplus.EntryPlus(frame).grd(row=30, column=20)

        # button to explicitly generate code
        tk.Button(frame, text="Sign half transaction", command=self.generate
                  ).grd(row=35, column=10)

        tk.Button(frame, text="Copy to clipboard", command=self.copy_to_clipboard
                  ).grd(row=35, column=20)
        
        # code output
        tk.Label(frame, justify="left", text="Offer code:").grd(row=40, column=10, columnspan=20)
        self.textCode = tk.Text(frame, width=80, height=10).grd(row=50, column=10, columnspan=20)

    def copy_to_clipboard(self, event=None):
        try:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(self.D["rawTx"])
        except:
            raise
            raise Exception("Copy to clipboard failed.")

    def generate(self):
        print "entry amount:", self.entryAmount.get()
        self.D = self.apc.create_offer(self.name, decimal.Decimal(self.entryAmount.get()))
        self.textCode.insert(tk.END, self.D["rawTx"])


class AcceptOfferDialog(TradeDialog):
    dialogTitle = "Accept Offer"
    def body(self, master):
        frame = tk.Frame(master).grd(row=10, column=10, columnspan=100)

        tk.Button(frame, text="Paste from clipboard", command=self.paste_from_clipboard
                  ).grd(row=5, column=10)

        # code input
        tk.Label(frame, justify="left", text="Paste code:").grd(row=10, column=10, columnspan=100)
        self.textCode = tk.Text(frame, width=80, height=10).grd(row=20, column=10, columnspan=100)

        tk.Button(frame, text="decode", command=self.decode
                  ).grd(row=25, column=10)

        tk.Button(frame, text="sign", command=self.sign
                  ).grd(row=25, column=20)

        tk.Button(frame, text="broadcast", command=self.broadcast
                  ).grd(row=25, column=30)

        tk.Label(frame, justify="left", text="Name:").grd(row=30, column=10)
        self.labelName = tk.Label(frame, justify="left", text=""
                                     ).grd(row=30, column=20)
        tk.Label(frame, justify="left", text="Offer amount:").grd(row=40, column=10)
        self.labelAmount = tk.Label(frame, justify="left", text=""
                                     ).grd(row=40, column=20)
        tk.Label(frame, justify="left", text="Warning:").grd(row=50, column=10)        
        self.labelWarning = tk.Label(frame, foreground="red", justify="left", text=""
                                     ).grd(row=50, column=20)

    def set_text(self, s):
        self.textCode.delete('1.0', tk.END)
        self.textCode.insert(tk.END, s)

    def paste_from_clipboard(self, event=None):
        try:
            self.set_text(self.parent.clipboard_get())
        except:
            raise Exception("Copy from clipboard failed.")

    def decode(self):        
        self.D = self.apc.seller_decode(self.textCode.get("1.0",'end-1c'))
        self.labelName["text"] = self.D["name"]
        self.labelAmount["text"] = self.D["compensation"]
        self.labelWarning["text"] = self.D["warning"]


    def sign(self):
        self.apc.seller_sign()

    def broadcast(self):
        self.set_text(self.apc.seller_broadcast())

if __name__ == "__main__":
    root = tk.Tk()

    def shutdown():
        root.destroy()

    import namerpc

    myModel = namedialog.MyModel()

    root.protocol("WM_DELETE_WINDOW", shutdown)

    def create():
        CreateOfferDialog(myModel, root, "id/keynes")
    def accept():
        AcceptOfferDialog(myModel, root)

    tk.Button(text="create offer", command=create).pack()
    tk.Button(text="accept offer", command=accept).pack()

    root.mainloop()
