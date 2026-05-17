#NoEnv
#Persistent
#SingleInstance Force
SetTitleMatchMode, 2
SetBatchLines, -1

basePath := A_ScriptDir . "\"
gameExe := "PrimeDiablo.exe"

checkDelay := 2000
isMinimized := false

pulse := 120
pulseDir := 1
spinState := 1
loadPos := 0

particles := []
hoverBtn := ""
neonPulse := 120
neonDir := 1

if !A_IsAdmin
{
    Run *RunAs "%A_ScriptFullPath%"
    ExitApp
}

; ================= LOADER =================
Gui, Loader: +AlwaysOnTop -Caption +ToolWindow
Gui, Loader: Color, 000000

Gui, Loader: Font, cFF2A2A s32 Bold, Yu Gothic UI
Gui, Loader: Add, Text, x30 y10 vSpinIcon BackgroundTrans, K

Gui, Loader: Font, cFFFFFF s14 Bold, Yu Gothic UI
Gui, Loader: Add, Text, x70 y28 BackgroundTrans, Kakashi Hub

Gui, Loader: Font, cAA0000 s9 Bold
Gui, Loader: Add, Text, x20 y65 w200 Center vLoadStatus BackgroundTrans, Iniciando...

Gui, Loader: Add, Progress, x20 y85 w220 h8 vLoadBar Background222222 c550000
Gui, Loader: Show, w260 h110

SetTimer, LoaderAnim, 30

if !FileExist(basePath . gameExe)
{
    GuiControl, Loader:, LoadStatus, ERRO
    Sleep, 2000
    ExitApp
}

GuiControl, Loader:, LoadStatus, Abrindo jogo...
Sleep, 800
Run, %basePath%%gameExe%
Sleep, 1500

GuiControl, Loader:, LoadStatus, Carregando HUB...
Sleep, 800

SetTimer, LoaderAnim, Off
Gui, Loader: Destroy

; ================= AUTO UPDATE =================
urlVersion := "https://raw.githubusercontent.com/ghkusanagy-hub/KakashiHub/main/version.txt"
urlExe     := "https://raw.githubusercontent.com/ghkusanagy-hub/KakashiHub/main/KakashiHub.exe"

localVersion := "1.0"

tempFile := A_Temp "\version.txt"

UrlDownloadToFile, %urlVersion%, %tempFile%

FileRead, remoteVersion, %tempFile%

if (remoteVersion != localVersion)
{
    MsgBox, Nova versão encontrada! Atualizando...

    UrlDownloadToFile, %urlExe%, %A_ScriptDir%\update.exe

    Run, %A_ScriptDir%\update.exe
    ExitApp
}

; ================= GUI =================
Gui, +AlwaysOnTop -Caption +ToolWindow
Gui, Color, 000000

; --- ADICIONADO: Imagem de fundo ---
; O AutoHotkey vai carregar a imagem "kakashi.jpg" que estiver na mesma pasta do script
Gui, Add, Picture, x0 y0 w200 h250, %basePath%kakashi.jpg

Gui, Add, Text, x0 y0 w200 h2 vTopBorder Background550000
Gui, Add, Text, x0 y248 w200 h2 vBotBorder Background220000
Gui, Add, Text, x0 y0 w2 h250 vLeftBorder Background330000
Gui, Add, Text, x198 y0 w2 h250 vRightBorder Background110000

Gui, Font, cFFFFFF s10 Bold
; Adicionado BackgroundTrans para o fundo ficar transparente sobre a imagem
Gui, Add, Text, x10 y5 vTitulo BackgroundTrans, Kakashi BH HUB

Gui, Font, cFFFFFF s9 Bold
Gui, Add, Button, x140 y2 w20 h20 gMinimizar, _
Gui, Add, Button, x165 y2 w20 h20 gFechar, X

Gui, Font, cAAAAAA s9 Bold
; Adicionado BackgroundTrans para o fundo ficar transparente sobre a imagem
Gui, Add, Text, x10 y30 w180 Center vStatus BackgroundTrans, [NENHUM]


