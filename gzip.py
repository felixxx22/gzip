'''This script takes a file and compresses it using the delate algorithm as per rfc1951'''
    
def sliding_window(path, chunk_size=64*1024):
    buffer = bytearray() 
    start = 0 

    with open(path, "rb") as f:
        while chunk := f.read(chunk_size): 
            buffer.extend(chunk) 
            view = memoryview(buffer) 

            while start + 3 <= len(view):
                yield view[start:start+3] 
                start+=1 

            if start > 1024: 
                buffer = buffer[start:] 
                start = 0

if __name__ == "__main__":
    # Add command line interfacing 

    for window in sliding_window("input.txt"):
        b0, b1, b2 = window[0], window[1], window[2]    
        print(chr(b0)) 
