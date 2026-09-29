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
#include <QFile>
#include <QFrame>
#include <QHash>
#include <QJsonArray>
#include <QSet>

static QString focusTypeName(int type)
{
    static const char* names[]={"Normal","Kampf","Flug","Gift","Boden","Gestein","Käfer","Geist","Stahl","?","Feuer","Wasser","Pflanze","Elektro","Psycho","Eis","Drache","Unlicht"};
    return type>=0&&type<18?QString::fromUtf8(names[type]):QString("?");
}

static int focusMoveType(const QString& type)
{
    static const QHash<QString,int> types={{"NORMAL",0},{"FIGHTING",1},{"FLYING",2},{"POISON",3},
        {"GROUND",4},{"ROCK",5},{"BUG",6},{"GHOST",7},{"STEEL",8},{"FIRE",10},{"WATER",11},
        {"GRASS",12},{"ELECTRIC",13},{"PSYCHIC",14},{"ICE",15},{"DRAGON",16},{"DARK",17}};
    return types.value(type,-1);
}

static double focusTypeFactor(int attack,int defence)
{
    switch(attack){
    case 0:if(defence==5||defence==8)return .5;if(defence==7)return 0;break;
    case 1:if(defence==0||defence==5||defence==8||defence==15||defence==17)return 2;if(defence==2||defence==3||defence==6||defence==14)return .5;if(defence==7)return 0;break;
    case 2:if(defence==1||defence==6||defence==12)return 2;if(defence==5||defence==8||defence==13)return .5;break;
    case 3:if(defence==12)return 2;if(defence==3||defence==4||defence==5||defence==7)return .5;if(defence==8)return 0;break;
    case 4:if(defence==3||defence==5||defence==8||defence==10||defence==13)return 2;if(defence==6||defence==12)return .5;if(defence==2)return 0;break;
    case 5:if(defence==2||defence==6||defence==10||defence==15)return 2;if(defence==1||defence==4||defence==8)return .5;break;
    case 6:if(defence==12||defence==14||defence==17)return 2;if(defence==1||defence==2||defence==3||defence==7||defence==8||defence==10)return .5;break;
    case 7:if(defence==7||defence==14)return 2;if(defence==8||defence==17)return .5;if(defence==0)return 0;break;
    case 8:if(defence==5||defence==15)return 2;if(defence==8||defence==10||defence==11||defence==13)return .5;break;
    case 10:if(defence==6||defence==8||defence==12||defence==15)return 2;if(defence==5||defence==10||defence==11||defence==16)return .5;break;
    case 11:if(defence==4||defence==5||defence==10)return 2;if(defence==11||defence==12||defence==16)return .5;break;
    case 12:if(defence==4||defence==5||defence==11)return 2;if(defence==2||defence==3||defence==6||defence==8||defence==10||defence==12||defence==16)return .5;break;
    case 13:if(defence==2||defence==11)return 2;if(defence==12||defence==13||defence==16)return .5;if(defence==4)return 0;break;
    case 14:if(defence==1||defence==3)return 2;if(defence==8||defence==14)return .5;if(defence==17)return 0;break;
    case 15:if(defence==2||defence==4||defence==12||defence==16)return 2;if(defence==8||defence==10||defence==11||defence==15)return .5;break;
    case 16:if(defence==16)return 2;if(defence==8)return .5;break;
    case 17:if(defence==7||defence==14)return 2;if(defence==1||defence==8||defence==17)return .5;break;
    }
    return 1;
}

static double focusEffectiveness(int attack,const QJsonArray& types)
{
    double value=1;QSet<int> seen;
    for(const auto item:types){const int defence=item.toInt(-1);if(defence>=0&&!seen.contains(defence)){seen.insert(defence);value*=focusTypeFactor(attack,defence);}}
    return value;
}

