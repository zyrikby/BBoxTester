import os
import commander


class Dex2JarInterface:
    def __init__(self, javaPath = "java", javaOpts = "-Xms512m -Xmx1024m", pathDex2JarLibs="./auxiliary/dex2jar/lib/", classDex2Jar="com.googlecode.dex2jar.tools.Dex2jarCmd", classApksign="com.googlecode.dex2jar.tools.ApkSign"):
        self.javaPath = javaPath
        self.javaOpts = javaOpts
        self.pathDex2JarLibs = pathDex2JarLibs
        self.classDex2Jar = classDex2Jar
        self.classApksign = classApksign
        self.classpath = self._createClassPath()
    
    def _createClassPath(self):
        classpathList = [os.path.join(self.pathDex2JarLibs,f) for f in os.listdir(self.pathDex2JarLibs) if '.jar' in f]
        return ":".join(classpathList)
    
    def _previewDex2JarCommand(self, className, parameters):
        cmd = "%s %s" % (className, parameters)
        return cmd
    
    def _runCommand(self, cmdString):
        cmd = "'%s' %s -classpath '%s' %s" % (self.javaPath, self.javaOpts, self.classpath, cmdString)
        return commander.runOnce(cmd)
    
    def _interpResultsDex2JarCmd(self, returnCode, outputStr):
        '''
        This function interprets the returnCode and outputStr obtained from 
        external process and returns if the run has been successful or not.
        Args:
            returnCode:
            outputStr:
        Returns:
            True, None: in case if the command has been executed correctly
            False, outputStr: otherwise
        '''
        retCode = "Return code is: %s" % returnCode
        #NOTE: later we can select different routines to process different errors
        if "java.lang.RuntimeException" in outputStr or returnCode:
            output = "%s\n%s" % (retCode, outputStr)
            return (False, output)
        return (True, None)
    
    def dex2jar(self, source, output=None, force=True, debug_info=True):
        '''
        Args:
            source:
            output:
            force:
        Returns:
        '''
        options=""
        if output:
            options += " -o '%s'" % output
        if force:
            options += " -f"
        if debug_info:
            options += " -d"
        
        opts = "%s '%s'" % (options, source)
        cmd = self._previewDex2JarCommand(self.classDex2Jar, opts)
        
        (returnCode, outputStr) = self._runCommand(cmd)
        
        return self._interpResultsDex2JarCmd(returnCode, outputStr)
    

    def _interpResultsApkSignCmd(self, returnCode, outputStr):
        '''
        This function interprets the returnCode and output obtained from 
        external process and returns if the run has been successful or not.
        Args:
            returnCode:
            output:
        Returns:
            True, None: in case if the command has been executed correctly
            False, output: otherwise
        '''
        retCode = "Return code is: %s" % returnCode
        #NOTE: later we can select different routines to process different errors
        if "java.lang.RuntimeException" in outputStr or returnCode:
            output = "%s\n%s" % (retCode, outputStr)
            return (False, output)
        return (True, None)
    
    
    def apkSign(self, source, output=None, force=True):
        options=""
        if output:
            options += " -o '%s'" % output
        if force:
            options += " -f"
        
        opts = "%s %s" % (options, source)
        cmd = self._previewDex2JarCommand(self.classApksign, opts)
        (returnCode, outputStr) = self._runCommand(cmd)
        
        return self._interpResultsApkSignCmd(returnCode, outputStr)


    
