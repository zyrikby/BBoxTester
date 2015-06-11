import os
import commander

class EMMA_OUTMODE:
    COPY = "copy"
    OVERWRITE = "overwrite"
    FULLCOPY = "fullcopy"

class EMMA_MERGE:
    YES  = "yes"
    NO   = "no"

class EMMA_REPORT:
    HTML = "html"
    TXT = "txt"
    XML = "xml"

class EmmaInterface:
    def __init__(self, javaPath="java", javaOpts="-Xms512m -Xmx1024m", pathEmma="./auxiliary/emma/", jarEmma="emma.jar", jarEmmaDevice="emma_device.jar"):
        self.javaPath = javaPath
        self.javaOpts = javaOpts
        self.pathEmma = pathEmma
        self.jarEmma = jarEmma
        self.jarEmmaDevice = jarEmmaDevice
    
    def _runEmmaCommand(self, commandString):
        cmd = "'%s' %s -cp %s" % (self.javaPath, self.javaOpts, commandString)
        return commander.runOnce(cmd)
    

    def _previewEmmaCmd(self, action, options):
        path = os.path.join(self.pathEmma, self.jarEmma)
        cmd = "'%s' %s %s" % (path, action, options)
        return cmd
    
    
    def _interpResultsEmmaInstrCmd(self, returnCode, outputStr):
        retCode = "Return code is: %s" % returnCode
        #NOTE: later we can select different routines to process different errors
        if returnCode == 1:
            output = "%s\n%s\n%s" % (retCode, "Failure due to incorrect option usage. This error code is also returned when command line usage (-h) is requested explicitly.", outputStr)
            return (False, output)
        if returnCode == 2:
            output = "%s\n%s\n%s" % (retCode, "Unknown failure happened.", outputStr)
            return (False, output)
        return (True, None)
    
    
    def getEmmaDeviceJarPath(self):
        path = os.path.join(self.pathEmma, self.jarEmmaDevice)
        return path
    
    def instr(self, instrpaths=[], outdir=None, emmaMetadataFile=None, merge=EMMA_MERGE.YES, outmode=EMMA_OUTMODE.COPY, commonOptions={}, filters=[]):
        '''
        The command line interface can be found here: http://emma.sourceforge.net/reference/ch02s03s03.html
        Args:
            :param instrpaths:
            :param outdir:
            :param emmaMetadataFile:
            :param merge:
            :param outmode:
            :param filters:
        
        Returns:
        '''
        options = ""
        if instrpaths:
            options += " -instrpath "
            for pth in instrpaths:
                options += "'%s'," % pth
            options = options[0:-1]
        
        if outdir:
            options += " -outdir '%s'" % outdir
        
        if emmaMetadataFile:
            options +=  " -outfile '%s'" % emmaMetadataFile
        
        options += " -merge %s" % merge
        options += " -outmode %s" % outmode
        
        if commonOptions:
            for entry in commonOptions.iteritems():
                options += " -D%s=%s" % entry
        
        if filters:
            options += " -filter "
            for fltr in filters:
                options += "%s," % fltr
            options = options[0:-1]
        
        cmd = self._previewEmmaCmd("emma instr", options)
        (returnCode, outputStr) = self._runEmmaCommand(cmd)
        
        return self._interpResultsEmmaInstrCmd(returnCode, outputStr)
    
    
    def _interpResultsEmmaReportCmd(self, returnCode, outputStr):
        retCode = "Return code is: %s" % returnCode
        #NOTE: later we can select different routines to process different errors
        if returnCode == 1:
            output = "%s\n%s\n%s" % (retCode, "Failure due to incorrect option usage. This error code is also returned when command line usage (-h) is requested explicitly.", outputStr)
            return (False, output)
        if returnCode == 2:
            output = "%s\n%s\n%s" % (retCode, "Unknown failure happened.", outputStr)
            return (False, output)
        return (True, None)
    
    
    def report(self, inputs=[], report=EMMA_REPORT.HTML, sourcepath=[], commonOptions={}):
        '''
        The description of the command can be found here: http://emma.sourceforge.net/reference/ch02s04s03.html
        :param inputs:
        :param report:
        :param sourcepath:
        :param commonOptions:
        '''
        """Genoptions can be seen here: http://emma.sourceforge.net/reference/ch03s02.html#prop-ref.report.out.file"""
        options = ""
        if inputs:
            options += " -input "
            for f in inputs:
                options += f + ","
            options = options[0:-1]
        
        options += " -report " + report
        
        if sourcepath:
            options +=  " -sourcepath "
            for src in sourcepath:
                options += src + ","
            options = options[0:-1]
        
        if commonOptions:
            for entry in commonOptions.iteritems():
                options += " -D" + entry[0] + "=" + entry[1]
        
        cmd = self._previewEmmaCmd("emma report", options)
        (returnCode, outputStr) = self._runEmmaCommand(cmd)
        return self._interpResultsEmmaReportCmd(returnCode, outputStr)
    
    def reportToDir(self, inputs=[], toDir=None, report=EMMA_REPORT.HTML, sourcepath=[], commonoptions={}):
        '''
        This method produce a report into the specified directory.
        
        Args:
            :param inputs:
            :param toDir:
            :param report:
            :param sourcepath:
            :param commonoptions:
        
        Returns:
        '''
        options = ""
        if inputs:
            options += " -input "
            for f in inputs:
                options += f + ","
            options = options[0:-1]
        
        options += " -report " + report
        
        if sourcepath:
            options +=  " -sourcepath "
            for src in sourcepath:
                options += src + ","
            options = options[0:-1]
        
        if toDir:
            if report == EMMA_REPORT.HTML:
                opt = "report.html.out.file"
                value = os.path.join(toDir, "coverage", "index.html")
            elif report == EMMA_REPORT.XML:
                opt = "report.xml.out.file" 
                value = os.path.join(toDir, "coverage.xml")
            elif report == EMMA_REPORT.TXT:
                opt = "report.txt.out.file"
                value = os.path.join(toDir, "coverage.txt")
            options  += " -D%s=%s" % (opt, value)
        
        if commonoptions:
            for entry in commonoptions.iteritems():
                options += " -D" + entry[0] + "=" + entry[1]
        
        cmd = self._previewEmmaCmd("emma report", options)
        (returnCode, outputStr) = self._runEmmaCommand(cmd)
        return self._interpResultsEmmaReportCmd(returnCode, outputStr)


    def reportToDirWithName(self, inputs=[], toDir=None, mainFileName=None, report=EMMA_REPORT.HTML, sourcepath=[], commonoptions={}):
        '''
        This method produce a report into the specified directory.
        
        Args:
            :param inputs:
            :param toDir:
            :param mainFileName:
            :param report:
            :param sourcepath:
            :param commonoptions:
        
        Returns:
        '''
        options = ""
        if inputs:
            options += " -input "
            for f in inputs:
                options += f + ","
            options = options[0:-1]
        
        options += " -report " + report
        
        if sourcepath:
            options +=  " -sourcepath "
            for src in sourcepath:
                options += src + ","
            options = options[0:-1]
        
        if not mainFileName:
            mainFileName = "coverage"
        if not toDir:
            toDir=""
            
        if report == EMMA_REPORT.HTML:
            opt = "report.html.out.file"
            value = os.path.join(toDir, "coverage", "%s.html" % mainFileName)
        elif report == EMMA_REPORT.XML:
            opt = "report.xml.out.file" 
            value = os.path.join(toDir, "%s.xml" % mainFileName)
        elif report == EMMA_REPORT.TXT:
            opt = "report.txt.out.file"
            value = os.path.join(toDir, "%s.txt" % mainFileName)
        options  += " -D%s=%s" % (opt, value)
        
        if commonoptions:
            for entry in commonoptions.iteritems():
                options += " -D" + entry[0] + "=" + entry[1]
        
        cmd = self._previewEmmaCmd("emma report", options)
        (returnCode, outputStr) = self._runEmmaCommand(cmd)
        return self._interpResultsEmmaReportCmd(returnCode, outputStr)

#===============================================================================
# emma_helper = EmmaInterface()
# emma_helper.report(inputs=["coverage.ec", "coverage.em"], commonoptions={"report.html.out.file" : "mycoverage/coverage.html", "testkey" : "testvalue"})
#===============================================================================
    
    