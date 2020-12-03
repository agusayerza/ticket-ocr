import re as rgex
from NumberParser import parseNumber
from StringReader import ReadResult


def basicReconciler(a, p):
    if a == p:
        return a
    elif a == "" and p != "":
        return p
    elif p == "" and a != "":
        return a
    return None

def preferAlignReconciler(a, p):
    return a

def preferParseReconciler(a, p):
    return p

def preferLongerReconciler(a, p):
    if len(a) > len(p):
        return a
    elif len(p) > len(a):
        return p
    return None

def importRegexMatchReconciler(a, p):
    pattern = rgex.compile('(\d{1,3}([,.])?(\d{3})([,.])?\d{1,2})')
    aMatches = pattern.match(a)
    pMatches = pattern.match(p)
    if aMatches and not pMatches:
        return a
    if pMatches and not aMatches:
        return p
    if aMatches and pMatches:
        if len(a) > 10 and len(p) < 10:
            return p
    return None

def preferLowerNumberReconciler(a, p):
    a = parseNumber(a)
    p = parseNumber(p)
    if p is not None and a is not None:
        if p > a:
            return str(a)
        elif a < p:
            return str(p)
        elif a == p:
            return str(a)
    return None

def listReconciler(a, p, list):
    for rec in list:
        result = rec(a, p)
        if result is not None:
            return result
    return ""

def importeReconciler(a, p):
    return listReconciler(a, p, [basicReconciler, preferAlignReconciler])

def dateReconciler(a, p):
    return listReconciler(a, p, [basicReconciler, preferAlignReconciler])

def cardReconciler(a, p):
    return listReconciler(a, p, [basicReconciler, preferAlignReconciler])

def loteReconciler(a, p):
    return listReconciler(a, p, [basicReconciler, preferLongerReconciler, preferAlignReconciler])

def cuotasReconciler(a, p):
    return listReconciler(a, p, [basicReconciler, preferLowerNumberReconciler, preferParseReconciler])


class ResultDiffer:
    def __init__(self, align, parse):
        self.align = align
        self.parse = parse

    def reconcile(self, debug = False):
        # date, card, importe, lote, cuotas
        dateA = self.align.date
        dateP = self.parse.date
        date = dateReconciler(dateA, dateP)

        cardA = self.align.card
        cardP = self.parse.card
        card = cardReconciler(cardA, cardP)

        importA = self.align.importe
        importP = self.parse.importe
        importe = importeReconciler(importA, importP)

        loteA = self.align.lote
        loteP = self.parse.lote
        lote = loteReconciler(loteA, loteP)

        cuotasA = self.align.cuotas
        cuotasP = self.parse.cuotas
        cuotas = cuotasReconciler(cuotasA, cuotasP)

        if debug:
            print("Align:")
            print(self.align.csv())
            print("Parse:")
            print(self.parse.csv())
            print("Result:")
            print(self.align.headers())
            print(ReadResult(date, card, lote, cuotas, importe).csv())
            print("\n")

        return ReadResult(date, card, lote, cuotas, importe)
