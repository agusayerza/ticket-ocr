import glob
import os

import cv2, numpy as np
import sys

from OCR.Preprocessor import Preprocessor
from OCR.TicketExtractor import TicketExtractor


def get_new(old):
    new = np.ones(old.shape, np.uint8)
    cv2.bitwise_not(new,new)
    return new


def filterTicket(contours):
    for cont in contours:
        peri = cv2.arcLength(cont, True)
        rect = cv2.approxPolyDP(cont, 0.04 * peri, True).copy().reshape(-1, 2)
        if len(rect) == 4:
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

def crop_minAreaRect(img, rect):

    # rotate img
    (x, y), (width, height), angle = rect
    rows,cols = img.shape[0], img.shape[1]
    if (height < width):
        angle = 90 + angle
    M = cv2.getRotationMatrix2D((x, y),angle,1)
    img_rot = cv2.warpAffine(img,M,(cols,rows))

    # rotate bounding box
    rect0 = ((x, y), (height, width), angle)
    box = cv2.boxPoints(rect0)
    pts = np.int0(cv2.transform(np.array([box]), M))[0]
    pts[pts < 0] = 0

    # crop
    img_crop = img_rot[pts[1][1]:pts[0][1],
                       pts[1][0]:pts[2][0]]

    return img_crop

if __name__ == '__main__':

    fotos = os.getcwd()+'/input'
    output = os.getcwd()+'/output'
    os.chdir(fotos)
    files = glob.glob("*")

    for file in files:
        print(file)
        orig = cv2.imread(file)
        scale_percent = 30  # percent of original size
        width = int(orig.shape[1] * scale_percent / 100)
        height = int(orig.shape[0] * scale_percent / 100)
        dim = (width, height)
        # resize image
        orig = cv2.resize(orig, dim, interpolation=cv2.INTER_AREA)

        ticketExtractor = TicketExtractor(orig)
        ticket = ticketExtractor.extract()

        preprocessor = Preprocessor(ticket)
        result = preprocessor.preprocess()

        cv2.imshow('result', ticket)
        cv2.waitKey(0)
        cv2.imshow('result', result)
        cv2.waitKey(0)

        cv2.destroyAllWindows()