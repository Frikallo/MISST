[Setup]
AppName=MISST
AppVersion=3.1.0
AppPublisher=@Frikallo
AppPublisherURL=https://github.com/Frikallo/MISST
AppSupportURL=https://github.com/Frikallo/MISST
AppUpdatesURL=https://github.com/Frikallo/MISST
DefaultDirName={autopf}\MISST
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\MISST.exe
OutputDir=F:\Repos\MISST\output
OutputBaseFilename=MISST
SetupIconFile=F:\Repos\MISST\MISST\Assets\icon.ico
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
LicenseFile=F:\Repos\MISST\LICENSE
DisableWelcomePage=no
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Icons]
Name: "{autoprograms}\MISST"; Filename: "{app}\MISST\MISST.exe"
Name: "{autodesktop}\MISST"; Filename: "{app}\MISST\MISST.exe"; Tasks: desktopicon

[Files]
Source: "7za.exe"; DestDir: "{tmp}"; DestName: "7za.exe"; Flags: deleteafterinstall;
Source: "{tmp}\MISST.7z"; DestDir: "{app}"; Flags: external deleteafterinstall

[Code]
#IFDEF UNICODE
  #DEFINE AW "W"
#ELSE
  #DEFINE AW "A"
#ENDIF

const
  WAIT_TIMEOUT = $00000102;
  SEE_MASK_NOCLOSEPROCESS = $00000040;
  INFINITE = $FFFFFFFF;     { Infinite timeout }

type
  TShellExecuteInfo = record
    cbSize: DWORD;
    fMask: Cardinal;
    Wnd: HWND;
    lpVerb: string;
    lpFile: string;
    lpParameters: string;
    lpDirectory: string;
    nShow: Integer;
    hInstApp: THandle;
    lpIDList: DWORD;
    lpClass: string;
    hkeyClass: THandle;
    dwHotKey: DWORD;
    hMonitor: THandle;
    hProcess: THandle;
  end;

function ShellExecuteEx(var lpExecInfo: TShellExecuteInfo): BOOL;
  external 'ShellExecuteEx{#AW}@shell32.dll stdcall';
function WaitForSingleObject(hHandle: THandle; dwMilliseconds: DWORD): DWORD;
  external 'WaitForSingleObject@kernel32.dll stdcall';
function CloseHandle(hObject: THandle): BOOL; external 'CloseHandle@kernel32.dll stdcall';

type
  TMsg = record
    hwnd: HWND;
    message: UINT;
    wParam: Longint;
    lParam: Longint;
    time: DWORD;
    pt: TPoint;
  end;

const
  PM_REMOVE = 1;

function PeekMessage(var lpMsg: TMsg; hWnd: HWND; wMsgFilterMin, wMsgFilterMax, wRemoveMsg: UINT): BOOL; external 'PeekMessageA@user32.dll stdcall';
function TranslateMessage(const lpMsg: TMsg): BOOL; external 'TranslateMessage@user32.dll stdcall';
function DispatchMessage(const lpMsg: TMsg): Longint; external 'DispatchMessageA@user32.dll stdcall';

procedure AppProcessMessage;
var
  Msg: TMsg;
begin
  while PeekMessage(Msg, WizardForm.Handle, 0, 0, PM_REMOVE) do begin
    TranslateMessage(Msg);
    DispatchMessage(Msg);
  end;
end;

procedure Unzip(source: String; targetdir: String);
var
  unzipTool, unzipParams : String; // path and param for the unzip tool
  ExecInfo: TShellExecuteInfo;     // info object for ShellExecuteEx()
begin
  // source and targetdir might contain {tmp} or {app} constant, so expand/resolve it to path names
  source := ExpandConstant(source);
  targetdir := ExpandConstant(targetdir);

  // prepare 7zip execution
  unzipTool := ExpandConstant('{tmp}\7za.exe');
  ExtractTemporaryFile('7za.exe');
  unzipParams := ' x "' + source + '" -o"' + targetdir + '" -y';

  // prepare information about the application being executed by ShellExecuteEx()
  ExecInfo.cbSize := SizeOf(ExecInfo);
  ExecInfo.fMask := SEE_MASK_NOCLOSEPROCESS;
  ExecInfo.Wnd := 0;
  ExecInfo.lpFile := unzipTool;
  ExecInfo.lpParameters := unzipParams;
  ExecInfo.nShow := SW_HIDE;

  if not FileExists(unzipTool) then
  begin
    MsgBox('UnzipTool not found: ' + unzipTool, mbError, MB_OK);
  end
  else if not FileExists(source) then
  begin
    MsgBox('File was not found while trying to unzip: ' + source, mbError, MB_OK);
  end
  else
  begin
    {
      The unzip tool is executed via ShellExecuteEx().
      Then the installer uses a while loop with the condition
      WaitForSingleObject and a very minimal timeout
      to execute AppProcessMessage.

      AppProcessMessage is itself a helper function, because
      Inno Setup does not provide Application.ProcessMessages().
      Its job is to be the message pump to the Inno Setup GUI.

      This trick makes the window responsive/draggable again,
      while the extraction is done in the background.
    }
    if ShellExecuteEx(ExecInfo) then
    begin
      while WaitForSingleObject(ExecInfo.hProcess, 100) = WAIT_TIMEOUT do
      begin
        AppProcessMessage;
        if WizardForm.ProgressGauge.Position = 100 then
          WizardForm.ProgressGauge.Position := 0
        else
          WizardForm.ProgressGauge.Position := WizardForm.ProgressGauge.Position + 1;
      end;
      CloseHandle(ExecInfo.hProcess);
    end;
  end;
