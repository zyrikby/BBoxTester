'''
Created on Jul 2, 2014

@author: yury
'''

from bboxcoverage import BBoxCoverage
from interfaces.adb_interface import *
from interfaces.apktool_interface import *
from interfaces.dex2jar_interface import *
from interfaces.dx_interface import *
from interfaces.emma_interface import *
from utils.android_manifest import *



def main():
    bboxcoverage = BBoxCoverage()
    #bboxcoverage.instrumentApkForCoverage(pathToOrigApk="/home/yury/TMP/BBoxTester/Notepad.apk", resultsDir="/home/yury/TMP/BBoxTester/results/", tmpDir="/home/yury/TMP/BBoxTester/tmp", overwriteExisting=True, removeApkTmpDirAfterInstr=False, copyApkToRes=True)
    #bboxcoverage.installApkOnDevice()
    #bboxcoverage.startTesting()
    #time.sleep(30)
    #localReport = bboxcoverage.stopTesting()
    #bboxcoverage.generateReport([localReport], EMMA_REPORT.XML)
    
    #bboxcoverage.instrumentApkForCoverage(pathToOrigApk="/home/yury/PROJECTS/BBOXTESTING2/app/com.markuspage.android.atimetracker.apk", resultsDir="/home/yury/PROJECTS/BBOXTESTING2/app/results", tmpDir="/home/yury/TMP/BBoxTester/tmp", removeApkTmpDirAfterInstr=False, copyApkToRes=True)
    #bboxcoverage.installApkOnDevice()
    #bboxcoverage.startTesting()
    #time.sleep(30)
    #localReport = bboxcoverage.stopTesting()
    #bboxcoverage.generateReport([localReport], EMMA_REPORT.XML)
    
#     bboxcoverage.instrumentApkForCoverage(pathToOrigApk="/home/yury/PROJECTS/BBOXTESTING2/app/com.markuspage.android.atimetracker_17.apk", resultsDir="/home/yury/PROJECTS/BBOXTESTING2/app/results_packed", tmpDir="/home/yury/TMP/BBoxTester/tmp", removeApkTmpDirAfterInstr=False, copyApkToRes=True)
#     bboxcoverage.installApkOnDevice()
#     bboxcoverage.startTesting()
#     time.sleep(30)
#     localReport = bboxcoverage.stopTesting()
    
    bboxcoverage._signApk(bboxcoverage.bboxInstrumenter, "/home/yury/PROJECTS/BBOXTESTING2/app/com.markuspage.android.atimetracker_17_aligned.apk", "/home/yury/PROJECTS/BBOXTESTING2/app/com.markuspage.android.atimetracker_17_aligned_signed.apk")
    bboxcoverage.initAlreadyInstrApkEnv(pathToInstrApk="/home/yury/PROJECTS/BBOXTESTING2/app/com.markuspage.android.atimetracker_17_aligned_signed.apk", resultsDir="/home/yury/PROJECTS/BBOXTESTING2/app/results_packed/com.markuspage.android.atimetracker_17/")
    bboxcoverage.installApkOnDevice()
    bboxcoverage.startTesting()
    time.sleep(30)
    localReport = bboxcoverage.stopTesting()
    
#     bboxcoverage2 = BBoxCoverage()
#     bboxcoverage2.initAlreadyInstrApkEnv(pathToInstrApk="/home/yury/TMP/BBoxTester/Notepad_instr_final.apk", resultsDir="/home/yury/TMP/BBoxTester/results/Notepad")
#     bboxcoverage2.startTesting()
#     time.sleep(20)
#     lRep = bboxcoverage2.stopTesting()
#     bboxcoverage2.generateReport([lRep], EMMA_REPORT.XML)
    

if __name__ == '__main__':
    main()