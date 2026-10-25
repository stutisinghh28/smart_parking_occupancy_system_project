/**
  ******************************************************************************
  * @file    hcsr04.c
  * @brief   HC-SR04 Driver implementation: triggering, microsecond timer echo
  *          capture, distance calculation, and occupancy classification.
  ******************************************************************************
  */

#include "hcsr04.h"

static TIM_HandleTypeDef *s_htim = NULL;

void HCSR04_Init(TIM_HandleTypeDef *htim)
{
    s_htim = htim;
    if (s_htim != NULL) {
        HAL_TIM_Base_Start(s_htim);
    }
}

void HCSR04_DelayUs(uint32_t us)
{
    if (s_htim == NULL) {
        return;
    }
    uint16_t start = (uint16_t)__HAL_TIM_GET_COUNTER(s_htim);
    while ((uint16_t)(__HAL_TIM_GET_COUNTER(s_htim) - start) < (uint16_t)us) {
        /* Busy-wait for microsecond tick */
    }
}

bool HCSR04_ReadSlot(ParkingSlot_t *slot)
{
    if (slot == NULL || s_htim == NULL) {
        return false;
    }

    /* 1. Ensure Trigger pin is LOW for at least 2 microseconds to ensure clear pulse */
    HAL_GPIO_WritePin(slot->trig.port, slot->trig.pin, GPIO_PIN_RESET);
    HCSR04_DelayUs(2);

    /* 2. Generate 10 microsecond HIGH pulse on TRIG pin */
    HAL_GPIO_WritePin(slot->trig.port, slot->trig.pin, GPIO_PIN_SET);
    HCSR04_DelayUs(10);
    HAL_GPIO_WritePin(slot->trig.port, slot->trig.pin, GPIO_PIN_RESET);

    /* 3. Wait for ECHO pin to go HIGH (with timeout, using 16-bit wrap-around math) */
    uint16_t timeout_start = (uint16_t)__HAL_TIM_GET_COUNTER(s_htim);
    while (HAL_GPIO_ReadPin(slot->echo.port, slot->echo.pin) == GPIO_PIN_RESET) {
        if ((uint16_t)(__HAL_TIM_GET_COUNTER(s_htim) - timeout_start) > HCSR04_TIMEOUT_US) {
            /* Sensor didn't respond or disconnected */
            slot->last_echo_us = 0;
            slot->last_distance_cm = 400.0f; /* Out of range (Free) */
            slot->is_occupied = false;
            return false;
        }
    }

    /* 4. Record timestamp when ECHO went HIGH */
    uint16_t echo_start = (uint16_t)__HAL_TIM_GET_COUNTER(s_htim);

    /* 5. Wait for ECHO pin to go LOW (with timeout) */
    while (HAL_GPIO_ReadPin(slot->echo.port, slot->echo.pin) == GPIO_PIN_SET) {
        if ((uint16_t)(__HAL_TIM_GET_COUNTER(s_htim) - echo_start) > HCSR04_TIMEOUT_US) {
            /* Echo pulse exceeded max measurable distance (~5 meters) */
            slot->last_echo_us = HCSR04_TIMEOUT_US;
            slot->last_distance_cm = (float)HCSR04_TIMEOUT_US / HCSR04_SPEED_OF_SOUND_DIV;
            slot->is_occupied = false;
            return false;
        }
    }

    /* 6. Record timestamp when ECHO went LOW */
    uint16_t echo_end = (uint16_t)__HAL_TIM_GET_COUNTER(s_htim);

    /* 7. Calculate elapsed pulse duration in microseconds (16-bit modulo arithmetic) */
    uint32_t pulse_duration_us = (uint16_t)(echo_end - echo_start);
    slot->last_echo_us = pulse_duration_us;

    /* 8. Distance calculation: Distance (cm) = Echo time (us) / 58.2 */
    float distance_cm = (float)pulse_duration_us / HCSR04_SPEED_OF_SOUND_DIV;
    slot->last_distance_cm = distance_cm;

    /* 9. Occupancy classification with sanity check */
    if (distance_cm > 2.0f && distance_cm < OCCUPANCY_THRESHOLD_CM) {
        slot->is_occupied = true;
    } else {
        slot->is_occupied = false;
    }

    return true;
}
