C:\Python27\Scripts\pyinstaller -p lib;gfx;src ^
    --hidden-import=asyncore --hidden-import=win32gui_struct --hidden-import=win32gui ^
    --hidden-import=winxpgui --hidden-import=commctrl --hidden-import=pywintypes ^
     --noconfirm --noconsole --icon=./gfx/favicon.ico nameguiwin.pyw

@if %errorlevel% EQU 0 goto continue
@pause
:continue

mkdir dist\nameguiwin\lib\
mkdir dist\nameguiwin\gfx\
mkdir dist\nameguiwin\src\

xcopy lib dist\nameguiwin\lib /s /e /h /y
xcopy gfx dist\nameguiwin\gfx /s /e /h /y
xcopy src dist\nameguiwin\src /s /e /h /y

rmdir dist\nameguiwin\tk\images /s /q
rmdir dist\nameguiwin\tcl\tzdata /s /q
rmdir dist\nameguiwin\tcl\msgs /s /q

del dist\*.pyc /s /q