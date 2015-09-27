#!/usr/bin/env python2
import sys
import hashlib
import base64
import csv
from time import mktime, strptime

DEFAULT_NB_RECORD = 15

def writeint(mbdb, int, intsize):
    while intsize > 0:
        intsize -= 1
        mbdb.write("%c" % ((int >> (intsize * 8)) & 0xFF))

def writestring(mbdb, str):
    if not len(str):
        mbdb.write("\xFF\xFF") # Blank string
    else:
        writeint(mbdb, len(str), 2) # 2-byte length
        mbdb.write(str)

def modeval(str):
    def type(char):
        if char == 'l': return 0xA
        elif char == '-': return 0x8
        elif char ==  'd': return 0x4
        else: return '?'
    def mode(char, i):
        # basic position test
        if char == 'r' and not (i + 1) % 3: return 0x1
        elif char == 'w' and not (i + 2) % 3: return 0x1
        elif char == 'x' and not (i + 3) % 3: return 0x1
        else: return 0x0
    modeint = type(str[0]) << 12
    str = str[1:] # slice the type
    i = 8
    for c in str:
        modeint = modeint + (mode(c, i) << i)
        i -= 1
    return modeint

def convert_times(time):
    return int(mktime(strptime(time, '%Y-%m-%d %H:%M:%S (%Z)')))

def parse_row(mbdb, row):
    # First, check for anomality
    filehash = hashlib.sha1(row[11] + '-' + row[9]).hexdigest() # domain-filename
    if row[8] != filehash: # fileID saved in the CSV
        print 'Error, the sha1 of %s returned %s while the CSV saved %s' % (row[9], filehash, row[8])
        return

    writestring(mbdb, row[11]) # domain
    # For some reason, an empty filename is just coded as \x00\x00:
    if len(row[9]):
        writestring(mbdb, row[9])
    else:
        mbdb.write("\x00\x00")
    writestring(mbdb, row[10]) # linktarget
    writestring(mbdb, base64.decodestring(row[13])) # datahash
    writestring(mbdb, base64.decodestring(row[14])) # enckey
    writeint(mbdb, modeval(row[0]), 2) # mode
    writeint(mbdb, int(row[1]), 8) # inode
    writeint(mbdb, int(row[2]), 4) # userid
    writeint(mbdb, int(row[3]), 4) # groupeid
    writeint(mbdb, convert_times(row[5]), 4) # mtime
    writeint(mbdb, convert_times(row[6]), 4) # atime
    writeint(mbdb, convert_times(row[7]), 4) # ctime
    writeint(mbdb, int(row[4]), 8) # filelen
    writeint(mbdb, int(row[12]), 1) # flag

    numprops = (len(row) - DEFAULT_NB_RECORD)
    if numprops % 2:
        print 'ERROR with %s: a property is missing an element (the last value is empty?) or ' \
              'the CSV delimiter is not unique (%s)' % (row[8], numprops)
        return
    numprops /= 2 # props: 1 name, 1 value

    writeint(mbdb, numprops, 1)
    for i in xrange(numprops):
        writestring(mbdb, row[DEFAULT_NB_RECORD + 2 * i]) # name
        writestring(mbdb, base64.decodestring(row[DEFAULT_NB_RECORD + 2 * i + 1])) # value

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "Usage: %s In.csv Out.mbdb" % sys.argv[0]
        sys.exit(2)

    with open(sys.argv[1], 'rb') as csvfile:
        csvreader =  csv.reader(csvfile)
        mbdb = open(sys.argv[2], 'w')
        mbdb.write('mbdb\x05\x00') # header

        for row in csvreader:
            parse_row(mbdb, row)
        mbdb.close()
