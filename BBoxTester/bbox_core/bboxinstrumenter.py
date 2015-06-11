'''
Created on Sep 30, 2014

@author: Yury Zhauniarovich <y.zhalnerovich{at}gmail.com>
'''

import os

from bbox_core.general_exceptions import MsgException
from bbox_core.bbox_config import BBoxConfig
from interfaces.apktool_interface import ApktoolInterface
from interfaces.dex2jar_interface import Dex2JarInterface
from interfaces.dx_interface import DxInterface
from interfaces.emma_interface import EMMA_MERGE, EMMA_OUTMODE, EmmaInterface
from interfaces.zipalign_interface import ZipalignInterface
from utils.android_manifest import AndroidManifest, \
    ManifestAlreadyInstrumentedException
from utils.auxiliary_utils import ensureDirExists
from utils.zip_utils import zipdir
import shutil


class BBoxInstrumenter:
    def __init__(self, config):
        self.config = config
    
#     def setConfig(self, config):
#         '''
#         Specify config for BBoxInstrumenter class.
#         
#         Args:
#             :param config: Reference to BBoxConfig object or
#                 path to a config file.
#         '''
#         if isinstance(config, BBoxConfig):
#             self.config = config
#         elif isinstance(config, basestring):
#             self.config = BBoxConfig(config)
#         else:
#             self.config = BBoxConfig()
# #         else:
# #             raise NotValidConfigError("Provided config parameter is neither a valid path to a config file nor a valid BBoxConfig object!")
    
    
    def decompileApk(self, pathToApk, dirToDecompile):
        '''
        Using Apktool tries to decompile an apk file. Currently decompile only resources
        (required to decompile AndroidManifest.xml).
        
        Args:
            :param pathToApk: path to a valid apk file that needs to be
                decompiled
            :param dirToDecompile: path to a dir where the result of the
                decompile process will be stored
        
        Returns:
        
        Raises:
            ApkCannotBeDecompiledException: if the provided apk file cannot be decompiled.
        '''
        ensureDirExists(dirToDecompile)
        apktool = ApktoolInterface(javaPath = self.config.getApktoolJavaPath(),
                                   javaOpts = self.config.getApktoolJavaOpts(),
                                   pathApktool = self.config.getApktoolPath(),
                                   jarApktool = self.config.getApktoolJar())
        
        (successfulRun, cmdOutput) = apktool.decode(apkPath = pathToApk,
                                          dirToDecompile = dirToDecompile,
                                          quiet = True,
                                          noSrc = True,
                                          noRes = False,
                                          debug = False,        #maybe true to enable debugging
                                          noDebugInfo = False,  #check this 
                                          force = True, #directory exist so without this this process finishes
                                          frameworkTag = "",
                                          frameworkDir = "",
                                          keepBrokenRes = True)
        
        if not successfulRun:
            err = "Cannot decompile file: [%s] into dir [%s]. ERRSTR: %s" % (pathToApk, dirToDecompile, cmdOutput)
            raise ApkCannotBeDecompiledException(err)
        
    
    
    def convertDex2Jar(self, dexFile, jarFile, overwrite = True):
        #TODO: Check how dex2jar behaves in case if force = false and file exists
        '''
        Converts the provided dex file into jar file using dex2jar utility.
        
        Args:
            :param dexFile: the path to a dex file that needs to be converted
            :param jarFile: the path to a file jar file that will be converted to 
            :param override: if True - override the destination jar file if exists
            
        Returns:
        
        Raises:
            Dex2JarConvertionError: if the provided dex file cannot be converted to jar. 
        '''
        dex2jar = Dex2JarInterface(javaPath = self.config.getDex2JarJavaPath(),
                                   javaOpts = self.config.getDex2JarJavaOpts(),
                                   pathDex2JarLibs = self.config.getDex2LibsPath(),
                                   classDex2Jar = self.config.getDex2JarClassForDex2Jar(),
                                   classApksign = self.config.getDex2JarClassForApksign())
        
        (successfulRun, cmdOutput) = dex2jar.dex2jar(source = dexFile, 
                                                     output = jarFile, 
                                                     force = overwrite)
        
        if not successfulRun:
            err = "Cannot convert dex [%s] into jar file [%s]. ERRSTR: %s" % (dexFile, cmdOutput)
            raise Dex2JarConvertionError(err)
        
    
    
    def convertDex2JarFiles(self, dexFileNames, outputFolder, overwrite=True, proceedOnError=True):
        '''
        Converts provided dex files into the specified folder. Returns the map
        that shows the correspondence between successfully converted dex files
        and jar files.
        
        Args:
            :param dexFileNames: list of files that need to be converted to
                corresponding jar files
            :param outputFolder: the path to the folder where the results of the
                convertion will be placed
            :param override: override jar file in the output folder if it exists
            :param proceedOnError: if True - proceed converting provided files
                even if an error during a file convertion occurred. The entry
                with dex and jar file, where an error occurred, will not be
                included into the final map. 
        
        Returns:
            dex2jarCorrespondence: tuple that reflects the correspondence between successfully
                converted dex and jar files.
        '''
        ensureDirExists(outputFolder)
        dex2jarCorrespondence = []
        for dexFile in dexFileNames:
            jarFilename = os.path.splitext(os.path.basename(dexFile))[0] + ".jar"
            jarFile = os.path.join(outputFolder, jarFilename)
            try:
                self.convertDex2Jar(dexFile, jarFile, overwrite)
            except Dex2JarConvertionError:
                if proceedOnError:
                    continue
                else:
                    raise
            dex2jarTuple = (dexFile, jarFile)
            dex2jarCorrespondence.append(dex2jarTuple) 
            
        return dex2jarCorrespondence 
    
    def convertDex2JarFilesWithRelativePaths(self, dexRootDir, dexFileNames, jarFilesRootDir, overwrite=True, proceedOnError=True):
        '''
        Converts provided dex files with relative paths into the specified 
        folder. Returns a list containing tuples that show the correspondence 
        between successfully converted dex files  and jar files (relative paths).
        
        Args:
            :param dexRootDir: root dir for dex files
            :param dexFileNames: list of dex file paths against dexRootDir that need
                to be converted to corresponding jar file
            :param jarFilesRootDir: the path to the folder where the results of the
                convertion will be placed
            :param override: override jar file in the output folder if it exists
            :param proceedOnError: if True - proceed converting provided files
                even if an error during a file convertion occurred. The entry
                with dex and jar file, where an error occurred, will not be
                included into the final map 
        
        Returns:
            dex2jarRelativeCorrespondence: list of tuples that reflect 
            the correspondence between successfully converted dex and jar files
        '''
        ensureDirExists(jarFilesRootDir)
        dex2jarRelativeCorrespondence = []
        for dexFileRelative in dexFileNames:
            dexFileFull = os.path.join(dexRootDir, dexFileRelative)
            jarFileRelative = os.path.splitext(dexFileRelative)[0] + ".jar"
            jarFileFull = os.path.join(jarFilesRootDir, jarFileRelative)
            try:
                self.convertDex2Jar(dexFileFull, jarFileFull, overwrite)
            except Dex2JarConvertionError:
                if proceedOnError:
                    continue
                else:
                    raise
            dex2jarRelativeTuple = (dexFileRelative, jarFileRelative)
            dex2jarRelativeCorrespondence.append(dex2jarRelativeTuple) 
            
        return dex2jarRelativeCorrespondence  

    
    def convertJar2Dex(self, jarFile, dexFile, withFiles=[], overwrite=True):
        '''
        Converts the provided jar file into dex file using dx utility.
        
        Args:
            :param jarFile: the path to a jar file that needs to be converted
            :param dexFile: the path to the file, to which jarFile will be 
                converted to 
            :param withFiles: additional files that need to be included into the
                final dex file
            :param override: if True - override the destination jar file if 
                exists
            
        Returns:
        
        Raises:
            Jar2DexConvertionError: if the provided files cannot be converted to jar. 
        '''
        dx = DxInterface(javaPath = self.config.getDxJavaPath(),
                         javaOpts = self.config.getDxJavaOpts(),
                         pathDx = self.config.getDxPath(),
                         jarDx = self.config.getDxJar())
        
        filesToConvert = []
        filesToConvert.append(jarFile)
        filesToConvert.extend(withFiles)
        
        # dx does not create folder. Thus, if you specify the folder that do not exist
        # dx tool will not create it and you will receive and error. This can be corrected by 
        # adding additional code for folder creation 
        (successfulRun, cmdOutput) = dx.dex(inFiles = filesToConvert,
                                            output = dexFile,
                                            noLocals = True)
        if not successfulRun:
            err = "Cannot convert jar [%s] to dex [%s]. ERRSTR: %s" % (jarFile, dexFile, cmdOutput)
            raise Jar2DexConvertionError(err)
    
    
    def convertJar2DexFiles(self, jarFiles, outputFolder, withFiles=[], overwrite=True, proceedOnError=True):
        '''
        Converts provided jar files into dex files to the specified folder. 
        Returns the map that shows the correspondence between successfully 
        converted jar files and dex files.
        
        Args:
            :param jarFiles: list of jar files that are required to be converted
                to dex files
            :param outputFolder: the path to the folder where to store the
                resulting dex files
            :param withFiles: additional files that need to be included into the
                final dex file
            :param override: if True - override the destination jar file if 
                exists
            :param proceedOnError: if True - proceed converting provided files
                even if an error during a file convertion occurred. The entry
                with dex and jar file, where an error occurred, will not be
                included into the final map.
        
        Returns:
            jar2dexMap: map that reflects the correspondence between 
                successfully converted jar and dex files.
        '''
        ensureDirExists(outputFolder)
        jar2dexMap = {}
        for jarFile in jarFiles:
            dexFilename = os.path.splitext(os.path.basename(jarFile))[0] + ".dex"
            dexFile = os.path.join(outputFolder, dexFilename)
            try:
                self.convertJar2Dex(jarFile, dexFile, withFiles, overwrite)
            except Jar2DexConvertionError:
                if proceedOnError:
                    continue
                else:
                    raise
            jar2dexMap[jarFile] = dexFile 
            
        return jar2dexMap   
    
    
    def instrumentJarWithEmma(self, jarFile, outputFolder, emmaMetadataFile):
        '''
        Instruments provided jar file with Emma code coverage tool code. The
        resulting emmaMetadataFile is create with merge==yes, i.e., if the file
        exists the information about instrumentation will be merged with the 
        existing data. Only instrumented jar files will be copied to the
        outputFolder. 
        
        Args:
            :param jarFile: a jar file to instrument
            :param outputFolder: where to store instrumented file
            :param emmaMetadataFile: path to the file with emma instrumentation
                results
        '''
        ensureDirExists(outputFolder)
        emma = EmmaInterface(javaPath = self.config.getEmmaJavaPath(),
                             javaOpts = self.config.getEmmaJavaOpts(),
                             pathEmma = self.config.getEmmaDir(),
                             jarEmma = self.config.getEmmaJar(),
                             jarEmmaDevice = self.config.getEmmaDeviceJar())
        
        (successfulRun, cmdOutput) = emma.instr(instrpaths = [jarFile],
                                      outdir = outputFolder,
                                      emmaMetadataFile = emmaMetadataFile,
                                      merge = EMMA_MERGE.YES,
                                      outmode = EMMA_OUTMODE.FULLCOPY)
        if successfulRun:
            #emma put instrumented jar files into lib folder so we need to move
            #them back to the output folder and delete
            jarsOutDir = os.path.join(outputFolder, "lib")
            for filename in os.listdir(jarsOutDir):
                shutil.move(os.path.join(jarsOutDir, filename), os.path.join(outputFolder, filename))
            shutil.rmtree(jarsOutDir)
            return
        
        if not successfulRun:
            err = "Cannot instrument jar file [%s] with Emma. %s" % (jarFile, cmdOutput)
            raise EmmaCannotInstrumentException(err)
    
    
    
    #TODO: Maybe we need a method to instrument a number of jar files
