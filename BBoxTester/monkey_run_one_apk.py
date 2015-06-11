'''
Created on Dec 2, 2014

@author: Yury Zhauniarovich <y.zhalnerovich{at}gmail.com>
'''

import os, sys, time
from interfaces.adb_interface import AdbInterface
from bboxcoverage import BBoxCoverage
from running_strategies import MonkeyStrategy
from utils import auxiliary_utils

INSTRUMENTED_APK_PATH = "/home/yury/TMP/BBoxTester/errors_exploration/Dictionary-4/Dictionary-4_aligned.apk"
EVENTS_COUNT = 10000
SEED = 3
THROTTLE = 50



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

def runMonkeyStrategy(adb, package_name, eventsCount, seed, throttle):
    automaticTriggeringStrategy = MonkeyStrategy(adbDevice=adb, packageName=package_name, eventsCount=eventsCount,  seed=seed, verbosityLevel=2, throttle=throttle)
    automaticTriggeringStrategy.run()



#main part
adb = AdbInterface()
device = getExecutionDevice()
if not device:
    exit(1)
    
adb.setTargetSerial(device)
bboxcoverage = BBoxCoverage()

apk_file = INSTRUMENTED_APK_PATH
if apk_file:
    print "Starting monkeyrunner strategy experiment for apk: %s" % apk_file
    res_dir = os.path.split(os.path.abspath(apk_file))[0]
#     if not os.path.exists(res_dir):
#         auxiliary_utils.mkdir(res_dir, mode=0777, overwrite=True)
    print "Putting results in directory: %s" % res_dir
    try:
        bboxcoverage.initAlreadyInstrApkEnv(pathToInstrApk=apk_file, resultsDir=res_dir)
        bboxcoverage.installApkOnDevice()
        
        bboxcoverage.startTesting()
        package_name =  bboxcoverage.getPackageName()
        runMonkeyStrategy(adb=adb, package_name=package_name, 
                          eventsCount=EVENTS_COUNT, seed=SEED, 
                          throttle=THROTTLE)
        
        params={}
        params["strategy"] = "monkey"
        params["package_name"] = package_name
        params["events_count"] = EVENTS_COUNT
        params["seed"] = SEED
        params["throttle"] = THROTTLE
        time.sleep(3)
        bboxcoverage.stopTesting("monkey_events_%d_seed_%d_throttle_%d" % (EVENTS_COUNT, SEED, THROTTLE), paramsToWrite=params)
        time.sleep(3)
        bboxcoverage.uninstallPackage()
        time.sleep(5)
    except Exception as e:
        print "EXCEPTION while execution: " + str(e)
    except:
        print "UNKNOWN EXCEPTION"