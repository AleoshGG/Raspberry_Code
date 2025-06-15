#!/usr/bin/env python3
import time
from smbus2 import SMBus
import pigpio
from PIL import Image

# --- 1) Parámetros de pines y direcciones ---
I2C_BUS = 1
OV7670_ADDR = 0x21

PIN_XCLK  = 18  # XCLK por PWM
PIN_VSYNC = 23  # VSYNC (input)
PIN_HSYNC = 24  # HSYNC (input)
PIN_PCLK  = 25  # PCLK  (input)

# Datos: D0-D7 conectados a GPIOs 4–11 (ajusta según tu cableado)
DATA_PINS = [6, 12, 13, 19, 16, 26, 20, 21]

# Resolución (QVGA)
WIDTH, HEIGHT = 320, 240

# --- 2) Tabla simplificada de registros para RGB565 + QVGA ---
# (Extraída de varios ejemplos OV7670)
REG_CFG = [
    (0x12, 0x14),  # COM7: RGB output, QVGA
    (0x40, 0xd0),  # COM15: RGB565
    (0x3a, 0x04),  # TSLB: set UV ordering
    (0x17, 0x16),  # HSTART
    (0x18, 0x04),  # HSTOP
    (0x19, 0x02),  # VSTART
    (0x1a, 0x7a),  # VSTOP
    (0x03, 0x0a),  # VREF
    # ... (puedes añadir más para brillo, contraste, etc.)
]

# --- 3) Función para escribir la configuración ---
def init_camera(bus):
    for reg, val in REG_CFG:
        bus.write_byte_data(OV7670_ADDR, reg, val)
    time.sleep(0.1)

# --- 4) Setup pigpio y líneas de datos ---
pi = pigpio.pi()
if not pi.connected:
    raise RuntimeError("pigpio daemon no está corriendo (sudo pigpiod)")

# Configura XCLK como hardware PWM
XCLK_HZ = 8_000_000
pi.hardware_PWM(PIN_XCLK, XCLK_HZ, 500_000)  # 50% duty

# Configura señales de sincronía como inputs
for pin in (PIN_VSYNC, PIN_HSYNC, PIN_PCLK):
    pi.set_mode(pin, pigpio.INPUT)

# Configura pines de datos D0–D7 como inputs
for p in DATA_PINS:
    pi.set_mode(p, pigpio.INPUT)

# --- 5) Inicializa la cámara ---
with SMBus(I2C_BUS) as bus:
    init_camera(bus)
    print("Cámara inicializada en RGB565/QVGA")

# --- 6) Captura un frame ---
frame = [[0]*WIDTH for _ in range(HEIGHT)]
line = 0

print("⏳ Esperando VSYNC (inicio de frame)...")
# Espera flanco de bajada de VSYNC
pi.wait_for_edge(PIN_VSYNC, pigpio.FALLING_EDGE)

print("📸 Capturando líneas...")
while line < HEIGHT:
    # Espera HSYNC para inicio de línea
    pi.wait_for_edge(PIN_HSYNC, pigpio.RISING_EDGE)
    col = 0

    # Para cada píxel (2 bytes cada píxel en RGB565)
    while col < WIDTH:
        # Espera flanco de subida de PCLK
        pi.wait_for_edge(PIN_PCLK, pigpio.RISING_EDGE)

        # Leer D0–D7
        byte_hi = 0
        for i in range(8):
            if pi.read(DATA_PINS[i]):
                byte_hi |= (1 << i)

        # Ahora espera el siguiente PCLK para leer el byte bajo
        pi.wait_for_edge(PIN_PCLK, pigpio.RISING_EDGE)

        byte_lo = 0
        for i in range(8):
            if pi.read(DATA_PINS[i]):
                byte_lo |= (1 << i)

        # Combina en RGB565
        word = (byte_hi << 8) | byte_lo
        frame[line][col] = word
        col += 1

    line += 1

print("✅ Frame capturado")

# --- 7) Convertir a imagen y guardar ---
img = Image.new('RGB', (WIDTH, HEIGHT))
for y in range(HEIGHT):
    for x in range(WIDTH):
        w = frame[y][x]
        # Extrae componentes
        r = ((w >> 11) & 0x1F) << 3
        g = ((w >> 5) & 0x3F) << 2
        b = (w & 0x1F) << 3
        img.putpixel((x, y), (r, g, b))

img.save('capture.ppm')
print("🖼️ Imagen guardada como capture.ppm")

# --- 8) Cleanup ---
pi.hardware_PWM(PIN_XCLK, 0)
pi.stop()
