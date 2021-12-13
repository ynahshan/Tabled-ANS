import numpy as np


# Return the Index of the First Non-Zero Bit.
def first1Index(val):
    counter = 0
    while val > 1:
        counter += 1
        val = val >> 1
    return counter

# Output NbBits to a BitStream
def outputNbBits(state, nbBits):
    mask = (1 << nbBits) -1
    little = state & mask
    if nbBits >0:
        string = "{:b}".format(little)
    else:
        return ""
    while len(string) < nbBits:
        string = "0" + string
    return string

# Convert Bits from Bitstream to the new State.
def bitsToState(bitStream, nbBits):
    if nbBits == 0 or len(bitStream) == 0:
        return 0, bitStream
    if nbBits == len(bitStream):
        rest = int(bitStream, 2)
        return rest, ""

    bits = bitStream[-nbBits:]
    rest = int(bits, 2)
    remaining = bitStream[:-nbBits]
    return rest, remaining

# Return a Symbol + New State + Bitstream from the bitStream and State.
def decodeSymbol(state, bitStream, stateT):
    symbol = stateT[state]['symbol']
    nbBits = stateT[state]['nbBits']
    rest, bitStream = bitsToState(bitStream, nbBits)
    state = stateT[state]['newX'] + rest
    return symbol, state, bitStream


class TabledANS:
    def __init__(self, symbol_occurrences, tableLog=5):
        self.tableLog = tableLog
        self.tableSize = 1 << tableLog

        if self.tableSize < len(symbol_occurrences):
            raise RuntimeError("Table size {} less than number of symbols {}".format(self.tableSize, len(symbol_occurrences)))

        freq_sum = np.sum(list(symbol_occurrences.values()))
        if freq_sum != self.tableSize:
            # Normalize frequencies table
            freq_norm = [np.floor(self.tableSize * symbol_occurrences[sym] / freq_sum) for sym in symbol_occurrences.keys()]
            for i in range(len(freq_norm)):
                if freq_norm[i] == 0:
                    freq_norm[i] += 1

            freq_sum_norm = np.sum(freq_norm)
            reminder = self.tableSize - freq_sum_norm
            for i in range(len(freq_norm)):
                if reminder == 0:
                    break
                elif reminder > 0:
                    freq_norm[i] += 1
                    reminder -= 1
                elif freq_norm[i] > 1:
                    freq_norm[i] -= 1
                    reminder += 1

            symbol_occurrences = dict([(k, int(freq_norm[i])) for i, k in enumerate(symbol_occurrences.keys())])
        
        ####
        # Define the Initial Positions of States in StateList.
        ####
        symbol_list = [symbol for symbol,occcurences in symbol_occurrences.items()]
        cumulative = [0 for _ in range(len(symbol_list)+2)]
        for u in range(1, len(symbol_occurrences.items())+ 1):
            cumulative[u] = cumulative[u - 1] + list(symbol_occurrences.items())[u-1][1]
        cumulative[-1] = self.tableSize +1
        
        #####
        # Spread Symbols to Create the States Table
        #####
        highThresh = self.tableSize - 1
        stateTable = [0 for _ in range(self.tableSize)]
        tableMask = self.tableSize - 1
        step = ((self.tableSize >> 1) + (self.tableSize >> 3) + 3)
        pos = 0
        for symbol, occurrences in symbol_occurrences.items():
            for i in range(occurrences):
                stateTable[pos] = symbol
                pos = (pos + step) & tableMask
                # while pos > highThresh:
                #     position = (pos + step) & tableMask
        # assert(pos == 0)
        # print(stateTable)
        
        #####
        # Build Coding Table from State Table
        #####
        outputBits = [0 for _ in range(self.tableSize)]
        self.codingTable = [0 for _ in range(self.tableSize)]
        cumulative_cp = cumulative.copy()
        for i in range(self.tableSize):
            s = stateTable[i]
            index = symbol_list.index(s)
            self.codingTable[cumulative_cp[index]] = self.tableSize + i
            cumulative_cp[index] += 1
            outputBits[i] = self.tableLog - first1Index(self.tableSize + i)
            
        #####
        # Create the Symbol Transformation Table
        #####
        total = 0
        self.symbolTT = {}
        for symbol, occurrences in symbol_occurrences.items():
            self.symbolTT[symbol] = {}
            if occurrences == 1:
                self.symbolTT[symbol]['deltaNbBits'] = (self.tableLog << 16) - (1 << self.tableLog)
                self.symbolTT[symbol]['deltaFindState'] = total - 1
            elif occurrences > 0:
                maxBitsOut = self.tableLog - first1Index(occurrences - 1)
                minStatePlus = occurrences << maxBitsOut
                self.symbolTT[symbol]['deltaNbBits'] = (maxBitsOut << 16) - minStatePlus
                self.symbolTT[symbol]['deltaFindState'] = total - occurrences
            total += occurrences
        # print(self.symbolTT)
        
        #####
        # Generate a Decoding Table
        #####
        self.decodeTable = [{} for _ in range(self.tableSize)]
        nextt = list(symbol_occurrences.items())
        for i in range(self.tableSize):
            t = {}
            t['symbol'] = stateTable[i]
            index = symbol_list.index(t['symbol'])
            x = nextt[index][1]
            nextt[index] = (nextt[index][0], nextt[index][1] + 1)
            t['nbBits'] = self.tableLog - first1Index(x)
            t['newX'] = (x << t['nbBits']) - self.tableSize
            self.decodeTable[i] = t
        
    @staticmethod
    def from_frequencies(symbol_occurrences, tableLog=None):
        if tableLog is None:
            tableLog = max(int(np.ceil(np.log2(len(symbol_occurrences)))), 5)

        return TabledANS(symbol_occurrences, tableLog)

    @staticmethod
    def from_data(data, tableLog=None):
        v, c = np.unique(data, return_counts=True)
        symbol_occurrences = dict([(v_, c_) for v_, c_ in zip(v, c)])

        return TabledANS.from_frequencies(symbol_occurrences, tableLog)

    # Encode a Symbol Using tANS, giving the current state, the symbol, and the bitstream and STT
    def encodeSymbol(self, symbol, state, bitStream, symbolTT):
        symbolTT = symbolTT[symbol]
        nbBitsOut = (state + symbolTT['deltaNbBits']) >> 16
        bitStream += outputNbBits(state,nbBitsOut)
        state = self.codingTable[(state >> nbBitsOut) + symbolTT['deltaFindState']]
        return state, bitStream

    #####
    # Functions to Encode and Decode Streams of Data.
    #####
    def encodeData(self, inpu):
        bitStream = ""
        state, bitStream = self.encodeSymbol(inpu[0], 0, "", self.symbolTT)
        bitStream = ""
        for char in inpu:
            state, bitStream = self.encodeSymbol(char, state, bitStream, self.symbolTT)
        bitStream += outputNbBits(state - self.tableSize, self.tableLog) #Includes Current Bit
        return bitStream

    def decodeData(self, bitStream):
        output = []
        state, bitStream = bitsToState(bitStream, self.tableLog)
        while len(bitStream) > 0:
            symbol, state, bitStream = decodeSymbol(state, bitStream, self.decodeTable)
            output = [symbol] + output

        # cover a corner case when last symbols encoded with zero bits
        while self.decodeTable[state]['nbBits'] == 0 and self.decodeTable[state]['newX'] != 0:
            symbol, state, bitStream = decodeSymbol(state, bitStream, self.decodeTable)
            output = [symbol] + output

        return output
