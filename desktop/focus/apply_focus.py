"""Reproducible, checked source transformation for the pinned melonDS 1.1."""
from pathlib import Path
import shutil


def replace(path, old, new):
    text=path.read_text()
    if text.count(old)!=1:
        raise ValueError(f'Unexpected upstream source: {path.name}: {old[:70]}')
    path.write_text(text.replace(old,new))


def apply(source: Path):
    # Retain the original install name: modern ICU uses @loader_path aliases,
    # while the upstream bundler copies the resolved, fully-versioned filename.
    bundler=source/'tools/mac-libs.rb'
    replace(bundler,'.map { |it| expand_load_path(orig_path, it) }',
            '.map { |it| [*expand_load_path(orig_path, it), it] }')
    replace(bundler,'    libpath, libtype = lib','    libpath, libtype, loadname = lib')
    replace(bundler,'''      unless libtype == :rpath
        changes += [:change, libpath, File.join("@rpath", fwname, fwlib)]
      end''','''      changes += [:change, loadname, File.join("@rpath", fwname, fwlib)]''')
    replace(bundler,'''      if libtype == :absolute
        changes += [:change, libpath, File.join("@rpath", libname)]
      end''','''      changes += [:change, loadname, File.join("@rpath", libname)]''')
    replace(source/'tools/mac-libs.rb','$fallback_rpaths = []',
            '$fallback_rpaths = ENV.fetch("SOULLINK_FRAMEWORK_PATHS", "").split(File::PATH_SEPARATOR)')
    replace(source/'tools/mac-libs.rb','fixup_libs(executable, executable)',
            'fixup_libs(executable, executable)\n'
            'if ENV["SOULLINK_SDL3_SOURCE"]\n'
            '  fixup_libs(File.join(frameworks_dir, "libSDL3.dylib"), ENV["SOULLINK_SDL3_SOURCE"])\n'
            'end')
    qt=source/'src/frontend/qt_sdl'
    replace(qt/'Screen.cpp','#include "version.h"',
            '#include "version.h"\n#include <QSaveFile>\n#include <QFileInfo>\n#include "FocusCapture.inc"')
    replace(qt/'Screen.cpp','    glContext->SwapBuffers();',
            '    if (emuThread->emuIsActive()) focusCaptureGame(w,h);\n    glContext->SwapBuffers();')
    shutil.copy2(Path(__file__).with_name('FocusCapture.inc'),qt/'FocusCapture.inc')
    # The macOS bundler must include Qt's JPEG encoder for private previews.
    replace(bundler,'  "imageformats/libqsvg.dylib"','  "imageformats/libqsvg.dylib",\n  "imageformats/libqjpeg.dylib"')
    window=qt/'Window.cpp'
    replace(qt/'Window.h','    void onOpenFile();','    void initFocus();\n    void focusReturn(const QString& action);\n    void finishFocusRequest();\n    void onOpenFile();')
    replace(window,'    updateMPInterface(MPInterface::GetType());\n}', '    updateMPInterface(MPInterface::GetType());\n    initFocus();\n}')
    replace(window,'    QMainWindow::closeEvent(event);','    finishFocusRequest();\n    QMainWindow::closeEvent(event);')
    replace(window,'    setWindowTitle(title);','''    setWindowTitle("Soul Link · Focus · " + qEnvironmentVariable("SOULLINK_PLAYER", "Optimus"));
    if (auto* status = findChild<QLabel*>("focusStatus"))
        status->setText(title.replace("melonDS " MELONDS_VERSION, "SoulSilver"));''')
    replace(window,'#include <QApplication>','#include <QApplication>\n#include <QLabel>')
    replace(window,'            menuBar()->setFixedHeight(menuBarHeight);','            menuBar()->setFixedHeight(0);')
    # Keep the original GL panel/window/thread ownership; only add Qt toolbars.
    with window.open('a') as stream: stream.write('\n#include "FocusWindow.inc"\n')
    shutil.copy2(Path(__file__).with_name('FocusWindow.inc'),qt/'FocusWindow.inc')
    layout=source/'src/frontend/ScreenLayout.cpp'
    replace(layout,'    HybEnable = screenLayout == 3;', '''    // SoulLink Focus: preserve 4:3 on both screens and the inverse touch transform.
    if (screenLayout == screenLayout_Horizontal && sizing == screenSizing_EmphTop
        && rotation == screenRot_0Deg && !swapScreens && topAspect == 1 && botAspect == 1)
    {
        TopEnable = BotEnable = true; HybEnable = false;
        const float gap = 16;
        float large = std::min(std::max(1.f, (screenWidth-gap)*0.72f)/256.f, std::max(1,screenHeight)/192.f);
        float small = std::min(std::max(1.f, screenWidth-gap-large*256.f)/256.f, large*0.48f);
        if (integerScale) { large=std::max(1.f,std::floor(large)); small=std::max(1.f,std::floor(small)); }
        float x=(screenWidth-(large+small)*256.f-gap)/2.f;
        float y=(screenHeight-large*192.f)/2.f;
        M23_Identity(TopScreenMtx); M23_Scale(TopScreenMtx,large); M23_Translate(TopScreenMtx,x,y);
        float bx=x+large*256.f+gap;
        M23_Identity(BotScreenMtx); M23_Scale(BotScreenMtx,small); M23_Translate(BotScreenMtx,bx,y);
        M23_Identity(TouchMtx); M23_Translate(TouchMtx,-bx,-y); M23_Scale(TouchMtx,1.f/small);
        return;
    }
    HybEnable = screenLayout == 3;''')


if __name__=='__main__':
    import sys
    apply(Path(sys.argv[1]))
