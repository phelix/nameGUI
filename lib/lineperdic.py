"""
linewise persistant dictionary

* human readable
* robust?

todo:
* purge
* logging

"""

import json

class LPD(dict):
    """linewise persistant dictionary
key must be a string
everything ever written kept in a file
caution: only a root dict setitem will make the data persistant"""
    def __init__(self, filename):
        dict.__init__(self)
        self.filename = filename
        try:
            with open(filename, "r") as f:
                self._read(f)
        except IOError as e:
            print e.errno
            if e.errno != 2:  # No such file or directory
                raise
        self.f = open(filename, "a", 1)  # append, 1 --> line buffered
    def _read(self, f):
        data = f.read()
        if "\r\n" in data:
            lines = data.split("\r\n")
        else:
            lines = data.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if not " " in line:
                raise Exception("Corrupted data, space missing. Line content: " + repr(line))
            key, js = line.split(" ", 1)
            val = json.loads(js)
            dict.__setitem__(self, key, val)
    def __setitem__(self, key, val):
        assert type(key) == str
        assert not "\n" in key
        assert not " " in key  # use different separator?
        dict.__setitem__(self, key, val)
        js = json.dumps(val)
        assert not "\n" in js
        self.f.write(key + " " + js + "\n")
        self.f.flush()  # should not be necessary with line buffering

##    def __enter__(self):
##        return self
##    def __exit__(self, type, value, traceback):
##        try:
##            self.f.close()
##        except AttributeError:
##            pass


if __name__ == "__main__":
    lpd = LPD("testlpd.txt")
    lpd["1"] = {"a":1}
    print lpd["1"]
    lpd["key"] = 2
    lpd["key"] = "2b"
    print lpd["key"]
    print "keys:", lpd.keys()
