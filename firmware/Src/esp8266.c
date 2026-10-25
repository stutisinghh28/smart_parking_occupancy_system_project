/**
  ******************************************************************************
  * @file    esp8266.c
  * @brief   ESP8266 AT-command communication driver for STM32 HAL.
  *          Formats and posts 6-slot parking telemetry to FastAPI over HTTP.
  ******************************************************************************
  */

#include "esp8266.h"
#include <string.h>
#include <stdio.h>

static UART_HandleTypeDef *s_huart = NULL;
/* Optimized RAM buffers for STM32F103 (20 KB SRAM limit) */
static char s_rx_buffer[256];
static char s_tx_buffer[512];
static char s_json_body[320];

static bool send_command(const char *cmd, const char *expected_resp, uint32_t timeout_ms)
{
    if (s_huart == NULL) {
        return false;
    }

    memset(s_rx_buffer, 0, sizeof(s_rx_buffer));
    HAL_UART_Transmit(s_huart, (uint8_t *)cmd, strlen(cmd), timeout_ms);

    /* Read response */
    uint16_t idx = 0;
    uint32_t start_time = HAL_GetTick();

    while ((HAL_GetTick() - start_time) < timeout_ms && idx < (sizeof(s_rx_buffer) - 1)) {
        uint8_t ch;
        if (HAL_UART_Receive(s_huart, &ch, 1, 10) == HAL_OK) {
            s_rx_buffer[idx++] = ch;
            s_rx_buffer[idx] = '\0';
            if (strstr(s_rx_buffer, expected_resp) != NULL) {
                return true;
            }
        }
    }

    return (strstr(s_rx_buffer, expected_resp) != NULL);
}

bool ESP8266_Init(UART_HandleTypeDef *huart)
{
    s_huart = huart;
    if (s_huart == NULL) {
        return false;
    }

    /* Test AT basic connection */
    if (!send_command("AT\r\n", "OK", 1000)) {
        return false;
    }

    /* Set Station mode (client) */
    send_command("AT+CWMODE=1\r\n", "OK", 1000);

    /* Optional: Disable echo */
    send_command("ATE0\r\n", "OK", 500);

    return true;
}

bool ESP8266_ConnectWiFi(const char *ssid, const char *pass)
{
    char cmd[128];
    snprintf(cmd, sizeof(cmd), "AT+CWJAP=\"%s\",\"%s\"\r\n", ssid, pass);
    return send_command(cmd, "OK", 8000);
}

bool ESP8266_SendTelemetry(ParkingSlot_t *slots, uint8_t count)
{
    if (s_huart == NULL || slots == NULL || count == 0) {
        return false;
    }

    /* 1. Build JSON Payload (without floating-point printf to save ~12 KB Flash) */
    int offset = snprintf(s_json_body, sizeof(s_json_body), "{\"readings\":[");
    for (uint8_t i = 0; i < count; i++) {
        int dist_int = (int)slots[i].last_distance_cm;
        int dist_dec = (int)((slots[i].last_distance_cm - (float)dist_int) * 10.0f);
        if (dist_dec < 0) dist_dec = 0;
        if (dist_dec > 9) dist_dec = 9;

        offset += snprintf(
            s_json_body + offset,
            sizeof(s_json_body) - offset,
            "{\"slot_id\":%u,\"distance_cm\":%d.%d,\"is_occupied\":%s,\"echo_time_us\":%lu}%s",
            (unsigned int)slots[i].slot_id,
            dist_int,
            dist_dec,
            slots[i].is_occupied ? "true" : "false",
            (unsigned long)slots[i].last_echo_us,
            (i < count - 1) ? "," : ""
        );
    }
    snprintf(s_json_body + offset, sizeof(s_json_body) - offset, "]}");

    /* 2. Format HTTP POST Request */
    int json_len = strlen(s_json_body);
    int http_len = snprintf(
        s_tx_buffer,
        sizeof(s_tx_buffer),
        "POST %s HTTP/1.1\r\n"
        "Host: %s:%d\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: %d\r\n"
        "Connection: close\r\n\r\n"
        "%s\r\n",
        BACKEND_TELEMETRY_PATH,
        BACKEND_SERVER_IP,
        BACKEND_SERVER_PORT,
        json_len,
        s_json_body
    );

    /* 3. Open TCP Socket with Backend Server */
    char conn_cmd[128];
    snprintf(conn_cmd, sizeof(conn_cmd), "AT+CIPSTART=\"TCP\",\"%s\",%d\r\n", BACKEND_SERVER_IP, BACKEND_SERVER_PORT);
    if (!send_command(conn_cmd, "OK", 3000)) {
        send_command("AT+CIPCLOSE\r\n", "OK", 500);
        return false;
    }

    /* 4. Prepare Transmission */
    char send_cmd[32];
    snprintf(send_cmd, sizeof(send_cmd), "AT+CIPSEND=%d\r\n", http_len);
    if (!send_command(send_cmd, ">", 2000)) {
        send_command("AT+CIPCLOSE\r\n", "OK", 500);
        return false;
    }

    /* 5. Transmit Data Buffer */
    HAL_UART_Transmit(s_huart, (uint8_t *)s_tx_buffer, http_len, 3000);

    /* 6. Wait for HTTP 200 Response */
    bool success = false;
    uint32_t start_time = HAL_GetTick();
    uint16_t idx = 0;
    memset(s_rx_buffer, 0, sizeof(s_rx_buffer));

    while ((HAL_GetTick() - start_time) < 4000 && idx < (sizeof(s_rx_buffer) - 1)) {
        uint8_t ch;
        if (HAL_UART_Receive(s_huart, &ch, 1, 10) == HAL_OK) {
            s_rx_buffer[idx++] = ch;
            s_rx_buffer[idx] = '\0';
            if (strstr(s_rx_buffer, "200 OK") != NULL || strstr(s_rx_buffer, "status\":\"success\"") != NULL) {
                success = true;
                break;
            }
        }
    }

    /* 7. Close Socket */
    send_command("AT+CIPCLOSE\r\n", "OK", 500);
    return success;
}
