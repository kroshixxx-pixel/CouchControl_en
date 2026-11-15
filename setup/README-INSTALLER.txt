CouchControl — Windows installer project

BUILD
1. Install Inno Setup 6: https://jrsoftware.org/isinfo.php
2. Open CouchControl\\CouchControl.iss in Inno Setup Compiler.
3. Select Build -> Compile (Ctrl+F9).
4. The EXE will be created at CouchControl\\Output\\CouchControl-Setup.exe.

INSTALLATION
- The installer targets 64-bit Windows 10/11.
- Internet access is required: the private Python runtime and Python packages are downloaded during setup.
- The user enters a Telegram Bot Token and numeric Telegram User ID.
- Python is installed in the application's own directory, then a virtual environment is created and dependencies are installed.
- Desktop shortcut and Windows sign-in startup options are offered by the installer.
- The token is saved locally in .env. Never publish or share this file.

DIAGNOSTICS
If setup fails, inspect:
%TEMP%\\CouchControl-install-diagnostic.log
%TEMP%\\CouchControl-Python-install.log (if created by the Python installer)

IMPORTANT
This folder contains Inno Setup source files, not a prebuilt EXE. Test the installer on a clean Windows 10/11 x64 machine before distributing it. The current development environment is not Windows, so the actual Windows installation cannot be tested here.
