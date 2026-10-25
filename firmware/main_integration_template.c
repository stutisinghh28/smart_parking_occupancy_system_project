/**
  ******************************************************************************
  * @file    main_integration_template.c
  * @brief   Reference template showing exact placement of Parking App code
  *          inside CubeMX-generated Core/Src/main.c.
  *
  * NOTE: When STM32CubeMX generates main.c, only insert code between the
  * "USER CODE BEGIN" and "USER CODE END" comments. This guarantees that
  * re-generating code in CubeMX will never overwrite your custom application.
  ******************************************************************************
  */

/* -------------------------------------------------------------------------- */
/* 1. In Core/Src/main.c -> USER CODE Includes                                */
/* -------------------------------------------------------------------------- */
/* USER CODE BEGIN Includes */
#include "parking_app.h"
/* USER CODE END Includes */


/* -------------------------------------------------------------------------- */
/* 2. In Core/Src/main.c -> USER CODE 2 (inside main(), right before while(1))*/
/* -------------------------------------------------------------------------- */
/* USER CODE BEGIN 2 */

  /* Retrieve pointer to the 6-slot parking array */
  ParkingSlot_t *slots = ParkingApp_GetSlots();

  /*
   * =========================================================================
   * HARDWARE PIN BINDING (RULE 9 COMPLIANT: PLACEHOLDERS ONLY)
   *
   * Once you choose your pins in the STM32CubeMX pinout (.ioc) and give them
   * User Labels (e.g., TRIG1, ECHO1, LED1), STM32CubeIDE automatically
   * creates macros like TRIG1_GPIO_Port and TRIG1_Pin in main.h.
   *
   * Replace the placeholders below with your confirmed labels:
   * =========================================================================
   */

  /* --- Slot 1 --- */
  /* slots[0].trig.port = TRIG1_GPIO_Port; slots[0].trig.pin = TRIG1_Pin; */
  /* slots[0].echo.port = ECHO1_GPIO_Port; slots[0].echo.pin = ECHO1_Pin; */
  /* slots[0].led.port  = LED1_GPIO_Port;  slots[0].led.pin  = LED1_Pin;  */

  /* --- Slot 2 --- */
  /* slots[1].trig.port = TRIG2_GPIO_Port; slots[1].trig.pin = TRIG2_Pin; */
  /* slots[1].echo.port = ECHO2_GPIO_Port; slots[1].echo.pin = ECHO2_Pin; */
  /* slots[1].led.port  = LED2_GPIO_Port;  slots[1].led.pin  = LED2_Pin;  */

  /* --- Slot 3 --- */
  /* slots[2].trig.port = TRIG3_GPIO_Port; slots[2].trig.pin = TRIG3_Pin; */
  /* slots[2].echo.port = ECHO3_GPIO_Port; slots[2].echo.pin = ECHO3_Pin; */
  /* slots[2].led.port  = LED3_GPIO_Port;  slots[2].led.pin  = LED3_Pin;  */

  /* --- Slot 4 --- */
  /* slots[3].trig.port = TRIG4_GPIO_Port; slots[3].trig.pin = TRIG4_Pin; */
  /* slots[3].echo.port = ECHO4_GPIO_Port; slots[3].echo.pin = ECHO4_Pin; */
  /* slots[3].led.port  = LED4_GPIO_Port;  slots[3].led.pin  = LED4_Pin;  */

  /* --- Slot 5 --- */
  /* slots[4].trig.port = TRIG5_GPIO_Port; slots[4].trig.pin = TRIG5_Pin; */
  /* slots[4].echo.port = ECHO5_GPIO_Port; slots[4].echo.pin = ECHO5_Pin; */
  /* slots[4].led.port  = LED5_GPIO_Port;  slots[4].led.pin  = LED5_Pin;  */

  /* --- Slot 6 --- */
  /* slots[5].trig.port = TRIG6_GPIO_Port; slots[5].trig.pin = TRIG6_Pin; */
  /* slots[5].echo.port = ECHO6_GPIO_Port; slots[5].echo.pin = ECHO6_Pin; */
  /* slots[5].led.port  = LED6_GPIO_Port;  slots[5].led.pin  = LED6_Pin;  */

  /*
   * Initialize the Parking System:
   * Pass the hardware timer handle (e.g., &htim2) configured for 1 MHz ticks,
   * and the hardware UART handle (e.g., &huart1) configured for 115200 baud.
   */
  ParkingApp_Init(&htim2, &huart1);

/* USER CODE END 2 */


/* -------------------------------------------------------------------------- */
/* 3. In Core/Src/main.c -> USER CODE WHILE (inside while (1))                */
/* -------------------------------------------------------------------------- */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /*
     * Continuously scans Slot 1..6, measures echo pulses, updates LEDs,
     * and periodically transmits JSON telemetry to ESP8266 over UART.
     */
    ParkingApp_Process();

    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
