import cv2
import numpy as np

class TicketExtractor:
    def __init__(self, orig, filename):
        # these constants are carefully picked
        self.MORPH = 9
        self.CANNY = 84
        self.HOUGH = 25
        self.orig = orig
        self.filename = filename

    def extract(self):
        img = cv2.cvtColor(self.orig, cv2.COLOR_BGR2GRAY)
        cv2.GaussianBlur(img, (3, 3), 0, img)

        # this is to recognize white on white
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (self.MORPH, self.MORPH))
        dilated = cv2.dilate(img, kernel)

        edges = cv2.Canny(dilated, 0, self.CANNY, apertureSize=3)

        lines = cv2.HoughLinesP(edges, 1, 3.14 / 180, self.HOUGH)
        for line in lines[0]:
            cv2.line(edges, (line[0], line[1]), (line[2], line[3]),
                     (255, 0, 0), 2, 8)

        # finding contours
        contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_TC89_KCOS)
        contours = filter(lambda cont: cv2.arcLength(cont, False) > 500, contours)
        contours = sorted(contours, key=lambda x: -cv2.contourArea(x))

        cv2.drawContours(self.orig, contours, -1, (255, 0, 0))
        # cv2.imshow('result', self.orig)
        # cv2.waitKey(0)
        # cv2.imshow('result', dilated)
        # cv2.waitKey(0)
        # cv2.imshow('result', edges)
        # cv2.waitKey(0)

        # simplify contours down to polygons and find rectangle with rotation matrix
        rect, rotMatrix, rotation_rectangle = self.filterTicket(contours)

        # that's basically it, crop it
        orig = self.crop_minAreaRect(self.orig, rotation_rectangle)
        return orig

    def filterTicket(self, contours):
        for cont in contours:
            peri = cv2.arcLength(cont, True)
            rect = cv2.approxPolyDP(cont, 0.04 * peri, True).copy().reshape(-1, 2)
            if len(rect) >= 4:
                # rects.append(rect)
                # get rotated rectangle from outer contour
                rotrect = cv2.minAreaRect(rect)
                # get angle from rotated rectangle
                (x, y), (width, height), angle = rotrect
                if (height < width):
                    angle = 90 + angle
                mapMatrix = cv2.getRotationMatrix2D((x, y), angle, 1.0)

                print(angle, "deg")
                return rect, mapMatrix, rotrect

    def crop_minAreaRect(self, img, rect):

        # rotate img
        (x, y), (width, height), angle = rect
        rows, cols = img.shape[0], img.shape[1]
        if (height < width):
            angle = 90 + angle
        M = cv2.getRotationMatrix2D((x, y), angle, 1)
        img_rot = cv2.warpAffine(img, M, (cols, rows))

        # rotate bounding box
        rect0 = ((x, y), (height, width), angle)
        box = cv2.boxPoints(rect0)
        pts = np.int0(cv2.transform(np.array([box]), M))[0]
        pts[pts < 0] = 0

        # crop
        img_crop = img_rot[pts[1][1]:pts[0][1],
                   pts[1][0]:pts[2][0]]

        return img_crop