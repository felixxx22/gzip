gzip — simple DEFLATE compressor
=============================================

Overview
--------
This small project implements parts of the DEFLATE (gzip-style) compressor based on RFC 1951 and RFC 1952

Requirements
------------
- Python 3.8+ (tested with modern CPython)
- Optional: a virtual environment for isolation

Quick start
-----------
Compress a single file with the simple CLI:

```powershell
python gzip.py input/test.txt
```

The script writes raw DEFLATE bytes to a sibling file with the `.bin` suffix (for example `input/test.txt.bin`).

To do 
---------
* Fix Dynamic Huffman implementation 
