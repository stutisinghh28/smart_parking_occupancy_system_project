# STM32CubeIDE Firmware Integration Guide

This guide walks you through integrating the modular C firmware into your STM32CubeIDE project.

---

## 📁 1. Where Each File Belongs

When you create a project in STM32CubeIDE, it generates the following directory structure:

```text
Your_STM32_Project/
├── Core/
│   ├── Inc/
│   │   ├── main.h
│   │   │   /* Copy your project headers here: */
│   │   ├── parking_config.h
│   │   ├── hcsr04.h
│   │   ├── led_indicators.h
│   │   ├── esp8266.h
│   │   └── parking_app.h
│   └── Src/
│       ├── main.c
│       │   /* Copy your project source files here: */
│       ├── hcsr04.c
│       ├── led_indicators.c
│       ├── esp8266.c
│       └── parking_app.c
```

Simply copy the files from:
- `smart_parking_predictor/firmware/Inc/` ➡️ `Your_STM32_Project/Core/Inc/`
- `smart_parking_predictor/firmware/Src/` ➡️ `Your_STM32_Project/Core/Src/`

---

## ⚙️ 2. CubeMX Peripheral Configuration

Open the `.ioc` file inside STM32CubeIDE:

### A. Microsecond Hardware Timer (e.g. TIM2 or TIM3)
* **Mode:** Clock Source = Internal Clock.
* **Prescaler (PSC):** Set to `(Timer_Clock_in_MHz) - 1`.
  * *Example:* If your APB timer clock is $84\,\text{MHz}$, set Prescaler to `83`.
  * *Example:* If your timer clock is $72\,\text{MHz}$, set Prescaler to `71`.
  * *Example:* If your timer clock is $16\,\text{MHz}$, set Prescaler to `15`.
  * This guarantees the timer counts at exactly **$1\,\text{MHz}$ ($1\,\mu\text{s}$ per tick)**.
* **Counter Period (ARR):** Set to `65535` (or `0xFFFFFFFF` for 32-bit timers like TIM2 on F4).

### B. GPIO Pins
Configure your chosen pins:
1. **6 Trigger Pins:** Mode = `GPIO_Output`, Output level = `Low`, Pull-up/Pull-down = `No pull`, Speed = `Medium`.
2. **6 Echo Pins:** Mode = `GPIO_Input`, Pull-up/Pull-down = `Pull-down` (prevents floating noise).
3. **6 LED Pins:** Mode = `GPIO_Output`, Output level = `Low`.

### C. USART / UART (for ESP8266)
* **Mode:** Asynchronous.
* **Baud Rate:** `115200` Bits/s.
* **Word Length:** 8 Bits (including Parity).
* **Parity:** None.
* **Stop Bits:** 1.

Click **Ctrl + S** in STM32CubeIDE to generate code.

---

## 💻 3. Connecting to `main.c`

Open `Core/Src/main.c`. Add the following user code blocks between the safe `USER CODE` comments:

### In `USER CODE Includes`:
```c
/* USER CODE BEGIN Includes */
#include "parking_app.h"
/* USER CODE END Includes */
```

### In `USER CODE 2` (Inside `main()`, right before `while(1)`):
```c
  /* USER CODE BEGIN 2 */
  /* Retrieve the 6 parking slots array */
  ParkingSlot_t *slots = ParkingApp_GetSlots();

  /* 
   * NOTE (Rule 9): The pin mappings below are placeholders.
   * Replace GPIOx and GPIO_PIN_x with the exact pins you configure
   * and label in your STM32CubeIDE (.ioc) pinout:
   */
  /* Slot 1: [Trig, Echo, LED] */
  slots[0].trig.port = TRIG1_GPIO_Port; slots[0].trig.pin = TRIG1_Pin;
  slots[0].echo.port = ECHO1_GPIO_Port; slots[0].echo.pin = ECHO1_Pin;
  slots[0].led.port  = LED1_GPIO_Port;  slots[0].led.pin  = LED1_Pin;

  /* Slot 2: [Trig, Echo, LED] */
  slots[1].trig.port = TRIG2_GPIO_Port; slots[1].trig.pin = TRIG2_Pin;
  slots[1].echo.port = ECHO2_GPIO_Port; slots[1].echo.pin = ECHO2_Pin;
  slots[1].led.port  = LED2_GPIO_Port;  slots[1].led.pin  = LED2_Pin;

  /* (Repeat for Slots 3 through 6 with your configured labels) */

  /* Initialize Parking App with your Timer and UART handles */
  /* e.g., htim2 and huart1 */
  ParkingApp_Init(&htim2, &huart1);
  /* USER CODE END 2 */
```

### In `USER CODE While` (Inside the `while (1)` loop):
```c
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* Executes sensor scanning, LED updates, and Wi-Fi telemetry */
    ParkingApp_Process();

    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
```

---

## 🔨 4. How to Build & Flash on Windows (Blue Pill STM32F103C8T6)

> [!IMPORTANT]
> **Blue Pill Flashing Notice:**  
> The onboard micro-USB connector on a Blue Pill does **not** contain an ST-LINK programmer (unlike Nucleo boards). Plugging the micro-USB into your laptop will only provide 5V power to the board and will **not** be detected as an ST-LINK debugger in STM32CubeIDE.

To flash and debug the firmware:
1. **Connect an external ST-Link V2 USB dongle** to the 4-pin SWD header at the board's edge:
   - `3.3V` ➡️ `3.3V` (Pin 1)
   - `SWDIO` ➡️ `SWDIO` (PA13)
   - `SWCLK` ➡️ `SWCLK` (PA14)
   - `GND` ➡️ `GND` (Pin 4)
2. **Boot Jumpers:** Ensure both `BOOT0` and `BOOT1` yellow jumpers are set to position `0` (operating mode from Flash memory).
3. In STM32CubeIDE, click **Project ➡️ Build Project** (or press `Ctrl + B`).
4. Click **Run ➡️ Debug** (or `F11`).
5. *Note on Clone Chips:* If your board uses a clone STM32F103 chip (e.g. CS32, CKS32) and OpenOCD reports `UNEXPECTED idcode: 0x2ba01477`, switch the Debug Probe configuration in STM32CubeIDE from *ST-LINK (ST-LINK GDB server)* to *ST-LINK (OpenOCD)* with `-c set CPUTAPID 0x2ba01477` in the Debug Configuration options.
