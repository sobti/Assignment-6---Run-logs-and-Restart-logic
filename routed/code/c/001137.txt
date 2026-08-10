#include "VDP_Extra.h"

#include <tab_vram.h>

void MyVDP_setTileMapRect(u16 plan, const u16 *data, u16 basetile, u16 x, u16 y, u16 w, u16 h)
{
    vu32 *plctrl;
    vu16 *pwdata;
    const u16 *src;
    u32 addr;
    u32 planwidth;
    u16 i, j;

    VDP_setAutoInc(2);

    /* point to vdp port */
    plctrl = (u32 *) GFX_CTRL_PORT;
    pwdata = (u16 *) GFX_DATA_PORT;

    planwidth = VDP_getPlanWidth();
    addr = plan + ((x + (planwidth * y)) << 1);
    src = data;

    i = h;
    while (i--)
    {
	    *plctrl = GFX_WRITE_VRAM_ADDR(addr);

        j = w;
		//while (j--) *pwdata = basetile | *src++; // old "buggy" line.
        while (j--) *pwdata = basetile + *src++; // "fixed" version.

		addr += planwidth << 1;
	}
}

void VDP_setAllHorizontalScrollLines(u16 plan, u16 value)
{
    vu16 *pw;
    vu32 *pl;
    u16 addr;

    /* Point to vdp port */
    pw = (u16 *) GFX_DATA_PORT;
    pl = (u32 *) GFX_CTRL_PORT;

    addr = HSCRL;
    if (plan == BPLAN) addr += 2;

    VDP_setAutoInc(4);
    *pl = GFX_WRITE_VRAM_ADDR(addr);

    u16 loop = 224;
    while(loop--)
    {
        *pw = value;
    }
}

void VDP_setHorizontalScrollLines(u16 plan, u16* lines, u16 value)
{
    vu16 *pw;
    vu32 *pl;
    u16 addr;

    /* Point to vdp port */
    pw = (u16 *) GFX_DATA_PORT;
    pl = (u32 *) GFX_CTRL_PORT;

    addr = HSCRL;
    if (plan == BPLAN) addr += 2;

    VDP_setAutoInc(4);
    *pl = GFX_WRITE_VRAM_ADDR(addr);

    u16* tempLines = lines;

    u16 loop = 224;
    while(loop--)
    {
        *pw = *tempLines;
        tempLines++;
    }
}


void MyVDP_doVRamDMACopy(u16 from, u16 to, u16 len, u16 autoInc)
{
    vu16 *pw;
    vu32 *pl;

    VDP_setAutoInc(autoInc);

    pw = (u16 *) GFX_CTRL_PORT;

    // Setup DMA length
    *pw = 0x9300 + (len & 0xff);
    *pw = 0x9400 + ((len >> 8) & 0xff);

    // Setup DMA address
    *pw = 0x9500 + (from & 0xff);
    *pw = 0x9600 + ((from >> 8) & 0xff);

    // Setup DMA operation (VRAM COPY)
    *pw = 0x97C0;

    // Write VRam DMA destination address (start DMA copy operation)
    pl = (u32 *) GFX_CTRL_PORT;
    *pl = GFX_DMA_VRAM_ADDR(to);
}


void MyVDP_doDMA(u8 location, u32 from, u16 to, u16 len, u16 autoInc)
{
    vu16 *pw;
    vu32 *pl;
    u32 newlen;
    u32 banklimit;

    // DMA works on 128 KB bank
    banklimit = 0x20000 - (from & 0x1FFFF);
    // bank limit exceded
    if (len > banklimit)
    {
        // we first do the second bank transfert
        MyVDP_doDMA(location, from + banklimit, to + banklimit, len - banklimit, autoInc);
        newlen = banklimit;
    }
    // ok, use normal len
    else newlen = len;

    VDP_setAutoInc(autoInc);

    pw = (u16 *) GFX_CTRL_PORT;

    // Setup DMA length (in word here)
    newlen >>= 1;
    *pw = 0x9300 + (newlen & 0xff);
    newlen >>= 8;
    *pw = 0x9400 + (newlen & 0xff);

    // Setup DMA address
    from >>= 1;
    *pw = 0x9500 + (from & 0xff);
    from >>= 8;
    *pw = 0x9600 + (from & 0xff);
    from >>= 8;
    *pw = 0x9700 + (from & 0x7f);

    // Halt the Z80 for DMA
//    Z80_RequestBus(0);

    // Enable DMA
    pl = (u32 *) GFX_CTRL_PORT;
    switch(location)
    {
        case VDP_DMA_VRAM:
            *pl = GFX_DMA_VRAM_ADDR(to);
            break;

        case VDP_DMA_CRAM:
            *pl = GFX_DMA_CRAM_ADDR(to);
            break;

        case VDP_DMA_VSRAM:
            *pl = GFX_DMA_VSRAM_ADDR(to);
            break;
    }

    // Enable Z80
//    Z80_ReleaseBus();
}

void MyVDP_waitVSync()
{
    vu16 *pw;
    u16 vdp_state;

    vdp_state = VDP_VBLANK_FLAG;
    pw = (u16 *) GFX_CTRL_PORT;

    while (vdp_state & VDP_VBLANK_FLAG) vdp_state = *pw;
    while (!(vdp_state & VDP_VBLANK_FLAG)) vdp_state = *pw;
}
