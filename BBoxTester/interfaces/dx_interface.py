import os
import commander


class DxInterface:
    def __init__(self, javaPath = "java", javaOpts = "-Xms512m -Xmx1024m", pathDx = "./auxiliary/dx/", jarDx="dx.jar"):
        self.javaPath = javaPath
        self.javaOpts = javaOpts
        self.pathDx = pathDx
        self.jarDx = jarDx


    def _previewDexCmd(self, action, options):
        path = os.path.join(self.pathDx, self.jarDx)
        cmd = "%s %s %s" % (path, action, options)
        return cmd
    
    
    def _interpResultsDexCmd(self, returnCode, outputStr):
        retCode = "Return code is: %s" % returnCode
        #NOTE: later we can select different routines to process different errors
        if returnCode:
            output = "%s\n%s" % (retCode, outputStr)
            return (False, output)
        return (True, None)
    
    
    def dex(self, inFiles, output, noLocals=False):
        """
        There are a number of other options of dx tool. However, here we do not
        use them, because we do not need them
        """
        options = ""
        if noLocals:
            options += " --no-locals"
        
        # TODO: dx does not create folder. Thus, if you specify the folder that do not exist
        # dx tool will not create it and you will receive and error. This can be corrected by 
        # adding additional code for folder creation 
        options += " --output='" + output + "'"
        
        options += " "
        for inFile in inFiles:
            options += "'" + inFile + "' "
        
        dexCmd = self._previewDexCmd("--dex", options)
        (result_code, outputStr) = self._runDxCommand(dexCmd)
        
        return self._interpResultsDexCmd(result_code, outputStr)
        
    
    def _runDxCommand(self, commandString):
        cmd = "'%s' %s -jar %s" % (self.javaPath, self.javaOpts, commandString)
        return commander.runOnce(cmd)
    
