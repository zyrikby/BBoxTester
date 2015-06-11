'''
Created on Nov 11, 2014

@author: Yury Zhauniarovich <y.zhalnerovich{at}gmail.com>
'''
import time
from utils.android_manifest import AndroidManifest
from interfaces.adb_interface import CATEGORY_DEFAULT

class RunningStrategy():
    def run(self):
        pass

class MonkeyStrategy(RunningStrategy):
    '''
    
    '''


    def __init__(self, adbDevice, packageName, eventsCount, seed, verbosityLevel, throttle, timeout=None):
        '''
        Constructor
        '''
        self.adbDevice = adbDevice
        self.eventsCount = eventsCount
        self.packageName = packageName
        self.seed = seed
        self.verbosityLevel = verbosityLevel
        self.throttle = throttle
        self.timeout = timeout
        
    
    def run(self):
        self.adbDevice.runMonkeyTest(timeout=self.timeout, packageName=self.packageName, 
            verbosityLevel=self.verbosityLevel, seed=self.seed, throttle=self.throttle, 
            eventsCount=self.eventsCount, dbgNoEvents=False, hprof=False, ignoreCrashes=True, 
            ignoreTimeouts=True, ignoreSecurityExceptions=True, killProcessAfterError=False, 
            monitorNativeCrashes=False, waitDbg=False)




class IntentInvocationStrategy(RunningStrategy):
    def __init__(self, adbDevice, pathToAndroidManifest):
        self.adbDevice = adbDevice
        self.androidManifest=AndroidManifest(pathToAndroidManifest)
    
    
    def run(self, delay=10):
        print "Activities:"
        activities = self.androidManifest.getActivities()
        for activity in activities:
            self._invokeActivityExplicitely(activity)
            time.sleep(delay)
        
        print "Services:"    
        services = self.androidManifest.getServices()
        for service in services:
            self._invokeServiceExplicitely(service)
            time.sleep(delay)
         
        print "Receivers:"        
        receivers = self.androidManifest.getReceivers()
        for receiver in receivers:
            self._invokeReceiver(receiver)
            time.sleep(delay)
             
    
    def _invokeActivityExplicitely(self, activity):
        self.adbDevice.startActivityExplicitly(package_name=self.androidManifest.getPackageName(),
                                                   activity_name=activity)
    
    def _invokeActivity(self, activity):
        intentFilters = self.androidManifest.getActivityIntentFilters(activity)
        if not intentFilters:
            self.adbDevice.startActivityExplicitly(package_name=self.androidManifest.getPackageName(),
                                                   activity_name=activity)
            return
        for filt in intentFilters:
            action = self._getAction(filt)
            category = self._getCategory(filt)
            mimeType = self._getMiMeType(filt)
            self.adbDevice.startActivityImplicitely(action=action, mimeType=mimeType, category=category)
    
    def _invokeServiceExplicitely(self, service):
        self.adbDevice.startServiceExplicitly(package_name=self.androidManifest.getPackageName(),
                                                   service_name=service)
            
    def _invokeService(self, service):
        intentFilters = self.androidManifest.getServiceIntentFilters(service)
        if not intentFilters:
            self.adbDevice.startServiceExplicitly(package_name=self.androidManifest.getPackageName(),
                                                   service_name=service)
            return
        
        for filt in intentFilters:
            action = self._getAction(filt)
            category = self._getCategory(filt)
            mimeType = self._getMiMeType(filt)
            self.adbDevice.startServiceImplicitely(action=action, mimeType=mimeType, category=category)
    
    def _invokeReceiver(self, receiver):
        intentFilters = self.androidManifest.getReceiverIntentFilters(receiver)
        if not intentFilters:
            return
        
        for filt in intentFilters:
            action = self._getAction(filt)
            category = self._getCategory(filt)
            mimeType = self._getMiMeType(filt)
            self.adbDevice.sendBroadcast(action=action, mimeType=mimeType, category=category)
    
    
    def _getAction(self, filt):
        action = None
        actions = filt.get("action")
        if actions:
            action = actions[0]
        return action    
        
    def _getCategory(self, filt):
        category = None
        categories = filt.get("category")
        if categories:
            category = categories[0]
        else:
            category = CATEGORY_DEFAULT
        return category
    
    def _getMiMeType(self, filt):
        mimeType = None
        mimeTypes = filt.get("mimeType")
        if mimeTypes:
            mimeType = mimeTypes[0]
        return mimeType
    
class MainActivityInvocationStrategy(RunningStrategy):
    def __init__(self, adbDevice, pathToAndroidManifest):
        self.adbDevice = adbDevice
        self.androidManifest=AndroidManifest(pathToAndroidManifest)
    
    def run(self, delay=10):
        mainActivity = self.androidManifest.getMainActivity()
        if mainActivity:
            self.adbDevice.startActivityExplicitly(package_name=self.androidManifest.getPackageName(),
                                                       activity_name=mainActivity)
            time.sleep(delay)
        
