import sys
sys.path.append("lib")

import ttkinter as tk
import tkMessageBox

import tkSimpleDialog
# workaround to ttk style tkSimpleDialog
# todo: make this more general (list of widget names from tk?)
for s in ["Toplevel", "Button", "Label"]:
    tkSimpleDialog.__dict__[s] = tk.__dict__[s]

import json

import model

class MyModel(model.Model):
    def get_passphrase(self, guiParent=None):
        if not guiParent:
            raise Exception("MyModel:get_passphrase: guiParent must be set")
        return PassphraseDialog(guiParent).passphrase

class PassphraseDialog(tkSimpleDialog.Dialog):
    def __init__(self, parent):
        self.passphrase = None
        tkSimpleDialog.Dialog.__init__(self, parent, title="Walletpassphrase Dialog")
    def body(self, master):
        # todo: give more information to the user about what operation needs unlocking
        tk.Label(master, justify="left", text="Enter the wallet passphrase:\n" +
                 "(Note the passphrase will remain in memory until you close nameGUI.\n" +
                 "Alternatively you can also manually unlock the wallet and retry.)").grd()
        self.entry = tk.Entry(master, width=60, show="*").grd(sticky="ew")
        return self.entry
    def apply(self):
        self.passphrase = self.entry.get()

class NameDialog(tkSimpleDialog.Dialog):
    dialogTitle = "NameDialog"
    def __init__(self, model, parent, name):
        self.model = model
        self.parent = parent
        self.name = name
        tkSimpleDialog.Dialog.__init__(self, parent, title=self.dialogTitle)
    def config(self, master):
        frame = tk.Frame(master)
        tk.Label(frame, justify="left", text="Name:").grd(row=10, column=10)
        tk.Label(frame, justify="left", text=self.name).grd(row=10, column=20)

        self.notebook = tk.Notebook(frame)
        self.page1 = tk.Frame(self.notebook); # first page
        self.page2 = tk.Frame(self.notebook); # second page
        self.notebook.add(self.page1, text='Custom Configuration')
        self.notebook.add(self.page2, text='tbd')
        self.notebook.grd(column=10, columnspan=20)

        tk.Label(self.page1, justify="left", text="Value:").grd(row=30, column=10)
        self.valueEntry = tk.Entry(self.page1).grd(row=30, column=20)
        tk.Label(self.page1, justify="left", text="Value:").grd(row=30, column=10)

        tk.Label(self.page1, justify="left", text="Valid JSON:").grd(row=40, column=10)
        self.validJsonLabel = tk.Label(self.page1, justify="left", text="...").grd(row=40, column=20)

        self.valueEntry.bind("<FocusIn>", self.check_json)
        self.valueEntry.bind("<FocusOut>", self.check_json)
        self.valueEntry.bind("<KeyRelease>", self.check_json)
        self.valueEntry.bind("<<menu_modified>>", self.check_json)  # copy / paste

        self.focus = self.valueEntry

        return frame

    def check_json(self, trash):
        s = self.valueEntry.get()
        try:
            json.loads(s)
            self.validJsonLabel["foreground"] = "black"
            self.validJsonLabel["text"] = "ok"
        except:
            self.validJsonLabel["foreground"] = "red"
            self.validJsonLabel["text"] = "fail"

    def body(self, master):
        self.config(master).grd(row=10, column=10, columnspan=100)
        return self.focus  # set by config

##    def buttonbox(self):
##        '''override standard button box.'''
##        pass

    def validate(self):
        """hook"""
        return 1

    def apply(self):
        '''This method is called automatically to process the data,
        *after* the dialog is destroyed.'''
        self.value = self.valueEntry.get()