Gui, Font, cFFFFFF s9
Gui, Add, Text, x10 y60  w180 h25 vBtn1 gNormal  Center BackgroundTrans, NORMAL
Gui, Add, Text, x10 y90  w180 h25 vBtn2 gElite   Center BackgroundTrans, ELITE
Gui, Add, Text, x10 y120 w180 h25 vBtn3 gRW      Center BackgroundTrans, KAKASHI
Gui, Add, Text, x10 y150 w180 h25 vBtn4 gMF      Center BackgroundTrans, MF
Gui, Add, Text, x10 y180 w180 h25 vBtn5 grwall   Center BackgroundTrans, RW ALL
Gui, Add, Text, x10 y210 w180 h25 gBuilds        Center BackgroundTrans, BUILDS

SysGet, MonitorWorkArea, MonitorWorkArea
xPos := MonitorWorkAreaRight - 210
yPos := MonitorWorkAreaTop + 5

Gui, Show, x%xPos% y%yPos% w200 h250, BH HUB
WinSet, Transparent, 230, BH HUB

SetTimer, MonitorarJogo, %checkDelay%
SetTimer, AnimacaoUI, 80
SetTimer, NeonAnim, 60
SetTimer, HoverCheck, 50
SetTimer, Particulas, 100

return

; ================= BUILDS MENU ================= 
Builds:
Gui, Builds: Destroy
Gui, Builds: +AlwaysOnTop +ToolWindow
Gui, Builds: Color, 000000

; Gui, Builds: Add, Picture, x0 y0 w400 h420, %basePath%kakashi.jpg

Gui, Builds: Font, cFF2A2A s11 Bold
Gui, Builds: Add, Text, x10 y5 BackgroundTrans, BUILDS GUIDE

Gui, Builds: Font, cFFFFFF s9 Bold
Gui, Builds: Add, Button, x10 y30 w120 gBuild_Sorc, Sorceress
Gui, Builds: Add, Button, x140 y30 w120 gBuild_Pala, Paladin
Gui, Builds: Add, Button, x270 y30 w120 gBuild_Ama, Amazon

Gui, Builds: Add, Button, x10 y60 w120 gBuild_Barb, Barbarian
Gui, Builds: Add, Button, x140 y60 w120 gBuild_Nec, Necromancer
Gui, Builds: Add, Button, x270 y60 w120 gBuild_Ass, Assassin

; ===== NOVO BOTÃO DRUID =====
Gui, Builds: Add, Button, x140 y90 w120 gBuild_Druid, Druid

; ===== AJUSTE DO CAMPO DE TEXTO =====
Gui, Builds: Font, cFFFFFF s9, Consolas
Gui, Builds: Add, Edit, x10 y130 w380 h270 vBuildInfo ReadOnly

Gui, Builds: Show,, Builds
return

; ================= BUILDS DETALHADAS =================

Build_Sorc:
GuiControl,, BuildInfo,
(
 SORCERESS

SKILLS:
1-15 Fire Bolt
15-30 Fireball
30+ Frozen Orb + Fireball

RW:
Leaf / Stealth / Spirit / Insight

DICAS:
Farm Countess > Mephisto
)
return

Build_Pala:
GuiControl,, BuildInfo,
(
 PALADIN

SKILLS:
Zeal > Hammer

RW:
Spirit / Stealth / Insight

DICAS:
Melhor farm build
)
return

Build_Ama:
GuiControl,, BuildInfo,
(
 AMAZON

SKILLS:
Poison > Lightning Fury

RW:
Stealth / Insight / Titans

DICAS:
Melhor pra cows
)
return

; 🔥 DRUIDA SEPARADO CORRETAMENTE
Build_Druid:
GuiControl,, BuildInfo,
(
 DRUID

SKILLS:
Fire > Wind (Tornado / Hurricane)

RW:
Leaf > Spirit > Hoto

DICAS:
Muito forte mid/late game
Excelente controle de mobs
)
return

Build_Barb:
GuiControl,, BuildInfo,
(
 BARB

SKILLS:
Double Swing > WW

RW:
Honor / Oath / Grief

DICAS:
Dependente de arma
)
return

Build_Nec:
GuiControl,, BuildInfo,
(
 NECRO

SKILLS:
Skeleton + CE

RW:
White / Spirit

DICAS:
Muito seguro
)
return

