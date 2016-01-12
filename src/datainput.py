
"""
todo:
  parse existing value for configure
  array input
  check all inputs
  implement fancy TLS ?

"""

import sys
sys.path.append("..")
sys.path.append("../lib")

import json
import collections
import ttkinter as tk
import tkMessageBox

import validators

import namedialog
import shared
import tkentryplus

log = shared.get_my_logger(name=__file__)

def is_json(s):
    try:
        json.loads(s)
    except:
        return False
    return True

def is_hex(s):
    """without 0x at start"""
    if s.lower().startswith("0x"):
        return False
    if len(s) % 2:
        return False
    try:
        int(s, 16)
    except:
        return False
    return True

class Container(tk.Frame):
    def __init__(self, parent, key=None, text=None, visible=True, padx=(20,0), **kwargs):
        self.key = key
        self.parent = parent
        if key and not text:
            text = key.capitalize() + ":"
        self.outerFrame = tk.Frame(master=self.parent).pk(side=tk.TOP, anchor=tk.NW,
                                                     fill=tk.X, expand=1)
        if text:
            tk.Label(self.outerFrame, text=text).pk(side=tk.TOP, anchor=tk.NW)
        self.visible = visible
        tk.Frame.__init__(self, self.outerFrame, **kwargs)
        self.pk(side=tk.TOP, anchor=tk.NW, padx=padx, fill=tk.X, expand=1)
        try:
            self.parent.items.append(self)
        except AttributeError:  # parent is not a container
            pass
        self.items = []
        self.setup()
    def setup(self):
        pass
    def refresh(self):
        self.parent.refresh()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def get_data(self):
        oD = collections.OrderedDict()
        visible = False
        for i in self.items:
            r = i.get_data()
            if not r or not r[1]:
                continue
            oD[r[0]] = r[1]
            if i.visible:
                visible = True
        if not visible:
            oD = {}
        return (self.key, oD)

class NamespaceContainer(Container):
    def __init__(self, *args, **kwargs):
        kwargs["padx"] = None  # no indentation for top level container
        Container.__init__(self, *args, **kwargs)
        tk.Label(self.outerFrame, text="Preview:").pk(side=tk.TOP, anchor=tk.NW, pady=(20,1))
        self.preview = tk.Message(self.outerFrame, text="", anchor=tk.NW).pk(side=tk.TOP,
                                                  anchor=tk.NW)
    def refresh(self):
        self.preview["text"]= json.dumps(self.get_data())
        self.preview["width"] = self.outerFrame.winfo_width() - 30
    def get_data(self):
        key, oD = Container.get_data(self)  # key should be None
        return oD

class InputGUI(object):
    def __init__(self, parent, text, visible):
        frame = tk.Frame(master=parent)
        if visible:
            frame.pk(side=tk.TOP, anchor=tk.NW, pady=1, fill=tk.X, expand=1)
        self.label = tk.Label(frame, text=text).pk(side=tk.LEFT, padx=1)
        self.entry = tkentryplus.EntryPlus(frame).pk(side=tk.LEFT, fill=tk.X, expand=1, padx=2)
        self.entry.bind('<KeyRelease>', self.refresh)
        self.entry.bind('<<menu_modified>>', self.refresh)        
        self.entry.bind("<FocusIn>", self.refresh)
        self.entry.bind("<FocusOut>", self.refresh)

    def mood(self, happy=True):
        if happy:
            self.label["foreground"] = "black"
        else:
            self.label["foreground"] = "red"            
    def get(self):
        return self.entry.get()
    def set(self, s):
        self.entry.set(s)

class Input(InputGUI):
    def __init__(self, parent, key, text=None, validator=None, visible=True, default=None):
        self.visible = visible
        self.parent = parent
        if not text:
            text = key.capitalize() + ":"
        InputGUI.__init__(self, self.parent, text, visible)
        self.key = key
        self.validator = validator
        self.parent.items.append(self)
        if default != None:
            self.entry.set(default)
    def refresh(self, trash):
        self.mood(self.validate())
        self.parent.refresh()        
    def validate(self):
        if self.validator:
            s = self.get()
            if s == '':
                return True
            r = self.validator(s)
            return bool(r)
        return True
    def get_data(self):
        s = self.get()
        if not s:
            return None
        return self.key, s

class NamespaceCustom(NamespaceContainer):
    def setup(self):
        self.input = Input(self, 'value', "Value (json):", validator=is_json)
    def get_data(self):
        return self.input.get()

class NamespaceId(NamespaceContainer):
    def setup(self):
        f = self
        Input(f, 'name')
        Input(f, 'email', "eMail:", validator=validators.email)
        Input(f, 'country', "Country (two letter code):")
        Input(f, 'locality')
        Input(f, 'photo_url', "Photo (URL):", validator=validators.url)
        Input(f, 'description')
        Input(f, 'weblog', "Blog (URL):", validator=validators.url)
        Input(f, 'namecoin')
        Input(f, 'bitcoin')        
        Input(f, 'bitmessage')
        Input(f, 'xmpp', "XMPP/Jabber contact:")
        Input(f, 'otr', "OTR public key fingerprint:")
        Input(f, 'signer', "Addresses allowed to \"sign\" on behalf of this identity:")
        with Container(f, 'gpg', "GPG encryption public key data:") as gpg:
            #Input(gpg, 'v', visible=False, default="pka1")  # pka1 is default anyway
            Input(gpg, 'fpr', "GPG Fingerprint (>20 bytes)", validator=is_hex)
            Input(gpg, 'uri', "URI where the key can be obtained (optional)",
                  validator=validators.url)

class NamespaceD(NamespaceContainer):
    def setup(self):
        f = self
        Input(f, 'ip', "IPv4 address:", validator=validators.ipv4)
        Input(f, 'tor')
        Input(f, 'i2p', "i2p:")
        Input(f, 'email', "eMail:", validator=validators.email)
        Input(f, 'info')
        Input(f, 'fingerprint', "TLS fingerprint:", validator=is_hex)
        
if __name__ == "__main__":
    root = tk.Tk()

    def shutdown():
        root.destroy()


    with NamespaceId(root) as f:
        pass
    Container(root, '-', '-------')
    
    with NamespaceD(root) as d:
              pass
    Container(root, '-', '-------')
    
    with Container(root, 'test', 'test'):
        Input(f, "ipv4", "IPv4:", validator=validators.ipv4)
        with Container(f, 'c2') as f2:
            Input(f2, 'fav1')
            Input(f2, 'fav2')
            with Container(f2, 'c3') as f3:
                Input(f3, 'blub')


    def output():
        print f.get_data()
        print json.dumps(f.get_data())

    tk.Button(text="empty", command=output).pk()

    root.mainloop()
