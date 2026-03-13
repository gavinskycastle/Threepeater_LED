#include <ESP32-HUB75-MatrixPanel-I2S-DMA.h>

uint16_t color565(uint8_t r, uint8_t g, uint8_t b) {
  return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);
}

class Animation {
    public:
        // frames is a pointer to an array of frames, where each frame is an
        // array of 4096 uint16_t pixels (width*height). frames[currentFrame]
        // decays to const uint16_t* when passed to drawRGBBitmap.
        Animation(const uint16_t (*frames)[4096], uint8_t frame_count, float frame_time) : 
            frames(frames), frame_count(frame_count), frame_time(frame_time) {}

        const uint16_t (*frames)[4096];
        uint8_t frame_count;
        float frame_time;
        uint16_t currentFrame = 0;
        
        void drawNextFrame(MatrixPanel_I2S_DMA* dma_display) {
            dma_display->drawRGBBitmap(0, 0, frames[currentFrame], dma_display->width(), dma_display->height());
            delay(frame_time * 1000);
            currentFrame = (currentFrame + 1) % frame_count;
        }
};