'''
Created on Oct 13, 2014

@author: Yury Zhauniarovich <y.zhalnerovich{at}gmail.com>
'''
import os


def checkInputApkFile(inputPath):
    if not inputPath:
        return (False, "File is not provided!")
    if not os.path.isfile(inputPath):
        return (False, "Provided path is not pointing on a file!")
    
    fileType = is_android(inputPath)
    if fileType != "APK":
        return (False, "Provided file is not an apk file!")
    
    return (True, None)
                

def is_android(filename) :
    """Return the type of the file

        @param filename : the filename
        @rtype : "APK", "DEX", "ELF", None 
    """
    if not filename:
        return None

    with open(filename, "r") as fd:
        f_bytes = fd.read(7)
    
    val = is_android_raw(f_bytes)
    return val


def is_android_raw(raw):
    val = None
    f_bytes = raw[:7]

    if f_bytes[0:2] == "PK":
        val = "APK"
    elif f_bytes[0:3] == "dex":
        val = "DEX"
    elif f_bytes[0:3] == "dey":
        val = "DEY"
    elif f_bytes[0:7] == "\x7fELF\x01\x01\x01":
        val = "ELF"
    elif f_bytes[0:4] == "\x03\x00\x08\x00":
        val = "AXML"
    elif f_bytes[0:4] == "\x02\x00\x0C\x00":
        val = "ARSC"

    return val

def is_valid_android_raw(raw) :
    return raw.find("classes.dex") != -1