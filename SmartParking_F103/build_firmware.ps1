$gcc = "C:\ST\STM32CubeIDE_2.2.0\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32.14.3.rel1.win32_1.0.100.202602081740\tools\bin\arm-none-eabi-gcc.exe"
$size = "C:\ST\STM32CubeIDE_2.2.0\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32.14.3.rel1.win32_1.0.100.202602081740\tools\bin\arm-none-eabi-size.exe"

$projDir = "C:\Users\stuti\Documents\SmartParkingESN\SmartParking_F103"
Set-Location $projDir

$includes = @(
    "-ICore/Inc",
    "-IDrivers/STM32F1xx_HAL_Driver/Inc",
    "-IDrivers/CMSIS/Device/ST/STM32F1xx/Include",
    "-IDrivers/CMSIS/Include"
)

$defines = @(
    "-DSTM32F103xB",
    "-DUSE_HAL_DRIVER"
)

$cflags = @(
    "-mcpu=cortex-m3",
    "-mthumb",
    "-Os",
    "-Wall",
    "-fdata-sections",
    "-ffunction-sections"
) + $includes + $defines

$sources = @(
    "Core/Src/main.c",
    "Core/Src/stm32f1xx_hal_msp.c",
    "Core/Src/stm32f1xx_it.c",
    "Core/Src/system_stm32f1xx.c",
    "Core/Src/syscalls.c",
    "Core/Src/sysmem.c",
    "Core/Src/hcsr04.c",
    "Core/Src/led_indicators.c",
    "Core/Src/esp8266.c",
    "Core/Src/parking_app.c",
    "Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal.c",
    "Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_rcc.c",
    "Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_rcc_ex.c",
    "Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_gpio.c",
    "Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_dma.c",
    "Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_cortex.c",
    "Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_pwr.c",
    "Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_flash.c",
    "Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_flash_ex.c",
    "Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_tim.c",
    "Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_tim_ex.c",
    "Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_uart.c"
)

$objects = @()

New-Item -ItemType Directory -Force -Path "build" | Out-Null

# Compile C files
foreach ($src in $sources) {
    $obj = "build/" + [System.IO.Path]::GetFileNameWithoutExtension($src) + ".o"
    $objects += $obj
    Write-Host "Compiling $src..."
    & $gcc $cflags -c $src -o $obj
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to compile $src"
        exit 1
    }
}

# Compile Assembly startup
Write-Host "Assembling startup..."
$startupObj = "build/startup_stm32f103c8tx.o"
$objects += $startupObj
& $gcc -mcpu=cortex-m3 -mthumb -c Core/Startup/startup_stm32f103c8tx.s -o $startupObj
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to assemble startup"
    exit 1
}

# Link ELF
Write-Host "Linking SmartParking_F103.elf..."
$elf = "build/SmartParking_F103.elf"
$ldflags = @(
    "-mcpu=cortex-m3",
    "-mthumb",
    "-TSTM32F103C8TX_FLASH.ld",
    "-Wl,--gc-sections",
    "-specs=nano.specs",
    "-specs=nosys.specs"
)

& $gcc $ldflags $objects -o $elf -lm
if ($LASTEXITCODE -ne 0) {
    Write-Error "Linking failed"
    exit 1
}

Write-Host "`nBUILD SUCCESSFUL!`n"
& $size $elf
