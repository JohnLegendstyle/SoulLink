// Capture only the emulator's own GL backbuffer, never the OS desktop.
// Called on the rendering thread before swapping, at most four times/second.
static void focusCaptureGame(int width, int height)
{
    static const QString path=qEnvironmentVariable("SOULLINK_MIRROR");
    static qint64 last=0;
    const qint64 now=QDateTime::currentMSecsSinceEpoch();
    if(path.isEmpty()||now-last<250) return;
    last=now;
    if(!QFileInfo::exists(path+".enabled")||width<1||height<1||width>8192||height>8192) return;
    QImage pixels(width,height,QImage::Format_RGBA8888);
    if(pixels.isNull()) return;
    GLint pack=4,buffer=0;glGetIntegerv(GL_PACK_ALIGNMENT,&pack);glGetIntegerv(GL_PIXEL_PACK_BUFFER_BINDING,&buffer);
    glBindBuffer(GL_PIXEL_PACK_BUFFER,0);glPixelStorei(GL_PACK_ALIGNMENT,4);
    glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.bits());
    glPixelStorei(GL_PACK_ALIGNMENT,pack);
    glBindBuffer(GL_PIXEL_PACK_BUFFER,buffer);
    QImage preview=pixels.mirrored().scaled(960,720,Qt::KeepAspectRatio,Qt::SmoothTransformation);
    QSaveFile file(path);
    if(file.open(QIODevice::WriteOnly)&&preview.save(&file,"JPEG",70)) file.commit();
}