#     def _instrumentJarFilesWithEmma(self, jarFiles):
#         self.emFileName = os.path.join(self.coverageReportsDir, "coverage.em")
#         (result, output) = self.emma.instr(instrpaths=jarFiles, outdir=self.tmpJarPath, outfile=self.emFileName, merge=EMMA_MERGE.NO, outmode=EMMA_OUTMODE.OVERWRITE)
#         if not result:
#             logger.error(output)
#             raise EmmaCannotInstrumentException()
    
    
    def instrumentAndroidManifestFile(self, pathToUnmodifiedFile, pathToModifiedFile=None, addSdCardPermission=True):
        '''
        Adds instrumentation tag with predefined attributes corresponding to our
        instrumentation classes to the provided manifest file. If 
        instrumentation tag exists, this method substitutes it with appropriate
        one. Adds (if necessary) to the provided AndroidManifest file permission
        to write to the external storage.
        
        Args:
            :param pathToUnmodifiedFile: path to the unmodified 
                AndroidManifest.xml file
            :param pathToModifiedFile: path where to store modified
                AndroidManifest.xml file. If pathToModifiedFile==None, the 
                initial pathToUnmodifiedFile will be overridden.
        '''
        if not os.path.isfile(pathToUnmodifiedFile):
            raise IllegalArgumentException("File [%s] does not exist!" % pathToUnmodifiedFile) 
        androidManifest = AndroidManifest(pathAndroidManifest=pathToUnmodifiedFile)
        packageName = androidManifest.getPackageName()
        #TODO: think how to substitute these constants later
        try:
            androidManifest.addInstrumentation("com.zhauniarovich.bbtester.EmmaInstrumentation", packageName)
        except ManifestAlreadyInstrumentedException:
            #removing all existing instrumentation tags and creating our new
            androidManifest.removeExistingInstrumentation() #TODO: this can throw an exception
            androidManifest.addInstrumentation("com.zhauniarovich.bbtester.EmmaInstrumentation", packageName)
        
        if addSdCardPermission:
            androidManifest.addUsesPermission("android.permission.WRITE_EXTERNAL_STORAGE")
        
        if not pathToModifiedFile or (pathToUnmodifiedFile == pathToModifiedFile):
            androidManifest.exportManifest(path=None)
        else: 
            androidManifest.exportManifest(path=pathToModifiedFile)
        
    
    def addResourcesToApk(self, pathToApk, pathToResourcesBaseDir):
        '''
        Adds directory tree with files into the apk file.
        
        Args:
            :param pathToApk: path to the apk file
            :param pathToResourcesBaseDir: path to the base folder where the
            resources are stored
        '''
        zipdir(basedir = pathToResourcesBaseDir, archivename = pathToApk)
    
    
    def buildApk(self, sourceFolder, destinationApk, force=True):
        #TODO: Maybe it's worth to check later how the apktool behaves in case
        #      if force = False
        '''
        Builds an apk file from the provided folder path.
        
        Args:
        :param sourceFolder: base directory which contains decompiled files of 
            an apk file
        :param destinationApk: the path to the apk file that will be obtained as
            a result of the compilation
        :param force: if True - rewrite apk file if it is exists
        '''
        apktool = ApktoolInterface(javaPath = self.config.getApktoolJavaPath(),
                                   javaOpts = self.config.getApktoolJavaOpts(),
                                   pathApktool = self.config.getApktoolPath(),
                                   jarApktool = self.config.getApktoolJar())
        
        (successfulRun, cmdOutput) = apktool.build(srcPath = sourceFolder,
                                                   finalApk = destinationApk,
                                                   quiet = True,
                                                   forceAll = force,
                                                   debug = False,     #maybe true but I did not change
                                                   aaptPath=self.config.getAaptPath())
        
        if not successfulRun:
            err = "Cannot build apk file [%s] from folder [%s] using apktool. ERRSTR: %s" % (destinationApk, sourceFolder, cmdOutput)
            raise ApktoolBuildException(err)
    
        
    def signApk(self, unsignedApk, signedApk, force=True):
        dex2jar = Dex2JarInterface(javaPath = self.config.getDex2JarJavaPath(),
                                   javaOpts = self.config.getDex2JarJavaOpts(),
                                   pathDex2JarLibs = self.config.getDex2LibsPath(),
                                   classDex2Jar = self.config.getDex2JarClassForDex2Jar(),
                                   classApksign = self.config.getDex2JarClassForApksign())
        
        (successfulRun, cmdOutput) = dex2jar.apkSign(source=unsignedApk,
                                                     output=signedApk,
                                                     force=force)
        if not successfulRun:
            err = "Cannot sign apk file [%s]. ERRSTR: %s" % (unsignedApk, cmdOutput)
            raise SignApkException(err)
        
    
    def alignApk(self, unalignedApk, alignedApk, force=True):
        zipalign = ZipalignInterface(dirZipalign=self.config.getZipalignDir(),
                                     exeZipalign=self.config.getZipalingExe())
        
        (successfulRun, cmdOutput) = zipalign.align(inFile=unalignedApk,
                                                    outFile=alignedApk,
                                                    alignment=4,
                                                    verbose=False,
                                                    overwrite=True)
        if not successfulRun:
            err = "Cannot align apk file [%s]. ERRSTR: %s" % (unalignedApk, cmdOutput)
            raise AlignApkException(err)
        
