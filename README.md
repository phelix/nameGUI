nameGUI
=======
An RPC frontend GUI to a Namecoin client for name operations.

Start by launching namegui.py or nameguiwin.pyw on Windows to suppress the console window.

There are command line options '--datadir=<dir>' and '--namecoindatadir=<dir>' available.

Source on Github: https://github.com/phelixnmc/nameGUI
Discussion on the Namecoin forum: https://forum.namecoin.info/viewtopic.php?p=14920


Install Dependencies
====================
'pip install validators'


toDo
====
* scroll value display
* copy value/adress not working after name_new before name_firstupdate
* clear log file on load
* show value for pending operations
* review database
x? * fix wrong wallet locked display while downloading blocks
x* display value if clicking on own name
x* parse value with configure
x* Namecoin Core not shutting down until nameGUI is closed
x * bug: pending shows name in value
x * auto lookup name new field
x * sort columns
x * unlock wallet / lock / forget pw (model?)
x * copy/paste menues
x * get proper conf folder for logfile and namenewdb


canDo
=====
* display: "go back" function
* display: follow import on click
* better error handling and messages
* right click menu for treeview table
* warn from expiry
* launch namecoin client? / check if client available
* filter columns
* lock file to be only able to open one instance
* allow empty values / space only in values
* stash name_firstupdate fee into name_new address (needs raw tx?)
* make tkMessageBox styled (should be with py3)
* allow selection and processing of multiple items
* less rpc calls while blockchain not up to date yet
* identify wallet via getnewaddress / getaccount <address> ???
x * integrate atomic name trading (antpy / nametrade.py)
x * make lookup data clickable (e.g. email)
x * obsolete with cookie auth: offer to create .conf file if missing
x * improve display of lookup data

License
=======
LGPL unless it says otherwise in the source file.
