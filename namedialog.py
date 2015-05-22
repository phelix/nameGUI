import sys
sys.path.append("lib")

import ttkinter as tk

import tkSimpleDialog
import tkMessageBox

import json

# workaround to ttk style tkSimpleDialog
# todo: make this more general (list of widget names from tk?)
for s in ["Toplevel", "Button", "Label"]:
    tkSimpleDialog.__dict__[s] = tk.__dict__[s]

class NameDialog(tkSimpleDialog.Dialog):
    def __init__(self, parent, name, title):
        self.name = name
        tkSimpleDialog.Dialog.__init__(self, parent, title=title)
    def config(self, master):
        frame = tk.Frame(master)
        tk.Label(frame, justify="left", text="Name:").grd(row=10, column=10)
        tk.Label(frame, justify="left", text=self.name).grd(row=10, column=20)

        self.notebook = tk.Notebook(frame)
        self.page1 = tk.Frame(self.notebook); # first page
        self.page2 = tk.Frame(self.notebook); # second page
        self.notebook.add(self.page1, text='Custom Configuration')
        self.notebook.add(self.page2, text='Two')
        self.notebook.grd(column=10, columnspan=20)

        tk.Label(self.page1, justify="left", text="Value:").grd(row=30, column=10)
        self.valueEntry = tk.Entry(self.page1).grd(row=30, column=20)
        #self.valueEntry.insert(0, "d/")
        tk.Label(self.page1, justify="left", text="Value:").grd(row=30, column=10)

        tk.Label(self.page1, justify="left", text="Valid JSON:").grd(row=40, column=10)
        self.validJsonLabel = tk.Label(self.page1, justify="left", text="...").grd(row=40, column=20)

        self.valueEntry.bind("<FocusIn>", self.check_json)
        self.valueEntry.bind("<FocusOut>", self.check_json)
        self.valueEntry.bind("<KeyRelease>", self.check_json)
        self.valueEntry.bind("<<menu_modified>>", self.check_json)  # copy / paste

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
        return self.valueEntry  # initial focus

##    def buttonbox(self):
##        '''override standard button box.'''
##        pass

    def validate(self):
        return 1
        #print "validate:", self.valueEntry.get()
    # hook

    def apply(self):
        '''This method is called automatically to process the data,
        *after* the dialog is destroyed.'''
        print "apply"
        self.value = self.valueEntry.get()
        pass

class NameNewDialog(NameDialog):
    def __init__(self, parent, name):
        self.value = None
        NameDialog.__init__(self, parent, name, "New Name")
    def body(self, master):
        tk.Label(master, justify="left", text="About to register:").grd()
        self.config(master).grd()
        tk.Label(master, justify="left", text=
        "This will issue both a name_new and a postponed\n" +
        "name_firstupdate. Let the program and client\n" +
        "run for three hours to ensure the process can finish.").grd()
        return self.valueEntry

class NameConfigureDialog(NameDialog):
    def __init__(self, parent, name):
        self.value = None
        NameDialog.__init__(self, parent, name, "Configure Name")

class NameTransferDialog(NameDialog):
    def __init__(self, parent, name, validate_address_callback):
        self.result = None  # only for readybility, is also in parent class
        self.targetAddress = None
        self.validate_address_callback = validate_address_callback
        NameDialog.__init__(self, parent, name, "Transfer Name")
    def body(self, master):
        tk.Label(master, justify="left", text="About to TRANSFER:").grd()
        self.config(master).grd(columnspan=100)
        tk.Label(master, justify="left", text="Target Namecoin address:").grd(row=100)
        self.targetAddressEntry = tk.Entry(master, justify="left",
                                           text="Target Namecoin address:").grd(row=100, column=20)
        return self.targetAddressEntry

    def validate(self):
        if not self.validate_address_callback(self.targetAddressEntry.get()):
            tkMessageBox.showerror('Error', "Invalid target address.")
            self.targetAddressEntry.focus()
            return 0
        return 1

    def apply(self):
        self.result = (self.valueEntry.get(), self.targetAddressEntry.get())

# obsolete ?
class MessageDialog(tkSimpleDialog.Dialog):
    def __init__(self, parent, title=None, msg="test"):
        self.msg = msg
        tkSimpleDialog.Dialog.__init__(self, parent, title)
    def body(self, master):
        tk.Label(master, text=self.msg).pack()
    def buttonbox(self):
        box = tk.Frame(self)
        w = tk.Button(box, text="OK", width=10, command=self.ok, default=tk.ACTIVE)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        self.bind("<Return>", self.ok)  # what happens with cancel focussed?
        self.bind("<Escape>", self.ok)
        box.pack()

if __name__ == "__main__":
    def validate_address_callback(s):
        if s == "ok":
            return 1
        return 0
    def onClickNew():
        print "NameNewDialog:", NameNewDialog(root, "d/dummyname").result
    def onClickConfigure():
        print "NameConfigureDialog:", NameConfigureDialog(root, "d/dummyname").result
    def onClickTransfer():
        print "NameTransferDialog:", NameTransferDialog(root, "d/dummyname",
                                                        validate_address_callback).result

    root = tk.Tk()
    mainLabel = tk.Label(root, text='Example for pop up input box')
    mainLabel.pack()
    mainButton = tk.Button(root, text='new', command=onClickNew)
    mainButton.pack()
    mainButton = tk.Button(root, text='configure', command=onClickConfigure)
    mainButton.pack()
    mainButton = tk.Button(root, text='transfer', command=onClickTransfer)
    mainButton.pack()
    root.mainloop()
