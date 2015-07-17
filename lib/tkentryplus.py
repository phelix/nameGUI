# MIT license

try:
    from Tkinter import *  # Python3
except ImportError:
    from tkinter import *

from ttk import *

class EntryPlus(Entry):
    def __init__(self, *args, **kwargs):
        Entry.__init__(self, *args, **kwargs)
        _rc_menu_install(self)

        self.bind("<Control-a>", self.event_select_all)
        self.bind("<Button-3><ButtonRelease-3>", self.show_menu)
        self.bind("<Control-c>", self.event_copy)
        self.bind("<<Copy>>", self.event_copy)

        self.bind("<Control-v>", self.event_paste)
        self.bind("<<Paste>>", self.event_paste)

        self.bind("<Control-x>", self.event_cut)
        self.bind("<<Cut>>", self.event_cut)

    def queue_modified(self, e):
        self.after(10, self.generate_modified_event)  # workaround event order
    def generate_modified_event(self):
        self.event_generate("<<menu_modified>>")

    def event_select_all(self, *args):
        self.focus_force()
        self.selection_range(0, END)
        return "break"

    def show_menu(self, e):
        self.focus_force()
        self.tk.call("tk_popup", self.menu, e.x_root, e.y_root)
        return "break"

    def set(self, s):
        self.delete(0, END)  # removes selection if any
        self.insert(0, s)

    def event_copy(self, event=None):
        if self.selection_present():
            self.clipboard_clear()
            self.clipboard_append(self.selection_get())
        return "break"

    def event_cut(self, event=None):
        self.event_copy()
        if self.selection_present():
            self.delete(SEL_FIRST, SEL_LAST)
        self.queue_modified(event)
        return "break"

    def event_paste(self, event=None):
        try:
            s = self.clipboard_get()
        except TclError:  # probably empty clipboard
            return "break"
        if self.selection_present():
            self.delete(SEL_FIRST, SEL_LAST)
        self.insert(INSERT, s)
        self.queue_modified(event)
        return "break"

    def entry_select_all(self, *args):
        self.entryQrData.selection_range(0, END)
        return "break"

def _rc_menu_install(w):
    w.menu = Menu(w, tearoff=0)
    w.menu.add_command(label="Cut")
    w.menu.add_command(label="Copy")
    w.menu.add_command(label="Paste")
    w.menu.add_separator()
    w.menu.add_command(label="Select all")

    w.menu.entryconfigure("Cut", command=lambda: w.focus_force() or w.event_generate("<<Cut>>"))
    w.menu.entryconfigure("Copy", command=lambda: w.focus_force() or w.event_generate("<<Copy>>"))
    w.menu.entryconfigure("Paste", command=lambda: w.focus_force() or w.event_generate("<<Paste>>"))
    w.menu.entryconfigure("Select all", command=w.event_select_all)

if __name__ == "__main__":
    class App(Tk):
        def __init__(self, *args, **kwargs):
            Tk.__init__(self, *args, **kwargs)
            self.entry = EntryPlus(self)
            self.entry.pack()
            self.entry.bind("<<menu_modified>>", self.event_menu_modified)
            Button(text='set entry to "test"', command=self.event_button).pack()
        def event_menu_modified(self, e):
            print "entry modified by menu: new content:", self.entry.get()
        def event_button(self):
            self.entry.set("test")

    app = App()
    app.mainloop()
