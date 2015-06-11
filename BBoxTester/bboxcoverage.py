'''
Created on Oct 14, 2014

@author: Yury Zhauniarovich <y.zhalnerovich{at}gmail.com>
'''
import os, sys, shutil
import ConfigParser
from bbox_core.bbox_config import BBoxConfig
from utils.state_machine import StateMachine
from utils import apk_utils, auxiliary_utils, zip_utils
from bbox_core.bboxreporter import MsgException, BBoxReporter
from bbox_core.bboxinstrumenter import BBoxInstrumenter,\
    ApkCannotBeDecompiledException, Dex2JarConvertionError,\
    EmmaCannotInstrumentException, Jar2DexConvertionError,\
    IllegalArgumentException, ApktoolBuildException, SignApkException,\
    AlignApkException
from bbox_core.bboxexecutor import BBoxExecutor, ApkCannotBeInstalledException
from logconfig import logger
from string import rfind
from utils.android_manifest import AndroidManifest
from time import localtime
import datetime
from interfaces.emma_interface import EMMA_REPORT
import time
from six import iteritems


#print os.path.dirname(os.path.realpath(__file__)) #TODO: if we call from external modules we need later to rely on this path

RESULTS_RELATIVE_DIR = "RESULTS"
TMP_RELATIVE_DIR = "TMP"
DEVICE_REPORT_FOLDER_PATH = "/mnt/sdcard"

PARAMS_SECTION = "parameters"



STATE_UNINITIALIZED = "UNINITIALIZED"
STATE_APK_VALID = "APK_IS_VALID"
STATE_FOLDERS_CREATED = "FOLDERS_CREATED"
STATE_APK_DECOMPILED = "APK_IS_DECOMPILED"
STATE_DEX_CONVERTED_TO_JAR = "DEX_FILES_CONVERTED_TO_JARS"
STATE_JARS_INSTRUMENTED = "JAR_FILES_INSTRUMENTED"
STATE_JAR_CONVERTED_TO_DEX = "JAR_FILES_CONVERTED_TO_DEX"
STATE_MANIFEST_INSTRUMENTED = "ANDROID_MANIFEST_IS_INSTRUMENTED"
STATE_INSTRUMENTED_APK_BUILD = "INSTRUMENTED_APK_IS_BUILT"
STATE_FINAL_INSTRUMENTED_APK_BUILD = "FINAL_INSTRUMENTED_APK_IS_BUILT"
STATE_INSTRUMENTED_APK_SIGNED = "INSTRUMENTED_APK_IS_SIGNED"
STATE_INSTRUMENTED_APK_ALIGNED = "INSTRUMENTED_APK_IS_ALIGNED"
STATE_APK_INSTRUMENTED = "APK_IS_INSTRUMENTED"
STATE_VALID_SETTINGS_PROVIDED = "VALID_SETTINGS_PROVIDED"
STATE_APK_INSTALLED = "APK_IS_INSTALLED"
STATE_APK_TEST_STARTED = "TEST_IS_STARTED"
STATE_APK_FINISHED_TESTING = "TEST_IS_FINISHED"




STATES = [(STATE_UNINITIALIZED, STATE_APK_VALID),
          (STATE_APK_VALID, STATE_FOLDERS_CREATED),
          (STATE_FOLDERS_CREATED, STATE_APK_DECOMPILED),
          (STATE_APK_DECOMPILED, STATE_DEX_CONVERTED_TO_JAR),
          (STATE_DEX_CONVERTED_TO_JAR, STATE_JARS_INSTRUMENTED),
          (STATE_JARS_INSTRUMENTED, STATE_JAR_CONVERTED_TO_DEX),
          (STATE_JAR_CONVERTED_TO_DEX, STATE_MANIFEST_INSTRUMENTED),
          (STATE_MANIFEST_INSTRUMENTED, STATE_INSTRUMENTED_APK_BUILD),
          (STATE_INSTRUMENTED_APK_BUILD, STATE_FINAL_INSTRUMENTED_APK_BUILD),
          (STATE_FINAL_INSTRUMENTED_APK_BUILD, STATE_INSTRUMENTED_APK_SIGNED),
          (STATE_INSTRUMENTED_APK_SIGNED, STATE_INSTRUMENTED_APK_ALIGNED),
          (STATE_INSTRUMENTED_APK_ALIGNED, STATE_APK_INSTRUMENTED),
          #this is installation check
          (STATE_APK_INSTRUMENTED, STATE_APK_INSTALLED),
          (STATE_VALID_SETTINGS_PROVIDED, STATE_APK_INSTALLED),
          #start testing
          (STATE_APK_INSTRUMENTED, STATE_APK_TEST_STARTED),
          (STATE_VALID_SETTINGS_PROVIDED, STATE_APK_TEST_STARTED),
          (STATE_APK_INSTALLED, STATE_APK_TEST_STARTED),
          #stop testing
          (STATE_APK_TEST_STARTED, STATE_APK_FINISHED_TESTING),
          ]


