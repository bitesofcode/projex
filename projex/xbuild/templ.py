""" 
Defines the templates for this build.
"""

NSISPACKAGE = """
    ; install the product
    SetOutPath '$INSTDIR\\{product}\\'
    
    ; install python source code
    File /nonfatal /r /x .svn /x *.pyc {compilepath}\*
    
    ; install the auto-generated documentation
    SetOutPath '$INSTDIR\\{product}\\resources\\docs\\'
    File /nonfatal /r /x .svn /x *.pyc {buildpath}\\docs\\*
    
    ; install the license
    SetOutPath '$INSTDIR\\{product}\\'
    File /nonfatal {buildpath}\\license.txt
    
    SetOutPath '$INSTDIR\\{product}\\resources\\'
    File /nonfatal {buildpath}\\{product}.xdk
"""

NSISCHOOSEDIRECTORY = "!insertmacro MUI_PAGE_DIRECTORY"

NSISMODULE = """
    ; install the product
    SetOutPath '$INSTDIR'
    
    ; install python module
    File /nonfatal {compilepath}
"""

NSISLICENSERADIO = """
!define MUI_LICENSEPAGE_RADIOBUTTONS
"""

NSISLIB = """\
!include "MUI2.nsh"
!include LogicLib.nsh

; defined by the xbuild system
!define MUI_ABORTWARNING
!define MUI_PRODUCT                     '{product}'
!define MUI_VERSION                     '{version}'
!define MUI_COMPANY                     '{company}'
!define MUI_ICON                        '{logo}'
!define MUI_UNICON                      '{logo}'
!define MUI_COMPONENTSPAGE_SMALLDESC
!define MUI_BGCOLOR                     'ffffff'
!define MUI_INSTFILESPAGE_PROGRESSBAR   'colored'

{require_license_approval}

!define MUI_HEADERIMAGE 
!define MUI_HEADERIMAGE_BITMAP          '{header_image}'
!define MUI_WELCOMEFINISHPAGE_BITMAP    '{finish_image}'

BrandingText '{product} {version} from {company}'
InstallDir '{instpath}'

; define the name of the product
Name '{product} {version}'

; define the generated output file
OutFile '{outpath}\\{instname}-{platform}.exe'
RequestExecutionLevel admin

#SilentInstall silent

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE 'license.txt'
{choose_directory}
!insertmacro MUI_PAGE_INSTFILES

!insertmacro MUI_LANGUAGE '{language}'

; pre section plugins
{pre_section_plugins}

; include the customized install and uninstall files
Section 'Install'
    ; install plugins
    {install_plugins}

    {install}
    
    ; register the product
    WriteRegStr HKLM 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{company}\\{product}' 'DisplayName' '{product} (remove only)'
    WriteRegStr HKLM 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{company}\\{product}' 'UninstallString' '$INSTDIR\\{product}\\uninstall-{exname}.exe'
    
    ; create the uninstaller
    WriteUninstaller '$INSTDIR\\{product}\\uninstall-{exname}.exe'
    
SectionEnd

Section 'Uninstall'
    ; uninstall section plugins
    {uninstall_plugins}

    ; call the uninstaller
    RMDir /r '$INSTDIR'
    Delete '$DESKTOP\\{product}.lnk'
    
    ; remove the registry information
    DeleteRegKey HKLM 'SOFTWARE\\{company}\\{product}'
    DeleteRegKey HKLM 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{company}\\{product}'

SectionEnd

; post section plugins
{post_section_plugins}
"""

