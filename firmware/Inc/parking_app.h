/**
  ******************************************************************************
  * @file    parking_app.h
  * @brief   High-level application coordinator for the Smart Parking System.
  ******************************************************************************
  */

#ifndef PARKING_APP_H
#define PARKING_APP_H

#include "parking_config.h"
#include "hcsr04.h"
#include "led_indicators.h"
#include "esp8266.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
  * @brief  Initializes all hardware subsystems (sensors, LEDs, Wi-Fi link).
  * @param  htim: Hardware microsecond timer handle for HC-SR04.
  * @param  huart: Hardware USART handle connected to ESP8266.
  */
void ParkingApp_Init(TIM_HandleTypeDef *htim, UART_HandleTypeDef *huart);

/**
  * @brief  Main cyclic processing task.
  *         Call this repeatedly inside the main while(1) loop of main.c.
  */
void ParkingApp_Process(void);

/**
  * @brief  Exposes pointer to slot structure array for pin mapping setup.
  */
ParkingSlot_t* ParkingApp_GetSlots(void);

#ifdef __cplusplus
}
#endif

#endif /* PARKING_APP_H */