class BBoxCoverage:
    PREFIX_ONSTOP = "onstop";
    PREFIX_ONERROR = "onerror";
    
    '''
    This class unites all separate classes needed for instrumentation and
    testing of the instrumented apk and provides a consistent workflow for a 
    developer.
    '''
#     def __init__(self, resultsRootDir=None, pathToBBoxConfigFile="./config/bbox_config.ini"):
#         '''
#         Constructor.
#         '''
#         #getting resultsRootDir
#         self.resultsRootDir = None
#         if not resultsRootDir:
#             self.resultsRootDir = os.path.join(os.getcwd(), )
#         else:
#             self.resultsRootDir = os.path.abspath(resultsRootDir)
#         
#         self.config = BBoxConfig(pathToBBoxConfigFile)
#         self._bboxStateMachine = StateMachine(states=STATES)
    
    def __init__(self, pathToBBoxConfigFile="./config/bbox_config.ini"):
        self.androidManifestFile = None
        self.instrumentedApk = None
        self.config = BBoxConfig(pathToBBoxConfigFile)
        self.bboxInstrumenter = BBoxInstrumenter(self.config)
        self.bboxExecutor = BBoxExecutor(self.config)
        self.bboxReporter = BBoxReporter(self.config)
        self._bboxStateMachine = StateMachine(states=STATES)
    
    def getInstrumentedApk(self):
        return self.instrumentedApk

    def getPackageName(self):
        return self.packageName
    
    def instrumentApkForCoverage(self, pathToOrigApk, resultsDir=None, tmpDir=None, 
                                 removeApkTmpDirAfterInstr=True, 
                                 copyApkToRes = True):
        '''
        Args:
            :param pathToOrigApk:
            :param resultsDir:
            :param tmpDir:
        
        Returns:
            :ret True - if instrumentation was successful, False otherwise
        '''
        self._bboxStateMachine.start(STATE_UNINITIALIZED)
        
        valid = self._checkProvidedApk(pathToOrigApk)
        if not valid:
            return False
        self._bboxStateMachine.transitToState(STATE_APK_VALID)
        
        resultsRootDir = None
        if not resultsDir:
            resultsRootDir = os.path.join(os.getcwd(), RESULTS_RELATIVE_DIR)
        else:
            resultsRootDir = os.path.abspath(resultsDir)
        
        tmpRootDir = None
        if not tmpDir:
            tmpRootDir = os.path.join(os.getcwd(), TMP_RELATIVE_DIR)
        else:
            tmpRootDir = os.path.abspath(tmpDir)
        
        apkFileName = os.path.splitext(os.path.basename(pathToOrigApk))[0]
        
        self.apkTmpDir = self._createDir(tmpDir, apkFileName, False, True)
        self.apkResultsDir = self._createDir(resultsRootDir, apkFileName, False, True)
        self.coverageMetadataFolder = self._createDir(self.apkResultsDir, self.config.getCoverageMetadataRelativeDir(), False, True)
        self.runtimeReportsRootDir = self._createDir(self.apkResultsDir, self.config.getRuntimeReportsRelativeDir(), False, True)
        self._bboxStateMachine.transitToState(STATE_FOLDERS_CREATED)
        
        #coping initial apk file if required
        if copyApkToRes:
            shutil.copy2(pathToOrigApk, self.apkResultsDir)
        
        #decompiling apk into a folder
        decompileDir = os.path.join(self.apkTmpDir, self.config.getDecompiledApkRelativeDir())
        success = self._decompileApk(self.bboxInstrumenter, pathToOrigApk, decompileDir)
        if not success:
            return False
        self._bboxStateMachine.transitToState(STATE_APK_DECOMPILED)
        
        #getting all available dex files
        dexFilesRelativePaths = self._getDexFilePathsRelativeToDir(decompileDir)
        if not dexFilesRelativePaths:
            logger.error("There is no dex files to convert!")
            return False
        if "classes.dex" not in dexFilesRelativePaths:
            # "classes.dex" must be in the decompile root directory
            logger.error("There is no classes.dex file found in the list of dex files")
            return False
        
        
        #converting dex to jar files
        rawJarFilesRootDir = os.path.join(self.apkTmpDir, self.config.getTmpJarRelativeDir())
        jarFilesRelativePaths = self._convertDex2JarFiles(
                                    converter=self.bboxInstrumenter, 
                                    dexFilesRootDir=decompileDir, 
                                    dexFilesRelativePaths=dexFilesRelativePaths,
                                    jarFilesRootDir=rawJarFilesRootDir,
                                    proceedOnError=True)
        self._bboxStateMachine.transitToState(STATE_DEX_CONVERTED_TO_JAR)
        
        if "classes.jar" not in jarFilesRelativePaths:
            #main file is not converted
            logger.error("Conversion from classes.dex to classes.jar was not successful!")
            return False
        
        #instrumenting available jar files
        self.coverageMetadataFile = os.path.join(self.coverageMetadataFolder, self.config.getCoverageMetadataFilename())
        emmaInstrJarFilesRootDir = os.path.join(self.apkTmpDir, self.config.getInstrumentedFilesRelativeDir())
        emmaInstrJarFileRelativePaths = self._instrFilesWithEmma(
                            instrumenter=self.bboxInstrumenter, 
                            jarFilesRootDir=rawJarFilesRootDir, 
                            jarFilesRelativePaths=jarFilesRelativePaths, 
                            instrJarsRootDir=emmaInstrJarFilesRootDir,
                            coverageMetadataFile=self.coverageMetadataFile,
                            proceedOnError=True)
        self._bboxStateMachine.transitToState(STATE_JARS_INSTRUMENTED)
        
        if "classes.jar" not in emmaInstrJarFileRelativePaths:
            #main file is not instrumented
            logger.error("Instrumentation of classes.jar was not successful!")
            return False
        
        #converting jar files back to dex files
        instrDexFilesRelativePaths = self._convertJar2DexWithInstr(
                    converter=self.bboxInstrumenter,
                    instrJarsRootDir=emmaInstrJarFilesRootDir, 
                    instrJarFilesRelativePaths=emmaInstrJarFileRelativePaths,
                    finalDexFilesRootDir=decompileDir,
                    proceedOnError=True)
        self._bboxStateMachine.transitToState(STATE_JAR_CONVERTED_TO_DEX)
        
        if "classes.dex" not in instrDexFilesRelativePaths:
            logger.error("There is no classes.dex file found in the list of dex files")
            return False
        
        #checking what files have not been converted
        uninstrumentedFiles = self._getUnInstrFilesRelativePaths(dexFilesRelativePaths, instrDexFilesRelativePaths)
        if uninstrumentedFiles:
            logger.debug("The following files were not instrumented: %s" + str(uninstrumentedFiles))
        
        #instrument AndroidManifest.xml
        decompiledAndroidManifestPath = os.path.join(decompileDir, "AndroidManifest.xml")
        success = self._instrAndroidManifest(self.bboxInstrumenter, decompiledAndroidManifestPath)
        if not success:
            logger.error("Cannot instrument AndroidManifest.xml file!")
            return False
        #coping instrumented AndroidManifest.xml to result folder
        shutil.copy2(decompiledAndroidManifestPath, self.apkResultsDir)
        self.androidManifestFile = os.path.join(self.apkResultsDir, "AndroidManifest.xml")
        self._bboxStateMachine.transitToState(STATE_MANIFEST_INSTRUMENTED)
        
        compiledApkFilePath = os.path.join(self.apkResultsDir, "%s%s.apk" % (apkFileName, self.config.getInstrFileSuffix()))
        success = self._compileApk(self.bboxInstrumenter, decompileDir, compiledApkFilePath)
        if not success:
            logger.error("Cannot build apk!")
            return False
        self._bboxStateMachine.transitToState(STATE_INSTRUMENTED_APK_BUILD)
        
        #need to copy resources into file
        compiledApkFilePathWithEmmaRes = os.path.join(self.apkResultsDir, "%s%s.apk" % (apkFileName, self.config.getFinalInstrFileSuffix()))
        shutil.copy2(compiledApkFilePath, compiledApkFilePathWithEmmaRes)
        self._putAdditionalResources(apk=compiledApkFilePathWithEmmaRes, resources=self.config.getEmmaResourcesDir())
        self._bboxStateMachine.transitToState(STATE_FINAL_INSTRUMENTED_APK_BUILD)
        
        signedApkFilePath = os.path.join(self.apkResultsDir, "%s%s.apk" % (apkFileName, self.config.getSignedFileSuffix()))
        success = self._signApk(self.bboxInstrumenter, compiledApkFilePathWithEmmaRes, signedApkFilePath)
        if not success:
            logger.error("Cannot sign apk!")
            return False
        self._bboxStateMachine.transitToState(STATE_INSTRUMENTED_APK_SIGNED)
        
        alignedApkFilePath = os.path.join(self.apkResultsDir, "%s%s.apk" % (apkFileName, self.config.getAlignedFileSuffix()))
        success = self._alignApk(self.bboxInstrumenter, signedApkFilePath, alignedApkFilePath)
        if not success:
            logger.error("Cannot align apk!")
            return False
        self._bboxStateMachine.transitToState(STATE_INSTRUMENTED_APK_ALIGNED)
        
        #cleaning: if tmp dir needs to be removed after instrumentation
        if removeApkTmpDirAfterInstr:
            shutil.rmtree(self.apkTmpDir)
        
        self.instrumentedApk = alignedApkFilePath
        self.androidManifest = AndroidManifest(self.androidManifestFile)
        self.packageName = self.androidManifest.getInstrumentationTargetPackage()
        self.runnerName = self.androidManifest.getInstrumentationRunnerName()
        
        #Final node transition
        self._bboxStateMachine.transitToState(STATE_APK_INSTRUMENTED)
        return True
        
    
    def _createDir(self, root, directory, createNew=True, overwrite=False):
        resDir = os.path.join(root, directory)
        if createNew:
            i = 0
            while os.path.exists(resDir):
                i += 1
                resDir = os.path.join(root, "%s_%d" % (directory, i))
        auxiliary_utils.mkdir(path=resDir, mode=0777, overwrite=overwrite)
                
