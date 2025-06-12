import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import Adafruit_DHT
import RPi.GPIO as GPIO
import time
import threading


DHT_SENSOR = Adafruit_DHT.DHT11
DHT_PIN = 23

TRIG = 20
ECHO = 21

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

cap = cv2.VideoCapture(0)
filter_type = None


def show_frame():
    global filter_type

_, frame = cap.read()

if filter_type == "Gray":
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGBA)
elif filter_type == "Blur":
    frame = cv2.GaussianBlur(frame, (15, 15), 0)
elif filter_type == "Edge":
    frame = cv2.Canny(frame, 100, 200)
    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGBA)
else:
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)

img = Image.fromarray(frame)
imgtk = ImageTk.PhotoImage(image=img)
lmain.imgtk = imgtk
lmain.configure(image=imgtk)
lmain.after(10, show_frame)


def read_sensors():
    while True:

        humedad, temperatura = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
        if humedad is not None and temperatura is not None:
            readings_list.insert(tk.END, f'Temperatura: {temperatura}°C, Humedad: {humedad}%')
        else:
            readings_list.insert(tk.END, 'Error al obtener la lectura del sensor DHT11')
            readings_list.yview(tk.END)


        GPIO.output(TRIG, True)
        time.sleep(0.00001)
        GPIO.output(TRIG, False)
        while GPIO.input(ECHO) == 0:
            pulse_start = time.time()
        while GPIO.input(ECHO) == 1:
            pulse_end = time.time()
            pulse_duration = pulse_end
            pulse_start
            distance = pulse_duration * 17150
            distance = round(distance, 2)
            readings_list.insert(tk.END, f'Distancia: {distance} cm')
            readings_list.yview(tk.END)


        time.sleep(2)

        def apply_filter(selected_filter):
            global filter_type
            filter_type = selected_filter


        root = tk.Tk()
        root.title("Interfaz de Sensores y Cámara")

        lmain = tk.Label(root)
        lmain.pack()

        readings_list = tk.Listbox(root, height=10, width=50)
        readings_list.pack()

        buttons_frame = tk.Frame(root)
        buttons_frame.pack()

        btn_gray = ttk.Button(buttons_frame, text="Gris", command=lambda: apply_filter("Gray"))
        btn_gray.grid(row=0, column=0)

        btn_blur = ttk.Button(buttons_frame, text="Desenfoque", command=lambda: apply_filter("Blur"))
        btn_blur.grid(row=0, column=1)

        btn_edge = ttk.Button(buttons_frame, text="Bordes", command=lambda: apply_filter("Edge"))
        btn_edge.grid(row=0, column=2)


        sensors_thread = threading.Thread(target=read_sensors)
        sensors_thread.daemon = True
        sensors_thread.start()


        show_frame()

        root.mainloop()


        cap.release()
        GPIO.cleanup()