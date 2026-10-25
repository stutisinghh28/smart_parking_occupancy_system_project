/**
  ******************************************************************************
  * @file    hcsr04.h
  * @brief   Ultrasonic sensor driver for HC-SR04 using STM32 Hardware Timer.
  ******************************************************************************
  */

#ifndef HCSR04_H
#define HCSR04_H

#include "parking_config.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
  * @brief  Initializes the HC-SR04 driver with a hardware microsecond timer.
  * @param  htim: Pointer to a TIM_HandleTypeDef configured with 1 MHz clock
  *               (1 microsecond per tick).
  */
void HCSR04_Init(TIM_HandleTypeDef *htim);

/**
  * @brief  Provides an accurate blocking microsecond delay using timer counter.
  * @param  us: Number of microseconds to delay.
  */
void HCSR04_DelayUs(uint32_t us);

/**
  * @brief  Triggers an ultrasonic pulse and measures echo response time for a slot.
  * @param  slot: Pointer to ParkingSlot_t structure containing pins and state.
  * @retval true if measurement succeeded within timeout, false if timed out.
  */
bool HCSR04_ReadSlot(ParkingSlot_t *slot);

#ifdef __cplusplus
}
#endif

#endif /* HCSR04_H */
