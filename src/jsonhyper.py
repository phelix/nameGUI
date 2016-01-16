import sys
sys.path.append('../lib')
import tkHyperlinkManager
import ttkinter as tk


generalKeywords = {"email": "mailto:",
                   "bitcoin": "bitcoin:",
                   "namecoin": "namecoin:"}

maxSchemeLength = 10  # arbitrary

# http://stackoverflow.com/questions/17317219/is-there-an-platform-independent-equivalent-of-os-startfile
import os, subprocess
def open_file(filename):
    if sys.platform == "win32":
        os.startfile(filename)
    else:
        opener ="open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, filename])

def scheme_opener_factory(url):
    return lambda *args, **kwargs: open_file(url)


def is_uri_scheme(s):
    """e.g. 'bitcoin:' or 'mailto:'"""
    if not s.endswith(":"):
        return False
    if not s.islower():  # stricter than URI spec
        return False
    if len(s) > maxSchemeLength:  # stricter than URI spec
        return False
    if not s.replace(":", "").isalpha():  # stricter than URI spec
        return False
    return True

def startswith_uri_scheme(s):
    s = unicode(s)
    if not ":" in s:
        return False
    s = s.split(":")[0] + ":"
    return is_uri_scheme(s)

class Parser(object):
    """Parse object and output processed string representation."""
    def __init__(self, tkText, baseUrl="nmc:", spaceChar=" "):
        self.spaceChar = spaceChar
        self.baseUrl = baseUrl
        self.t = tkText
        self.hyperlink = tkHyperlinkManager.HyperlinkManager(self.t)
    def refresh(self):  # should be moved to a fancy text class instead
        self.t.config (height=int(float(self.t.index(tk.END))))
    def clear(self):
        self.t.delete('1.0', tk.END)
    def add(self, s, link=None):
        if s.startswith("."):
            raise
        tag = None
        if link:
            tag = self.hyperlink.add(scheme_opener_factory(link))
        self.t.insert(tk.INSERT, s, tag)
    def spaces(self, indent):
        return 4 * indent * self.spaceChar
    def parse(self, X, indent=0, key=""):
        if type(X) == dict or type(X) == tuple or type(X) == list:  # recurse
            if type(X) == dict:
                for x in sorted(X.keys()):
                    self.add(self.spaces(indent))
                    self.add((x[:-1] if x.endswith(":") else x) + " : \n")
                    self.parse(X[x], indent + 1, key=x)
            else:
                for x in X:
                    self.parse(x, indent + 1)

        else:
            # detect URI if any
            u = unicode(X)
            isUri = False
            uri = ""
            displayUri = None
            if startswith_uri_scheme(u):
                isUri = True
            elif is_uri_scheme(key):
                isUri = True
                uri = key
            if not isUri:
                if key in generalKeywords:
                    isUri = True
                    uri = generalKeywords[key]
                elif key == "import" or key == "next" or key == "t":
                    isUri = True
                    uri = self.baseUrl + "name="
                    displayUri = "name:"
                elif len(key) > 1 and key[0] == "t":
                    try:
                        int(key[1:])
                        isUri = True
                        uri = self.baseUrl + "name="
                        displayUri = "name:"
                    except ValueError:
                        pass
            if isUri:
                if displayUri:
                    self.add(self.spaces(indent))
                    self.add(displayUri + u, displayUri + u)
                    self.add("\n")
                else:
                    self.add(self.spaces(indent))
                    self.add(uri + u, uri + u)
                    self.add("\n")
            else:  # plain text
                self.add(self.spaces(indent) + u + "\n")
        return self.t


if __name__ == "__main__":
    root = tk.Tk()
    D = {"a": 1, "b": 2, "c": "ceee", "d": {"da": 1, "db": 2},
         "e": (["ee1", "ee2"], "e2", "https://namecoin.com"), "email": "e@test.com",
         "uri": "https://dot-bit.org/files/gpg/khalahan.asc"}
    hyperParser = Parser(root)
    text = hyperParser.parse(D)
    text.pack()
    root.mainloop()
