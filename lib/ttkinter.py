# MIT license

try:
    from Tkinter import *  # Python3
except ImportError:
    from tkinter import *

from tkSimpleDialog import *

from ttk import *

from tkentryplus import EntryPlus as Entry
from tktreeviewplus import TreeviewPlus as Treeview

# monkey patch to make grid more comfortable
def grd(self, *args, **kwargs):
    """grid shortcut that returns self"""
    if not "sticky" in kwargs:
        kwargs["sticky"] = "w"
    self.grid(*args, **kwargs)
    return self
Widget.grd = grd

# monkey patch to make pack more comfortable
def pk(self, *args, **kwargs):
    """pack shortcut that returns self"""
    self.pack(*args, **kwargs)
    return self
Widget.pk = pk

if __name__ == "__main__":
    import tkMessageBox
    def messagebox():
        tkMessageBox.showerror("test", "message")
    root = Tk()
    if 0:
        label = Label(root, justify="left", text="grd test").grd()
        label["text"] += " ok"
    else:
        label = Label(root, justify="left", text="pk test").pk(side=LEFT)
        label["text"] += " ok"
        button = Button(root, text="ErrorBox", command=messagebox).pk()
        button = Button(root, text="OK", command=root.quit).pk()
    root.mainloop()
