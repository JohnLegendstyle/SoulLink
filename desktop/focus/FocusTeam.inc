// Read-only HGSS team (20 s), map-position (1 s) and battle snapshots.
// Never calls SaveState, touches cartridge saves, or writes emulated memory.
// SaveData layout: pret/pokeheartgold include/save.h and constants/save_arrays.h.
#include <QSaveFile>
#include <QElapsedTimer>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QtEndian>

static bool focusRamPointer(quint32 pointer, quint32 size, quint32 need, quint32& offset)
{
    if(pointer<0x02000000||pointer>=0x02000000+size)return false;
    offset=pointer-0x02000000;
    return offset<=size&&need<=size-offset;
}

static bool focusBattleMon(const quint8* ram,quint32 size,quint32 ctx,int slot,QJsonObject* result=nullptr)
{
    constexpr quint32 battleMons=0x2D40,battleMonSize=0xC0;
    const quint32 p=ctx+battleMons+slot*battleMonSize;
    if(p+0x54>size)return false;
    const quint16 species=qFromLittleEndian<quint16>(ram+p);
    const quint8 type1=ram[p+0x24],type2=ram[p+0x25],level=ram[p+0x34];
    const qint32 hp=qFromLittleEndian<qint32>(ram+p+0x4C);
    const quint32 maxHp=qFromLittleEndian<quint32>(ram+p+0x50);
    if(!species||species>493||type1>17||type2>17||type1==9||type2==9
       ||!level||level>100||!maxHp||maxHp>65535||hp<0||quint32(hp)>maxHp)return false;
    if(result){
        QJsonArray moves;
        for(int i=0;i<4;i++){
            const quint16 move=qFromLittleEndian<quint16>(ram+p+0x0C+i*2);
            if(move>467)return false;
            moves.append(move);
        }
        (*result)={{"species",species},{"level",level},{"hp",hp},{"maxHp",int(maxHp)},
                   {"types",QJsonArray{type1,type2}},{"moves",moves}};
    }
    return true;
}

static bool focusReadBattle(const quint8* ram,quint32 size,quint32 system,QJsonObject& snapshot)
{
    if(system+0x80>size)return false;
    const quint32 maxBattlers=qFromLittleEndian<quint32>(ram+system+0x48);
    if(maxBattlers!=2&&maxBattlers!=4)return false;
    quint32 ctx=0;
    if(!focusRamPointer(qFromLittleEndian<quint32>(ram+system+0x30),size,0x3040,ctx))return false;
    quint32 playerParty=0,enemyParty=0;
    if(!focusRamPointer(qFromLittleEndian<quint32>(ram+system+0x6C),size,16,playerParty)
       ||!focusRamPointer(qFromLittleEndian<quint32>(ram+system+0x70),size,16,enemyParty))return false;
    const auto partyOk=[ram,size](quint32 p){
        if(p+8>size)return false;
        const quint32 maximum=qFromLittleEndian<quint32>(ram+p),count=qFromLittleEndian<quint32>(ram+p+4);
        return maximum==6&&count>=1&&count<=6&&p+8+count*236<=size;
    };
    if(!partyOk(playerParty)||!partyOk(enemyParty))return false;
    QJsonObject player,enemy;
    if(!focusBattleMon(ram,size,ctx,0,&player)||!focusBattleMon(ram,size,ctx,1,&enemy))return false;
    snapshot={{"format",1},{"active",true},{"player",player},{"enemy",enemy}};
    if(maxBattlers==4){QJsonObject enemy2;if(focusBattleMon(ram,size,ctx,3,&enemy2))snapshot.insert("enemy2",enemy2);}
    return true;
}

static quint32 focusFindBattleSystem(const quint8* ram,quint32 size,QJsonObject& snapshot)
{
    for(quint32 p=0;p+0x80<=size;p+=4){
        const quint32 count=qFromLittleEndian<quint32>(ram+p+0x48);
        if((count==2||count==4)&&focusReadBattle(ram,size,p,snapshot))return p;
    }
    return 0;
}

static quint32 focusFindSaveData(const quint8* ram, quint32 size)
{
    constexpr quint32 regionSize=0x23000, headerOffset=0x23014, headerSize=42*16;
    if(!ram||size!=0x400000)return 0;
    auto u32=[ram](quint32 p){return qFromLittleEndian<quint32>(ram+p);};
    quint32 found=0;int matches=0;
    for(quint32 h=headerOffset;h+headerSize<=size;h+=4){
        if(u32(h)!=0||u32(h+8)!=0||u32(h+16)!=1||u32(h+32)!=2)continue;
        bool valid=true;quint32 previousEnd=0;
        for(quint32 i=0;i<42;i++){
            const auto p=h+i*16,len=u32(p+4),off=u32(p+8);
            if(u32(p)!=i||!len||off<previousEnd||off>regionSize||len>regionSize-off
               ||qFromLittleEndian<quint16>(ram+p+14)>1){valid=false;break;}
            previousEnd=off+len;
        }
        if(!valid)continue;
        const quint32 start=h-headerOffset;
        if(u32(start)!=1||u32(start+4)!=1||u32(start+8)!=0)continue;
        found=h;if(++matches>1)return 0;
    }
    return matches==1?found:0;
}

