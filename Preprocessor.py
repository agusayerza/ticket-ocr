import cv2
import numpy as np
from skimage.filters import threshold_local
class Preprocessor:
    def __init__(self, img):
        self.img = img

    def preprocess(self):
        gray = self.get_grayscale(self.img)
        ret, thresh4 = cv2.threshold(gray, 120, 255, cv2.THRESH_TOZERO)

        lower_blue = np.array([150 / 2, 25, 150])
        upper_blue = np.array([260 / 2, 255, 255])

        hsv = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        mask = 255 - mask
        # Paste white over SIN VALIDEZ FISCAL
        white = np.zeros(thresh4.shape, thresh4.dtype)
        white[:, :] = 210
        fg = cv2.bitwise_or(thresh4, thresh4, mask=mask)
        mask_inv = cv2.bitwise_not(mask)
        fg_back_inv = cv2.bitwise_or(white, white, mask=mask_inv)
        final = cv2.bitwise_or(fg, fg_back_inv)
        return final

    def thresholdLocal(self, image):
        T = threshold_local(image, 11, offset=10, method="gaussian")
        warped = (image > T).astype("uint8") * 255
        return warped

    # get grayscale image
    def get_grayscale(self, image):
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


    # noise removal
    def remove_noise(self, image):
        return cv2.medianBlur(image, 5)


    # thresholding
    def thresholding(self, image):
        return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


    # dilation
    def dilate(self, image):
        kernel = np.ones((5, 5), np.uint8)
        return cv2.dilate(image, kernel, iterations=1)


    # erosion
    def erode(self, image):
        kernel = np.ones((5, 5), np.uint8)
        return cv2.erode(image, kernel, iterations=1)


    # opening - erosion followed by dilation
    def opening(self, image):
        kernel = np.ones((5, 5), np.uint8)
        return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)


    # canny edge detection
    def canny(self, image):
        return cv2.Canny(image, 100, 200)


    # skew correction
    def deskew(self, image):
        coords = np.column_stack(np.where(image > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return rotated


    # template matching
    def match_template(self, image, template):
        return cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)