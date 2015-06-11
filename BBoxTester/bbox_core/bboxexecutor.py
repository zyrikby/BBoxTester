'''
Created on Sep 30, 2014

@author: Yury Zhauniarovich <y.zhalnerovich{at}gmail.com>
'''
import string

from bbox_core.general_exceptions import MsgException
from interfaces.adb_interface import AdbInterface, TYPE_STRING, TYPE_BOOLEAN
from logconfig import logger
import os


#taken from EmmaInstrumentation.java
# TAG_COVERAGE                        = "coverage"
# TAG_PREANALYSIS_COVERAGE_FILE_PATH  = "coverageFile"
# TAG_GENERATE_REPORT                 = "generateReport"
# TAG_POSTANALYSIS_COVERAGE_FILE_PATH = "reportFilePath"


KEY_COVERAGE = "coverage"
KEY_REPORT_FOLDER = "coverageDir"
KEY_CANCEL_ANALYSIS = "cancelAnalysis"
KEY_PROCEED_ON_ERROR = "proceedOnError"
KEY_GENERATE_COVERAGE_REPORT_ON_ERROR = "generateCoverageReportOnError"

ACTION_FINISH_TESTING = "com.zhauniarovich.bbtester.finishtesting"
DEFAULT_COVERAGE_FILE_PATH  = "/mnt/sdcard/coverage.ec"

class BBoxExecutor:
    #TODO: State machine?
    def __init__(self, config):
        self.isDeviceActive = False
        self.testStarted = False
        self.device = AdbInterface()
        self.config = config #maybe it will be required for future use
        
    def selectExecutionDevice(self):
        '''
        This method allows a user to select a device that is used to for further
        analysis.
        '''
        dev_list = AdbInterface.getDeviceSerialsList()
        devNum = len(dev_list)
        
        if devNum <= 0:
            print "No device has been detected! Connect your device and restart the application!"
            return
        
        if devNum == 1:
            self.device.setTargetSerial(dev_list[0])
            self.isDeviceActive = True
            return
        
        choice = None
        if devNum > 1:
            print "Select the device to use for analysis:\n"
            for i in xrange(0, devNum):
                print "%d. %s\n" % ((i + 1), dev_list[i])
            
            while not choice:
                try:
                    choice = int(raw_input())
                    if choice not in range(1, devNum+1):
                        choice = None
                        print 'Invalid choice! Choose right number!'
                    
                except ValueError:
                    print 'Invalid Number! Choose right number!'
            
        self.device.setTargetSerial(dev_list[choice - 1])
        self.isDeviceActive = True
    
    
    def setExecutionDevice(self, device):
        if not isinstance(device, AdbInterface):
            logger.error("Provided object is not of AdbInterface class")
        self.device=device
        self.isDeviceActive = True

    def installApkOnDevice(self, pathToApk):
        '''
        This method installs selected apk file on the device.
        
        Args:
            :param pathToApk: path to the apk file that has to be installed on 
            the device
        Raises:
            ApkCannotBeInstalledException: if the error occurred during the 
            installation process.
        '''
        if not self.isDeviceActive:
            self.selectExecutionDevice()
        
        output = self.device.install(pathToApk)
        success = self._interpretApkInstallCmd(output)
        if not success:
            raise ApkCannotBeInstalledException(output)
        
    
    def uninstallPackage(self, packageName, keepData=False):
        '''
        This method uninstalls specified package from the device.
        
        Args:
            :param packageName: the name of the package to uninstall
            :param keepData: True if the data of the application should be 
                preserved (should be not deleted)
        '''
        if not self.isDeviceActive:
            self.selectExecutionDevice()
        output = self.device.uninstall(package_name=packageName,
                                       keep_data=keepData)
        #logger.info(output)
        
    
    def startOndeviceTesting(self, packageName, runnerName, coverage=True, reportFolder=None, proceedOnError=False, generateCoverageReportOnError=True):
        '''
        This methods starts testing process on the device.
        
        Args:
            :param packageName: the name of the package that is instrumented and
                needs to be tested
            :param runnerName: the name of the runner that runs the testing
            :param coverage: True - if the coverage report should be generated
            :param coverageFile: the path to the file, where the coverage report
                is stored. Notice, that there are two main ways to provide this 
                file path: before the analysis or after the analysis. The path
                provided after analysis has more power then the file path 
                provided before the analysis. This means that if you provided 
                file path before and after analysis, the file will be stored in 
                the place according to the latter. 
        '''
        #Checking if there is an available device for execution
        #if not self.isDeviceActive:
        #    self.selectExecutionDevice()
        if not self.isDeviceActive:
            self.selectExecutionDevice()
        
        
        instrArgs = {}
        instrArgs[KEY_COVERAGE] = coverage
        if reportFolder:
            instrArgs[KEY_REPORT_FOLDER] = reportFolder
        
        instrArgs[KEY_PROCEED_ON_ERROR] = proceedOnError
        instrArgs[KEY_GENERATE_COVERAGE_REPORT_ON_ERROR] = generateCoverageReportOnError
        
        self.device.startInstrumentationNoResults(package_name=packageName,
                                                runner_name=runnerName,
                                                wait=False,
                                                instrumentation_args=instrArgs)
        self.testStarted = True
        
    
    def stopOndeviceTesting(self, cancelAnalysis=False):
        '''
        This method stops testing the application on the device.
        
        Args:
            :param generateReport: True - if the coverage report needs to be 
                generated
        '''
        if not self.testStarted:
            print "The testing on the device has not be started. Nothing to stop!"
            return
        extra = {}
        extra[KEY_CANCEL_ANALYSIS] = (TYPE_BOOLEAN, cancelAnalysis)
        
        self.device.sendBroadcast(action=ACTION_FINISH_TESTING, extra=extra)
        self.testStarted = False
        
        
    def cancelAnalysis(self):
        '''
        This method stops the analysis without storing coverage report.
        '''
        self.stopOndeviceTesting(cancelAnalysis=True)
        
    def getFileFromDevice(self, srcPath, dstPath):
        '''
        The method gets a file (usually it is used to get a report) from a 
        device.
        
        Args:
            :param srcPath: the path on the device that needs to be copied
            :param dstPath: destination where to copy the file
        '''
        return self.device.pull(srcPath, dstPath)
        
    
    def _interpretApkInstallCmd(self, output):
        '''
        A helper method used to interpret the output of the app install command.
        
        Args: 
            :param output: output of the install command that needs to be parsed
        '''
        for line in output.split('\n'):
            line = line.strip(string.whitespace)
            if "Success" in line:
                return True
        
        return False
    
    def removeFile(self, target):
        return self.device.remove(target)


#Exceptions    
class ApkCannotBeInstalledException(MsgException):
    '''
    Apk cannot be installed.
    '''


# bboxexecutor = BBoxExecutor()
# bboxexecutor.selectExecutionDevice()
# print bboxexecutor.device.getSerialNumber()
# print bboxexecutor.installApkOnDevice("/home/yury/research_tmp/bboxtester/Notepad.apk")
#bboxexecutor.startOndeviceTesting("package", "runner", True, coverageFile = "/mnt/sd")
# print bboxexecutor.device.previewInstrumentationCommand(package_name="packageName", 
#                                                         runner_name="runnerName",
#                                                         wait=False)

# bboxexecutor.stopOndeviceTesting(generateReport=False, postAnalysisCoverageFilePath="/my_path")