import cv2
import pytesseract
import glob, os
import re
import numpy as np


pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'


def on_trackbar(val):
    pass

if __name__ == "__main__":
    fotos = os.getcwd()+'\input'
    output = os.getcwd()+'\output'
    os.chdir(fotos)
    files = []
    lineas = 2

    title_window = 'Prediction'
    title_window_2 = 'Result'
    cv2.namedWindow(title_window)
    cv2.namedWindow(title_window_2)
    cv2.createTrackbar("Threshold 1", title_window, 0, 100, on_trackbar)
    cv2.createTrackbar("Mat 1 x", title_window_2, 2, 9, on_trackbar)
    cv2.createTrackbar("Mat 1 y", title_window_2, 2, 9, on_trackbar)
    cv2.createTrackbar("Mat 2 x", title_window_2, 2, 9, on_trackbar)
    cv2.createTrackbar("Mat 2 y", title_window_2, 2, 9, on_trackbar)
    cv2.createTrackbar("Mode", title_window_2, 0, 3, on_trackbar)


    file = glob.glob("*")[0]

    original = cv2.imread(file, cv2.IMREAD_UNCHANGED)

    # assign blue channel to zeros
    # original[:, :, 0] = np.zeros([original.shape[0], original.shape[1]])
    imgray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
    while(True):
        thresh1 = imgray
        threshold1 = cv2.getTrackbarPos("Threshold 1", title_window)
        mat1x = cv2.getTrackbarPos("Mat 1 x", title_window_2)
        mat1y = cv2.getTrackbarPos("Mat 1 y", title_window_2)
        mat2x = cv2.getTrackbarPos("Mat 2 x", title_window_2)
        mat2y = cv2.getTrackbarPos("Mat 2 y", title_window_2)
        mode = cv2.getTrackbarPos("Mode", title_window_2)

        thresh1 = cv2.adaptiveThreshold(thresh1, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 67, threshold1)
        # ret, thresh1 = cv2.threshold(thresh1, threshold1, 255, cv2.THRESH_BINARY)
        cv2.imshow(title_window, thresh1)
        inv = thresh1
        kernel = np.ones((mat1x, mat1y), np.uint8)  # Tamaño del bloque a recorrer
        if(mode == 0 or mode == 1):
            inv = cv2.morphologyEx(inv, cv2.MORPH_ERODE, kernel)
        kernel = np.ones((mat2x, mat2y), np.uint8)  # Tamaño del bloque a recorrer
        if (mode == 0 or mode == 2):
            inv = cv2.morphologyEx(inv, cv2.MORPH_DILATE, kernel)
        cv2.imshow(title_window_2, inv)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break



