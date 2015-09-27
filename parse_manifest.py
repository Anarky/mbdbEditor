#!/usr/bin/env python2
# From http://stackoverflow.com/questions/3085153/how-to-parse-the-manifest-mbdb-file-in-an-ios-4-0-itunes-backup
import sys
import hashlib
import base64
from time import localtime, strftime

def getint(data, offset, intsize):
    """Retrieve an integer (big-endian) and new offset from the current offset"""
    value = 0
    while intsize > 0:
        value = (value<<8) + ord(data[offset])
        offset = offset + 1
        intsize = intsize - 1
    return value, offset

def getstring(data, offset):
    """Retrieve a string and new offset from the current offset into the data"""
    if data[offset] == chr(0xFF) and data[offset+1] == chr(0xFF):
        return '', offset+2 # Blank string
    length, offset = getint(data, offset, 2) # 2-byte length
    value = data[offset:offset+length]
    return value, (offset + length)

def process_mbdb_file(filename):
    mbdb = [] # List, we want to keep the same order
    file = open(filename)
    data = file.read()
    if data[0:6] != "mbdb\x05\x00": raise Exception("This does not look like an MBDB file")
    offset = 6
    while offset < len(data):
        fileinfo = {}
        fileinfo['domain'], offset = getstring(data, offset)
        fileinfo['filename'], offset = getstring(data, offset)
        fileinfo['linktarget'], offset = getstring(data, offset)
        fileinfo['datahash'], offset = getstring(data, offset)
        fileinfo['enckey'], offset = getstring(data, offset)
        fileinfo['mode'], offset = getint(data, offset, 2)
        fileinfo['inode'], offset = getint(data, offset, 8)
        fileinfo['userid'], offset = getint(data, offset, 4)
        fileinfo['groupid'], offset = getint(data, offset, 4)
        fileinfo['mtime'], offset = getint(data, offset, 4)
        fileinfo['atime'], offset = getint(data, offset, 4)
        fileinfo['ctime'], offset = getint(data, offset, 4)
        fileinfo['filelen'], offset = getint(data, offset, 8)
        fileinfo['flag'], offset = getint(data, offset, 1)
        fileinfo['numprops'], offset = getint(data, offset, 1)
        fileinfo['properties'] = []
        for ii in range(fileinfo['numprops']):
            propname, offset = getstring(data, offset)
            propval, offset = getstring(data, offset)
            fileinfo['properties'].append([propname, propval])
        fullpath = fileinfo['domain'] + '-' + fileinfo['filename']
        id = hashlib.sha1(fullpath)
        fileinfo['fileID'] = id.hexdigest()
        mbdb.append(fileinfo)
    file.close()
    return mbdb

def modestr(val):
    def mode(val):
        if (val & 0x4): r = 'r'
        else: r = '-'
        if (val & 0x2): w = 'w'
        else: w = '-'
        if (val & 0x1): x = 'x'
        else: x = '-'
        return r+w+x
    return mode(val>>6) + mode((val>>3)) + mode(val)

def convert_time(datecode):
    return strftime('%Y-%m-%d %H:%M:%S (%Z)', localtime(datecode))

def fileinfo_str(f):
    if (f['mode'] & 0xE000) == 0xA000: type = 'l' # symlink
    elif (f['mode'] & 0xE000) == 0x8000: type = '-' # file
    elif (f['mode'] & 0xE000) == 0x4000: type = 'd' # dir
    else:
        print >> sys.stderr, "Unknown file type %04x for %s" % (f['mode'], fileinfo_str(f, False))
        type = '?' # unknown
    info = ("%s%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" %
            (type, modestr(f['mode']&0x0FFF), f['inode'], f['userid'], f['groupid'], f['filelen'],
             convert_time(f['mtime']), convert_time(f['atime']), convert_time(f['ctime']),
             f['fileID'], f['filename'], f['linktarget'], f['domain'], f['flag'],
             base64.b64encode(f['datahash']), base64.b64encode(f['enckey'])))
    for name, value in f['properties']: # extra properties
        info = info + ',' + name + ',' + base64.b64encode(value)
    return info

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "Usage: %s In.mbdb Out.csv" % sys.argv[0]
        sys.exit(2)

    mbdb = process_mbdb_file(sys.argv[1])
    csv = open(sys.argv[2], 'w')
    for fileinfo in mbdb:
        csv.write(fileinfo_str(fileinfo) + '\n')
    csv.close()
