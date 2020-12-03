import re

from fuzzywuzzy import process, fuzz
import regex
from NumberParser import parseNumber


class StringReader:


    def __init__(self, string):
        self.string = string.upper()
        self.lines = self.string.splitlines()
        self.words = self.string.split()
        self.cards = ["VISA", "MASTERCARD", "AMEX-MM", "CABAL"]
        self.importe_regex = r'(\d{1,3}(,|\.)?(\d{3})(,|\.)?\d{1,2})' # 1.000,00 1039,22 39.2 334,2
        self.date_regex = r'\d{1,2}\/\d{1,2}\/\d{2,4}' # 1/1/20 10/12/2020 01/2/2020 1/02/2020
        self.dot_comma_translate_dict = {
            ",":".",
            ".":","
        }

    def getCreditCard(self):
        results = []
        if len(self.lines) > 10:
            max = 10
        else:
            max = len(self.lines)
        first_lines = self.lines[0:max]
        first_words = "".join(first_lines).split()

        for card in self.cards:
            best_match = process.extractOne(card, first_words, scorer=fuzz.ratio)
            results.append((best_match[0], best_match[1], card))
        # Sort by acc
        results = sorted(results, key=lambda tup: -tup[1])
        return results[0][2]

    def getDate(self):
        return self.getLongestSequenceSize(self.date_regex, self.string)

    def getImport(self):
        imp_total = self.extractOneOrEmpty("IMP.TOTAL:", self.words)
        imp_total_index = self.words.index(imp_total)
        line = self.extractOneOrEmpty(imp_total, self.lines)
        str_number = self.getLongestSequenceSize(self.importe_regex, line)
        str_number_patched = "".join([i.translate(self.dot_comma_translate_dict) for i in str_number])
        result = parseNumber(str_number_patched)
        if result is None:
            # lets try to extract with a näive method
            sublist = self.words[imp_total_index + 1:imp_total_index + 3]
            for word in sublist:
                if self.hasNumbers(word):
                    # find first word after imp total that has digits and keep the digits, adding the comma if found
                    digits = "".join([char if char.isdigit() else "" for char in word])
                    secondToLastChar = ""
                    thirdToLastChar = ""
                    if len(digits) >= 2:
                        if len(word) > 1:
                            secondToLastChar = word[-2:-1][0]
                        if len(word) > 2:
                            thirdToLastChar = word[-3:-2][0]
                        if secondToLastChar == "," or secondToLastChar == ".":
                            digits = digits[0:-1] + "." + digits[-1:]
                        elif thirdToLastChar == "," or thirdToLastChar == ".":
                            digits = digits[0:-2] + "." + digits[-2:]
                        return parseNumber(digits)
            result = ""
        return result

    def hasNumbers(self, inputString):
        return any(char.isdigit() for char in inputString)

    def getLote(self):
        lote_str = self.extractOneOrEmpty("NRO.LOTE:", self.words, scorer=fuzz.ratio)
        index_cuotas = self.words.index(lote_str)
        sublist = self.words[index_cuotas:index_cuotas + 6]
        return self.findFirstNumber(sublist, maxLen=6)

    def getCuotas(self):
        cuotas_str = self.extractOneOrEmpty("CUOTAS:", self.words, scorer=fuzz.ratio)
        index_cuotas = self.words.index(cuotas_str)
        sublist = self.words[index_cuotas + 1:index_cuotas + 5]
        return self.findFirstNumber(sublist, maxLen=2)

    def findFirstNumber(self, list, maxLen=1):
        regex = r'\d{1,' + str(maxLen) + '}'
        return self.findFirstByRegex(regex, " ".join(list))

    def findFirstByRegex(self, regex, string):
        list_result = re.findall(regex, string)
        if (len(list_result) >= 1):
            return list_result[0]
        else:
            return ""

    def getLongestSequenceSize(self, regex, polymer_str):
        list_result = sorted(re.findall(regex, polymer_str), key=len, reverse=True)
        if(len(list_result) >= 1):
            return list_result[0][0]
        else:
            return ""

    def extractOneOrEmpty(self, match, words, scorer=fuzz.WRatio):
        list_result = process.extractOne(match,words,scorer=scorer)
        if(len(list_result) >= 1):
            return list_result[0]
        else:
            return ""

    def parse(self):
        return ReadResult(self.getDate(), self.getCreditCard(), self.getLote(), self.getCuotas(), self.getImport())

def headers():
    return ",".join(headers_list())

def headers_list():
    return ["Fecha", "Tarjeta", "Lote", "Cuotas", "Importe"]

class ReadResult:

    def __init__(self, date, card, lote, cuotas, importe):
        self.date = str(date)
        self.card = str(card)
        self.lote = str(lote)
        self.cuotas = str(cuotas)
        self.importe = str(importe)

    def asList(self):
        return [self.date, self.card, self.lote, self.cuotas, self.importe]
    def csv(self):
        return ",".join([str(i) for i in self.asList()])

