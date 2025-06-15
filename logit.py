import RPi.GPIO as GPIO
import time

XCLK = 18
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(XCLK, GPIO.OUT)

pwm = GPIO.PWM(XCLK, 8000000)  # 8 MHz
pwm.start(50)
print("⏳ Generando XCLK... espera 3 segundos")

time.sleep(3)

# Aquí no paramos el PWM aún
