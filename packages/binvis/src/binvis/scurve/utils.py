"""
    A lot of these functions are written for clarity rather than speed. We'll
    fix that in time.

### `bitwise` operators in Python

`https://wiki.python.org/moin/BitwiseOperators`

x << y : left shift operator
    Returns x with the bits shifted to the left by y places 
    (and new bits on the right-hand-side are zeros). This is 
    the same as multiplying x by 2**y.

x >> y : right shift operator
    Returns x with the bits shifted to the right by y places. 
    This is the same as //'ing x by 2**y.

x & y : bitwise and
    Does a "bitwise and". Each bit of the output is 1 if the 
    corresponding bit of x AND of y is 1, otherwise it's 0.

x | y : bitwise or
    Does a "bitwise or". Each bit of the output is 0 if the 
    corresponding bit of x AND of y is 0, otherwise it's 1.

~ x : complement of x
    Returns the complement of x - the number you get by switching 
    each 1 for a 0 and each 0 for a 1. This is the same as -x - 1.

x ^ y : bitwise exclusive or
    Does a "bitwise exclusive or". Each bit of the output is the 
    same as the corresponding bit in x if that bit in y is 0, and 
    it's the complement of the bit in x if that bit in y is 1.

"""

import math

def graycode(x):
    """
    Convert binary representation to graycode.

    Two steps:
    - Right shift (>>) input `num` by `
    - Exlusive or (XOR, ^) `num` with right-shifted `num` (by 1)

    Parameters
    ----------
    x : int
        An integer to be converted to graycode.
    
    Returns
    -------
    int 
        An integer corresponding to the integer
        converted to graycode.
    """
    x = int(x)

    return x^(x>>1)


def igraycode(x):
    """
    Convert graycode representation to binary.
    
    // Each Gray code bit is exclusive-ored with all more significant bits.
    
    uint mask = num;
    while (mask) {
        mask >>= 1;
        num   ^= mask;
    }
    return num;

    Parameters
    ----------
    x : int
        An integer to be converted to graycode.
    
    Returns
    -------
    int 
        An integer corresponding to the integer
        converted to graycode.
    """
    if x == 0:
        return x
    
    m = int(math.ceil(math.log(x, 2)))+1

    i, j = x, 1
    while j < m:
        i = i ^ (x>>j)
        j += 1
    return i


def bits(n, width):
    """
        Convert n to a list of bits of length width.
    """
    assert n < 2**width
    bin = []
    for i in range(width):
        bin.insert(0, 1 if n&(1<<i) else 0)
    return bin


def bits2int(bits):
    """
        Convert a list of bits to an integer.
    """
    n = 0
    for p, i in enumerate(reversed(bits)):
        n += i*2**p
    return n


def rrot(x, i, width):
    """
        Right bit-rotation.

        width: the bit width of x.
    """
    assert x < 2**width
    i = i%width
    x = (x>>i) | (x<<width-i)
    return x&(2**width-1)


def lrot(x, i, width):
    """
        Left bit-rotation.

        width: the bit width of x.
    """
    assert x < 2**width
    i = i%width
    x = (x<<i) | (x>>width-i)
    return x&(2**width-1)


def tsb(x, width):
    """
        Trailing set bits.
    """
    assert x < 2**width
    i = 0
    while x&1 and i <= width:
        x = x >> 1
        i += 1
    return i


def setbit(x, w, i, b):
    """
        Sets bit i in an integer x of width w to b.
        b must be 1 or 0
    """
    assert b in [1, 0]
    assert i < w
    if b:
        return x | 2**(w-i-1)
    else:
        return x & ~2**(w-i-1)


def bitrange(x, width, start, end):
    """
        Extract a bit range as an integer.
        (start, end) is inclusive lower bound, exclusive upper bound.
    """
    return x >> (width-end) & ((2**(end-start))-1)


def entropy(data, blocksize, offset, symbols=256):
    """
        Returns local byte entropy for a location in a file.
    """
    if len(data) < blocksize:
        raise ValueError("Data length must be larger than block size.")
    if offset < blocksize/2:
        start = 0
    elif offset > len(data)-blocksize/2:
        start = len(data)-blocksize/2
    else:
        start = offset-blocksize/2
    hist = {}
    for i in data[start:start+blocksize]:
        hist[i] = hist.get(i, 0) + 1
    base = min(blocksize, symbols)
    entropy = 0
    for i in hist.values():
        p = i/float(blocksize)
        # If blocksize < 256, the number of possible byte values is restricted.
        # In that case, we adjust the log base to make sure we get a value
        # between 0 and 1.
        entropy += (p * math.log(p, base))
    return -entropy