NSISAPP = r"""\
!include "MUI2.nsh"
!include LogicLib.nsh

; define variables
Var StartMenuFolder

; defined by the xbuild system
!define MUI_ABORTWARNING
!define MUI_PRODUCT                     '{product}'
!define MUI_VERSION                     '{version}'
!define MUI_COMPANY                     '{company}'
!define MUI_ICON                        '{logo}'
!define MUI_UNICON                      '{logo}'
!define MUI_COMPONENTSPAGE_SMALLDESC
!define MUI_BGCOLOR                     'ffffff'
!define MUI_INSTFILESPAGE_PROGRESSBAR   'colored'

{signed}
{require_license_approval}

!define MUI_HEADERIMAGE 
!define MUI_HEADERIMAGE_BITMAP          '{header_image}'
!define MUI_WELCOMEFINISHPAGE_BITMAP    '{finish_image}'

;Start Menu Folder Page Configuration
!define MUI_STARTMENUPAGE_REGISTRY_ROOT 'HKCU' 
!define MUI_STARTMENUPAGE_REGISTRY_KEY 'Software\{company}\{product}'
!define MUI_STARTMENUPAGE_REGISTRY_VALUENAME 'Start Menu Folder'
!define MUI_STARTMENUPAGE_DEFAULTFOLDER '{product}'

!define MUI_FINISHPAGE_SHOWREADME
!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
!define MUI_FINISHPAGE_SHOWREADME_TEXT "Create Desktop Shortcut"
!define MUI_FINISHPAGE_SHOWREADME_FUNCTION "CreateDesktopIcon"

!define MUI_FINISHPAGE_RUN '$INSTDIR\{product}\{exname}.exe'
!define MUI_FINISHPAGE_RUN_TEXT 'Launch {product}'

BrandingText '{product} {version} from {company}'

InstallDir '{instpath}'

; define the name of the product
Name '{product} {version}'
RequestExecutionLevel admin

!ifdef INNER
    !echo "Building Signed Uninstaller"
    OutFile "{buildpath}\setup-{exname}-uninstall.exe"
!else
    ; generate the signable installer
    !system '"{nsis_exe}" /DINNER "{__file__}"' = 0
    
    ; run the installer that was just created
    !system '{buildpath}\setup-{exname}-uninstall.exe --silent' = 2
    
    !ifdef SIGNED
    ; sign the uninstaller
    !system '{signcmd} {buildpath}\uninstall-{exname}.exe' = 0
    !endif
    
    !echo "Building Installer"
    OutFile '{outpath}\{instname}-{platform}.exe'
!endif

#SilentInstall silent

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE 'license.txt'
!insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder
{choose_directory}
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!ifdef INNER
    !insertmacro MUI_UNPAGE_CONFIRM
    !insertmacro MUI_UNPAGE_INSTFILES
!endif

!insertmacro MUI_LANGUAGE '{language}'

Function .onInit
!ifdef INNER
    WriteUninstaller "{buildpath}\uninstall-{exname}.exe"
    Quit
!endif
FunctionEnd

Function CreateDesktopIcon
    ; create desktop shortcuts
    CreateShortCut '$DESKTOP\{product}.lnk' '$INSTDIR\{product}\{exname}.exe'
FunctionEnd

; pre section plugins
{pre_section_plugins}

; include the customized install and uninstall files
Section 'Install'
    SetShellVarContext all

    ; install the product
    SetOutPath '$INSTDIR\{product}'

    ; install section plugins
    {install_plugins}

    ; install application code
    File /nonfatal /r /x .svn /x *.pyc {compilepath}\*
    
    ; store the installation folder
    WriteRegStr HKCU 'Software\{company}\{product}' '' '$INSTDIR\{product}'
    
    ; register the product
    WriteRegStr HKLM 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{company}\{product}' 'DisplayName' '{product} (remove only)'
    WriteRegStr HKLM 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{company}\{product}' 'UninstallString' '$INSTDIR\{product}\uninstall-{exname}.exe'
    
    !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
        ;create start-menu items
        CreateDirectory '$SMPROGRAMS\$StartMenuFolder'
        CreateShortCut '$SMPROGRAMS\$StartMenuFolder\Uninstall {product}.lnk' '$INSTDIR\{product}\uninstall-{exname}.exe' '' '$INSTDIR\{product}\uninstall-{exname}.exe' 0
        CreateShortCut '$SMPROGRAMS\$StartMenuFolder\{product}.lnk' '$INSTDIR\{product}\{exname}.exe' '' '$INSTDIR\{product}\{exname}.exe' 0
    !insertmacro MUI_STARTMENU_WRITE_END

    ; create the uninstaller
    !ifndef INNER
    File {buildpath}\uninstall-{exname}.exe
    !endif
    
    ; additional commands
{addtl_commands}

SectionEnd

!ifdef INNER
Section 'Uninstall'
    SetShellVarContext all

    ; uninstall section plugins
    {uninstall_plugins}

    ; call the uninstaller
    Delete '$INSTDIR\uninstall-{exname}.exe'
    RMDir /r '$INSTDIR'
    
    ; remove the registry information
    DeleteRegKey HKLM 'SOFTWARE\{company}\{product}'
    DeleteRegKey HKLM 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{company}\{product}'
    
    ; remove the start menu information
    !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
    Delete '$SMPROGRAMS\$StartMenuFolder\{product}.lnk'
    Delete '$SMPROGRAMS\$StartMenuFolder\Uninstall {product}.lnk'
    RMDir '$SMPROGRAMS\$StartMenuFolder'
    
    ; remove the registry key
    DeleteRegKey /ifempty HKCU 'Software\{company}\{product}'

    ; remove the desktop information
    Delete '$DESKTOP\{product}.lnk'
    
SectionEnd
!endif

; post section plugins
{post_section_plugins}
"""

