import shared  # needs to be imported early because of configuration and cli parsing

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
import util

import json

util.ensure_dirs(shared.CONFFOLDER)

log = mylogging.getMyLogger(name="gui", levelConsole=shared.LOGLEVELCONSOLE,
                            filename=shared.LOGFILENAMEPATH, levelFile=shared.LOGLEVELFILE)

class SelectionEmptyError(Exception):
    pass

class Gui(object):
    def __init__(self):
        log.info("__init__ #########################################################")
        self.root = tk.Tk()
        self.root.withdraw()  # hide for now in case an error comes up so the error window is visible

        # client info
        tk.Label(self.root, justify="left", text="Connected:").grd(row=10, column=10)
        self.labelConnected = tk.Label(self.root, justify="left", text="...").grd(row=10, column=20)

        tk.Label(self.root, justify="left", text="Block height:").grd(row=20, column=10)
        self.labelBlockCount = tk.Label(self.root, justify="left", text="...").grd(row=20,column=20)

        # remove as it is not so precise?
        tk.Label(self.root, justify="left", text="Blockchain is up to date:").grd(row=20, column=30)
        self.labelBlockchainIsUpToDate = tk.Label(self.root, justify="left", text="...").grd(row=20,column=40)

        tk.Label(self.root, justify="left", text="Balance:").grd(row=25, column=10)
        self.labelBalance = tk.Label(self.root, justify="left", text="...").grd(row=25,column=20)

        tk.Label(self.root, justify="left", text="Wallet locked:").grd(row=25, column=30)
        self.labelWalletLocked = tk.Label(self.root, justify="left", text="...").grd(row=25,column=40)

        # register name
        tk.Label(self.root, justify="left", text="New name:").grd(row=30, column=10)
        self.newEntry = tk.Entry(self.root).grd(row=30, column=20)
        self.newEntry.insert(0, "d/")
        self.newEntry.bind("<Return>", self.register_name)
        self.newEntry.bind("<KeyRelease>", self.event_key_release_register)
        self.newEntry.bind("<<menu_modified>>", self.event_key_release_register)
        self.newEntry.bind("<Escape>", lambda trash: self.newEntry.set(""))
        nameNewButton = tk.Button(self.root, text="register", command=self.register_name
                                  ).grd(row=30, column=30)
        tk.Button(self.root, text="copy value", command=lambda: self.copy_field_external("value")
                  ).grd(row=30, column=40)
        tk.Button(self.root, text="copy address", command=lambda: self.copy_field_external("address")
                  ).grd(row=30, column=50)

        # name lookup info
        self.displayNameDataLabel = tk.Label(self.root, justify="left", text=""
                                         ).grd(row=35, column=20, columnspan=120, sticky="w")
        self.displayValueLabel = tk.Label(self.root, justify="left", text=""
                                          ).grd(row=36, column=20, columnspan=120, sticky="w")

        # name table
        columns = ("name", "value", "address", "status", "expires_in")
        self.tv = tk.Treeview(self.root, columns=columns, capitalizeHeadings=True
                              ).grd(row=40, column=10, columnspan=100, sticky="nesw")
        self.root.columnconfigure(105, weight=10)  #minsize=minColumnWidth
        self.root.rowconfigure(40, weight=10)
        self.tv["selectmode"] = "browse"  # only allow to select a single item

        self.tv['show'] = 'headings'  # hide identifier and +
        ysb = tk.Scrollbar(self.root, orient='vertical', command=self.tv.yview).grd(
            row=40, column=110, sticky="nesw")
        #xsb = ttk.Scrollbar(self, orient='horizontal', command=self.t.xview)  # enable/hide automatically?
        self.tv.configure(yscroll=ysb.set) #, xscroll=xsb.set)
        for c in self.tv["columns"]:
            self.tv.heading(c, text=c.capitalize(), anchor="w")

        # mouse wheel scrolling for table
        self.root.bind("<MouseWheel>", self.on_scroll_event)  # Windows
        self.root.bind("<Button-4>", self.on_scroll_event) # Linux A
        self.root.bind("<Button-5>", self.on_scroll_event) # Linux B

        # name buttons
        tk.Button(self.root, text="renew", command=self.renew
                  ).grd(row=50, column=10)
        tk.Button(self.root, text="configure value", command=self.configure
                  ).grd(row=50, column=20)
        tk.Button(self.root, text="transfer name", command=self.transfer
                  ).grd(row=50, column=30)

        tk.Button(self.root, text="copy name", command=lambda: self.copy_field("name")
                  ).grd(row=50, column=40)
        tk.Button(self.root, text="copy value", command=lambda: self.copy_field("value")
                  ).grd(row=50, column=50)
        tk.Button(self.root, text="copy address", command=lambda: self.copy_field("address")
                  ).grd(row=50, column=60)

        # set up model
        self.model = namedialog.MyModel()
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
        self.root.deiconify()

        # start gui loop
        log.info("__init__: starting mainloop")
        self.root.mainloop()

    def set_clipboard(self, s):
        self.root.clipboard_clear()
        self.root.clipboard_append(s, type="STRING")

    def copy_field_external(self, f):
        name = self.newEntry.get()
        r = self.model.name_show(name)
        self.set_clipboard(r[f])

    def copy_field(self, f):
        name = self.get_selection()
        if f == "name":
            self.set_clipboard(name)
        else:
            self.set_clipboard(self.model.names[name][f])

    def event_key_release_register(self, *trash):
        name = self.newEntry.get()
        if name == "":
            self.displayValueLabel["text"] = ""
            self.displayNameDataLabel["text"] = ""
            return
        try:
            r = self.model.name_show(name)
        except model.NameDoesNotExistError:
            self.displayValueLabel["text"] = "<available for registration>"
            self.displayNameDataLabel["text"] = ""
            return

        v = str(r["value"])
        if len(v) > 100:
            v = v[:130] + "..."
        self.displayValueLabel["text"] = v

        r.pop("value")  # in place operation
        r.pop("txid")
        self.displayNameDataLabel["text"] = json.dumps(r)

    def show_error(self, exc_type, exc_value, exc_traceback):
        if exc_type == SelectionEmptyError:
            return
        err = traceback.format_exception(exc_type, exc_value, exc_traceback)
        log.exception("Error in GUI loop:")
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
        #log.debug("set_info")
        try:
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
                data = self.model.names[name]

                # make sure all names are listed
                if not name in items:
                    self.tv.insert('', "end", name)

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
                            if not data["known"] and not data["update"]:
                                s += "unknown "
                            if data["new"]:
                                s += "pending_new" + "(" + str(data["confirmations"]) + ") "
                            if data["update"]:
                                s += "pending_update"
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
        #log.debug("set_info: unlockNeeded?")
        try:
            if self.model.unlockNeeded:
                self.model.unlock(guiParent=self.root)
        except:
            log.exception("set_info:unlock:")

        if not self.stopping:
            self.root.after(1000, func=self.set_info)

    # remove callbacks alltogether?
    def _model_callback_poll_start(self):
        # careful, tkinter is not thread safe by default
        #self.labelModelUpdating["text"] = "working..."
        #self.root.update_idletasks()
        pass
    def _model_callback_poll_end(self):
        # careful, tkinter is not thread safe by default
        #self.labelModelUpdating["text"] = "waiting"
        #self.root.update_idletasks()
        pass

    def renew(self):
        name = self.get_selection()
        if tkMessageBox.askokcancel("renew", 'About to renew name "' + name + '". Proceed?'):
            r = self.model.name_renew(name, guiParent=self.root)
            tkMessageBox.showinfo(title="renew: name_update", message=r)

    def register_name(self, trash=None):
        name = self.newEntry.get()
        if name in self.model.names:
            tkMessageBox.showerror(title="Register Name Error", message=
                                   'pending operations on name "%s"' % name)
            return
        if self.model.check_name_exists(name):
            tkMessageBox.showerror(title="Register Name Error", message=
                                   'name "%s" is already registered' % name)
            return
        namedialog.NameNewDialog(self.model, self.root, name)

    def configure(self):
        name = self.get_selection()
        namedialog.NameConfigureDialog(self.model, self.root, name)

    def transfer(self):
        name = self.get_selection()
        namedialog.NameTransferDialog(self.model, self.root, name,
                                      self.validate_address)

    def validate_address(self, address):
        return self.model.validate_address(address)


def run():
    try:
        global gui  # for easy console access
        gui = Gui()
    except:
        log.exception("Launch error:")
        root = tk.Tk()
        tk.Label(root, justify="left", text=traceback.format_exc()).pack()
        tk.Button(root, text="OK", command=root.quit).pack()
        root.focus_force()
        root.mainloop()

if __name__ == "__main__":
    run()