static const char* focusStyle = R"QSS(
QMainWindow, QDialog, QMenu, QWidget#focusPopup { background: #101214; color: #eceff1; }
QWidget { color: #eceff1; font-family: "Segoe UI", "Arial"; font-size: 13px; }
QToolBar { background: #101214; border: none; spacing: 9px; padding: 10px; }
QLabel { background: transparent; }
QLabel#focusBrand { font-size: 22px; font-weight: 700; padding-right: 22px; }
QLabel#focusStatus, QLabel#focusHint { color: #969b9f; font-size: 12px; }
QFrame#focusPill { background: #191c1f; border: 1px solid #34383c; border-radius: 24px; }
QFrame#focusBattle { background: rgba(16,18,20,238); border: 1px solid #4b4433; border-radius: 14px; }
QLabel#focusBattleTitle { color: #efc572; font-size: 11px; font-weight: 700; }
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
    const QString battlePath=qEnvironmentVariable("SOULLINK_BATTLE");
    const QString battleDataPath=qEnvironmentVariable("SOULLINK_BATTLE_DATA");
    if(!battlePath.isEmpty()&&centralWidget()){
        auto* battleCard=new QFrame(centralWidget());battleCard->setObjectName("focusBattle");battleCard->setFixedWidth(330);
        battleCard->setAttribute(Qt::WA_TransparentForMouseEvents);battleCard->setMinimumHeight(88);
        auto* battleLayout=new QVBoxLayout(battleCard);battleLayout->setContentsMargins(16,14,16,14);battleLayout->setSpacing(7);
        auto* battleHeading=new QLabel("KAMPFHILFE · LIVE",battleCard);battleHeading->setObjectName("focusBattleTitle");battleLayout->addWidget(battleHeading);
        auto* enemyLabel=new QLabel("Warte auf einen Kampf …",battleCard);enemyLabel->setStyleSheet("font-size:16px;font-weight:650;");battleLayout->addWidget(enemyLabel);
        auto* weakLabel=new QLabel("Gegnerschwächen erscheinen automatisch.",battleCard);weakLabel->setObjectName("focusHint");weakLabel->setWordWrap(true);battleLayout->addWidget(weakLabel);
        auto* movesHeading=new QLabel("DEINE ATTACKEN",battleCard);movesHeading->setObjectName("focusBattleTitle");movesHeading->hide();battleLayout->addWidget(movesHeading);
        QList<QLabel*> moveLabels;
        for(int i=0;i<4;i++){auto* label=new QLabel(battleCard);label->setWordWrap(true);label->hide();battleLayout->addWidget(label);moveLabels.append(label);}
        QJsonObject moveData;
        QFile metadata(battleDataPath);
        if(metadata.open(QIODevice::ReadOnly))moveData=QJsonDocument::fromJson(metadata.readAll()).object().value("moves").toObject();
        auto* battleTimer=new QTimer(this);
        connect(battleTimer,&QTimer::timeout,this,[battleCard,enemyLabel,weakLabel,movesHeading,moveLabels,moveData,battlePath]{
            auto place=[battleCard]{
                auto* parent=battleCard->parentWidget();if(!parent)return;
                battleCard->adjustSize();
                battleCard->move(qMax(12,parent->width()-battleCard->width()-14),qMax(12,parent->height()-battleCard->height()-14));battleCard->raise();
            };
            QFile file(battlePath);
            if(!file.open(QIODevice::ReadOnly)){place();return;}
            const QJsonObject state=QJsonDocument::fromJson(file.readAll()).object();
            if(!state.value("active").toBool()){
                enemyLabel->setText("Warte auf einen Kampf …");weakLabel->setText("Gegnerschwächen erscheinen automatisch.");
                movesHeading->hide();for(auto* label:moveLabels)label->hide();place();return;
            }
            const auto enemy=state.value("enemy").toObject(),player=state.value("player").toObject();
            const auto enemyTypes=enemy.value("types").toArray();
            QStringList typeLabels;QSet<int> uniqueTypes;
            for(const auto value:enemyTypes){const int type=value.toInt(-1);if(type>=0&&!uniqueTypes.contains(type)){uniqueTypes.insert(type);typeLabels<<focusTypeName(type);}}
            enemyLabel->setText(QString("Gegner · Lv. %1 · %2").arg(enemy.value("level").toInt()).arg(typeLabels.join(" / ")));
            QStringList weaknesses;
            for(int type=0;type<18;type++)if(type!=9){const double factor=focusEffectiveness(type,enemyTypes);if(factor>1)weaknesses<<focusTypeName(type)+(factor>=4?" ×4":" ×2");}
            weakLabel->setText("Schwach gegen: "+(weaknesses.isEmpty()?QString("keine Typschwäche"):weaknesses.join(" · ")));
            movesHeading->show();const auto moves=player.value("moves").toArray();
            for(int i=0;i<moveLabels.size();i++){
                const int id=i<moves.size()?moves[i].toInt():0;
                if(!id){moveLabels[i]->hide();continue;}
                const auto info=moveData.value(QString::number(id)).toObject();
                const QString name=info.value("name").toString(QString("Attacke #%1").arg(id)).toHtmlEscaped();
                const int type=focusMoveType(info.value("type").toString());
                const bool statusMove=info.value("category").toString()=="STATUS";
                const double factor=type<0?1:focusEffectiveness(type,enemyTypes);
                QString verdict,color;
                if(statusMove){verdict="Statusattacke";color="#9ca2a7";}
                else if(factor==0){verdict="Keine Wirkung";color="#dc8686";}
                else if(factor<1){verdict="Nicht effektiv";color="#dc9a76";}
                else if(factor>1){verdict=factor>=4?"Sehr effektiv · ×4":"Sehr effektiv";color="#8ed19a";}
                else{verdict="Effektiv";color="#d8dce0";}
                moveLabels[i]->setText(QString("<b>%1</b> <span style='color:#9ca2a7'>%2</span><br><span style='color:%3'>%4</span>")
                    .arg(name,focusTypeName(type),color,verdict));moveLabels[i]->show();
            }
            place();
        });
        battleTimer->start(400);battleCard->show();
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
