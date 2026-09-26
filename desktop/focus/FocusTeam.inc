// Read-only HGSS team snapshot, sampled BETWEEN emulated frames every 25 s.
// Never calls SaveState, touches cartridge saves, or writes emulated memory.
// SaveData layout: pret/pokeheartgold include/save.h and constants/save_arrays.h.
#include <QSaveFile>
#include <QElapsedTimer>
#include <QtEndian>

static void focusSnapshotTeam(melonDS::NDS* nds)
{
    static const QString path=qEnvironmentVariable("SOULLINK_TEAM");
    static QElapsedTimer clock;
    if(path.isEmpty())return;
    if(clock.isValid()&&clock.elapsed()<25000)return;
    clock.start();
    const auto* cart=nds->GetNDSCart();
    if(!cart||cart->GetROMLength()<16||memcmp(cart->GetROM()+12,"IPGD",4)!=0)return;
    const auto* ram=nds->MainRAM;
    constexpr quint32 regionSize=0x23000, headerOffset=0x23014, headerSize=42*16;
    const quint32 size=nds->MainRAMMask+1;
    if(!ram||size!=0x400000)return;
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
        // Only a loaded existing game, not a title-screen/new-game placeholder.
        if(u32(start)!=1||u32(start+4)!=1||u32(start+8)!=0)continue;
        found=h;if(++matches>1)return; // ambiguity must never publish a wrong team
    }
    if(matches!=1)return;
    QSaveFile file(path);
    if(file.open(QIODevice::WriteOnly)){
        file.setPermissions(QFileDevice::ReadOwner|QFileDevice::WriteOwner);
        file.write("SLTEAM01",8);
        file.write(reinterpret_cast<const char*>(ram+found-headerOffset+16),regionSize);
        file.write(reinterpret_cast<const char*>(ram+found),headerSize);
        file.commit();
    }
}
