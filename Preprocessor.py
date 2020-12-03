import cv2
import numpy as np
from skimage.filters import threshold_local, threshold_otsu


class Preprocessor:
    def __init__(self, img):
        self.img = img

    def blueMask(self, gray, image, upper = None, lower = None):
                            #  h      s      v
        if upper is None:
            upper = np.array([270 / 2, 255, 255])
        if lower is None:
            lower = np.array([120 / 2, 20, 20])

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower, upper)
        mask = 255 - mask

        # Paste white over SIN VALIDEZ FISCAL
        white = np.zeros(gray.shape, gray.dtype)
        white[:, :] = 255
        fg = cv2.bitwise_or(gray, gray, mask=mask)
        mask_inv = cv2.bitwise_not(mask)
        fg_back_inv = cv2.bitwise_or(white, white, mask=mask_inv)
        final = cv2.bitwise_or(fg, fg_back_inv)
        return final

    def correctSize(self, img, MaxSize = 700):
        # set the size of the image to something in the region of the 1500px if bigger than that
        (X, Y) = img.shape
        if X > MaxSize or Y > MaxSize:
            if X > Y:
                fy = fx = (1 / (X/MaxSize))
            else:
                fx = fy = (1 / (Y/MaxSize))
            img = cv2.resize(img, None, fx=fx, fy=fy, interpolation=cv2.INTER_AREA)
        return img

    def correctSizeBRG(self, img, MaxSize = 700):
        # set the size of the image to something in the region of the 1500px if bigger than that
        (X, Y, depth) = img.shape
        if X > MaxSize or Y > MaxSize:
            if X > Y:
                fy = fx = (1 / (X/MaxSize))
            else:
                fx = fy = (1 / (Y/MaxSize))
            img = cv2.resize(img, None, fx=fx, fy=fy, interpolation=cv2.INTER_AREA)
        return img

    def thresholdOtsu(self, image):
        thresh = threshold_otsu(image)
        binary = image > thresh
        return binary

    def thresholdLocal(self, image):
        T = threshold_local(image, 17, offset=10, method="gaussian")
        warped = (image > T).astype("uint8") * 255
        return warped

    # get grayscale image
    def get_grayscale(self, image):
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


    # noise removal
    def remove_noise(self, image):
        return cv2.medianBlur(image, 3)


    # thresholding
    def thresholding(self, image):
        return cv2.threshold(image, 190, 255, cv2.THRESH_BINARY)[1]


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

    def preprocess(self, upper = None, lower = None, threshold= True):
        final = self.get_grayscale(self.img)
        if threshold:
            final = self.thresholdLocal(final)

        return self.correctSize(final)