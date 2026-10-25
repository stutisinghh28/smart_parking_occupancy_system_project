/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  */

#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

#include "stm32f1xx_hal.h"

void Error_Handler(void);

/*
 * =============================================================================
 * USER PIN DEFINITIONS (PLACEHOLDERS: PENDING HARDWARE WIRING CONFIRMATION)
 * =============================================================================
 */

/* Placeholder pin definitions for 6 Ultrasonic Sensors (TRIG & ECHO) */
#define TRIG1_Pin GPIO_PIN_0
#define TRIG1_GPIO_Port GPIOA
#define ECHO1_Pin GPIO_PIN_10
#define ECHO1_GPIO_Port GPIOB

#define TRIG2_Pin GPIO_PIN_1
#define TRIG2_GPIO_Port GPIOA
#define ECHO2_Pin GPIO_PIN_11
#define ECHO2_GPIO_Port GPIOB

#define TRIG3_Pin GPIO_PIN_2
#define TRIG3_GPIO_Port GPIOA
#define ECHO3_Pin GPIO_PIN_12
#define ECHO3_GPIO_Port GPIOB

#define TRIG4_Pin GPIO_PIN_3
#define TRIG4_GPIO_Port GPIOA
#define ECHO4_Pin GPIO_PIN_13
#define ECHO4_GPIO_Port GPIOB

#define TRIG5_Pin GPIO_PIN_4
#define TRIG5_GPIO_Port GPIOA
#define ECHO5_Pin GPIO_PIN_15
#define ECHO5_GPIO_Port GPIOB

#define TRIG6_Pin GPIO_PIN_5
#define TRIG6_GPIO_Port GPIOA
#define ECHO6_Pin GPIO_PIN_14
#define ECHO6_GPIO_Port GPIOB

/* Placeholder pin definitions for 6 Slot Indicator LEDs */
#define LED1_Pin GPIO_PIN_0
#define LED1_GPIO_Port GPIOB
#define LED2_Pin GPIO_PIN_1
#define LED2_GPIO_Port GPIOB
#define LED3_Pin GPIO_PIN_5
#define LED3_GPIO_Port GPIOB
#define LED4_Pin GPIO_PIN_6
#define LED4_GPIO_Port GPIOB
#define LED5_Pin GPIO_PIN_7
#define LED5_GPIO_Port GPIOB
#define LED6_Pin GPIO_PIN_8
#define LED6_GPIO_Port GPIOB

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
