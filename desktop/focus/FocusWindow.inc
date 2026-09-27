// SoulLink Focus frontend additions, GPL-3.0-or-later.
// Compiled into the unmodified melonDS 1.1 emulation core's Qt frontend.
#include <QToolBar>
#include <QToolButton>
#include <QPushButton>
#include <QLabel>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QWidgetAction>
#include <QComboBox>
#include <QCheckBox>
#include <QSlider>
#include <QSaveFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <QRegularExpression>
#include <QSignalBlocker>
#include <QDesktopServices>
#include <QTimer>
#include <QDateTime>
#include <QFileInfo>

static const char* focusStyle = R"QSS(
QMainWindow, QDialog, QMenu, QWidget#focusPopup { background: #101214; color: #eceff1; }
QWidget { color: #eceff1; font-family: "Segoe UI", "Arial"; font-size: 13px; }
QToolBar { background: #101214; border: none; spacing: 9px; padding: 10px; }
QLabel { background: transparent; }
QLabel#focusBrand { font-size: 22px; font-weight: 700; padding-right: 22px; }
QLabel#focusStatus, QLabel#focusHint { color: #969b9f; font-size: 12px; }
QFrame#focusPill { background: #191c1f; border: 1px solid #34383c; border-radius: 24px; }
QPushButton, QToolButton { background: #1b1e21; border: 1px solid #353a3e; border-radius: 9px; padding: 10px 18px; }
QPushButton:hover, QToolButton:hover { background: #2b2c29; border-color: #bb964c; }
QPushButton:pressed, QToolButton:pressed { background: #373021; }
QPushButton:disabled, QToolButton:disabled { color: #676e74; }
QPushButton#focusPlayer, QPushButton#focusNew { border-color: #d6ac57; color: #efc572; background: #272319; }
QPushButton#focusFlat { border: none; background: transparent; }
QMenu { border: 1px solid #3c4146; border-radius: 12px; padding: 8px; }
QMenu::item { padding: 8px 18px; }
QMenu::item:selected { background: #343024; color: #efc572; }
QComboBox, QSpinBox, QLineEdit { background: #22262a; border: 1px solid #484e54; border-radius: 6px; padding: 7px; }
QComboBox QAbstractItemView { background: #22262a; color: #eceff1; selection-background-color: #66502b; }
QCheckBox { spacing: 8px; padding: 4px; }
QCheckBox::indicator { width: 16px; height: 16px; }
QSlider::groove:horizontal { height: 4px; background: #3e4449; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #d6ac57; }
QSlider::handle:horizontal { background: #efc572; width: 16px; margin: -6px 0; border-radius: 8px; }
QGroupBox { border: 1px solid #42484d; border-radius: 6px; margin-top: 16px; padding-top: 16px; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; }
QTabWidget::pane { border: 1px solid #42484d; }
QTabBar::tab { background: #22262a; padding: 9px; }
QTabBar::tab:selected { color: #efc572; }
)QSS";

void MainWindow::focusReturn(const QString& action)
{
    auto answer = QMessageBox::question(this, "Soul Link",
        "Bitte zuerst im Spiel speichern. Dieser Wechsel speichert nicht automatisch.\n\n"
        "Das Spielfenster jetzt schließen und zum Launcher wechseln?",
        QMessageBox::Yes | QMessageBox::No, QMessageBox::No);
    if (answer != QMessageBox::Yes) return;
    setProperty("focusReturnAction", action);
    close();
}

void MainWindow::finishFocusRequest()
{
    QString action = property("focusReturnAction").toString();
    QString path = qEnvironmentVariable("SOULLINK_REQUEST");
    if (action.isEmpty() || path.isEmpty()) return;
    QSaveFile file(path);
    if (file.open(QIODevice::WriteOnly))
    {
        file.write(QJsonDocument(QJsonObject{{"action", action}}).toJson());
        file.commit();
    }
}

void MainWindow::initFocus()
{
    QApplication::setStyle("Fusion");
    qApp->setStyleSheet(focusStyle);
    menuBar()->setFixedHeight(0); // Original menus remain available through Mehr.
    QString player = qEnvironmentVariable("SOULLINK_PLAYER", "Optimus");
    setWindowTitle("Soul Link · Focus · " + (player=="Optimus"?QString("Anakin"):QString("Obi-Wan")));
    setMinimumSize(860, 590);
    if (windowCfg.GetString("Geometry").empty()) resize(1200, 800);

    auto button = [](const QString& text, QWidget* parent) {
        auto* b = new QPushButton(text, parent);
        b->setFocusPolicy(Qt::NoFocus);
        b->setCursor(Qt::PointingHandCursor);
        return b;
    };
    auto* header = new QToolBar(this);
    header->setMovable(false); header->setFloatable(false);
    addToolBar(Qt::TopToolBarArea, header);
    auto* brand = new QLabel("SOUL <span style='color:#efc572'>LINK</span>", header);
    brand->setObjectName("focusBrand"); header->addWidget(brand);
    for (QString name : {QString("Optimus"), QString("Bee")})
    {
        auto* b = button(name=="Optimus"?QString("Anakin"):QString("Obi-Wan"),header);
        b->setObjectName(name == player ? "focusPlayer" : "focusFlat");
        header->addWidget(b);
        if (name != player) connect(b,&QPushButton::clicked,this,[this,name]{focusReturn("start:"+name);});
    }
    auto* stretch = new QWidget(header);
    stretch->setSizePolicy(QSizePolicy::Expanding,QSizePolicy::Preferred); header->addWidget(stretch);
    auto* status = new QLabel("SoulSilver  ·  Focus",header);
    status->setObjectName("focusStatus"); header->addWidget(status);
    auto* newRound = button("+ Neue Runde",header); newRound->setObjectName("focusNew");
    header->addWidget(newRound);
    connect(newRound,&QPushButton::clicked,this,[this]{focusReturn("new-round");});
    const QString mirrorPath=qEnvironmentVariable("SOULLINK_MIRROR");
    const QString website=qEnvironmentVariable("SOULLINK_WEBSITE");
    if(!website.isEmpty()) {
        auto* web=button("Website ↗",header);header->addWidget(web);
        connect(web,&QPushButton::clicked,this,[website]{QDesktopServices::openUrl(QUrl(website));});
    }
    auto* streamBar=new QToolBar(this);streamBar->setMovable(false);streamBar->setFloatable(false);
    addToolBar(Qt::BottomToolBarArea,streamBar);
    if(!mirrorPath.isEmpty()) {
        auto* mirror=button("Übertragung starten",streamBar);streamBar->addWidget(mirror);
        auto* connectionStatus=new QLabel("Verbindung wird geprüft",streamBar);streamBar->addWidget(connectionStatus);
        connectionStatus->setMaximumWidth(270);
        const QFileInfo info(mirrorPath);
        const QString stem=info.path()+"/"+info.completeBaseName();
        auto refresh=[mirror,mirrorPath,connectionStatus,stem]{
            const bool enabled=QFileInfo::exists(mirrorPath+".enabled");
            mirror->setText(enabled?"Übertragung stoppen":"Übertragung starten");
            QString text=enabled?"Warte auf Spielbild":"Übertragung aus";
            QFile file(stem+".status.json");
            if(enabled&&file.open(QIODevice::ReadOnly)){
                const auto obj=QJsonDocument::fromJson(file.readAll()).object();
                if(QDateTime::currentSecsSinceEpoch()-obj.value("at").toDouble()<8)
                    text=obj.value("message").toString(text);
            }
            connectionStatus->setText(text);connectionStatus->setToolTip(text);
        };
        refresh();
        connect(mirror,&QPushButton::clicked,this,[this,mirrorPath,refresh]{
            const QString flag=mirrorPath+".enabled";
            if(QFileInfo::exists(flag)) QFile::remove(flag);
            else {QSaveFile f(flag);if(f.open(QIODevice::WriteOnly)){f.write("on");f.commit();globalCfg.SetBool("PauseLostFocus",false);}}
            refresh();
        });
        auto* retry=button("Neu verbinden",streamBar);streamBar->addWidget(retry);
        connect(retry,&QPushButton::clicked,this,[stem]{QSaveFile file(stem+".reconnect");if(file.open(QIODevice::WriteOnly)){file.write("retry");file.commit();}});
        auto* connectionTimer=new QTimer(this);
        connect(connectionTimer,&QTimer::timeout,this,refresh);connectionTimer->start(1000);
    } else if(!website.isEmpty()) {
        streamBar->addWidget(new QLabel("Teams & Fangkarte verbunden · Bildübertragung entfernt",streamBar));
    } else {
        streamBar->addWidget(new QLabel("Website nicht verbunden",streamBar));
        auto* connectWebsite=button("Website verbinden",streamBar);streamBar->addWidget(connectWebsite);
        connect(connectWebsite,&QPushButton::clicked,this,[this]{focusReturn("connect-website");});
    }

    auto* footer = new QToolBar(this);
    footer->setMovable(false); footer->setFloatable(false);
    addToolBarBreak(Qt::BottomToolBarArea);
    addToolBar(Qt::BottomToolBarArea,footer);
    auto* left = new QWidget(footer); left->setSizePolicy(QSizePolicy::Expanding,QSizePolicy::Preferred);
    footer->addWidget(left);
    auto* pill = new QFrame(footer); pill->setObjectName("focusPill");
    auto* controls = new QHBoxLayout(pill); controls->setContentsMargins(12,5,12,5); controls->setSpacing(4);
    footer->addWidget(pill);
    auto* right = new QWidget(footer); right->setSizePolicy(QSizePolicy::Expanding,QSizePolicy::Preferred);
    footer->addWidget(right);
    auto* pause = button("Pause",pill); pause->setObjectName("focusFlat"); controls->addWidget(pause);
    auto updatePause = [this,pause]{pause->setEnabled(actPause->isEnabled());pause->setText(actPause->isChecked()?"Weiter":"Pause");};
    connect(actPause,&QAction::changed,this,updatePause); updatePause();
    connect(pause,&QPushButton::clicked,actPause,&QAction::trigger);

    auto makePopup = [this](QPushButton* anchor) {
        auto* menu = new QMenu(this);
        auto* contents = new QWidget(menu); contents->setObjectName("focusPopup"); contents->setMinimumWidth(320);
        auto* layout = new QVBoxLayout(contents); layout->setSpacing(12); layout->setContentsMargins(18,18,18,18);
        auto* item = new QWidgetAction(menu); item->setDefaultWidget(contents); menu->addAction(item);
        connect(anchor,&QPushButton::clicked,this,[menu,anchor]{
            menu->adjustSize();
            menu->popup(anchor->mapToGlobal(QPoint(anchor->width()/2-menu->sizeHint().width()/2,-menu->sizeHint().height()-12)));
        });
        connect(menu,&QMenu::aboutToShow,this,[this]{emuThread->emuPause();});
        connect(menu,&QMenu::aboutToHide,this,[this]{if(emuInstance){Config::Save();emuThread->emuUnpause();}});
        return std::make_pair(menu,layout);
    };
    auto* sound = button("Sound",pill); sound->setObjectName("focusFlat"); controls->addWidget(sound);
    auto audio = makePopup(sound);
    audio.second->addWidget(new QLabel("Lautstärke",this));
    auto* volume = new QSlider(Qt::Horizontal,this); volume->setRange(0,100);
    volume->setValue(qRound(emuInstance->audioVolume*100.0/256.0)); audio.second->addWidget(volume);
    auto* volText = new QLabel(this); audio.second->addWidget(volText);
    connect(audio.first,&QMenu::aboutToShow,this,[this,volume,volText]{
        volume->setValue(qRound(emuInstance->audioVolume*100.0/256.0));volText->setText(QString::number(volume->value())+" %");});
    connect(volume,&QSlider::valueChanged,this,[this,volText](int value){
        int vol=qRound(value*256.0/100.0);localCfg.SetInt("Audio.Volume",vol);
        onUpdateAudioVolume(vol,0);volText->setText(QString::number(value)+" %");});

    auto* keys = button("Tasten",pill); keys->setObjectName("focusFlat"); controls->addWidget(keys);
    connect(keys,&QPushButton::clicked,this,&MainWindow::onOpenInputConfig);
    auto* image = button("Bild",pill); image->setObjectName("focusFlat"); controls->addWidget(image);
    auto visual = makePopup(image);
    auto* heading=new QLabel("Bild & Auflösung",this);heading->setStyleSheet("font-size:17px;font-weight:600;");visual.second->addWidget(heading);
    visual.second->addWidget(new QLabel("Interne 3D-Auflösung",this));
    auto* resolution=new QComboBox(this);
    for(int factor=1;factor<=16;factor++) resolution->addItem(QString("%1×  ·  %2 × %3").arg(factor).arg(256*factor).arg(192*factor),factor);
    resolution->setCurrentIndex(resolution->findData(globalCfg.GetInt("3D.GL.ScaleFactor")));
    visual.second->addWidget(resolution);
    connect(resolution,QOverload<int>::of(&QComboBox::activated),this,[this,resolution](int index){
        globalCfg.SetInt("3D.GL.ScaleFactor",resolution->itemData(index).toInt());onUpdateVideoSettings(false);});
    visual.second->addWidget(new QLabel("Pixel-Skalierung",this));
    auto* filter=new QComboBox(this);filter->addItem("Scharf · klare Pixel",false);filter->addItem("Weich · geglättet",true);
    filter->setCurrentIndex(windowCfg.GetBool("ScreenFilter")?1:0);visual.second->addWidget(filter);
    connect(filter,QOverload<int>::of(&QComboBox::activated),this,[this](int index){
        onChangeScreenFiltering(index==1);actScreenFiltering->setChecked(index==1);});
    auto* integer=new QCheckBox("Ganzzahlige Pixel-Skalierung",this);
    integer->setChecked(windowCfg.GetBool("IntegerScaling"));visual.second->addWidget(integer);
    connect(integer,&QCheckBox::toggled,this,[this](bool value){onChangeIntegerScaling(value);actIntegerScaling->setChecked(value);});
    visual.second->addWidget(new QLabel("Bildschirmlayout",this));
    auto* layout=new QComboBox(this);layout->addItems({"Focus · Spiel groß + Touch rechts","Nebeneinander · gleich groß","Untereinander"});
    layout->setCurrentIndex(windowCfg.GetInt("ScreenLayout")==1?2:windowCfg.GetInt("ScreenSizing")==0?1:0);
    visual.second->addWidget(layout);
    connect(layout,QOverload<int>::of(&QComboBox::activated),this,[this](int index){
        int arrangement=index==2?1:2, sizing=index==0?1:0;
        windowCfg.SetInt("ScreenLayout",arrangement);windowCfg.SetInt("ScreenSizing",sizing);
        windowCfg.SetInt("ScreenRotation",0);windowCfg.SetBool("ScreenSwap",false);
        actScreenLayout[arrangement]->setChecked(true);actScreenSizing[sizing]->setChecked(true);
        actScreenRotation[0]->setChecked(true);actScreenSwap->setChecked(false);emit screenLayoutChange();});
    visual.second->addWidget(new QLabel("FPS / Spieltempo",this));
    auto* speed=new QComboBox(this);
    for(int fps : {60,90,120,0}) speed->addItem(fps?QString::number(fps)+" FPS":"Unbegrenzt",fps);
    speed->setCurrentIndex(speed->findData(emuInstance->doLimitFPS?qRound(emuInstance->targetFPS):0));visual.second->addWidget(speed);
    connect(speed,QOverload<int>::of(&QComboBox::activated),this,[this,speed](int index){
        int fps=speed->itemData(index).toInt();globalCfg.SetDouble("TargetFPS",fps?fps:60);
        emuInstance->targetFPS=fps?fps:60;onChangeLimitFramerate(fps!=0);onChangeAudioSync(fps==60);
        actLimitFramerate->setChecked(fps!=0);actAudioSync->setChecked(fps==60);
        globalCfg.SetBool("Screen.VSync",fps==60);onUpdateVideoSettings(false);});
    auto* hint=new QLabel("3D-Auflösung schärft 3D-Flächen, nicht 2D-Sprites.\nÜber 60 FPS beschleunigt auch Spiel und Ton.",this);
    hint->setObjectName("focusHint");hint->setWordWrap(true);visual.second->addWidget(hint);
    connect(visual.first,&QMenu::aboutToShow,this,[this,resolution,filter,integer,layout,speed]{
        QSignalBlocker blocked(integer);
        resolution->setCurrentIndex(resolution->findData(globalCfg.GetInt("3D.GL.ScaleFactor")));
        resolution->setEnabled(globalCfg.GetInt("3D.Renderer")!=renderer3D_Software);
        filter->setCurrentIndex(windowCfg.GetBool("ScreenFilter")?1:0);
        integer->setChecked(windowCfg.GetBool("IntegerScaling"));
        layout->setCurrentIndex(windowCfg.GetInt("ScreenLayout")==1?2:windowCfg.GetInt("ScreenSizing")==0?1:0);
        speed->setCurrentIndex(speed->findData(emuInstance->doLimitFPS?qRound(emuInstance->targetFPS):0));
    });
    auto* fullscreen=button("Vollbild",pill);fullscreen->setObjectName("focusFlat");controls->addWidget(fullscreen);
    connect(fullscreen,&QPushButton::clicked,this,&MainWindow::toggleFullscreen);
    auto* more=button("Mehr",pill);more->setObjectName("focusFlat");controls->addWidget(more);
    auto* advanced=new QMenu(this);for(auto* action : menuBar()->actions()) advanced->addAction(action);
    connect(more,&QPushButton::clicked,this,[advanced,more]{advanced->popup(more->mapToGlobal(QPoint(0,-advanced->sizeHint().height())));});
}
