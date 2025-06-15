import cv2 
import numpy as np 

def print_howto(): 
    print("""
        cambio de imagen:
            1. Agrandar'a'
            2. Disminuir 'd'
    """)
 
if __name__=='__main__': 
    print_howto()
    cap = cv2.VideoCapture(1) 
 
    cur_mode = None
    fx=1.5
    fy=1.5

    while True: 
        ret, frame = cap.read() 
        frame = cv2.resize(frame, None, fx=fx, fy=fy, interpolation=cv2.INTER_AREA) 
        cv2.imshow('Cartoonize', frame)

        c = cv2.waitKey(1) & 0xFF

        if c == 27: 
            break
        elif c == ord('a'):
            fx += 0.1
            fy += 0.1
        elif c == ord('d'):
            fx = max(0.1, fx - 0.1)
            fy = max(0.1, fy - 0.1)
 
    cap.release() 
    cv2.destroyAllWindows()