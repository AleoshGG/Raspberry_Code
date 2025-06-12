import tkinter as tk
import cv2
from PIL import Image, ImageTk
import Adafruit_DHT
import RPi.GPIO as GPIO
import time
import threading

# Sensor and GPIO setup
DHT_SENSOR = Adafruit_DHT.DHT11
DHT_PIN = 23

TRIG = 20
ECHO = 21

# LED pins mapping for each filter
LED_PINS = {
    'Gray': 14,
    'Blur': 15,
    'Edge': 18
}

GPIO.setmode(GPIO.BCM)
# Setup ultrasonic sensor pins
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
# Setup LED pins
for pin in LED_PINS.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# Video capture
cap = cv2.VideoCapture(0)
filter_type = None

# GUI root
root = tk.Tk()
root.title("Interfaz de Sensores y Cámara")

# Video display label
lmain = tk.Label(root)
lmain.pack()

# Sensor readings listbox
readings_list = tk.Listbox(root, height=10, width=50)
readings_list.pack(pady=5)

# Frame for filter buttons
buttons_frame = tk.Frame(root)
buttons_frame.pack(pady=5)

# Dictionary to hold button widgets
buttons = {}

def apply_filter(selected_filter):
    global filter_type
    filter_type = selected_filter
    # Turn on the LED for this filter, turn off others
    for f, pin in LED_PINS.items():
        GPIO.output(pin, GPIO.HIGH if f == selected_filter else GPIO.LOW)
    # Update button colors
    for f, btn in buttons.items():
        if f == selected_filter:
            btn.config(bg='red', fg='white')
        else:
            btn.config(bg='lightgray', fg='black')

# Create filter buttons
buttons['Gray'] = tk.Button(buttons_frame, text="Gris", width=12,
                            command=lambda: apply_filter('Gray'), bg='lightgray')
buttons['Gray'].grid(row=0, column=0, padx=5)

buttons['Blur'] = tk.Button(buttons_frame, text="Desenfoque", width=12,
                            command=lambda: apply_filter('Blur'), bg='lightgray')
buttons['Blur'].grid(row=0, column=1, padx=5)

buttons['Edge'] = tk.Button(buttons_frame, text="Bordes", width=12,
                            command=lambda: apply_filter('Edge'), bg='lightgray')
buttons['Edge'].grid(row=0, column=2, padx=5)

# Thread-safe insert for listbox
listbox_lock = threading.Lock()

def read_sensors():
    while True:
        # DHT11 reading
        humedad, temperatura = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
        with listbox_lock:
            if humedad is not None and temperatura is not None:
                readings_list.insert(tk.END, f'Temperatura: {temperatura:.1f}°C, Humedad: {humedad:.1f}%')
            else:
                readings_list.insert(tk.END, 'Error al obtener la lectura del DHT11')
            readings_list.yview(tk.END)

        # Ultrasonic reading
        GPIO.output(TRIG, True)
        time.sleep(0.00001)
        GPIO.output(TRIG, False)

        pulse_start = time.time()
        while GPIO.input(ECHO) == 0:
            pulse_start = time.time()
        pulse_end = time.time()
        while GPIO.input(ECHO) == 1:
            pulse_end = time.time()

        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150
        distance = round(distance, 2)
        with listbox_lock:
            readings_list.insert(tk.END, f'Distancia: {distance} cm')
            readings_list.yview(tk.END)

        time.sleep(2)


def show_frame():
    global filter_type
    ret, frame = cap.read()
    if not ret:
        root.after(10, show_frame)
        return

    # Apply selected filter
    if filter_type == "Gray":
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGBA)
    elif filter_type == "Blur":
        frame = cv2.GaussianBlur(frame, (15, 15), 0)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    elif filter_type == "Edge":
        edges = cv2.Canny(frame, 100, 200)
        frame = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGBA)
    else:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)

    img = Image.fromarray(frame)
    imgtk = ImageTk.PhotoImage(image=img)
    lmain.imgtk = imgtk
    lmain.configure(image=imgtk)
    root.after(10, show_frame)

# Start sensor thread
def start_threads():
    sensor_thread = threading.Thread(target=read_sensors, daemon=True)
    sensor_thread.start()

start_threads()
show_frame()

# Run GUI loop
def on_closing():
    cap.release()
    GPIO.cleanup()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
