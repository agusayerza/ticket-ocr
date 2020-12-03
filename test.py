import glob
import os
import pytesseract
import cv2, numpy as np
import csv

from AccuracyMeter import AccuracyMeter
from AlignmentExtractor import AlignmentExtractor
from Preprocessor import Preprocessor
from ResultDiffer import ResultDiffer
from StringReader import StringReader, headers, headers_list
from TicketExtractor import TicketExtractor

def get_new(old):
    new = np.ones(old.shape, np.uint8)
    cv2.bitwise_not(new,new)
    return new


def filterTicket(contours):
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
    single = os.getcwd()+'/single'
    processed = os.getcwd()+'/processed'
    os.chdir(fotos)
    files = glob.glob("*.jpg")
    os.chdir(single)
    template = cv2.imread("template.jpg")
    results = []
    for file in files:
        print(file)
        os.chdir(fotos)
        orig = cv2.imread(file)

        # ticketExtractor = TicketExtractor(orig.copy(), file)
        # ticket = ticketExtractor.extract()

        preprocessor = Preprocessor(orig)

        image = preprocessor.preprocess(upper= np.array([130 / 2, 10, 10]), lower=np.array([270 / 2, 255, 255]))
        custom_config = r'--oem 3 --psm 6'
        string = pytesseract.image_to_string(image, lang="custom", config=custom_config)

        image_align = preprocessor.correctSizeBRG(orig)
        extractor = AlignmentExtractor(image_align, template)
        result_align = extractor.extract(debug=False)

        reader = StringReader(string)
        result_parse = reader.parse()

        final_result = ResultDiffer(result_align, result_parse).reconcile(debug=False)
        print(final_result.csv())
        results.append((file, final_result))
        os.chdir(processed)
        cv2.imwrite(file, image)
        # print(string)
        # print(accuracyMeter.measure())

    os.chdir(output)
    with open('results.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers_list())
        for r in results:
            res = r[1].asList()
            res.append(r[0])
            writer.writerow(res)