# http://stackoverflow.com/questions/22032152/python-ttk-treeview-sort-numbers
# changes MIT license


try:
    from Tkinter import *  # Python3
except ImportError:
    from tkinter import *

from ttk import *

class TreeviewPlus(Treeview):
    """kwarg: capitalizeHeadings"""
    def __init__(self, *args, **kwargs):
        if not "columns" in kwargs:
            raise Exception("TreeviewPlus needs columns to be set.")

        self.capitalize = False
        if "capitalizeHeadings" in kwargs:
            self.capitalize = kwargs.pop("capitalizeHeadings")
            

        Treeview.__init__(self, *args, **kwargs)
        for col in kwargs["columns"]:
            print "init:col:", col
            text = col
            if self.capitalize:
                text = col.capitalize()
            self.heading(col, text=text,
                         command=lambda _col=col: self.sort_column(_col, False))
        self.currentSortCol = None
        self.currentSortReverse = None
        self.sort_column()

    def get_sort_key(self, s):
        try:
            s = int(s[0])
        except ValueError:
            pass
        return s

    def sort_column(self, col=None, reverse=None):
        if not col:
            col = self.currentSortCol
            reverse = self.currentSortReverse
        if not col:
            return
        l = [(self.set(k, col), k) for k in self.get_children('')]
        l.sort(key=self.get_sort_key, reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.move(k, '', index)

        self.heading(col,
                   command=lambda _col=col: self.sort_column(_col, not reverse))

        self.currentSortCol = col
        self.currentSortReverse = reverse

        for col in self["columns"]:
            text = col
            if self.capitalize:
                text = text.capitalize()
            if col == self.currentSortCol:
                text += " " + ("<<" if self.currentSortReverse else ">>")
            self.heading(col, text=text, anchor="w")
        
    def insert(self, *args, **kwargs):
        Treeview.insert(self, *args, **kwargs)
        self.sort_column()

if __name__ == "__main__":
    import random
    def add_random_item(tv):
        t = random.randint(20, 40)
        tv.insert('', END, values=(str(t), chr(70+t), chr(80+t)))
    root = Tk()
    columns = ('number', "text", "text2")
    treeview = TreeviewPlus(root, columns=columns, show='headings', capitalizeHeadings=True)
    for t in (1, 10, 11, 2, 3):
        treeview.insert('', END, values=(str(t), chr(70+t), chr(80+t)))
    treeview.pack()
    Button(text="add random item", command=lambda: add_random_item(treeview)).pack()
    root.mainloop()
