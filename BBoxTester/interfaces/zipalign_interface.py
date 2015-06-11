'''
Created on Oct 1, 2014

@author: Yury Zhauniarovich <y.zhalnerovich{at}gmail.com>
'''
import os
from interfaces import commander



class ZipalignInterface:
    def __init__(self, dirZipalign="./auxiliary/zipalign", exeZipalign="zipalign"):
        self.dirZipalign = dirZipalign
        self.exeZipalign = exeZipalign
        self.pathToZipalign = os.path.join(self.dirZipalign, self.exeZipalign)
    
    
    
    def align(self, inFile, outFile, alignment=4, verbose=True, overwrite=True):
        options = ""
        if verbose:
            options += " -v"
        if overwrite:
            options += " -f"
        
        options += " %d '%s' '%s'" % (alignment, inFile, outFile)
        cmd = self._previewZipalignCmd(options)
        (returnCode, output) = self._runZipalignCommand(cmd)
        (successfulRun, cmdOutput) = self._interpretAlignCmdResults(returnCode, output)
        return (successfulRun, cmdOutput)    
    
    #TODO: Need to refactor commander.runOnce command and then it is possible
    #      to add this command because we need to interpret results obtained
    #      from the stdout
#     def isAligned(self, inFile, alignment=4, verbose=True):
#         options = "-c"
#         if verbose:
#             options += " -v"
#         
#         options += " %d '%s'" % (alignment, inFile)
#         cmd = self._previewZipalignCmd(options)
#         (returnCode, output) = self._runZipalignCommand(cmd)
#         (successfulRun, cmdOutput) = self._interpretCheckAlignmentCmdResults(returnCode, output)
#         return (successfulRun, cmdOutput)
        
    def _previewZipalignCmd(self, options):
        zipalignCommand = "'%s' %s" % (self.pathToZipalign, options)
        return zipalignCommand
    
    def _runZipalignCommand(self, cmd):
        return commander.runOnce(cmd)
    
    def _interpretAlignCmdResults(self, returnCode, output):
        output = "Return code is: [%s].\nCommand output: %s" % (returnCode, output)
        #TODO: later we can select different routines to process different errors
        if returnCode:
            return (False, output)
        return (True, output)
    
    