static void focusSnapshotTeam(melonDS::NDS* nds)
{
    static const QString teamPath=qEnvironmentVariable("SOULLINK_TEAM");
    static const QString positionPath=qEnvironmentVariable("SOULLINK_POSITION");
    static const QString battlePath=qEnvironmentVariable("SOULLINK_BATTLE");
    static QElapsedTimer teamClock,positionClock,battleClock;
    static quint32 positionSequence=0;
    static quint32 cachedSaveHeader=0;
    static quint32 cachedBattleSystem=0;
    const bool teamDue=!teamPath.isEmpty()&&(!teamClock.isValid()||teamClock.elapsed()>=20000);
    const bool positionDue=!positionPath.isEmpty()&&(!positionClock.isValid()||positionClock.elapsed()>=1000);
    const bool battleDue=!battlePath.isEmpty()&&(!battleClock.isValid()||battleClock.elapsed()>=400);
    if(!teamDue&&!positionDue&&!battleDue)return;
    if(teamDue){if(teamClock.isValid())teamClock.restart();else teamClock.start();}
    if(positionDue){if(positionClock.isValid())positionClock.restart();else positionClock.start();}
    if(battleDue){if(battleClock.isValid())battleClock.restart();else battleClock.start();}
    const auto* cart=nds->GetNDSCart();
    if(!cart||cart->GetROMLength()<16||memcmp(cart->GetROM()+12,"IPGD",4)!=0)return;
    const auto* ram=nds->MainRAM;
    constexpr quint32 regionSize=0x23000,headerOffset=0x23014,headerSize=42*16;
    auto u32=[ram](quint32 p){return qFromLittleEndian<quint32>(ram+p);};
    const quint32 ramSize=nds->MainRAMMask+1;
    if(battleDue){
        QJsonObject snapshot;
        if(cachedBattleSystem&&!focusReadBattle(ram,ramSize,cachedBattleSystem,snapshot))cachedBattleSystem=0;
        if(!cachedBattleSystem)cachedBattleSystem=focusFindBattleSystem(ram,ramSize,snapshot);
        if(!cachedBattleSystem)snapshot={{"format",1},{"active",false}};
        QSaveFile battle(battlePath);
        if(battle.open(QIODevice::WriteOnly)){
            battle.setPermissions(QFileDevice::ReadOwner|QFileDevice::WriteOwner);
            battle.write(QJsonDocument(snapshot).toJson(QJsonDocument::Compact));battle.commit();
        }
    }
    if(cachedSaveHeader){
        const quint32 start=cachedSaveHeader-headerOffset;
        if(cachedSaveHeader+headerSize>ramSize||u32(start)!=1||u32(start+4)!=1||u32(start+8)!=0
           ||u32(cachedSaveHeader)!=0||u32(cachedSaveHeader+2*16)!=2||u32(cachedSaveHeader+5*16)!=5)cachedSaveHeader=0;
    }
    if(teamDue||!cachedSaveHeader)cachedSaveHeader=focusFindSaveData(ram,ramSize);
    const quint32 found=cachedSaveHeader;
    if(!found)return;
    if(positionDue){
        // SAVE_LOCAL_FIELD_DATA (array 5) starts with Location:
        // signed mapId, warpId, x, y and direction.
        const quint32 entry=found+5*16;
        const quint32 offset=qFromLittleEndian<quint32>(ram+entry+8);
        const quint32 length=qFromLittleEndian<quint32>(ram+entry+4);
        if(length>=20&&offset<=regionSize-20){
            const quint8* location=ram+found-headerOffset+16+offset;
            const qint32 values[]={qFromLittleEndian<qint32>(location),qFromLittleEndian<qint32>(location+8),
                                  qFromLittleEndian<qint32>(location+12),qFromLittleEndian<qint32>(location+16),
                                  qint32(positionSequence++)};
            if(values[0]>=0&&values[0]<=1000&&values[1]>=0&&values[2]>=0&&values[3]>=0&&values[3]<=3){
                QSaveFile file(positionPath);
                if(file.open(QIODevice::WriteOnly)){
                    file.setPermissions(QFileDevice::ReadOwner|QFileDevice::WriteOwner);
                    file.write("SLPOS01",8);
                    for(const qint32 value:values){const qint32 little=qToLittleEndian(value);file.write(reinterpret_cast<const char*>(&little),4);}
                    file.commit();
                }
            }
        }
    }
    if(teamDue){
        QSaveFile file(teamPath);
        if(file.open(QIODevice::WriteOnly)){
            file.setPermissions(QFileDevice::ReadOwner|QFileDevice::WriteOwner);
            file.write("SLTEAM01",8);
            file.write(reinterpret_cast<const char*>(ram+found-headerOffset+16),regionSize);
            file.write(reinterpret_cast<const char*>(ram+found),headerSize);
            file.commit();
        }
    }
}
