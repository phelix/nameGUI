
#         tk.Frame.columnconfigure(10, minsize=minColumnWidth)

import sys
sys.path.append("lib")

import splashscreen
import os

favicon = None
#favicon = "gfx/favicon.gif"  # somebody try this on linux / mac
if os.name == "nt":
    favicon = "gfx/favicon.ico"
splashscreen.splash("gfx/splash.gif", favicon=favicon)

import ttkinter as tk

import tkMessageBox
import namedialog

import model

import time
import traceback

import mylogging
import shared

log = mylogging.getMyLogger(name="gui", levelConsole=shared.LOGLEVELCONSOLE,
                            filename=shared.LOGFILENAMEPATH, levelFile=shared.LOGLEVELFILE)

class SelectionEmptyError(Exception):
    pass

class Gui(object):
    def __init__(self):
        log.info("__init__ #########################################################")
        self.root = tk.Tk()

##        # logo - transparent logo is more complicated
##        image = tk.PhotoImage(file="namecoin_gui_g.gif")
##        canvas = tk.Canvas(self.root, width=image.width() + 10,
##                           height=image.height() + 10).grd(column=10)
##        canvas.create_image((5,5), anchor="nw", image=image)
##        canvas.image = image  # keep reference

        tk.Label(self.root, justify="left", text="Connected:").grd(row=10, column=10)
        self.labelConnected = tk.Label(self.root, justify="left", text="...").grd(row=10, column=20)

        tk.Label(self.root, justify="left", text="Model RPC update:").grd(row=15, column=10)
        self.labelModelUpdating = tk.Label(self.root, justify="left", text="...").grd(row=15, column=20)

        # remove as it is not so precise?
        tk.Label(self.root, justify="left", text="Blockchain is up to date:").grd(row=17, column=10)
        self.labelBlockchainIsUpToDate = tk.Label(self.root, justify="left", text="...").grd(row=17,column=20)

        tk.Label(self.root, justify="left", text="Block height:").grd(row=20, column=10)
        self.labelBlockCount = tk.Label(self.root, justify="left", text="...").grd(row=20,column=20)

        tk.Label(self.root, justify="left", text="Wallet locked:").grd(row=23, column=10)
        self.labelWalletLocked = tk.Label(self.root, justify="left", text="...").grd(row=23,column=20)

        tk.Label(self.root, justify="left", text="Balance:").grd(row=25, column=10)
        self.labelBalance = tk.Label(self.root, justify="left", text="...").grd(row=25,column=20)

        tk.Label(self.root, justify="left", text="New name:").grd(row=30, column=10)
        self.newEntry = tk.Entry(self.root).grd(row=30, column=20)
        self.newEntry.insert(0, "d/")
        self.newEntry.bind("<Return>", self.name_new)
        nameNewButton = tk.Button(self.root, text="register", command=self.name_new).grd(row=30, column=30)
        #nameNewButton = tk.Button(self.root, text="quit", command=self.shutdown).grd()

        # table
        self.tv = tk.Treeview(self.root).grd(row=40, column=10, columnspan=100)
        self.tv["selectmode"] = "browse"  # only allow to select a single item
        self.tv["columns"] = ("name", "value", "address", "status", "expires_in")
        self.tv['show'] = 'headings'  # hide identifier and +
        ysb = tk.Scrollbar(self.root, orient='vertical', command=self.tv.yview).grd(
            row=40, column=110, sticky="ns")
        #xsb = ttk.Scrollbar(self, orient='horizontal', command=self.t.xview)
        self.tv.configure(yscroll=ysb.set) #, xscroll=xsb.set)
        for c in self.tv["columns"]:
            self.tv.heading(c, text=c.capitalize(), anchor="w")

        # mouse wheel scrolling for table
        self.root.bind("<MouseWheel>", self.on_scroll_event)  # Windows
        self.root.bind("<Button-4>", self.on_scroll_event) # Linux A
        self.root.bind("<Button-5>", self.on_scroll_event) # Linux B

        # buttons
        renewButton = tk.Button(self.root, text="renew", command=self.renew
                                ).grd(row=50, column=10)
        configureButton = tk.Button(self.root, text="configure value",
                                    command=self.configure).grd(row=50, column=20)
        transferButton = tk.Button(self.root, text="transfer name",
                                   command=self.transfer).grd(row=50, column=30)

        self.model = model.Model()
        self.model.callback_poll_start = self._model_callback_poll_start
        self.model.callback_poll_end = self._model_callback_poll_end

        # update loop
        self.root.after(300, func=self.set_info)

        self.stopping = False

        # set up window
        self.root.report_callback_exception = self.show_error
        self.root.title("nameGUI - Namecoin RPC Frontend")
        self.root.wm_iconbitmap(bitmap=favicon, default=favicon)
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)
        self.root.focus_force()
        self.root.mainloop()

    def show_error(self, *args):
        err = traceback.format_exception(*args)
        tkMessageBox.showerror('Exception', err)

    def shutdown(self):
        log.info("shutdown")
        self.model.stop()
        #time.sleep(2)
        self.root.destroy()

    def on_scroll_event(self, event):
        """mouse wheel scrolling"""
        direction = 1
        if event.delta > 0:
            direction = -1
        self.tv.yview("scroll", direction, "units")
        return("break")

    def get_selection(self):
        s = self.tv.selection()
        if not s:  # nothing selected
            raise SelectionEmptyError
        if type(s) == tuple:
            s = s[0]
        return s

    def set_info(self):
        name = None
        data = None
        try:
            # can't call rpc functions here, causes rpc id mismatches --> model
            self.labelConnected["text"] = "yes" if self.model.connected else "no"
            self.labelBlockCount["text"] = self.model.blockCount
            self.labelBalance["text"] = "%.6f" % self.model.balance
            self.labelBlockchainIsUpToDate["text"] = "yes" if self.model.blockchain_is_uptodate() else "no"
            self.labelWalletLocked["text"] = "yes" if self.model.is_locked() else "no"

            # remove non existing items - maybe not necessary as names should never disappear?
            items = self.tv.get_children()  # used again below
            for item in items:
                if not item in self.model.names:
                    self.tv.delete(item)

            # todo: only update changed data
            for name in self.model.names:
                #print n, self.model.names[n]
                data = self.model.names[name]

                # make sure all names are listed
                if not name in items:
                    self.tv.insert('', "end", name)
                    #self.tv.insert(name, 'end', text=data["value"])  # fill tab

                # set data
                for col in self.tv["columns"]:
                    try:
                        if col == "name":
                            s = name  # name for name_new is not known by client
                            if "name" in data:
                                assert data["name"] == name
                        elif col == "value":
                            if "value" in data:
                                s = data["value"]
                            else:
                                valuePostponed = self.model.names[name]["name_new"]["valuePostponed"]
                                if valuePostponed != None:
                                    s = "(postponed:) " + valuePostponed
                        elif col == "status":
                            # todo: several separate status fields
                            s = ""
                            if not data["known"]:
                                s += "unknown "
                            if data["new"]:
                                s += "pending " + "(" + str(data["confirmations"]) + ") "
                            if data["transferred"]:
                                s += "transferred "  # todo: to address
                            if data["expired"]:
                                s += "expired "
                            if not s:
                                s = "ok"
                        else:
                            s = data[col]
                    except KeyError:
                        s = "---"
                    except:
                        # !!!
                        s = "-!-"
                        log.exception("set_info: error setting columns")
                    self.tv.set(name, col, s)
        except:
            log.exception("set_info: error. name: %s data: %s" % (name, data))

        if not self.stopping:
            self.root.after(1000, func=self.set_info)

    def _model_callback_poll_start(self):
        # careful, tkinter is not thread safe by default
        self.labelModelUpdating["text"] = "working..."
        #self.root.update_idletasks()
    def _model_callback_poll_end(self):
        # careful, tkinter is not thread safe by default
        self.labelModelUpdating["text"] = "waiting"
        #self.root.update_idletasks()

    def renew(self):
        name = self.get_selection()
        if tkMessageBox.askokcancel("renew", 'About to renew name "' + name + '". Proceed?'):
            r = self.model.name_renew(name)
            tkMessageBox.showinfo(title="renew: name_update", message=r)

    def name_new(self, trash=None):
        name = self.newEntry.get()
        if name in self.model.names:
            tkMessageBox.showerror(title="name_new", message=
                                   'pending operations on name "%s"' % name)
            return
        value = namedialog.NameNewDialog(self.root, name).value
        if value == None:  # cancelled
            return
        r = self.model.name_new(name, value)
        tkMessageBox.showinfo(title="name_new", message=r)

    def configure(self):
        name = self.get_selection()
        value = namedialog.NameConfigureDialog(self.root, name).value
        if value == None:  # cancelled
            return
        r = self.model.name_configure(name, value)
        tkMessageBox.showinfo(title="configure: name_update", message=r)

    def transfer(self):
        name = self.get_selection()
        result = namedialog.NameTransferDialog(self.root, name,
                                               self.validate_address).result
        if result == None:  # cancelled
            return
        value, targetAddress = result  # unpack tuple
        r = self.model.name_transfer(name, value, targetAddress)
        tkMessageBox.showinfo(title="transfer: name_update", message=r)

    def validate_address(self, address):
        return self.model.validate_address(address)

if __name__ == "__main__":
    gui = Gui()