#         resDir = os.path.join(root, directory)
#         if not overwrite:
#             i = 0
#             while os.path.exists(resDir):
#                 i += 1
#                 resDir = os.path.join(root, "%s_%d" % (directory, i))
#         
#         auxiliary_utils.mkdir(path=resDir, mode=0777, overwrite=overwrite)
        return resDir
    
    def _createFolder(self, root, dirName, overwrite=False):
        resultDir = os.path.join(root, dirName)
        auxiliary_utils.mkdir(path=resultDir, mode=0777, overwrite=overwrite)
        return resultDir
    
    
    def _checkProvidedApk(self, pathToApk):
        '''
        This methods validates the provided apk file.
        
        Raises:
            ApkIsNotValidException: if the provided apk file is not correct
        '''
        (valid, error) = apk_utils.checkInputApkFile(pathToApk)
        if not valid:
            logger.error("Path %s points to the invalid apk file! ERROR:%s" % (pathToApk, error))
            return valid
        
        return valid

    
    def _decompileApk(self, decompiler, apk, outputDir):
        try:
            decompiler.decompileApk(apk, outputDir)
        except ApkCannotBeDecompiledException as e:
            logger.error(e.msg)
            return False
        except:
            logger.error("Unknown error during decompile process! Exit")
            return False
        
        return True
    
    
    def _convertDex2JarFiles(self, converter, dexFilesRootDir, dexFilesRelativePaths, jarFilesRootDir, proceedOnError=True):
        jarFilesRelativePaths = []
        for dexFileRelativePath in dexFilesRelativePaths:
            dexFilePath = os.path.join(dexFilesRootDir, dexFileRelativePath)
            jarFileRelativePath = os.path.splitext(dexFileRelativePath)[0] + ".jar"
            jarFilePath = os.path.join(jarFilesRootDir, jarFileRelativePath)
            try:
                converter.convertDex2Jar(dexFilePath, jarFilePath, overwrite=True)
            except Dex2JarConvertionError as e:
                if proceedOnError:
                    logger.warning("Cannot convert [%s] to [%s]. %s" (dexFilePath, jarFilePath, e.msg))
                    continue
                else:
                    raise
            jarFilesRelativePaths.append(jarFileRelativePath) 
            
        return jarFilesRelativePaths
        
    
    def _instrFilesWithEmma(self, instrumenter, jarFilesRootDir, jarFilesRelativePaths, 
            instrJarsRootDir, coverageMetadataFile, proceedOnError=True):
        
        instrJarFilesRelativePaths = []
        for jarFileRelativePath in jarFilesRelativePaths:
            jarFileAbsPath = os.path.join(jarFilesRootDir, jarFileRelativePath)
            instrJarRelativeDir = jarFileRelativePath[:jarFileRelativePath.rfind("/")+1]
            instrJarFullDir = os.path.join(instrJarsRootDir, instrJarRelativeDir)
            
            try:
                instrumenter.instrumentJarWithEmma(jarFile=jarFileAbsPath, outputFolder=instrJarFullDir, emmaMetadataFile=coverageMetadataFile)
            except EmmaCannotInstrumentException as e:
                if proceedOnError:
                    logger.warning("Cannot instrument [%s]. %s" (jarFileAbsPath, e.msg))
                    continue
                else:
                    raise
            instrJarFilesRelativePaths.append(jarFileRelativePath)
        
        return instrJarFilesRelativePaths
    
    
    def _convertJar2DexWithInstr(self, converter, instrJarsRootDir, 
                                 instrJarFilesRelativePaths, 
                                 finalDexFilesRootDir, proceedOnError):
        instrDexFilesRelativePaths = []
        for jarFileRelativePath in instrJarFilesRelativePaths:
            jarFileAbsPath = os.path.join(instrJarsRootDir, jarFileRelativePath)
            dexFileRelativePath = os.path.splitext(jarFileRelativePath)[0] + ".dex"
            dexFileAbsPath = os.path.join(finalDexFilesRootDir, dexFileRelativePath)
            
            #we instrument main file with auxiliary classes
            print "jarFileRelativePath: " + jarFileRelativePath
            
            try:
                withFiles = []
                #we compile main file with additional instrumentation files
                #hack: emma copies instrumented jar files into lib folder
                if jarFileRelativePath == "classes.jar":
                    emmaDevicePath = os.path.join(self.config.getEmmaDir(), self.config.getEmmaDeviceJar())
                    withFiles.append(self.config.getAndroidSpecificInstrumentationClassesPath())
                    withFiles.append(emmaDevicePath)
                
                converter.convertJar2Dex(jarFile=jarFileAbsPath, 
                                         dexFile=dexFileAbsPath, 
                                         withFiles=withFiles, 
                                         overwrite=True)
            except Jar2DexConvertionError as e:
                if proceedOnError:
                    logger.warning("Cannot instrument [%s]. %s" % (jarFileAbsPath, e.msg))
                    continue
                else:
                    raise
            instrDexFilesRelativePaths.append(dexFileRelativePath)
        
        return instrDexFilesRelativePaths
    
    
    def _getUnInstrFilesRelativePaths(self, dexFilesRelativePaths, instrDexFilesRelativePaths):
        uninstrumentedFiles = []
        for dexFileRelativePath in dexFilesRelativePaths:
            if dexFileRelativePath not in instrDexFilesRelativePaths:
                uninstrumentedFiles.append(dexFileRelativePath)
        return uninstrumentedFiles
    
    
    def _instrAndroidManifest(self, instrumenter, initAndroidManifest, instrAndroidManifest=None, addSdCardPermission=True):
        success = True
        try:
            instrumenter.instrumentAndroidManifestFile(initAndroidManifest, instrAndroidManifest, addSdCardPermission)
        except IllegalArgumentException as e:
            logger.error("Cannot instrument AndroidManifest file. %s" % e.msg)
            success = False
        except:
            logger.error("Cannot instrument AndroidManifest file!")
            success = False
        return success
    
    
    def _compileApk(self, compiler, fromDir, apkPath):
        success = True
        try:
            compiler.buildApk(fromDir, apkPath)
        except ApktoolBuildException as e:
            logger.error("Cannot build apk! %s" % e.msg)
            success = False
        except:
            logger.error("Cannot build apk!")
            success = False
        return success
    
    def _putAdditionalResources(self, apk, resources):
        zip_utils.zipdir(resources, apk)
    
    def _signApk(self, signer, unsignedApkFile, signedApkFile):
        success = True
        try:
            signer.signApk(unsignedApkFile, signedApkFile)
        except SignApkException as e:
            logger.error("Cannot sign apk! %s" % e.msg)
            success = False
        except:
            logger.error("Cannot sign apk!")
            success = False
        return success
            
    
    
    def _alignApk(self, aligner, unalignedApkFile, alignedApkFile):
        success = True
        try:
            aligner.alignApk(unalignedApkFile, alignedApkFile)
        except AlignApkException as e:
            logger.error("Cannot align apk! %s" % e.msg)
            success = False
        except:
            logger.error("Cannot align apk!")
            success = False
        return success
            
    
