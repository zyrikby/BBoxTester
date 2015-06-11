'''
Created on Nov 26, 2014

@author: Yury Zhauniarovich <y.zhalnerovich{at}gmail.com>
'''
import os, time

from interfaces.adb_interface import AdbInterface
from bboxcoverage import BBoxCoverage
from running_strategies import IntentInvocationStrategy

import smtplib
import email.utils
from email.mime.text import MIMEText

APK_DIR_SOURCES = ["", ""]

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER = ""
PASSWORD = ""
TO_EMAIL = ""

def sendMessage(subj, email_message):
    msg = MIMEText(email_message)
    msg['To'] = email.utils.formataddr(('Recipient', TO_EMAIL))
    msg['From'] = email.utils.formataddr(('Author', SENDER))
    msg['Subject'] = subj
    
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    try:
        server.set_debuglevel(True)
    
        # identify ourselves, prompting server for supported features
        server.ehlo()
    
        # If we can encrypt this session, do it
        if server.has_extn('STARTTLS'):
            server.starttls()
            server.ehlo() # re-identify ourselves over TLS connection
    
        server.login(SENDER, PASSWORD)
        server.sendmail(SENDER, [TO_EMAIL], msg.as_string())
    finally:
        server.quit()

def getExecutionDevice():
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
            return dev_list[0]
        
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
            
        return dev_list[choice-1]


def getSubdirs(rootDir):
    return [os.path.join(rootDir, name) for name in os.listdir(rootDir)
            if os.path.isdir(os.path.join(rootDir, name))]

def getInstrApkInFolder(folder):
    for f in os.listdir(folder):
        if f.endswith("_aligned.apk"):
            filepath = os.path.join(folder, f)
            return filepath
    return None


def runMainIntentsStrategy(adb, androidManifest, delay=10):
    automaticTriggeringStrategy = IntentInvocationStrategy(adbDevice=adb, pathToAndroidManifest=androidManifest)
    automaticTriggeringStrategy.run(delay=delay)

#main part
adb = AdbInterface()
device = getExecutionDevice()
if not device:
    exit(1)
    
adb.setTargetSerial(device)
bboxcoverage = BBoxCoverage()

for apk_dir_source in APK_DIR_SOURCES:
    print "\n\nStarting experiment for directory: [%s]" % apk_dir_source
    result_directories = getSubdirs(apk_dir_source)
    for directory in result_directories:
        apk_file = getInstrApkInFolder(directory)
        if apk_file:
            print "Starting experiment for apk: [%s]" % apk_file
            try:
                bboxcoverage.initAlreadyInstrApkEnv(pathToInstrApk=apk_file, resultsDir=directory)
            except:
                print "Exception while initialization!"
                continue
            try:
                bboxcoverage.installApkOnDevice()
            except:
                print "Exception while installation apk on device!"
                bboxcoverage.uninstallPackage()
                try:
                    bboxcoverage.installApkOnDevice()
                except:
                    continue
                
            package_name =  bboxcoverage.getPackageName()
            params = {}
            params["strategy"] = "main_intents"
            params["package_name"] = package_name
            params["main_activity"] = bboxcoverage.androidManifest.getMainActivity()
            
            try: 
                bboxcoverage.startTesting()
            except:
                print "Exception while startTesting!"
                bboxcoverage.uninstallPackage()
                continue
            
            try:
                runMainIntentsStrategy(adb=adb, androidManifest=bboxcoverage.androidManifestFile, delay=10)
            except:
                print "Exception while running strategy!"
                bboxcoverage.uninstallPackage()
                continue
            
            try:    
                bboxcoverage.stopTesting("main_intents", paramsToWrite=params)
            except:
                print "Exception while running strategy!"
                bboxcoverage.uninstallPackage()
                continue
            
            time.sleep(3)
            bboxcoverage.uninstallPackage()
            time.sleep(5)
            
    sendMessage("[BBoxTester]", "Experiments done for directory [%s]!" % apk_dir_source)
