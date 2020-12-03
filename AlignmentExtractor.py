# import the necessary packages
from collections import namedtuple
import pytesseract
import argparse
import imutils
import cv2
# import the necessary packages
import numpy as np
import imutils
import cv2
from fuzzywuzzy import process, fuzz

from NumberParser import parseNumber
from StringReader import ReadResult


def keepNumericSymbolsOnly(string, exceptions=[]):
    return "".join([char if (char.isdigit() or char in exceptions) else "" for char in string])

def cleanDate(string):
    return keepNumericSymbolsOnly(string, ["/"])

cards = ["VISA", "MASTERCARD", "AMEX-MM", "CABAL"]

def cleanCard(string):
    results = []
    for card in cards:
        match = fuzz.ratio(card, string)
        results.append((match, card))
    # Sort by acc
    results = sorted(results, key=lambda tup: -tup[0])
    if len(string) > 10 and results[0][0] < 60:
        return cards[1] # big length, not a very good guess, probably mastercard

    return results[0][1]

def cleanLote(string):
    s = keepNumericSymbolsOnly(string)
    replaced = "".join(["0" if (c == "8" or c == "6" or c == "9") else c for c in string])
    if replaced == "004":
        return "004"
    elif replaced == "000004":
        return "000004"
    return s

def cleanCuotas(string):
    if(string == "T"):
        return "1"
    return keepNumericSymbolsOnly(string)

def doNothingCleaner(string):
    return string

def cleanImporte(string):
    result = parseNumber(string)
    if result is None:
        # find first word after imp total that has digits and keep the digits, adding the comma if found
        digits = "".join([char if char.isdigit() else "" for char in string])
        secondToLastChar = ""
        thirdToLastChar = ""
        if len(digits) >= 2:
            if len(string) > 1:
                secondToLastChar = string[-2:-1][0]
            if len(string) > 2:
                thirdToLastChar = string[-3:-2][0]
            if secondToLastChar == "," or secondToLastChar == ".":
                digits = digits[0:-1] + "." + digits[-1:]
            elif thirdToLastChar == "," or thirdToLastChar == ".":
                digits = digits[0:-2] + "." + digits[-2:]
            return str(parseNumber(digits))
        result = ""
    return str(result)

# create a named tuple which we can use to create locations of the
# input document which we wish to OCR
OCRLocation = namedtuple("OCRLocation", ["id", "bbox", "cleanup"])
# define the locations of each area of the document we wish to OCR
OCR_LOCATIONS = [
    OCRLocation("date", (80, 111, 120, 43),cleanDate),
    OCRLocation("card", (200, 111, 120, 43), cleanCard),
    # OCRLocation("hour", (320, 111, 120, 43), doNothingCleaner),
    OCRLocation("importe", (230, 375, 150, 40), cleanImporte),
    OCRLocation("cuotas", (150, 410, 25, 25), cleanCuotas),
    OCRLocation("lote", (162, 287, 70, 20), cleanLote),
]





def align_images(image, template, maxFeatures=500, keepPercent=0.2,
                 debug=False):
    # convert both the input image and template to grayscale
    imageGray = cv2.cvtColor(image.copy(), cv2.COLOR_BGR2GRAY)
    templateGray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    # use ORB to detect keypoints and extract (binary) local
    # invariant features
    orb = cv2.ORB_create(maxFeatures)
    (kpsA, descsA) = orb.detectAndCompute(imageGray, None)
    (kpsB, descsB) = orb.detectAndCompute(templateGray, None)

    # match the features
    method = cv2.DESCRIPTOR_MATCHER_BRUTEFORCE_HAMMING
    matcher = cv2.DescriptorMatcher_create(method)
    matches = matcher.match(descsA, descsB, None)

    # sort the matches by their distance (the smaller the distance,
    # the "more similar" the features are)
    matches = sorted(matches, key=lambda x: x.distance)

    # keep only the top matches
    keep = int(len(matches) * keepPercent)
    matches = matches[:keep]

    # check to see if we should visualize the matched keypoints
    if debug:
        matchedVis = cv2.drawMatches(imageGray, kpsA, template, kpsB,
                                     matches, None)
        matchedVis = imutils.resize(matchedVis, width=1000)
        cv2.imshow("Matched Keypoints", matchedVis)
        cv2.waitKey(0)

    # allocate memory for the keypoints (x,y-coordinates) from the
    # top matches -- we'll use these coordinates to compute our
    # homography matrix
    ptsA = np.zeros((len(matches), 2), dtype="float")
    ptsB = np.zeros((len(matches), 2), dtype="float")

    # loop over the top matches
    for (i, m) in enumerate(matches):
        # indicate that the two keypoints in the respective images
        # map to each other
        ptsA[i] = kpsA[m.queryIdx].pt
        ptsB[i] = kpsB[m.trainIdx].pt

    # compute the homography matrix between the two sets of matched
    # points
    (H, mask) = cv2.findHomography(ptsA, ptsB, method=cv2.RANSAC)

    # use the homography matrix to align the images
    (h, w) = template.shape[:2]
    aligned = cv2.warpPerspective(imageGray, H, (w, h))
    aligned_color = cv2.warpPerspective(image, H, (w, h))

    # return the aligned image
    return aligned, aligned_color