#     def _getMainDexFile(self, directory):
#         mainDexFile = os.path.join(directory, "classes.dex")
#         if not os.path.exists(mainDexFile):
#             logger.error("Cannot find classes.dex file!")
#             return (False, None)
#         
#         return (True, mainDexFile)
        
    def _getDexFiles(self, directory):
        dexFileNames = auxiliary_utils.searchFiles(where=directory, extension="dex")
        return dexFileNames
    
    def _getDexFilePathsRelativeToDir(self, target):
        dexFileRelativePaths = auxiliary_utils.searchFilesRelativeToDir(target=target, extension="dex")
        return dexFileRelativePaths
    
    
################################################################################
    
    def initAlreadyInstrApkEnv(self, pathToInstrApk, resultsDir, pathToInstrManifestFile=None):
        if not apk_utils.checkInputApkFile(pathToInstrApk):
            logger.error("Provided file [%s] is not a valid apk file!" % pathToInstrApk)
            return
        
        if not os.path.isdir(resultsDir):
            logger.error("Provided path to results dir [%s] do not point to dir!" % resultsDir)
            return
        
        coverageMetadataFolderPath = os.path.join(resultsDir, self.config.getCoverageMetadataRelativeDir())
        if not os.path.isdir(coverageMetadataFolderPath):
            logger.error("In the results dir [%s] there is no folder with coverage metadata!" % resultsDir)
            return
        self.coverageMetadataFolder = coverageMetadataFolderPath
        
        if self.config.getCoverageMetadataFilename() not in os.listdir(coverageMetadataFolderPath):
            logger.error("Cannot find metadata filename in the coverage metadata folder: %s!" % self.coverageMetadataFolder)
            return 
        
        self.coverageMetadataFile = os.path.join(self.coverageMetadataFolder, self.config.getCoverageMetadataFilename())
        
        #by default trying to look for a file in the 
        if pathToInstrManifestFile:
            androidManifestPath = pathToInstrManifestFile
        else:
            androidManifestPath = os.path.join(resultsDir, "AndroidManifest.xml")
        
        if not os.path.isfile(androidManifestPath):
            logger.warning("Path [%s] is not pointing to a real file! Leaving pointer to AndroidManifest.xml empty!" % androidManifestPath)
            return
        
        self.instrumentedApk = pathToInstrApk
        self.apkResultsDir = resultsDir
        self.runtimeReportsRootDir = self._createDir(resultsDir, self.config.getRuntimeReportsRelativeDir(), False, False)
        self.androidManifestFile = androidManifestPath
        
        self.androidManifest = AndroidManifest(self.androidManifestFile)
        self.packageName = self.androidManifest.getInstrumentationTargetPackage()
        self.runnerName = self.androidManifest.getInstrumentationRunnerName()
        
        self._bboxStateMachine.start(STATE_VALID_SETTINGS_PROVIDED)
        
    
    def installApkOnDevice(self):
        if not self._bboxStateMachine.isTransitionPossible(STATE_APK_INSTALLED):
            logger.error("Cannot install apk on device because the environment is not initialized!")
            return
        
        #selecting device for execution
        self.bboxExecutor.selectExecutionDevice()
        try:
            self.bboxExecutor.installApkOnDevice(self.instrumentedApk)
        except ApkCannotBeInstalledException as e:
            logger.error("Cannot install instrumented apk. %s" % e.msg)
            return
        self._bboxStateMachine.transitToState(STATE_APK_INSTALLED)
        
        
    
    def startTesting(self):
        if not self._bboxStateMachine.isTransitionPossible(STATE_APK_TEST_STARTED):
            logger.error("Cannot start testing apk on a device!")
            return
        
        self.deviceReportFolder = os.path.join(DEVICE_REPORT_FOLDER_PATH, self.packageName)
        self.bboxExecutor.selectExecutionDevice()
        self.bboxExecutor.startOndeviceTesting(packageName=self.packageName,
                                               runnerName=self.runnerName, 
                                               coverage=True,
                                               reportFolder=self.deviceReportFolder,
                                               proceedOnError=True,
                                               generateCoverageReportOnError=True)
        self._bboxStateMachine.transitToState(STATE_APK_TEST_STARTED)
        
        
    def stopTesting(self, localReportFolderName=None, paramsToWrite=None):
        if not self._bboxStateMachine.isTransitionPossible(STATE_APK_FINISHED_TESTING):
            logger.error("Cannot stop testing because it is not started!")
            return
        