#     def instrumentApk(self):
#         #decompiling
#         #TODO: Add parameters
#         self.decompileApk()
#         
#         #converting dex to jar
#         self.dexFileNames = self._getDexFiles(self.decompiledApkDir)
#         self._convertDex2Jar(self.dexFileNames)
#         
#         #emma instrumentation
#         jarFiles = self.jar2dexFiles.keys()
#         self._instrumentJarFilesWithEmma(jarFiles)
#         
#         #convert back to dex
#         self._convertJar2Dex(jarFiles)
#         
#         #instrument manifest file
#         self._instrumentManifestFile()
# 
#         #build apk file
#         self._buildApk()
#         
#         #add emma resource to dir
#         self._addEmmaResourcesToApk()
#         
#         
#         #sign apk file
#         self._signApkFile()
#         #align apk file   
    


#Exceptions
class NotValidConfigError(MsgException):
    '''
    Provided config parameter is neither a valid path to a config file nor a valid BBoxConfig object.
    '''

class ApkCannotBeDecompiledException(MsgException):
    '''
    Provided apk file cannot be decompiled. 
    '''

class Dex2JarConvertionError(MsgException):
    '''
    Provided dex file cannot be converted to a jar file.
    '''

class Jar2DexConvertionError(MsgException):
    '''
    Provided jar file cannot be converted to a dex file.
    '''

class EmmaCannotInstrumentException(MsgException):
    '''
    Provided files cannot be instrumented with Emma.
    '''
    
class ApktoolBuildException(MsgException):
    '''
    Provided folder cannot be converted to an apk file.
    '''
    
class SignApkException(MsgException):
    '''
    Provided apk file cannot be signed.
    '''

class AlignApkException(MsgException):
    '''
    Provided apk file cannot be aligned.
    '''

class IllegalArgumentException(MsgException):
    '''
    Incorrect parameter argument.
    '''
    