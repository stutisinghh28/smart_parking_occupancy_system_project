/**
  ******************************************************************************
  * @file    led_indicators.c
  * @brief   LED management implementation. Controls slot LED indicators
  *          according to occupancy status.
  ******************************************************************************
  */

#include "led_indicators.h"

void LED_Init(ParkingSlot_t *slots, uint8_t count)
{
    if (slots == NULL || count == 0) {
        return;
    }

    /* Startup self-test: Turn all LEDs ON for 500ms then OFF */
    for (uint8_t i = 0; i < count; i++) {
        HAL_GPIO_WritePin(slots[i].led.port, slots[i].led.pin, GPIO_PIN_SET);
    }
    HAL_Delay(500);

    for (uint8_t i = 0; i < count; i++) {
        HAL_GPIO_WritePin(slots[i].led.port, slots[i].led.pin, GPIO_PIN_RESET);
    }
    HAL_Delay(200);
}

void LED_UpdateSlot(ParkingSlot_t *slot)
{
    if (slot == NULL) {
        return;
    }

    /* Active High: If slot is occupied -> turn LED ON, else turn LED OFF */
    GPIO_PinState state = slot->is_occupied ? GPIO_PIN_SET : GPIO_PIN_RESET;
    HAL_GPIO_WritePin(slot->led.port, slot->led.pin, state);
}

void LED_UpdateAll(ParkingSlot_t *slots, uint8_t count)
{
    if (slots == NULL) {
        return;
    }

    for (uint8_t i = 0; i < count; i++) {
        LED_UpdateSlot(&slots[i]);
    }
}
