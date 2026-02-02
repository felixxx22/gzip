'''This script takes a file and compresses it using the delate algorithm as per rfc1951'''
from hash.SimpleChain import SimpleChain
from huffman.lengthLimitedCannonicalHuffman import lengthLimitedCannonicalHuffman

import argparse
import zlib

class BitWriter: 
    def __init__(self):
        self.buf = bytearray()
        self.bitbuf = 0 
        self.bitcount = 0 

    def emit_bits(self, value, nbits):
        while nbits: 
            self.bitbuf |= (value & 1) << self.bitcount
            self.bitcount += 1
            value >>= 1
            nbits -= 1

            if self.bitcount == 8:
                self.buf.append(self.bitbuf)
                self.bitbuf = 0 
                self.bitcount = 0

    def flush(self):
        if self.bitcount: 
            self.buf.append(self.bitbuf)
            self.bitbuf = 0 
            self.bitcount = 0

class Compressor:
    def __init__(self, fileName):
        self.fileName = fileName
        self.buffer = bytearray() 
        self.start = 0
        self.table = SimpleChain()

        self.MAX_DISTANCE = 32768 #32K 
        self.MAX_LENGTH = 258

    def sliding_window(self, path, chunk_size=64*1024):
        with open(path, "rb") as f:
            while chunk := f.read(chunk_size): 
                self.buffer.extend(chunk)
                self.buffer.append(0) 
                self.buffer.append(0) 
                self.view = memoryview(self.buffer) 

                while self.start + 3 <= len(self.view):
                    yield (self.start, self.view[self.start:self.start+3])
                    self.start+=1 

                if self.start >= 64*1024:
                    self.buffer = self.buffer[self.start:] 
                    self.start = 0

    def find_match(self, currentIndex, matchIndex):
        if currentIndex - matchIndex > self.MAX_DISTANCE: return (-1, 0) # TODO

        matchLength = 0

        if matchIndex >= currentIndex: return (-1, 0) # TODO
        try: 
            while 0 < currentIndex+matchLength < len(self.view) and self.view[currentIndex+matchLength] == self.view[matchIndex+matchLength]:
                matchLength+=1 

        except IndexError:
            print(f"comparing {currentIndex+matchLength} vs {matchIndex+matchLength}")

        if matchLength > self.MAX_LENGTH: matchLength = self.MAX_LENGTH

        if matchLength < 3: return (-1, 0)

        self.start += (matchLength-1)
        return (matchLength, currentIndex - matchIndex)
    
    def __dict_add(self, dict, value): 
        if value in dict: 
            dict[value] += 1
        else: 
            dict[value] = 1
    
    def dynamicHuffman(self): 
        BFINAL = 1
        BTYPE = 2

        writer = BitWriter()
        writer.emit_bits(BFINAL, 1)
        writer.emit_bits(BTYPE, 2)

        encoding  = []
        literal_length_freq = {}
        distance_freq = {}

        for index, window in self.sliding_window(self.fileName):
            if matchIndex := self.table.insert(window, index):
                potentialMatches = self.table.table[matchIndex]
                match = self.find_match(index, potentialMatches[-2])
                if match[0] == -1:
                    encoding.append(window[0])
                    self.__dict_add(literal_length_freq, window[0])
                else:
                    len_code, len_extra_bits, len_extra = self.__len_map(match[0])
                    encoding.append(len_code)
                    encoding.append(len_extra)
                    encoding.append(len_extra_bits)
                    self.__dict_add(literal_length_freq, len_code)

                    dist_code, dist_extra_bits, dist_extra = self.__dist_map(match[1])
                    encoding.append(dist_code)
                    encoding.append(dist_extra)
                    encoding.append(dist_extra_bits)
                    self.__dict_add(distance_freq, dist_code)

            else: 
                encoding.append(window[0])
                self.__dict_add(literal_length_freq, window[0])

        encoding.append(256)
        self.__dict_add(literal_length_freq, 256)

        literal_length_huffman, literal_length_bit_length = lengthLimitedCannonicalHuffman(literal_length_freq)
        distance_huffman, distance_bit_length = lengthLimitedCannonicalHuffman(distance_freq)

        print(distance_freq)
        print(distance_bit_length)

        ## add huffman trees 
        literal_code_length_seq = []
        for i in range(0, 285+1):
            if i in literal_length_bit_length:
                literal_code_length_seq.append(literal_length_bit_length[i])

            else: 
                literal_code_length_seq.append(0)

        distance_run_length_seq = []
        for i in range(0, 31+1):
            if i in distance_bit_length: 
                distance_run_length_seq.append(distance_bit_length[i])

            else: 
                distance_run_length_seq.append(0)    

        run_length_encoding_seq = self.__run_length_encode(literal_code_length_seq)
        distance_run_length_encoding_seq = self.__run_length_encode(distance_run_length_seq)

        run_length_freq = {}

        run_lengths = run_length_encoding_seq + distance_run_length_encoding_seq

        count = 0 
        while count < len(run_lengths):
            code = run_lengths[count] 
            if run_lengths[count] <= 15:
                self.__dict_add(run_length_freq, code)
                count+= 1

            elif 16 <= run_lengths[count] <= 18: 
                self.__dict_add(run_length_freq, code)
                count+=2 

        code_length_huffman, code_length_bit_length = lengthLimitedCannonicalHuffman(run_length_freq)

        # proproessing done, emitting header
        # fixed at maximum 
        self.__emit_extra(writer, 286-257, 5) # HLIT - 257 
        self.__emit_extra(writer, 32-1, 5) # HDIST - 1
        self.__emit_extra(writer, 19-4, 4) # HCLEN - 4

        # (HCLEN + 4) x 3 bits 
        for code in [16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15]:
            if code in code_length_huffman:
                self.__emit_huffman(writer, code_length_bit_length[code], 3)
            else:
                self.__emit_extra(writer, 0, 3)

        # HLIT + 257 code lengths for literal/length alphabet
        count = 0
        while count < len(run_length_encoding_seq):
            code = run_length_encoding_seq[count]
            if 0 <= code <= 15: 
                self.__emit_huffman(writer, code_length_huffman[code], code_length_bit_length[code])
                count+=1
            elif code == 16:
                self.__emit_huffman(writer, code_length_huffman[code], code_length_bit_length[code])
                extra = run_length_encoding_seq[count+1]
                self.__emit_extra(writer, extra, 2)
                count += 2

            elif code == 17:
                self.__emit_huffman(writer, code_length_huffman[code], code_length_bit_length[code])
                extra = run_length_encoding_seq[count+1]
                self.__emit_extra(writer, extra, 3)
                count += 2

            elif code == 18:
                self.__emit_huffman(writer, code_length_huffman[code], code_length_bit_length[code])
                extra = run_length_encoding_seq[count+1]
                self.__emit_extra(writer, extra, 7)
                count += 2

        # HDIST + 1 code lengths for distance alphabet
        count = 0
        while count < len(distance_run_length_encoding_seq):
            code = distance_run_length_encoding_seq[count]
            if 0 <= code <= 15: 
                self.__emit_huffman(writer, code_length_huffman[code], code_length_bit_length[code])
                count+=1
            elif code == 16:
                self.__emit_huffman(writer, code_length_huffman[code], code_length_bit_length[code])
                extra = distance_run_length_encoding_seq[count+1]
                self.__emit_extra(writer, extra, 2)
                count += 2

            elif code == 17:
                self.__emit_huffman(writer, code_length_huffman[code], code_length_bit_length[code])
                extra = distance_run_length_encoding_seq[count+1]
                self.__emit_extra(writer, extra, 3)
                count += 2

            elif code == 18:
                self.__emit_huffman(writer, code_length_huffman[code], code_length_bit_length[code])
                extra = distance_run_length_encoding_seq[count+1]
                self.__emit_extra(writer, extra, 7)
                count += 2

        ## add encoding blocks
        count = 0
        while count < len(encoding):
            code = encoding[count]
            self.__emit_huffman(writer, literal_length_huffman[code], literal_length_bit_length[code])

            count+=1 
            if 257 <= code <= 285:
                code = encoding[count]
                if code != 0: 
                    self.__emit_extra(writer, code, encoding[count+1])

                count+=2
                code = encoding[count]
                self.__emit_huffman(writer, distance_huffman[code], distance_bit_length[code])

                count+= 1
                code = encoding[count]
                if code != 0: 
                    self.__emit_extra(writer, code, encoding[count+1])
                count+=2

        writer.flush()
        return writer.buf

    def process(self): 
        BFINAL = 1
        BYTPE = 1 # Fixed Huffman 01

        writer = BitWriter()
        writer.emit_bits(BFINAL, 1)
        writer.emit_bits(BYTPE, 2)

        for index, window in self.sliding_window(self.fileName):
            if matchIndex := self.table.insert(window, index):
                potentialMatches = self.table.table[matchIndex]
                match = self.find_match(index, potentialMatches[-2])
                if match[0] == -1:
                    value, length = self.__fixed_huffman(window[0])
                    self.__emit_huffman(writer, value, length)
                else:
                    len_code, len_extra_bits, len_extra = self.__len_map(match[0])
                    value, length = self.__fixed_huffman(len_code)
                    self.__emit_huffman(writer, value, length)

                    self.__emit_extra(writer, len_extra, len_extra_bits)


                    dist_code, dist_extra_bits, dist_extra = self.__dist_map(match[1])
                    self.__emit_huffman(writer, dist_code, 5)

                    self.__emit_extra(writer, dist_extra, dist_extra_bits)

            else: 
                value, length = self.__fixed_huffman(window[0])
                self.__emit_huffman(writer, value, length)


        value, length = self.__fixed_huffman(256)
        self.__emit_huffman(writer, value, length)

        writer.flush()
        return writer.buf

    def __fixed_huffman(self, value) -> str: 
        if 0 <= value <= 143:
            return 48+value, 8

        elif value <= 255:
            return 400+value-144, 9

        elif value <= 279: 
            return 0+value-256, 7
        
        elif value <= 287:
            return 192+value-280, 8
        
        else:
            raise(ValueError)
        
    def __run_length_encode(self, sequence):
        if not sequence: return []
        
        run_length_encoding = []
        left = 0 

        count = 0 
        
        # Iterate up to len(sequence) + 1 to force the last group to process
        for right in range(1, len(sequence) + 1):
            if right == len(sequence) or sequence[right] != sequence[left]:
                length = right - left
                run_length_encoding.append((sequence[left], length))
                count+= length

                left = right 

        print(run_length_encoding)
        
        res = []
        for code, length in run_length_encoding:
            res.extend(self.__code_length_map(code, length))
        
        return res
        
    def __code_length_map(self, code, length):
        res = []
        if code == 0:
            while length > 0:
                if length <= 2:
                    for _ in range(length):
                        res.append(code)

                    return res
                
                if 3 <= length <= 10:
                    res.append(17)
                    res.append(length-3)
                    return res
                
                if 11 <= length <= 138: 
                    res.append(18)
                    res.append(length-11)
                    return res

                if length > 138: 
                    res.append(18)
                    res.append(138-11)
                    length -= 138

            return res

        else: 
            while length > 3: 
                res.append(code)
                length-=1

                if 3 <= length <= 6: 
                    res.append(16)
                    res.append(length-3)
                    return res

                if length > 6:
                    res.append(16)
                    res.append(6-3)
                    length-=6

            if length <= 3: 
                for _ in range(length):
                    res.append(code)

            return res        

    def __dist_map(self, distance):
        BASE_DISTANCE = [
            1, 2, 3, 4, 
            5, 7, 
            9, 13,
            17, 25, 
            33, 49, 
            65, 97, 
            129, 193, 
            257, 385, 
            513, 769, 
            1025, 1537, 
            2049, 3073, 
            4097, 6145,
            8193, 12289, 
            16385, 24577 
        ]

        EXTRA_BITS = [
            0, 0, 0, 0,
            1, 1,
            2, 2,
            3, 3,
            4, 4,
            5, 5,
            6, 6,
            7, 7,
            8, 8,
            9, 9,
            10, 10,
            11, 11,
            12, 12,
            13, 13
        ]

        for i in range(len(BASE_DISTANCE) - 1):
            if BASE_DISTANCE[i] <= distance < BASE_DISTANCE[i+1]:
                code = i
                extra = distance - BASE_DISTANCE[i]

                return (code, EXTRA_BITS[i], extra)
            
        else:
            code = i+1
            extra = distance - BASE_DISTANCE[i+1]

            return (code, EXTRA_BITS[i+1], extra)
        
    def __len_map(self, length):
        BASE_LENGTH = [
            3, 4, 5, 6, 7, 8, 9, 10, 
            11, 13, 15, 17, 
            19, 23, 27, 31, 
            35, 43, 51, 59, 
            67, 83, 99, 115, 
            131, 163, 195, 227, 
            258
        ]
        EXTRA_BITS = [
            0, 0, 0, 0, 0, 0, 0, 0, 
            1, 1, 1, 1,
            2, 2, 2, 2,
            3, 3, 3, 3,
            4, 4, 4, 4,
            5, 5, 5, 5,
            0
        ]
        if length == 258: return (285, 0, 0)

        for i in range(len(BASE_LENGTH) - 1):
            if BASE_LENGTH[i] <= length < BASE_LENGTH[i+1]:
                code = 257+i
                extra = length - BASE_LENGTH[i]

                return (code, EXTRA_BITS[i], extra)
                    
    def __emit_huffman(self, writer, code, length): 
        writer.emit_bits(self.__reverse_bits(code, length), length)

    def __emit_extra(self, writer, value, bits):
        writer.emit_bits(value, bits)

    def __reverse_bits(self, value, n_bits):
        rev = 0
        for i in range(n_bits):
            rev |= ((value >> i) & 1) << (n_bits - 1 - i)
        return rev
    
if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Simple CLI: require exactly one argument (input file)
    if len(sys.argv) != 2:
        print("Usage: python gzip.py <input-file>\nExample: python gzip.py input/test.txt")
        sys.exit(2)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: input file not found: {input_path}\nHint: provide a valid file path, e.g., input/test.txt")
        sys.exit(1)

    compressor = Compressor(str(input_path))
    try:
        block = compressor.process()
    except Exception as e:
        print("Compression failed:", e)
        sys.exit(1)

    # write raw DEFLATE bytes to '<name><orig-suffix>.deflate' (e.g. test.txt.deflate)
    out_path = input_path.with_suffix(input_path.suffix + ".bin")
    with open(out_path, "wb") as f:
        f.write(block)

    print(f"Wrote compressed output to {out_path}")