end;

var
  DownloadPage: TDownloadWizardPage;

function OnDownloadProgress(const Url, FileName: String; const Progress, ProgressMax: Int64): Boolean;
begin
  if Progress = ProgressMax then
    Log(Format('Successfully downloaded file to {tmp}: %s', [FileName]));
  Result := True;
end;

procedure InitializeWizard;
begin
  DownloadPage := CreateDownloadPage(SetupMessage(msgWizardPreparing), SetupMessage(msgPreparingDesc), @OnDownloadProgress);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  ProgramVersion: string;
  DownloadURL: string;
  DownloadFileName: string;
begin
  if CurPageID = wpReady then
  begin
    // Prompt the user to select the version of the program
    ProgramVersion := '';
    if MsgBox('Do you want to download the CUDA version of MISST 3.1.0?', mbConfirmation, MB_YESNO) = IDYES then
    begin
      ProgramVersion := 'cuda';
    end
    else
    begin
      ProgramVersion := 'cpu';
    end;

    // Set the download URL and filename based on the selected version
    if ProgramVersion = 'cuda' then
    begin
      DownloadURL := 'https://github.com/Frikallo/MISST/releases/download/V3.1.0/MISST_CUDA_3.1.0_Release_Win.7z';
      DownloadFileName := 'MISST.7z';
    end
    else
    begin
      DownloadURL := 'https://github.com/Frikallo/MISST/releases/download/V3.1.0/MISST_CPU_3.1.0_Release_Win.7z';
      DownloadFileName := 'MISST.7z';
    end;

    DownloadPage.Clear;
    DownloadPage.Add(DownloadURL, DownloadFileName, '');
    DownloadPage.Show;

    try
      try
        DownloadPage.Download;
        Result := True;
      except
        SuppressibleMsgBox(AddPeriod(GetExceptionMessage), mbCriticalError, MB_OK, IDOK);
        Result := False;
      end;
    finally
      DownloadPage.Hide;
    end;
  end
  else
    Result := True;
end;

function GetFirstSubfolder(Param: String): String;
var
  FindRec: TFindRec;
begin
  Result := '';

  if FindFirst(ExpandConstant('{app}\*'), FindRec) then
  begin
    try
      while FindNext(FindRec) do
      begin
        if (FindRec.Attributes and FILE_ATTRIBUTE_DIRECTORY <> 0) and (FindRec.Name <> '.') and (FindRec.Name <> '..') then
        begin
          Result := FindRec.Name;
          Break;
        end;
      end;
    finally
      FindClose(FindRec);
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ExtractResultCode: Integer;
  ArchivePath: string;
begin
  if CurStep = ssInstall then
  begin
    ArchivePath := ExpandConstant('{tmp}\MISST.7z');
    ExtractResultCode := 0;

    if not FileExists(ArchivePath) then
    begin
      MsgBox('The MISST.7z archive file is missing.', mbError, MB_OK);
      WizardForm.Close;
    end
    else
    begin
      WizardForm.StatusLabel.Caption := 'Extracting...';
      WizardForm.ProgressGauge.Max := 100; // Set the maximum value for the progress bar
      WizardForm.ProgressGauge.Position := 0; // Initialize the progress bar position

      Unzip(ArchivePath, ExpandConstant('{app}'));
      RenameFile(ExpandConstant('{app}\'+GetFirstSubfolder('')),ExpandConstant('{app}\MISST'));
    end;
  end;
end;

[Run]
Filename: "{app}\MISST\MISST.exe"; Description: "{cm:LaunchProgram,MISST}"; Flags: nowait postinstall skipifsilent