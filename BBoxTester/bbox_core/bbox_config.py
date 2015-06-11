import os
import ConfigParser
from utils import auxiliary_utils


DEFAULT_CONFIG= {
    "GENERAL" : {
            "DECOMPILED_APK_RELATIVE_DIR" : "decompiled_apk",
            "COVERAGE_METADATA_RELATIVE_DIR" : "coverage_metadata",
            "COVERAGE_METADATA_FILENAME"  : "coverage.em",
            "REPORTS_RELATIVE_DIR" : "reports",
            "RUNTIME_REPORTS_RELATIVE_DIR" : "runtime_reports",
            "TMP_JAR_RELATIVE_DIR" : "jars",
            "INSTRUMENTED_FILES_RELATIVE_DIR" : "instrumented",
            "INSTRUMENTED_FILE_SUFFIX" : "_instr",
            "FINAL_INSTRUMENTED_FILE_SUFFIX" : "_instr_final",
            "SIGNED_FILE_SUFFIX" : "_signed",
            "ALIGNED_FILE_SUFFIX" : "_aligned",
#             "DELETE_TMP_DIR" : "False",
        },
    "AAPT" : {
            "AAPT_DIR" : "./auxiliary/aapt",
            "AAPT_EXECUTABLE" : "aapt", 
        },
    "APKTOOL" : {
            "APKTOOL_JAVA_PATH" : "java", # it is possible that some tools will require different versions of java
            "APKTOOL_JAVA_OPTS" : "-Xms512m -Xmx1024m",    
            "APKTOOL_PATH" : "./auxiliary/apktool",
            "APKTOOL_JAR"  : "apktool.jar",
            "APKTOOL_QUITE" : "True"
        },
    "DEX2JAR" : {
            "DEX2JAR_JAVA_PATH" : "java",
            "DEX2JAR_JAVA_OPTS" : "-Xms512m -Xmx1024m",
            "DEX2JAR_LIBS_PATH" : "./auxiliary/dex2jar/lib",
            "DEX2JAR_CLASS_DEX2JAR" : "com.googlecode.dex2jar.tools.Dex2jarCmd",
            "DEX2JAR_CLASS_APKSIGN" : "com.googlecode.dex2jar.tools.ApkSign",
            #"DEX2JAR_" : "",
            #"DEX2JAR_" : "",
        },
    "DX" : {
            "DX_JAVA_PATH" : "java",
            "DX_JAVA_OPTS" : "-Xms512m -Xmx1024m",
            "DX_PATH" : "./auxiliary/dx",
            "DX_JAR"  : "dx.jar"
        },
    "EMMA" : {
            "EMMA_JAVA_PATH" : "java",
            "EMMA_JAVA_OPTS" : "-Xms512m -Xmx1024m",
            "EMMA_DIR" : "./auxiliary/emma",
            "EMMA_JAR"  : "emma.jar", 
            "EMMA_DEVICE_JAR" : "emma_device.jar",
            "EMMA_RESOURCES_DIR" : "./auxiliary/emma/resources",
            "ANDROID_SPECIFIC_INSTRUMENTATION_CLASSES_PATH": "./auxiliary/instrument_classes/", #trailing slash is important
        },
    "ZIPALIGN" : {
            "ZIPALIGN_DIR" : "./auxiliary/zipalign",
            "ZIPALIGN_EXE" : "zipalign",
        },
}

class BBoxConfig:
    def __init__(self, pathToConfigFile="./config/bbox_config.ini"):
        #TODO: May be it's worth to add check if path is None or exist
        self.config = ConfigParser.ConfigParser()
        read_files = self.config.read(pathToConfigFile)
        self.isRealFile = False
        if read_files: #file is read
            self.isRealFile = True
    
    
    
