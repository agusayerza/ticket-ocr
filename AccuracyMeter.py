# dd/mm/yy   vvvvvv    hh:mm:ss
#     (00) aprobada
# copie la tarjeta debajo

class AccuracyMeter:
    def __init__(self, string):
        self.__string = string
        self.__measured = False


    def best_Acc(self):
        if not self.__measured:
            self.measure()
        return self.__bestAcc

    def measure(self):
        bestAccFirstLine = self.__measureFirstLine()
        bestAccLastLine = self.__measureLastLine()
        best = max([bestAccFirstLine, bestAccLastLine])
        self.__bestAcc = best
        self.__measured = True

    def __measureFirstLine(self):
        return 9.9

    def __measureLastLine(self):
        return 3