; centerline-trace.nsi

!ifndef VERSION
  !define VERSION 'anonymous-build'
!endif

Name "inkscape-centerline-trace"
AllowRootDirInstall true
ShowInstDetails show

Caption "inkscape-centerline-trace ${VERSION} extension"
OutFile "inkscape-centerline-trace-${VERSION}-setup.exe"
InstallDir "C:\Program Files\Inkscape\share\extensions"

RequestExecutionLevel admin

;--------------------------------

; Pages

Page directory
Page instfiles

;--------------------------------

Section ""

  ; Set output path to the installation directory.
  SetOutPath $INSTDIR

  ; Put file there
  File /oname=centerline-trace.py  "../../centerline-trace.py"
  File /oname=centerline-trace.inx "../../centerline-trace.inx"

SectionEnd
