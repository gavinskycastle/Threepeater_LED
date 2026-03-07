#include "app/app_display.hpp"
#include "hw/hw_display.hpp"

#include <Arduino.h>

// Setup function
void setup()
{
  Serial.begin(115200);

  hw_display_init();
  app_display_init();
}

// Main loop
void loop()
{

  static unsigned long lastSendTime = 0;
  unsigned long currentMillis = millis();

  // Send data and update display every 100ms
  if (currentMillis - lastSendTime >= 100)
  {
    lastSendTime = currentMillis;

    uint32_t currentScore = 67;
    app_display_updateScore(currentScore);
  }

  // Print debug info every 1 second
  static unsigned long lastPrint = 0;
  if (currentMillis - lastPrint >= 1000)
  {
    lastPrint = currentMillis;
    uint32_t currentScore = 67;
    Serial.printf("Score: %d ",
                  currentScore);
  }

  delay(10); // Small delay to prevent watchdog issues
}
