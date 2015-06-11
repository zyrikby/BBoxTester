'''
Created on Jul 8, 2014

@author: Yury Zhauniarovich <y.zhalnerovich{at}gmail.com>
'''
from xml.dom import minidom
from bbox_core.general_exceptions import MsgException



class AndroidManifest:
    def __init__(self, pathAndroidManifest):
        self.pathAndroidManifest = pathAndroidManifest
        self.xml = minidom.parse(pathAndroidManifest)
        self.packageName = self.getElement("manifest", "package")
    
    def getUsesPermissions(self):
        return self.getElements("uses-permission", "android:name")
    
    def addUsesPermission(self, permName):
        if permName not in self.getUsesPermissions():
            self.createElement("manifest", "uses-permission", {"android:name" : permName})
    
    def getMainActivity(self):
        """
            Return the name of the main activity

            :rtype: string
        """
        x = set()
        y = set()

        for item in self.xml.getElementsByTagName("activity"):
            for sitem in item.getElementsByTagName("action") :
                val = sitem.getAttribute("android:name")
                if val == "android.intent.action.MAIN":
                    x.add(item.getAttribute("android:name"))
               
            for sitem in item.getElementsByTagName("category") :
                val = sitem.getAttribute("android:name")
                if val == "android.intent.category.LAUNCHER":
                    y.add(item.getAttribute("android:name"))
                
        z = x.intersection(y)
        if len(z) > 0 :
            return self.formatValue(z.pop())
        return None
    
    def getActivities(self):
        """
        Return the android:name attribute of all activities
        Return:
            :rtype: a list of string
        """
        return self.getElements("activity", "android:name")

    def getServices(self):
        """
            Return the android:name attribute of all services
            
            Return:
                :rtype: a list of string
        """
        return self.getElements("service", "android:name")

    def getReceivers(self) :
        """
            Return the android:name attribute of all receivers

            :rtype: a list of string
        """
        return self.getElements("receiver", "android:name")
    
    def getIntentFilters(self, category, name):
        filters = []
        for item in self.xml.getElementsByTagName(category):
            if self.formatValue(item.getAttribute("android:name")) == name:
                for sitem in item.getElementsByTagName("intent-filter"):
                    filter = self._getIntentFilterDetails(sitem)
                    filters.append(filter)
        return filters
        
    
    def _getIntentFilterDetails(self, sitem):
        d = {}
        d["action"] = []
        d["category"] = []
        d["mimeType"] = []
        
        for ssitem in sitem.getElementsByTagName("action"):
            if ssitem.getAttribute("android:name") not in d["action"]:
                d["action"].append(ssitem.getAttribute("android:name"))
        for ssitem in sitem.getElementsByTagName("category"):
            if ssitem.getAttribute("android:name") not in d["category"]:
                d["category"].append(ssitem.getAttribute("android:name"))
        for ssitem in sitem.getElementsByTagName("data"):
            if ssitem.getAttribute("android:mimeType") not in d["mimeType"]:
                d["mimeType"].append(ssitem.getAttribute("android:mimeType"))
        
        if not d["action"]:
            del d["action"]

        if not d["category"]:
            del d["category"]
        
        if not d["mimeType"]:
            del d["mimeType"]

        return d
    
    def getActivityIntentFilters(self, name):
        return self.getIntentFilters("activity", name)
    
    def getServiceIntentFilters(self, name):
        return self.getIntentFilters("service", name)
            
    def getReceiverIntentFilters(self, name):
        return self.getIntentFilters("receiver", name)
    
    def addInstrumentation(self, instrumentationClassName, targetPackage):
        instr = self.getElements("instrumentation", "android:name")
        #TODO: Check if several instrumentations are possible
        if len(instr) > 0:
            raise ManifestAlreadyInstrumentedException()
        
        self.createElement("manifest", "instrumentation", 
                           {"android:name" : instrumentationClassName,
                            "android:targetPackage" : targetPackage})
    
    def removeExistingInstrumentation(self):
        instr = self.getElements("instrumentation", "android:name")
        if len(instr) <= 0:
            raise NoInstrumentationTagFound()
        for elem in instr:
            self.xml.removeChild(elem)
    
        
    def getPackageName(self):
        return self.packageName
    
    def getInstrumentationRunnerName(self):
        return self.getElement("instrumentation", "android:name")
    
    def getInstrumentationTargetPackage(self):
        return self.getElement("instrumentation", "android:targetPackage")
    
    def getElement(self, tag_name, attribute):
        """
            Return element in xml files which matches with the tag name and the specific attribute

            :param tag_name: specify the tag name
            :type tag_name: string
            :param attribute: specify the attribute
            :type attribute: string

            :rtype: string
        """
        for item in self.xml.getElementsByTagName(tag_name) :
            value = item.getAttribute(attribute)

            if len(value) > 0 :
                return value
            
        return None
    
    def getElements(self, tag_name, attribute):
        """
            Return elements in xml files which match with the tag name and the specific attribute

            :param tag_name: a string which specify the tag name
            :param attribute: a string which specify the attribute
        """
        l = []
        for item in self.xml.getElementsByTagName(tag_name) :
            value = item.getAttribute(attribute)
            value = self.formatValue(value)
            l.append(str(value))

        return l
    
    def formatValue(self, value) :
        if len(value) > 0 :
            if value[0] == "." : 
                value = self.packageName + value
            else :
                v_dot = value.find(".")
                if v_dot == 0 :
                    value = self.packageName + "." + value
                elif v_dot == -1 :
                    value = self.packageName + "." + value
        return value
    
    def createElement(self, under_tag, tag, attributes):
        where = self.xml.getElementsByTagName(under_tag) #adding after the first occurrence
        if len(where) <= 0:
            raise NoTagException("Cannot find tag: %s" % under_tag)
        elem = self.xml.createElement(tag)
        if attributes:
            for entry in attributes.iteritems():
                elem.setAttribute(entry[0], entry[1])
        where[0].appendChild(elem)
    
    def getAndroidManifestXml(self):
        return self.xml.toprettyxml()
    
    def exportManifest(self, path=None):
        if not path:
            with open(self.pathAndroidManifest, "wb") as f:
                self.xml.writexml(f)
        else:
            with open(path, "wb") as f:
                self.xml.writexml(f)



# Exception classes
class NoTagException(MsgException):
    '''
    No tag found in the manifest file.
    '''

class ManifestAlreadyInstrumentedException(MsgException):
    '''
    Manifest already contains instrumentation tag.
    '''

class NoInstrumentationTagFound(MsgException):
    '''
    No instrumentation tag found.
    '''

   
#===============================================================================
# androidManifest = AndroidManifest("/home/yury/research_tmp/BBTester_tst/notepad/AndroidManifest.xml")
# print androidManifest.getPackageName()
#===============================================================================
#===============================================================================
# androidManifest.addUsesPermission("com.zhauniarovich.permission")
# androidManifest.addInstrumentation("com.example.instrumentation.EmmaInstrumentation", "com.example.i2at.tc")
# print androidManifest.getAndroidManifestXml()
# androidManifest.exportManifest("/home/yury/research_tmp/BBTester_tst/notepad/AndroidManifest1.xml")
#===============================================================================

    