C:\Python27\Scripts\pyinstaller -p lib;gfx ^
    --hidden-import=asyncore --hidden-import=win32gui_struct --hidden-import=win32gui ^
    --hidden-import=winxpgui --hidden-import=commctrl --hidden-import=pywintypes ^
    --noconfirm --icon=./gfx/favicon.ico nameguiwin.pyw --noconsole

@if %errorlevel% EQU 0 goto continue
@pause
:continue

mkdir dist\nameguiwin\lib\
mkdir dist\nameguiwin\gfx\

xcopy lib dist\nameguiwin\lib /s /e /h /y
xcopy gfx dist\nameguiwin\gfx /s /e /h /y

rmdir dist\nameguiwin\_MEI\tk\images /s /q
rmdir dist\nameguiwin\_MEI\tcl\tzdata /s /q
rmdir dist\nameguiwin\_MEI\tcl\msgs /s /q

del dist\*.pyc /s /q