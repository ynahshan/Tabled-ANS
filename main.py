from tabledans import TabledANS

if __name__ == "__main__":
    inp = [0, 1, 1, 1, 0]
    freq = {0: 10, 1: 5, 3: 5, 4: 6}
    # inp = [0, 1, 1, 1, 0]
    # freq = {0: 27, 1: 5}
    # inp = "022222220111100022222"
    # freq = {"0": 10, "1": 11, "2": 11}
    # inp = "01110011111"
    # freq = {"0": 3, "1": 2}

    tans = TabledANS.from_frequencies(freq)
    bitStream = tans.encodeData(inp)
    output = tans.decodeData(bitStream)
    print(inp)
    print(output)
    # print("".join(output))
