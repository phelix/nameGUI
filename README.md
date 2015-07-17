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
* d/ and id/ namespace config
* show pending operations (name_update, new value?)
* bug: pending shows name in value
* better error handling and messages
* review database
x? * fix wrong wallet locked display while downloading blocks
x * auto lookup name new field
x * sort columns
x * unlock wallet / lock / forget pw (model?)
x * copy/paste menues
x * get proper conf folder for logfile and namenewdb


canDo
=====
* right click menu for treeview table
* improve display of lookup data
* make lookup data clickable (e.g. email)
* warn from expiry
* integrate atomic name trading (antpy / nametrade.py)
* launch namecoin client? / check if client available
* filter columns
* lock file to be only able to open one instance
* allow empty values / space only in values
* stash name_firstupdate fee into name_new address (needs raw tx?)
* make tkMessageBox styled (should be with py3)
* allow selection and processing of multiple items
* less rpc calls while blockchain not up to date yet
* identify wallet via getnewaddress / getaccount <address> ???

License
=======
LGPL unless it says otherwise in the source file.
