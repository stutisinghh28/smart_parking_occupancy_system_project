/**
  ******************************************************************************
  * @file    parking_app.c
  * @brief   Main application processing loop for 6-slot parking detection.
  ******************************************************************************
  */

#include "parking_app.h"

/* Array holding configuration and live status for 6 parking slots */
static ParkingSlot_t s_slots[NUM_PARKING_SLOTS];
static uint32_t s_last_telemetry_tick = 0;
static bool s_wifi_connected = false;

ParkingSlot_t* ParkingApp_GetSlots(void)
{
    return s_slots;
}

void ParkingApp_Init(TIM_HandleTypeDef *htim, UART_HandleTypeDef *huart)
{
    /* 1. Setup slot IDs */
    for (uint8_t i = 0; i < NUM_PARKING_SLOTS; i++) {
        s_slots[i].slot_id = i + 1;
        s_slots[i].last_distance_cm = 200.0f;
        s_slots[i].last_echo_us = 11640;
        s_slots[i].is_occupied = false;
        
        /* 
         * Note: Physical pin assignments (slot[i].trig, slot[i].echo, slot[i].led)
         * are assigned in the user board setup function before calling this,
         * or via the CubeMX Pin Label bindings.
         */
    }

    /* 2. Initialize HC-SR04 microsecond timer */
    HCSR04_Init(htim);

    /* 3. Initialize LED indicators & run power-on test */
    LED_Init(s_slots, NUM_PARKING_SLOTS);

    /* 4. Initialize ESP8266 Wi-Fi module */
    if (ESP8266_Init(huart)) {
        s_wifi_connected = ESP8266_ConnectWiFi(WIFI_SSID, WIFI_PASSWORD);
    }
}

void ParkingApp_Process(void)
{
    /* 1. Sequentially scan each of the 6 ultrasonic sensors */
    for (uint8_t i = 0; i < NUM_PARKING_SLOTS; i++) {
        /* Read sensor */
        HCSR04_ReadSlot(&s_slots[i]);

        /* Update slot LED indicator immediately */
        LED_UpdateSlot(&s_slots[i]);

        /* 
         * 20ms pause between sensors to prevent acoustic reverberation
         * and cross-talk reflections between adjacent parking bays.
         */
        HAL_Delay(20);
    }

    /* 2. Check periodic telemetry transmission timer */
    uint32_t now = HAL_GetTick();
    if ((now - s_last_telemetry_tick) >= TELEMETRY_INTERVAL_MS) {
        s_last_telemetry_tick = now;

        if (s_wifi_connected) {
            ESP8266_SendTelemetry(s_slots, NUM_PARKING_SLOTS);
        } else {
            /* Try to reconnect Wi-Fi if lost */
            s_wifi_connected = ESP8266_ConnectWiFi(WIFI_SSID, WIFI_PASSWORD);
        }
    }
}
