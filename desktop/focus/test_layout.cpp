// Pure frontend geometry regression, no ROM or emulator dependencies.
#include "ScreenLayout.h"
#include <cassert>
#include <cmath>
#include <initializer_list>
int main() {
    for (int width : {860,1200,1920,2560}) for (int height : {430,640,1080}) for(bool integer : {false,true}) {
        ScreenLayout layout;
        layout.Setup(width,height,screenLayout_Horizontal,screenRot_0Deg,screenSizing_EmphTop,0,integer,false,1,1);
        float transform[18];int kind[3];
        assert(layout.GetScreenTransforms(transform,kind)==2);
        assert(kind[0]==0 && kind[1]==1);
        for(int i=0;i<2;i++) {
            float* m=transform+i*6;
            assert(m[0]>0 && fabs(m[0]-m[3])<0.001); // 4:3 remains 4:3
            assert(m[4]>=0 && m[5]>=0);
            assert(m[4]+m[0]*256<=width+0.01 && m[5]+m[3]*192<=height+0.01);
        }
        assert(fabs(transform[5]-transform[11])<0.001); // top aligned
        int x=std::lround(transform[10]+transform[6]*128);
        int y=std::lround(transform[11]+transform[9]*96);
        assert(layout.GetTouchCoords(x,y,false));
        assert(abs(x-128)<=1 && abs(y-96)<=1);
        x=0;y=0;assert(!layout.GetTouchCoords(x,y,false));
    }
}
