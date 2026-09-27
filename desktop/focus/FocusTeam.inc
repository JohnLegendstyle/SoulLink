// Read-only HGSS team (20 s) and map-position (1 s) snapshots.
// Never calls SaveState, touches cartridge saves, or writes emulated memory.
// SaveData layout: pret/pokeheartgold include/save.h and constants/save_arrays.h.
#include <QSaveFile>
#include <QElapsedTimer>
#include <QtEndian>

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
    static QElapsedTimer teamClock,positionClock;
    static quint32 positionSequence=0;
    static quint32 cachedSaveHeader=0;
    const bool teamDue=!teamPath.isEmpty()&&(!teamClock.isValid()||teamClock.elapsed()>=20000);
    const bool positionDue=!positionPath.isEmpty()&&(!positionClock.isValid()||positionClock.elapsed()>=1000);
    if(!teamDue&&!positionDue)return;
    if(teamDue){if(teamClock.isValid())teamClock.restart();else teamClock.start();}
    if(positionDue){if(positionClock.isValid())positionClock.restart();else positionClock.start();}
    const auto* cart=nds->GetNDSCart();
    if(!cart||cart->GetROMLength()<16||memcmp(cart->GetROM()+12,"IPGD",4)!=0)return;
    const auto* ram=nds->MainRAM;
    constexpr quint32 regionSize=0x23000,headerOffset=0x23014,headerSize=42*16;
    auto u32=[ram](quint32 p){return qFromLittleEndian<quint32>(ram+p);};
    const quint32 ramSize=nds->MainRAMMask+1;
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
