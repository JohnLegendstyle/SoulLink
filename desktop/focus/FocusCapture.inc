// Only the DS GL panel. One bounded encoder slot; no audio or desktop capture.
#include <QBuffer>
#include <QtEndian>
#include <QTcpSocket>
#include <QHostAddress>
#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <condition_variable>
#include <mutex>
#include <thread>

class FocusFrameEncoder
{
    std::mutex mutex;
    std::condition_variable changed;
    QImage pending;
    int pendingFPS=60;
    bool stopping=false;
    std::thread worker;
public:
    FocusFrameEncoder():worker([this]{run();}) {}
    ~FocusFrameEncoder(){stop();}
    void stop(){
        {std::lock_guard<std::mutex> lock(mutex);stopping=true;pending=QImage();}
        changed.notify_all();if(worker.joinable())worker.join();
    }
    void submit(QImage pixels,int fps){
        std::lock_guard<std::mutex> lock(mutex);
        if(stopping)return;
        pending=std::move(pixels);pendingFPS=fps;changed.notify_one();
    }
    void run(){
        const QString path=qEnvironmentVariable("SOULLINK_MIRROR");
        const QString endpoint=QFileInfo(path).path()+"/"+QFileInfo(path).completeBaseName()+".receiver.json";
        QTcpSocket pipe;
        for(;;){
            QImage pixels;int fps;
            {
                std::unique_lock<std::mutex> lock(mutex);
                changed.wait(lock,[this]{return stopping||!pending.isNull();});
                if(stopping)return;
                pixels=std::move(pending);pending=QImage();fps=pendingFPS;
            }
            QByteArray jpeg;QBuffer output(&jpeg);output.open(QIODevice::WriteOnly);
            if(!pixels.mirrored().save(&output,"JPEG",65)||jpeg.size()>300000)continue;
            if(!QFileInfo::exists(path+".enabled"))continue;
            char header[8];qToBigEndian<quint32>(jpeg.size(),header);
            qToBigEndian<quint16>(qBound(0,fps,1000),header+4);qToBigEndian<quint16>(1,header+6);
            // Loopback pipe avoids replacing a file up to 120 times/second.
            // It is private to this launcher; no desktop or audio is captured.
            if(QFileInfo::exists(endpoint)){
                if(pipe.state()!=QAbstractSocket::ConnectedState){
                    pipe.abort();QFile settings(endpoint);
                    if(!settings.open(QIODevice::ReadOnly))continue;
                    const auto config=QJsonDocument::fromJson(settings.read(4096)).object();
                    const int port=config.value("port").toInt();
                    const QByteArray token=config.value("token").toString().toLatin1();
                    if(port<1||port>65535||token.size()!=64)continue;
                    pipe.connectToHost(QHostAddress::LocalHost,quint16(port));
                    if(!pipe.waitForConnected(30))continue;
                    pipe.setSocketOption(QAbstractSocket::LowDelayOption,1);
                    pipe.write(token+"\n");
                }
                if(pipe.bytesToWrite()>2000000){pipe.abort();continue;}
                pipe.write(header,8);pipe.write(jpeg);pipe.flush();
                if(pipe.bytesToWrite())pipe.waitForBytesWritten(5);
                continue;
            }
            QSaveFile file(path);
            if(file.open(QIODevice::WriteOnly)){file.write(header,8);file.write(jpeg);file.commit();}
        }
    }
};
static FocusFrameEncoder& focusEncoder(){static FocusFrameEncoder encoder;return encoder;}
void focusStopCapture(){focusEncoder().stop();}

// Runs once per rendered frame: the native FPS setting determines cadence.
// Downscale on the GPU before readback, then encode off the emulation thread.
static void focusCaptureGame(int width,int height,int fps)
{
    static const QString path=qEnvironmentVariable("SOULLINK_MIRROR");
    if(path.isEmpty()||!QFileInfo::exists(path+".enabled")||width<1||height<1||width>8192||height>8192)return;
    const QSize size=QSize(width,height).scaled(720,540,Qt::KeepAspectRatio);
    QImage pixels(size,QImage::Format_RGBA8888);if(pixels.isNull())return;
    GLint readFbo,drawFbo,texture,pack,unpack,alignment,rowLength,skipRows,skipPixels;
    glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING,&readFbo);glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING,&drawFbo);
    glGetIntegerv(GL_TEXTURE_BINDING_2D,&texture);glGetIntegerv(GL_PIXEL_PACK_BUFFER_BINDING,&pack);
    glGetIntegerv(GL_PIXEL_UNPACK_BUFFER_BINDING,&unpack);glGetIntegerv(GL_PACK_ALIGNMENT,&alignment);
    glGetIntegerv(GL_PACK_ROW_LENGTH,&rowLength);glGetIntegerv(GL_PACK_SKIP_ROWS,&skipRows);glGetIntegerv(GL_PACK_SKIP_PIXELS,&skipPixels);
    const bool scissor=glIsEnabled(GL_SCISSOR_TEST);glDisable(GL_SCISSOR_TEST);
    GLuint target=0,fbo=0;glGenTextures(1,&target);glBindTexture(GL_TEXTURE_2D,target);
    glBindBuffer(GL_PIXEL_UNPACK_BUFFER,0);
    glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,size.width(),size.height(),0,GL_RGBA,GL_UNSIGNED_BYTE,nullptr);
    glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);
    glGenFramebuffers(1,&fbo);glBindFramebuffer(GL_DRAW_FRAMEBUFFER,fbo);
    glFramebufferTexture2D(GL_DRAW_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D,target,0);
    const bool complete=glCheckFramebufferStatus(GL_DRAW_FRAMEBUFFER)==GL_FRAMEBUFFER_COMPLETE;
    if(complete){
        glBlitFramebuffer(0,0,width,height,0,0,size.width(),size.height(),GL_COLOR_BUFFER_BIT,GL_LINEAR);
        glBindFramebuffer(GL_READ_FRAMEBUFFER,fbo);glReadBuffer(GL_COLOR_ATTACHMENT0);
        glBindBuffer(GL_PIXEL_PACK_BUFFER,0);glPixelStorei(GL_PACK_ALIGNMENT,4);
        glPixelStorei(GL_PACK_ROW_LENGTH,0);glPixelStorei(GL_PACK_SKIP_ROWS,0);glPixelStorei(GL_PACK_SKIP_PIXELS,0);
        glReadPixels(0,0,size.width(),size.height(),GL_RGBA,GL_UNSIGNED_BYTE,pixels.bits());
    }
    glBindFramebuffer(GL_READ_FRAMEBUFFER,readFbo);glBindFramebuffer(GL_DRAW_FRAMEBUFFER,drawFbo);
    glBindTexture(GL_TEXTURE_2D,texture);glBindBuffer(GL_PIXEL_PACK_BUFFER,pack);glBindBuffer(GL_PIXEL_UNPACK_BUFFER,unpack);
    glPixelStorei(GL_PACK_ALIGNMENT,alignment);glPixelStorei(GL_PACK_ROW_LENGTH,rowLength);
    glPixelStorei(GL_PACK_SKIP_ROWS,skipRows);glPixelStorei(GL_PACK_SKIP_PIXELS,skipPixels);
    if(scissor)glEnable(GL_SCISSOR_TEST);
    glDeleteFramebuffers(1,&fbo);glDeleteTextures(1,&target);
    if(complete)focusEncoder().submit(std::move(pixels),fps);
}