Build_Ass:
GuiControl,, BuildInfo,
(
 ASSASSIN

SKILLS:
Fire > Lightning Trap

RW:
Stealth / Spirit

DICAS:
Muito forte early
)
return
; ================= ANIMAÇÕES =================
LoaderAnim:
loadPos += 2
if (loadPos > 100)
    loadPos := 0
GuiControl, Loader:, LoadBar, %loadPos%
return

AnimacaoUI:
pulse += pulseDir * 5
if (pulse > 255)
    pulseDir := -1
if (pulse < 120)
    pulseDir := 1
cor := Format("{:02X}", pulse)
Gui, Font, c%cor%0000 s10 Bold
GuiControl, Font, Titulo
return

NeonAnim:
neonPulse += neonDir * 5
if (neonPulse > 255)
    neonDir := -1
if (neonPulse < 80)
    neonDir := 1
cor := Format("{:02X}", neonPulse)
GuiControl, +Background%cor%0000, TopBorder
GuiControl, +Background%cor%0000, BotBorder
return

HoverCheck:
MouseGetPos,,, win, ctrl

defaultColor := "cAAAAAA"
hoverColor   := "cFFFFFF"

; lista dos botões válidos
if (ctrl != "Btn1" && ctrl != "Btn2" && ctrl != "Btn3" && ctrl != "Btn4" && ctrl != "Btn5")
{
    ; se saiu de um botão, reseta o último
    if (hoverBtn != "")
    {
        Gui, Font, %defaultColor% s9
        GuiControl, Font, %hoverBtn%
        hoverBtn := ""
    }
    return
}

; se mudou de botão
if (ctrl != hoverBtn)
{
    ; reset antigo
    if (hoverBtn != "")
    {
        Gui, Font, %defaultColor% s9
        GuiControl, Font, %hoverBtn%
    }

    ; aplica hover novo
    Gui, Font, %hoverColor% s9 Bold
    GuiControl, Font, %ctrl%

    hoverBtn := ctrl
}
return

Particulas:
Random, px, 10, 180
id := "P" . A_TickCount
Gui, Add, Text, x%px% y220 w3 h3 v%id% BackgroundFF0000
particles.Push({id: id, y: 220, life: 255})

for index, p in particles.Clone() {
    p.y -= 4
    p.life -= 15
    if (p.life <= 0) {
        GuiControl, Hide, % p.id
        particles.RemoveAt(index)
        continue
    }
    cor := Format("{:02X}", p.life)
    GuiControl, Move, % p.id, % "y" p.y
    GuiControl, +Background%cor%0000, % p.id
}
return

; ================= CONTROLE =================
~LButton::
MouseGetPos,,, win
WinGetTitle, title, ahk_id %win%
if (title = "BH HUB")
    PostMessage, 0xA1, 2,,, A
return

MonitorarJogo:
Process, Exist, %gameExe%
if (ErrorLevel = 0)
    ExitApp
return

Minimizar:
if (!isMinimized)
{
    Gui, Show, w200 h25
    isMinimized := true
}
else
{
    Gui, Show, w200 h250
    isMinimized := false
}
return

Fechar:
Process, Close, %gameExe%
ExitApp

; ================= FILTROS =================
TrocarFiltro(nomeArquivo, nomeLabel) {
    global basePath
    FileCopy, % basePath . nomeArquivo, % basePath . "BH.cfg", 1
    Sleep, 150
    WinActivate, ahk_exe Game.exe
    SendInput, ^r
    GuiControl,, Status, [%nomeLabel%]
}

Normal:
TrocarFiltro("BH_normal.cfg", "NORMAL")
return

Elite:
TrocarFiltro("BH_elite.cfg", "ELITE")
return

RW:
TrocarFiltro("BH_rw.cfg", "KAKASHI")
return

MF:
TrocarFiltro("BH_mf.cfg", "MF")
return

rwall:
TrocarFiltro("BH_rwall.cfg", "RW ALL")
return

; ================= PYTHON INTEGRATION =================
SetTimer, LerComando, 500
return

LerComando:
FileRead, cmd, command.txt
if (cmd = "")
    return

FileDelete, command.txt

if (cmd = "NORMAL")
    Gosub, Normal
else if (cmd = "ELITE")
    Gosub, Elite
else if (cmd = "RW")
    Gosub, RW
else if (cmd = "MF")
    Gosub, MF
else if (cmd = "RWALL")
    Gosub, rwall

return