#         currentDateTime = datetime.datetime.now()
#         reportTimePrefix = currentDateTime.strftime("%Y_%m_%d__%H_%M_%S")
#         coverageReportName = "%s___%s" % (reportTimePrefix, "coverage.ec")
#         reportFileOnDevice = "%s/%s" % (DEVICE_REPORT_FOLDER_PATH, coverageReportName)
        
#         reportLocally = os.path.join(self.runtimeReportsRootDir, coverageReportName)
        if not localReportFolderName:
            localReportFolderName="test"
        
        localReportFolder = self._createDir(self.runtimeReportsRootDir, localReportFolderName, True, False)
        
        self.bboxExecutor.stopOndeviceTesting(cancelAnalysis=False)
        
        time.sleep(3) #waiting for several seconds for report to be generated
        
#         success = self.bboxExecutor.getFileFromDevice(reportFileOnDevice, reportLocally)
        success = self.bboxExecutor.getFileFromDevice(self.deviceReportFolder, localReportFolder)

        if not success:
            self.bboxExecutor.removeFile(self.deviceReportFolder)
            return None
        
        if paramsToWrite:
            params_config = ConfigParser.ConfigParser()
            params_config.add_section(PARAMS_SECTION)
            for param in iteritems(paramsToWrite):
                params_config.set(PARAMS_SECTION, param[0], param[1])
            with open(os.path.join(localReportFolder, "parameters.txt"), "w") as param_file:
                params_config.write(param_file)
                
        self.bboxExecutor.removeFile(self.deviceReportFolder)
        self._bboxStateMachine.transitToState(STATE_APK_FINISHED_TESTING)
        return localReportFolder
    
    
    def generateReport(self, reportFiles=[], reportName=None, reportType=EMMA_REPORT.XML):
        if not reportFiles:
            logger.error("No report files are provided!")
            return
        
        self.bboxReporter.cleanMetaFiles()
        self.bboxReporter.cleanReportFiles()
       
        self.bboxReporter.addMetaFile(self.coverageMetadataFile)
        for rFile in reportFiles:
            self.bboxReporter.addReportFile(rFile)
        
        reportsRoot = os.path.join(self.apkResultsDir, self.config.getReportsRelativeDir())
        where = self._createReportResultsDir(reportsRoot, "report_%s" % reportType) 
        self.bboxReporter.generateEmmaReport(where, reportName, reportType)
    
    
    def _createReportResultsDir(self, reportsRoot, reportDirName):
        i = 0
        resultsDir = os.path.join(reportsRoot, reportDirName)
        while os.path.exists(resultsDir):
            i += 1
            resultsDir = os.path.join(reportsRoot, "%s_%d" % (reportDirName, i))
        
        auxiliary_utils.mkdir(path=resultsDir, mode=0777, overwrite=False)
        return resultsDir   

    def uninstallPackage(self):
        self.bboxExecutor.uninstallPackage(packageName=self.packageName, keepData=False)
        self._bboxStateMachine.stop()
    
    @staticmethod    
    def getCoverageReportsFromFolderWithPrefix(folder, prefix):
        if not os.path.exists(folder):
            return None
        
        reports = []
        for file in os.listdir(folder):
            if file.endswith(".ec") and file.startswith(prefix):
                reports.append(os.path.join(folder, file))
        
        return  reports
        
class ApkIsNotValidException(MsgException):
    '''
    Path is pointing on a non-valid apk-path
    '''

class IncorrectStateSequenceException(MsgException):
    '''
    The state sequence is incorrect.
    '''
    

#bboxcover = BBoxCoverage()
#print bboxcover._getDexFilePathsRelativeToDir("/home/yury/research_tmp/bboxtester/resultsRoot/Notepad/decompiled_apk/")
#bboxcover.initApkAnalysis(pathToApkFile = "/home/yury/research_tmp/bboxtester/Notepad.apk", overwriteExisting=False)
