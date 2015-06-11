'''
Created on Oct 1, 2014

@author: Yury Zhauniarovich <y.zhalnerovich{at}gmail.com>
'''

import os

from interfaces.emma_interface import EmmaInterface, EMMA_REPORT


class BBoxReporter:
    def __init__(self, config):
        self.metaFiles = []
        self.reportFiles = []
        self.config = config
        
    def addMetaFile(self, pathToMetaFile):
        if not os.path.isfile(pathToMetaFile):
            raise NotFileException("The path [%s] is not a file!" 
                                   % pathToMetaFile)
        self.metaFiles.append(pathToMetaFile)
    
    def addReportFile(self, pathToReportFile):
        if not os.path.isfile(pathToReportFile):
            raise NotFileException("The path [%s] is not a file!" 
                                   % pathToReportFile)
        self.reportFiles.append(pathToReportFile)
        
    def cleanMetaFiles(self):
        self.metaFiles = []
        
    def cleanReportFiles(self):
        self.reportFiles = []
    
    def generateEmmaReport(self, where, reportName, emmaReportType=EMMA_REPORT.HTML):
        emma = EmmaInterface(javaPath = self.config.getEmmaJavaPath(),
                             javaOpts = self.config.getEmmaJavaOpts(),
                             pathEmma = self.config.getEmmaDir(),
                             jarEmma = self.config.getEmmaJar(),
                             jarEmmaDevice = self.config.getEmmaDeviceJar())
        
        if not (self.metaFiles and self.reportFiles):
            raise ReportGenerationError("A metafile or a report file is absent.\
                Cannot generate report without one of these files!") 
        
        inputs = []
        inputs.extend(self.metaFiles)
        inputs.extend(self.reportFiles)
        
        #TODO: check the output
        emma.reportToDirWithName(inputs=inputs, toDir=where, mainFileName=reportName, report=emmaReportType)


class MsgException(Exception):
    '''
    Generic exception with an optional string msg.
    '''
    def __init__(self, msg=""):
        self.msg = msg

class NotFileException(MsgException):
    '''
    The provided path does not point to the file.
    '''
    
class ReportGenerationError(object):
    '''
    The coverage report cannot be generated.
    '''