#     #GENERAL
#     def deleteTmpDirAfterInstrumentation(self):
#         section = "GENERAL"
#         option = "DELETE_TMP_DIR"
#         return auxiliary_utils.to_bool(self._getOption(section, option))
    
    def getDecompiledApkRelativeDir(self):
        section = "GENERAL"
        option = "DECOMPILED_APK_RELATIVE_DIR"
        return self._getOption(section, option)
    
    def getCoverageMetadataRelativeDir(self):
        section = "GENERAL"
        option = "COVERAGE_METADATA_RELATIVE_DIR"
        return self._getOption(section, option)
    
    def getCoverageMetadataFilename(self):
        section = "GENERAL"
        option = "COVERAGE_METADATA_FILENAME"
        return self._getOption(section, option)
    
    def getReportsRelativeDir(self):
        section = "GENERAL"
        option = "REPORTS_RELATIVE_DIR"
        return self._getOption(section, option)
    
    def getRuntimeReportsRelativeDir(self):
        section = "GENERAL"
        option = "RUNTIME_REPORTS_RELATIVE_DIR"
        return self._getOption(section, option)
    
    def getInstrumentedFilesRelativeDir(self):
        section = "GENERAL"
        option = "INSTRUMENTED_FILES_RELATIVE_DIR"
        return self._getOption(section, option)
    
    def getTmpJarRelativeDir(self):
        section = "GENERAL"
        option = "TMP_JAR_RELATIVE_DIR"
        return self._getOption(section, option)
    
    def getInstrFileSuffix(self):
        section = "GENERAL"
        option = "INSTRUMENTED_FILE_SUFFIX"
        return self._getOption(section, option)
    
    def getFinalInstrFileSuffix(self):
        section = "GENERAL"
        option = "FINAL_INSTRUMENTED_FILE_SUFFIX"
        return self._getOption(section, option)
    
    def getSignedFileSuffix(self):
        section = "GENERAL"
        option = "SIGNED_FILE_SUFFIX"
        return self._getOption(section, option)
    
    def getAlignedFileSuffix(self):
        section = "GENERAL"
        option = "ALIGNED_FILE_SUFFIX"
        return self._getOption(section, option)
    
 
    
    #AAPT
    def getAaptDir(self):
        section = "AAPT"
        option = "AAPT_DIR"
        return self._getOption(section, option)
    
    def getAaptExecutable(self):
        section = "AAPT"
        option = "AAPT_EXECUTABLE"
        return self._getOption(section, option)
    
    def getAaptPath(self):
        return os.path.join(self.getAaptDir(), self.getAaptExecutable())
    
    
    
    #APKTOOL    
    def getApktoolJavaPath(self):
        section = "APKTOOL"
        option = "APKTOOL_JAVA_PATH"
        return self._getOption(section, option)
    
    def getApktoolJavaOpts(self):
        section = "APKTOOL"
        option = "APKTOOL_JAVA_OPTS"
        return self._getOption(section, option)
    
    def getApktoolPath(self):
        section = "APKTOOL"
        option = "APKTOOL_PATH"
        return self._getOption(section, option)
    
    def getApktoolJar(self):
        section = "APKTOOL"
        option = "APKTOOL_JAR"
        return self._getOption(section, option)
    
    def getQuiteOptionValue(self):
        section = "APKTOOL"
        option = "APKTOOL_QUITE"
        return self._getOption(section, option)
    
    
    
    #DEX2JAR
    def getDex2JarJavaPath(self):
        section = "DEX2JAR"
        option = "DEX2JAR_JAVA_PATH"
        return self._getOption(section, option)
    
    def getDex2JarJavaOpts(self):
        section = "DEX2JAR"
        option = "DEX2JAR_JAVA_OPTS"
        return self._getOption(section, option)
    
    def getDex2LibsPath(self):
        section = "DEX2JAR"
        option = "DEX2JAR_LIBS_PATH"
        return self._getOption(section, option)
    
    def getDex2JarClassForDex2Jar(self):
        section = "DEX2JAR"
        option = "DEX2JAR_CLASS_DEX2JAR"
        return self._getOption(section, option)
    
    def getDex2JarClassForApksign(self):
        section = "DEX2JAR"
        option = "DEX2JAR_CLASS_APKSIGN"
        return self._getOption(section, option)
    
    
    
    #DX  
    def getDxJavaPath(self):
        section = "DX"
        option = "DX_JAVA_PATH"
        return self._getOption(section, option)
    
    def getDxJavaOpts(self):
        section = "DX"
        option = "DX_JAVA_OPTS"
        return self._getOption(section, option)
    
    def getDxPath(self):
        section = "DX"
        option = "DX_PATH"
        return self._getOption(section, option)
    
    def getDxJar(self):
        section = "DX"
        option = "DX_JAR"
        return self._getOption(section, option)
    
    
    
    #EMMA  
    def getEmmaJavaPath(self):
        section = "EMMA"
        option = "EMMA_JAVA_PATH"
        return self._getOption(section, option)
    
    def getEmmaJavaOpts(self):
        section = "EMMA"
        option = "EMMA_JAVA_OPTS"
        return self._getOption(section, option)
    
    def getEmmaDir(self):
        section = "EMMA"
        option = "EMMA_DIR"
        return self._getOption(section, option)
    
    def getEmmaJar(self):
        section = "EMMA"
        option = "EMMA_JAR"
        return self._getOption(section, option)
    
    def getEmmaDeviceJar(self):
        section = "EMMA"
        option = "EMMA_DEVICE_JAR"
        return self._getOption(section, option)
    
    def getEmmaResourcesDir(self):
        section = "EMMA"
        option = "EMMA_RESOURCES_DIR"
        return self._getOption(section, option)
    
    def getAndroidSpecificInstrumentationClassesPath(self):
        section = "EMMA"
        option = "ANDROID_SPECIFIC_INSTRUMENTATION_CLASSES_PATH"
        return self._getOption(section, option)
    
    
    
    #ZIPALIGN
    def getZipalignDir(self):
        section = "ZIPALIGN"
        option = "ZIPALIGN_DIR"
        return self._getOption(section, option)
    
    def getZipalingExe(self):
        section = "ZIPALIGN"
        option = "ZIPALIGN_EXE"
        return self._getOption(section, option)
    
    
    #AUXILIARY METHODS
    def _getOption(self, section, option):
        value = self._getOptionFromConfigFile(section, option)
        if not value:
            value = DEFAULT_CONFIG[section][option]
        return value
     
    def _getOptionFromConfigFile(self, section, option):
        value = None
        if self.isRealFile:
            try:
                value = self.config.get(section, option)
            except:
                value = None
        return value


    
    