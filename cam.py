#!/usr/bin/env python3
import time
from smbus2 import SMBus
import pigpio

# === 1) Parámetros de pines ===
I2C_BUS         = 1
OV7670_I2C_ADDR = 0x21  # dirección típica de la OV7670

PIN_RESET  = 17  # GPIO17, pin 11
PIN_PWDN   = 27  # GPIO27, pin 13
PIN_XCLK   = 18  # GPIO18, pin 12  (PWM)
PIN_PCLK   = 22  # GPIO22, pin 15  (input)
PIN_HSYNC  = 23  # GPIO23, pin 16  (input)
PIN_VSYNC  = 24  # GPIO24, pin 18  (input)

# Duración de la prueba
TEST_DURATION = 5.0  # segundos

# === 2) Inicializar pigpio ===
pi = pigpio.pi()
if not pi.connected:
    print("Error: pigpio daemon no está corriendo. Ejecuta: sudo pigpiod")
    exit(1)

# Configurar RESET y PWDN como salidas
pi.set_mode(PIN_RESET, pigpio.OUTPUT)
pi.set_mode(PIN_PWDN, pigpio.OUTPUT)

# Configurar XCLK como PWM (frecuencia de prueba 2 MHz)
FREQ_XCLK = 2_000_000  # Hz (puedes variar a 1–10 MHz según tolerancia)
pi.hardware_PWM(PIN_XCLK, FREQ_XCLK, 500_000)  # 50% duty

# Configurar PCLK, HSYNC y VSYNC como entradas con pull-down
for pin in (PIN_PCLK, PIN_HSYNC, PIN_VSYNC):
    pi.set_mode(pin, pigpio.INPUT)
    pi.set_pull_up_down(pin, pigpio.PUD_DOWN)

# === 3) Contadores de eventos ===
counts = {'pclk':0, 'hsync':0, 'vsync':0}

def cb_pclk(gpio, level, tick):
    if level == 1:
        counts['pclk'] += 1

def cb_hsync(gpio, level, tick):
    if level == 1:
        counts['hsync'] += 1

def cb_vsync(gpio, level, tick):
    if level == 1:
        counts['vsync'] += 1

# Crear callbacks
cb1 = pi.callback(PIN_PCLK, pigpio.RISING_EDGE, cb_pclk)
cb2 = pi.callback(PIN_HSYNC, pigpio.RISING_EDGE, cb_hsync)
cb3 = pi.callback(PIN_VSYNC, pigpio.RISING_EDGE, cb_vsync)

# === 4) Test I2C y control RESET/PWDN ===
with SMBus(I2C_BUS) as bus:
    print("Escaneando I2C en bus", I2C_BUS)
    found = []
    for addr in range(0x03, 0x78):
        try:
            bus.read_byte(addr)
            found.append(hex(addr))
        except:
            pass
    print("Dispositivos detectados:", found)
    if hex(OV7670_I2C_ADDR) in found:
        print("✔ OV7670 detectada en", hex(OV7670_I2C_ADDR))
    else:
        print("✖ OV7670 NO detectada en", hex(OV7670_I2C_ADDR))

    # Reset / PWDN toggle
    print("Pulsando RESET LOW → HIGH")
    pi.write(PIN_RESET, 0)
    time.sleep(0.1)
    pi.write(PIN_RESET, 1)
    time.sleep(0.1)
    print("PWDN HIGH → LOW (salir de power-down)")
    pi.write(PIN_PWDN, 1)
    time.sleep(0.1)
    pi.write(PIN_PWDN, 0)

# === 5) Medir pulsos durante TEST_DURATION ===
print(f"Midiendo PCLK/HSYNC/VSYNC durante {TEST_DURATION} segundos...")
time.sleep(TEST_DURATION)

# === 6) Mostrar resultados ===
print("---- Conteo de pulsos ----")
print(f"PCLK  (pixel clock): {counts['pclk']} flancos ↑")
print(f"HSYNC (h. sync)   : {counts['hsync']} flancos ↑")
print(f"VSYNC (v. sync)   : {counts['vsync']} flancos ↑")

# === 7) Limpiar ===
cb1.cancel()
cb2.cancel()
cb3.cancel()
pi.hardware_PWM(PIN_XCLK, 0, 0)  # Detener PWM
pi.stop()