def cleanup_text(text):
    # strip out non-ASCII text so we can draw the text on the image
    # using OpenCV
    return "".join([c if ord(c) < 128 else "" for c in text]).strip()

def crop_img(image, box):
    (x,y,w,h) = box
    crop_img = image[y:y + h, x:x + w]
    return crop_img


class AlignmentExtractor:
    def __init__(self, image, template):
        self.image = image
        self.template = template

    def extract(self, debug = False):
        aligned, color = align_images(self.image, self.template, debug=debug)

        parsingResults = []
        # loop over the locations of the document we are going to OCR
        for loc in OCR_LOCATIONS:
            # extract the OCR ROI from the aligned image
            (x, y, w, h) = loc.bbox
            roi = color[y:y + h, x:x + w]
            # OCR the ROI using Tesseract
            custom_config = r'--oem 3 --psm 6'
            # ret, roi = cv2.threshold(roi, 200, 255, cv2.THRESH_BINARY)
            cv2.imshow("ROI", roi)
            cv2.waitKey()
            text = pytesseract.image_to_string(roi, lang="custom", config=custom_config)
            line = loc.cleanup(text.upper())
            parsingResults.append((loc, line))

        # initialize a dictionary to store our final OCR results
        results = {}
        # loop over the results of parsing the document
        for (loc, line) in parsingResults:
            # grab any existing OCR result for the current ID of the document
            r = results.get(loc.id, None)
            # if the result is None, initialize it using the text and location
            # namedtuple (converting it to a dictionary as namedtuples are not
            # hashable)
            if r is None:
                results[loc.id] = (line, loc._asdict())
            # otherwise, there exists an OCR result for the current area of the
            # document, so we should append our existing line
            else:
                # unpack the existing OCR result and append the line to the
                # existing text
                (existingText, loc) = r
                text = "{}\n{}".format(existingText, line)
                # update our results dictionary
                results[loc["id"]] = (text, loc)

        # loop over the results
        for (locID, result) in results.items():
            # unpack the result tuple
            (text, loc) = result
            # display the OCR result to our terminal
            if debug:
                print("{}: {}".format(loc["id"], text))
                print("=" * len(loc["id"]))

            # extract the bounding box coordinates of the OCR location and
            # then strip out non-ASCII text so we can draw the text on the
            # output image using OpenCV
            (x, y, w, h) = loc["bbox"]
            # draw a bounding box around the text
            cv2.rectangle(color, (x, y), (x + w, y + h), (0, 255, 0), 1)
            # loop over all lines in the text
            cv2.putText(color, text, (x, y),cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

        # show the input and output images, resizing it such that they fit
        # on our screen
        if debug:
            cv2.imshow("Input", imutils.resize(self.image))
            cv2.imshow("Output", imutils.resize(color))
            cv2.waitKey(0)

        return ReadResult(results["date"][0], results["card"][0], results["lote"][0], results["cuotas"][0], results["importe"][0])
    #
    # class ReadResult:
    #     def __init__(self, date, card, lote, cuotas, importe):
