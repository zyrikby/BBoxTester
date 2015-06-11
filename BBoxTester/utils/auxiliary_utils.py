'''
Created on Jul 4, 2014

@author: Yury Zhauniarovich <y.zhalnerovich{at}gmail.com>
'''
import os, errno, shutil


def mkdir(path, mode=0777, overwrite=False):
    '''
    This method creates directory, additionally creating intermediate directories,
    if they do not exist. If overwrite == False and directory exists, the method
    returns happily.
     
    Args:
        :param path: path to the directory to create
        :param mode: permissions to the directory
        :param overwrite: True - to overwrite path if it exists 
    '''
    if os.path.exists(path) and overwrite:
        shutil.rmtree(path)
    #if overwrite==False and path exists mkdirs returns happily    
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise
    
def ensureDirExists(path, mode=0777):
    '''
    This method ensures that a directory exists. If it does not exists this
    method creates this directory.
    
    Args:
        :param path: path to the directory
        :param mode: permissions to the directory
    '''
    if not os.path.exists(path):
        os.makedirs(path, mode)
        
def searchFiles(where, extension):
    searched_files = []
    searched_extension = ".%s" % extension.lower()
    for root, dirs, files in os.walk(where):
        for f in files:
            if f.lower().endswith(searched_extension):
                searched_files.append(os.path.join(root, f))
    return searched_files

def searchFilesRelativeToDir(target, extension):
    '''
    This method searches for files with the provided extension in the provided 
    directory recursively and returns path to these files relative to the 
    specified directory.
    
    Args:
        :param target: directory in which
        :param extension:
    Returns:
        :ret paths to files relative to the target
    '''
    searched_files = []
    searched_extension = ".%s" % extension.lower()
    for root, dirs, files in os.walk(target):
        for f in files:
            if f.lower().endswith(searched_extension):
                searched_files.append(os.path.join(root[len(target):], f))
    return searched_files

def to_bool(value):
    """
       Converts 'something' to boolean. Raises exception for invalid formats
           Possible True  values: 1, True, "1", "TRue", "yes", "y", "t"
           Possible False values: 0, False, None, [], {}, "", "0", "faLse", "no", "n", "f", 0.0, ...
    """
    if str(value).lower() in ("yes", "y", "true",  "t", "1"): return True
    if str(value).lower() in ("no",  "n", "false", "f", "0", "0.0", "", "none", "[]", "{}"): return False
    raise Exception('Invalid value for boolean conversion: ' + str(value))

# def checkInputFile(inputPath):
#     logger.debug("Checking input path [%s]..." % inputPath)
#     if not os.path.isfile(inputPath):
#         logger.error("Input path [%s] does not point to a file!" % inputPath)
#         return False
#     logger.debug("The path [%s] point to the file!" % inputPath)
#     
#     ret_type = androconf.is_android(inputPath)
#     if ret_type != "APK":
#         logger.error("Input file [%s] is not APK file!" % inputPath)
#         return False
#     
#     logger.debug("File [%s] is an APK file!" % inputPath)
#     return True
#     
# def checkOutputPath(dst):
#     if os.path.exists(dst):
#         if not os.path.isdir(dst):
#             logger.error("[%s] is not a directory!" % dst)
#             return False
#     else:
#         logger.info("The path [%s] does not exist! Creating it!" % dst)
#         os.makedirs(dst)
#     
#     return True
# 
# def copyFileToDir(src, dst):
#     logger.debug("Coping file [%s] to output directory [%s]..." % (os.path.basename(src), dst))
#         
#     if not os.path.isfile(src):
#         logger.debug("[%s] is not a file! Cannot be copied!" % src)
#         return False
#     try:
#         shutil.copy2(src, dst)
#     except Exception as e:
#         logger.error(e)
#         logger.error("Could not copy file [%s] to directory [%s]!" % (src, dst))
#         return False
#     
#     logger.debug("File [%s] has been copied to directory [%s] successfully!" % (src, dst))
#     return True
