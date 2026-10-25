/**
  ******************************************************************************
  * @file    led_indicators.h
  * @brief   LED indicators driver for parking slot occupancy display.
  ******************************************************************************
  */

#ifndef LED_INDICATORS_H
#define LED_INDICATORS_H

#include "parking_config.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
  * @brief  Initializes slot indicator LEDs and performs startup blink test.
  * @param  slots: Array of parking slot structures.
  * @param  count: Number of slots (typically 6).
  */
void LED_Init(ParkingSlot_t *slots, uint8_t count);

/**
  * @brief  Updates LED state for an individual slot based on occupancy.
  * @param  slot: Pointer to slot structure.
  */
void LED_UpdateSlot(ParkingSlot_t *slot);

/**
  * @brief  Updates all 6 slot LEDs at once.
  * @param  slots: Array of parking slot structures.
  * @param  count: Number of slots.
  */
void LED_UpdateAll(ParkingSlot_t *slots, uint8_t count);

#ifdef __cplusplus
}
#endif

#endif /* LED_INDICATORS_H */
