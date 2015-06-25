nameGUI
=======
An RPC frontend GUI to a Namecoin client for name operations.

There should not be any dependencies outside the Python standard libraries.

Start by launching namegui.py or nameguiwin.pyw on Windows to suppress the console window.

There are no copy/paste menues yet but you can use ctrl-c/v

Source on Github: https://github.com/phelixnmc/nameGUI
Discussion on the Namecoin forum: https://forum.namecoin.info/viewtopic.php?p=14920

toDo
====
* bug: pending shows name in value
* review database
* better error handling and messages
* unlock wallet / lock / forget pw (model?)
* less rpc calls while blockchain not up to date yet
* copy/paste menues
* x get proper conf folder ("namecoin"?) for logfile and namenewdb
* lock file to be only able to open one instance
* launch namecoin client? / check if client available
* auto lookup name new field
* show pending operations (name_update)
* sort columns
  http://stackoverflow.com/questions/1966929/tk-treeview-column-sort
  http://stackoverflow.com/questions/22032152/python-ttk-treeview-sort-numbers

canDo
=====
* warn from expiry
* filter columns
* allow empty values / space only in values
* stash name_firstupdate fee into name_new address (needs raw tx?)
* make tkMessageBox styled (should be with py3)
* allow selection and processing of multiple items
* identify wallet via getnewaddress / getaccount <address> ???

License
=======
LGPL unless it says otherwise in the source file.