class NameNewDialog(NameDialog):
    dialogTitle = "New Name"
    def body(self, master):
        tk.Label(master, justify="left", text="About to register:").grd()
        self.config(master).grd()
        tk.Label(master, justify="left", text=
        "This will issue both a name_new and a postponed\n" +
        "name_firstupdate. Let the program and client\n" +
        "run for three hours to ensure the process can finish.").grd()
        return self.focus
    def apply(self):
        value = self.valueEntry.get()
        r = self.model.name_new(self.name, value, guiParent=self.parent)
        tkMessageBox.showinfo(title="name_new response", message=r)

class NameConfigureDialog(NameDialog):
    windowTitle = "Configure Name"
    def apply(self):
        value = self.valueEntry.get()
        # todo: check if value is the same as the current one?
        r = self.model.name_configure(self.name, value, guiParent=self.parent)
        tkMessageBox.showinfo(title="name_update response", message=r)

class NameTransferDialog(NameDialog):
    windowTitle = "Transfer Name"
    def __init__(self, model, parent, name, validate_address_callback):
        self.targetAddress = None
        self.validate_address_callback = validate_address_callback
        NameDialog.__init__(self, model, parent, name)
    def body(self, master):
        tk.Label(master, justify="left", text="About to TRANSFER:").grd()
        self.config(master).grd(columnspan=100)
        tk.Label(master, justify="left", text="Target Namecoin address:").grd(row=100)
        self.targetAddressEntry = tk.Entry(master, justify="left",
                                           text="Target Namecoin address:"
                                           ).grd(row=100, column=20)
        return self.targetAddressEntry

    def validate(self):
        if not self.validate_address_callback(self.targetAddressEntry.get()):
            tkMessageBox.showerror('Error', "Invalid target address.")
            self.targetAddressEntry.focus()
            return 0
        return 1

    def apply(self):
        value = self.valueEntry.get()
        targetAddress = self.targetAddressEntry.get()

        r = self.model.name_transfer(self.name, value=value,
                                     address=targetAddress, guiParent=self.parent)
        tkMessageBox.showinfo(title="name_update response", message=r)


### obsolete ?
##class MessageDialog(tkSimpleDialog.Dialog):
##    def __init__(self, parent, title=None, msg="test"):
##        self.msg = msg
##        tkSimpleDialog.Dialog.__init__(self, parent, title)
##    def body(self, master):
##        tk.Label(master, text=self.msg).pack()
##    def buttonbox(self):
##        box = tk.Frame(self)
##        w = tk.Button(box, text="OK", width=10, command=self.ok, default=tk.ACTIVE)
##        w.pack(side=tk.LEFT, padx=5, pady=5)
##        self.bind("<Return>", self.ok)  # what happens with cancel focussed?
##        self.bind("<Escape>", self.ok)
##        box.pack()

if __name__ == "__main__":
    root = tk.Tk()
    modelW = MyModel()

    def validate_address_callback(s):
        if s == "ok":
            return 1
        return 0
    def on_click_new():
        print "NameNewDialog:", NameNewDialog(modelW, root, "d/dummyname")
    def on_click_configure():
        print "NameConfigureDialog:", NameConfigureDialog(modelW, root, "d/dummyname")
    def on_click_transfer():
        print "NameTransferDialog:", NameTransferDialog(modelW, root, "d/dummyname",
                                                        validate_address_callback)
    def on_click_unlock():
        print "Unlock Dialog..."
        a = modelW.call("getnewaddress")
        print "new address:", a
        print "privkey for a:", modelW.call("dumpprivkey", [a], guiParent=root)

    def shutdown():
        modelW.stop()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", shutdown)
    mainLabel = tk.Label(root, text='Example for pop up input box')
    mainLabel.pack()
    mainButton = tk.Button(root, text='new', command=on_click_new)
    mainButton.pack()
    mainButton = tk.Button(root, text='configure', command=on_click_configure)
    mainButton.pack()
    mainButton = tk.Button(root, text='transfer', command=on_click_transfer)
    mainButton.pack()

    mainButton = tk.Button(root, text='unlockwallet', command=on_click_unlock)
    mainButton.pack()
    
    root.mainloop()