SETUPFILE = """\
import os
from setuptools import setup, find_packages
import {name}

here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, 'README.md')) as f:
        README = f.read()
except IOError:
    README = {name}.__doc__

try:
    VERSION = {name}.__version__
except AttributeError:
    VERSION = '{version}'

try:
    REQUIREMENTS = {name}.__depends__
except AttributeError:
    REQUIREMENTS = []

setup(
    name = '{distname}',
    version = VERSION,
    author = '{author}',
    author_email = '{author_email}',
    maintainer = '{author}',
    maintainer_email = '{author_email}',
    description = '''{brief}''',
    license = '{license}',
    keywords = '{keywords}',
    url = '{url}',
    include_package_data=True,
    packages = find_packages(),
    install_requires = REQUIREMENTS,
    tests_require = REQUIREMENTS,
    long_description= README,
    classifiers=[{classifiers}],
)"""

SPECTREE = """\
dataset += Tree(r'{path}', prefix='{prefix}', excludes=[{excludes}])
"""

SPECDATA = """\
dataset += [(r'{name}', r'{path}', r'{type}')]
"""

SPECFILE_CLI = """\
cli = EXE(pyz,
          results.scripts,
          exclude_binaries={excludeBinaries},
          name=os.path.join(os.path.join(r'build',
                                         r'pyi.{platform}',
                                         r'{cliname}',
                                         r'{cliname}.exe')),
          debug={debug},
          strip={strip},
          icon=r'{logo}',
          upx={upx},
          console=True)

coll = COLLECT(exe,
               cli,
               results.binaries,
               results.zipfiles,
               dataset,
               strip={strip},
               upx={upx},
               name=os.path.join(r'{distpath}', r'{exname}'))
"""

SPECFILE_COLLECT = """\
coll = COLLECT(exe,
               results.binaries,
               results.zipfiles,
               dataset,
               strip={strip},
               upx={upx},
               name=os.path.join(r'{distpath}', r'{exname}'))
"""

SPECFILE = """\
# -*- mode: python -*-
import logging
import os
import sys

logger = logging.getLogger(__name__)

# define analysis options
hookpaths = [{hookpaths}]
hiddenimports = [{hiddenimports}]
excludes = [{excludes}]

# generate the analysis for our executable
results = Analysis([r'{runtime}'],
                   pathex=[r'{srcpath}/..'],
                   hiddenimports=hiddenimports,
                   hookspath=hookpaths,
                   excludes=excludes)

dataset = results.datas

# load any additional data information
{datasets}

pyz = PYZ(results.pure)
exe = EXE(pyz,
          results.scripts,
          exclude_binaries={excludeBinaries},
          name=os.path.join(os.path.join(r'build',
                                         r'pyi.{platform}',
                                         r'{exname}',
                                         r'{exname}.exe')),
          debug={debug},
          strip={strip},
          icon=r'{logo}',
          upx={upx},
          console={console})

{collect}
"""

SPECFILE_ONEFILE = """\
# -*- mode: python -*-
import logging
import os
import sys

logger = logging.getLogger(__name__)

# define analysis options
hookpaths = [{hookpaths}]
hiddenimports = [{hiddenimports}]
excludes = [{excludes}]

# generate the analysis for our executable
results = Analysis([r'{runtime}'],
                   pathex=[r'{srcpath}/..'],
                   hiddenimports=hiddenimports,
                   hookspath=hookpaths,
                   excludes=excludes)

dataset = results.datas

# load any additional data information
{datasets}

pyz = PYZ(results.pure)
exe = EXE(pyz,
          results.scripts,
          results.binaries,
          results.zipfiles,
          dataset,
          name=os.path.join(os.path.join(r'build',
                                         r'pyi.{platform}',
                                         r'{exname}',
                                         r'{exname}.exe')),
          debug={debug},
          strip={strip},
          icon=r'{logo}',
          upx={upx},
          console={console})

coll = COLLECT(exe,
               dataset,
               strip={strip},
               upx={upx},
               name=os.path.join(r'{distpath}', r'{exname}'))
"""