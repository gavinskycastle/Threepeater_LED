#include <ESP32-HUB75-MatrixPanel-I2S-DMA.h>
#include "pinmaps.hpp"
#include "dancing.hpp"

#define PANEL_RES_X 64     // Number of pixels wide of each INDIVIDUAL panel module. 
#define PANEL_RES_Y 64     // Number of pixels tall of each INDIVIDUAL panel module.
#define PANEL_CHAIN 1      // Total number of panels chained one to another horizontally only.
 
//MatrixPanel_I2S_DMA dma_display;
MatrixPanel_I2S_DMA *dma_display = nullptr;

uint16_t white = dma_display->color565(255, 255, 255);

/************************* Arduino Sketch Setup and Loop() *******************************/
void setup() {
  Serial.begin(115200);

  HUB75_I2S_CFG mxconfig(
        PANEL_RES_X,
        PANEL_RES_Y,
        PANEL_CHAIN
    );

    // Custom pin mapping from pinmaps.hpp
    mxconfig.gpio.r1  = HW_DISPLAY_R1_PIN;
    mxconfig.gpio.g1  = HW_DISPLAY_G1_PIN;
    mxconfig.gpio.b1  = HW_DISPLAY_B1_PIN;
    mxconfig.gpio.r2  = HW_DISPLAY_R2_PIN;
    mxconfig.gpio.g2  = HW_DISPLAY_G2_PIN;
    mxconfig.gpio.b2  = HW_DISPLAY_B2_PIN;
    mxconfig.gpio.a   = HW_DISPLAY_A_PIN;
    mxconfig.gpio.b   = HW_DISPLAY_B_PIN;
    mxconfig.gpio.c   = HW_DISPLAY_C_PIN;
    mxconfig.gpio.d   = HW_DISPLAY_D_PIN;
    mxconfig.gpio.e   = HW_DISPLAY_E_PIN;  // Required for 64-row panels
    mxconfig.gpio.lat = HW_DISPLAY_LAT_PIN;
    mxconfig.gpio.oe  = HW_DISPLAY_OE_PIN;
    mxconfig.gpio.clk = HW_DISPLAY_CLK_PIN;
    
  // Display Setup
  dma_display = new MatrixPanel_I2S_DMA(mxconfig);
  dma_display->begin();
  dma_display->setBrightness8(127); //0-255
  dma_display->clearScreen();
  dma_display->fillScreen(white);

}

void loop() 
{
   for(uint16_t* frame : dancing_frames) {
    dma_display->clearScreen();

    for (uint16_t pixel = 0; pixel < (PANEL_RES_X * PANEL_RES_Y); pixel++) {
      dma_display->drawPixel(pixel % (PANEL_RES_X), pixel / (PANEL_RES_X), frame[pixel]);
    }

    // dma_display->drawRGBBitmap(0, 0, PANEL_RES_X, PANEL_RES_Y, frame);
    delay(dancing_frame_time * 1000);
  }
}