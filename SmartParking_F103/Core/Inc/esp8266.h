/**
  ******************************************************************************
  * @file    esp8266.h
  * @brief   UART AT-command driver for ESP8266 Wi-Fi module on STM32 HAL.
  ******************************************************************************
  */

#ifndef ESP8266_H
#define ESP8266_H

#include "parking_config.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
  * @brief  Initializes the ESP8266 module using STM32 UART peripheral.
  * @param  huart: Pointer to UART_HandleTypeDef connected to ESP8266.
  * @retval true if AT commands succeed and Wi-Fi connects, false otherwise.
  */
bool ESP8266_Init(UART_HandleTypeDef *huart);

/**
  * @brief  Connects to a Wi-Fi Access Point using stored credentials.
  * @param  ssid: Wi-Fi network name.
  * @param  pass: Wi-Fi password.
  * @retval true on success.
  */
bool ESP8266_ConnectWiFi(const char *ssid, const char *pass);

/**
  * @brief  Sends a batch of 6 parking slot measurements to the FastAPI backend.
  * @param  slots: Array of ParkingSlot_t structures.
  * @param  count: Number of slots (6).
  * @retval true if HTTP 200 response received, false otherwise.
  */
bool ESP8266_SendTelemetry(ParkingSlot_t *slots, uint8_t count);

#ifdef __cplusplus
}
#endif

#endif /* ESP8266_H */
