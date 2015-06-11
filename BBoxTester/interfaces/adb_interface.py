#!/usr/bin/python2.4
#
#
# Copyright 2008, The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

### This is a corrected version of adb_interface from AOSP adapted for our tasks

import os
import string
import time
import signal
import subprocess
import threading
import re

from logconfig import logger
from six import iteritems


TYPE_NULL_EXTRA      = 0
TYPE_STRING          = 1
TYPE_BOOLEAN         = 2
TYPE_INT             = 3
TYPE_LONG            = 4
TYPE_FLOAT           = 5
TYPE_URI             = 6
TYPE_COMPONENT_NAME  = 7
TYPE_INT_ARRAY       = 8
TYPE_LONG_ARRAY      = 9
TYPE_FLOAT_ARRAY     = 10

TYPE_KEY = {
        TYPE_NULL_EXTRA      : "--esn",
        TYPE_STRING          : "--es",
        TYPE_BOOLEAN         : "--ez",
        TYPE_INT             : "--ei",
        TYPE_LONG            : "--el",
        TYPE_FLOAT           : "--ef",
        TYPE_URI             : "--eu",
        TYPE_COMPONENT_NAME  : "--ecn",
        TYPE_INT_ARRAY       : "--eia",
        TYPE_LONG_ARRAY      : "--ela",
        TYPE_FLOAT_ARRAY     : "--efa"
    }

CATEGORY_DEFAULT = "android.intent.category.DEFAULT"


class AdbInterface:
    """Helper class for communicating with Android device via adb."""
    
    LOG_LEVELS = ['V', 'I', 'D', 'W', 'E', 'WTF']
    # argument to pass to adb, to direct command to specific device
    _target_arg = ""

    DEVICE_TEST_RESULTS_DIR = "/data/test_results/"

    @staticmethod
    def getDeviceSerialsList():
        logger.debug("Getting the list of running deviceSerials...")
        deviceSerials = []
        input_devices = None
        try:
            input_devices = runCommand("adb devices")
        except WaitForResponseTimedOutError:
            logger.error("Command timeout exception!")
            return deviceSerials
        except:
            logger.error("Could not find attached devices!")
            return deviceSerials
            
        lines = input_devices.splitlines()
        for i in range(0,len(lines)): #first line just announces the list of deviceSerials
            words = lines[i].split('\t')
            if (len(words) == 2 and (words[1].strip() == 'device' or words[1].strip() == 'offline')):
                deviceSerials.append(words[0].strip())
        
        logger.debug("Device list: %s", deviceSerials)
        return deviceSerials
    
    def setEmulatorTarget(self):
        """Direct all future commands to the only running emulator."""
        self._target_arg = "-e"

    def setDeviceTarget(self):
        """Direct all future commands to the only connected USB device."""
        self._target_arg = "-d"

    def setTargetSerial(self, serial):
        """Direct all future commands to Android target with the given serial."""
        self._target_arg = "-s %s" % serial
    
    def sendCommand(self, command_string, timeout_time=20, retry_count=3):
        """Send a command via adb.

        Args:
            command_string: adb command to run
            timeout_time: number of seconds to wait for command to respond before
                retrying
            retry_count: number of times to retry command before raising
                WaitForResponseTimedOutError
        Returns:
            string output of command

        Raises:
            WaitForResponseTimedOutError if device does not respond to command within time
        """
        adb_cmd = "adb %s %s" % (self._target_arg, command_string)
        logger.debug("about to run %s" % adb_cmd)
        return runCommand(adb_cmd, timeout_time=timeout_time, retry_count=retry_count)
    
    def sendShellCommand(self, cmd, timeout_time=20, retry_count=3):
        """Send a adb shell command.

        Args:
            cmd: adb shell command to run
            timeout_time: number of seconds to wait for command to respond before
                retrying
            retry_count: number of times to retry command before raising
                WaitForResponseTimedOutError

        Returns:
            string output of command

        Raises:
            WaitForResponseTimedOutError: if device does not respond to command
        """
        return self.sendCommand("shell %s" % cmd, timeout_time=timeout_time,
                                                        retry_count=retry_count)

    def bugReport(self, path):
        """Dumps adb bugreport to the file specified by the path.

        Args:
            path: Path of the file where adb bugreport is dumped to.
        """
        bug_output = self.sendShellCommand("bugreport", timeout_time=60)
        bugreport_file = open(path, "w")
        bugreport_file.write(bug_output)
        bugreport_file.close()

    def push(self, src, dest):
        """Pushes the file src onto the device at dest.

        Args:
            src: file path of host file to push
            dest: destination absolute file path on device
        """
        self.sendCommand("push %s %s" % (src, dest), timeout_time=60)

    def pull(self, src, dest):
        """Pulls the file src on the device onto dest on the host.

        Args:
            src: absolute file path of file on device to pull
            dest: destination file path on host

        Returns:
            True if success and False otherwise.
        """
        # Create the base dir if it doesn't exist already
        if not os.path.exists(os.path.dirname(dest)):
            os.makedirs(os.path.dirname(dest))

        if self.doesFileExist(src):
            self.sendCommand("pull %s %s" % (src, dest), timeout_time=60)
            return True
        else:
            logger.info("ADB pull Failed: Source file %s does not exist." % src)
            return False

    def remove(self, target):
        self.sendShellCommand("rm -r -f %s" % target)
        
    def install(self, apk_path):
        """Installs apk on device.

        Args:
            apk_path: file path to apk file on host

        Returns:
            output of install command
        """
        return self.sendCommand("install -r %s" % apk_path)
    

    
    def uninstall(self, package_name, keep_data = False):
        cmd = self._buildUninstallCommand(package_name = package_name, 
                                          keep_data=keep_data)
        
        return self.sendCommand(cmd)
    
    def _buildUninstallCommand(self, package_name, keep_data=False):
        options = ""
        if keep_data:
            options  += " -k"
        
        cmd = "uninstall %s %s" % (options, package_name)
        return cmd 

    def doesFileExist(self, src):
        """Checks if the given path exists on device target.

        Args:
            src: file path to be checked.

        Returns:
            True if file exists
        """

        output = self.sendShellCommand("ls %s" % src)
        error = "No such file or directory"

        if error in output:
            return False
        return True

    def enableAdbRoot(self):
        """Enable adb root on device."""
        output = self.sendCommand("root")
        if "adbd is already running as root" in output:
            return True
        elif "restarting adbd as root" in output:
            # device will disappear from adb, wait for it to come back
            time.sleep(2)
            self.sendCommand("wait-for-device")
            return True
        else:
            logger.info("Unrecognized output from adb root: %s" % output)
            return False

    def startInstrumentationForPackage(
            self, package_name, runner_name, timeout_time=60*10,
            no_window_animation=False, instrumentation_args={}):
        """Run instrumentation test for given package and runner.

        Equivalent to startInstrumentation, except instrumentation path is
        separated into its package and runner components.
        """
        instrumentation_path = "%s/%s" % (package_name, runner_name)
        return self.startInstrumentation(instrumentation_path, timeout_time=timeout_time,
                                                                         no_window_animation=no_window_animation,
                                                                         instrumentation_args=instrumentation_args)

    def startInstrumentation(
            self, instrumentation_path, timeout_time=60*10, no_window_animation=False,
            profile=False, instrumentation_args={}):

        """Runs an instrumentation class on the target.

        Returns a dictionary containing the key value pairs from the
        instrumentations result bundle and a list of TestResults. Also handles the
        interpreting of error output from the device and raises the necessary
        exceptions.

        Args:
            instrumentation_path: string. It should be the fully classified package
            name, and instrumentation test runner, separated by "/"
                e.g. com.android.globaltimelaunch/.GlobalTimeLaunch
            timeout_time: Timeout value for the am command.
            no_window_animation: boolean, Whether you want window animations enabled
                or disabled
            profile: If True, profiling will be turned on for the instrumentation.
            instrumentation_args: Dictionary of key value bundle arguments to pass to
            instrumentation.

        Returns:
            (test_results, inst_finished_bundle)

            test_results: a list of TestResults
            inst_finished_bundle (dict): Key/value pairs contained in the bundle that
                is passed into ActivityManager.finishInstrumentation(). Included in this
                bundle is the return code of the Instrumentation process, any error
                codes reported by the activity manager, and any results explicitly added
                by the instrumentation code.

         Raises:
             WaitForResponseTimedOutError: if timeout occurred while waiting for
                 response to adb instrument command
             DeviceUnresponsiveError: if device system process is not responding
             InstrumentationError: if instrumentation failed to run
        """

        command_string = self._buildInstrumentationCommandPath(
                instrumentation_path, no_window_animation=no_window_animation,
                profile=profile, raw_mode=True,
                instrumentation_args=instrumentation_args)
        logger.debug(command_string)
        (test_results, inst_finished_bundle) = (
                ParseAmInstrumentOutput(
                        self.sendShellCommand(command_string, timeout_time=timeout_time,
                                                                    retry_count=2)))

        if "code" not in inst_finished_bundle:
            raise InstrumentationError("no test results... device setup "
                                                                                "correctly?")

        if inst_finished_bundle["code"] == "0":
            short_msg_result = "no error message"
            if "shortMsg" in inst_finished_bundle:
                short_msg_result = inst_finished_bundle["shortMsg"]
                logger.error("Error! Test run failed: %s" % short_msg_result)
            raise InstrumentationError(short_msg_result)

        if "INSTRUMENTATION_ABORTED" in inst_finished_bundle:
            logger.debug("INSTRUMENTATION ABORTED!")
            raise DeviceUnresponsiveError

        return (test_results, inst_finished_bundle)

    def startInstrumentationNoResults(
            self, package_name, runner_name, no_window_animation=False,
            raw_mode=False, wait=True, instrumentation_args={}):
        """Runs instrumentation and dumps output to stdout.

        Equivalent to startInstrumentation, but will dump instrumentation
        'normal' output to stdout, instead of parsing return results. Command will
        never timeout.
        """
        adb_command_string = self.previewInstrumentationCommand(
                package_name, runner_name, no_window_animation=no_window_animation,
                raw_mode=raw_mode, wait=wait, instrumentation_args=instrumentation_args)
        logger.debug(adb_command_string)
        runCommand(adb_command_string, return_output=False)

    def previewInstrumentationCommand(
            self, package_name, runner_name, no_window_animation=False,
            raw_mode=False, wait=True, instrumentation_args={}):
        """Returns a string of adb command that will be executed."""
        inst_command_string = self._buildInstrumentationCommand(
                package_name, runner_name, no_window_animation=no_window_animation,
                raw_mode=raw_mode, wait=wait, instrumentation_args=instrumentation_args)
        return self.previewShellCommand(inst_command_string)

    def previewShellCommand(self, cmd):
        return "adb %s shell %s" % (self._target_arg, cmd)

    def _buildInstrumentationCommand(
            self, package, runner_name, no_window_animation=False, profile=False,
            raw_mode=True, wait=True, instrumentation_args={}):
        instrumentation_path = "%s/%s" % (package, runner_name)
        
        return self._buildInstrumentationCommandPath(
                instrumentation_path, no_window_animation=no_window_animation,
                profile=profile, raw_mode=raw_mode, wait=wait,
                instrumentation_args=instrumentation_args)

    def _buildInstrumentationCommandPath(
            self, instrumentation_path, no_window_animation=False, profile=False,
            raw_mode=True, wait=True, instrumentation_args={}):
        command_string = "am instrument"
        if no_window_animation:
            command_string += " --no_window_animation"
        if profile:
            self._createTraceDir()
            command_string += (
                    " -p %s/%s.dmtrace" %
                    (self.DEVICE_TEST_RESULTS_DIR, instrumentation_path.split(".")[-1]))

        for key, value in instrumentation_args.items():
            command_string += " -e %s '%s'" % (key, value)
        if raw_mode:
            command_string += " -r"
        if wait:
            command_string += " -w"
        command_string += " %s" % instrumentation_path
        
        return command_string
    
    #modified start instr
    def startInstrumentationNoResultsMod(
            self, package_name, runner_name, no_window_animation=False,
            raw_mode=False, wait=True, instrumentation_args={}):
        """Runs instrumentation and dumps output to stdout.

        Equivalent to startInstrumentation, but will dump instrumentation
        'normal' output to stdout, instead of parsing return results. Command will
        never timeout.
        """
        adb_command_string = self.previewInstrumentationCommandMod(
                package_name, runner_name, no_window_animation=no_window_animation,
                raw_mode=raw_mode, wait=wait, instrumentation_args=instrumentation_args)
        logger.debug(adb_command_string)
        runCommand(adb_command_string, return_output=False)

    def previewInstrumentationCommandMod(
            self, package_name, runner_name, no_window_animation=False,
            raw_mode=False, wait=True, instrumentation_args={}):
        """Returns a string of adb command that will be executed."""
        inst_command_string = self._buildInstrumentationCommandMod(
                package_name, runner_name, no_window_animation=no_window_animation,
                raw_mode=raw_mode, wait=wait, instrumentation_args=instrumentation_args)
        return self.previewShellCommand(inst_command_string)


    def _buildInstrumentationCommandMod(
            self, package, runner_name, no_window_animation=False, profile=False,
            raw_mode=True, wait=True, instrumentation_args={}):
        instrumentation_path = "%s/%s" % (package, runner_name)
        
        return self._buildInstrumentationCommandPathMod(
                instrumentation_path, no_window_animation=no_window_animation,
                profile=profile, raw_mode=raw_mode, wait=wait,
                instrumentation_args=instrumentation_args)

    def _buildInstrumentationCommandPathMod(
            self, instrumentation_path, no_window_animation=False, profile=False,
            raw_mode=True, wait=True, instrumentation_args={}):
        command_string = "am instrument"
        if no_window_animation:
            command_string += " --no_window_animation"
        if profile:
            self._createTraceDir()
            command_string += (
                    " -p %s/%s.dmtrace" %
                    (self.DEVICE_TEST_RESULTS_DIR, instrumentation_path.split(".")[-1]))

#         for key, value in instrumentation_args.items():
#             command_string += " -e %s '%s'" % (key, value)
        for entry in iteritems(instrumentation_args):
            command_string += " %s %s %s" % (TYPE_KEY.get(entry[1][0]), entry[0], entry[1][1]) 
        
        if raw_mode:
            command_string += " -r"
        if wait:
            command_string += " -w"
        command_string += " %s" % instrumentation_path
        
        return command_string
    #end instr mod
    
    
    
    
    #FIXME: Something wrong - incorrect folder, wrong folders, wrong commands
    def _createTraceDir(self):
        ls_response = self.sendShellCommand("ls /data/trace")
        if ls_response.strip("#").strip(string.whitespace) != "":
            self.sendShellCommand("create /data/trace", "mkdir /data/trace")
            self.sendShellCommand("make /data/trace world writeable",
                                                        "chmod 777 /data/trace")

    def waitForDevicePm(self, wait_time=120):
        """Waits for targeted device's package manager to be up.

        Args:
            wait_time: time in seconds to wait

        Raises:
            WaitForResponseTimedOutError if wait_time elapses and pm still does not
            respond.
        """
        logger.Log("Waiting for device package manager...")
        self.sendCommand("wait-for-device")
        # Now the device is there, but may not be running.
        # Query the package manager with a basic command
        try:
            self._waitForShellCommandContents("pm path android", "package:",
                                                                                wait_time)
        except WaitForResponseTimedOutError:
            raise WaitForResponseTimedOutError(
                    "Package manager did not respond after %s seconds" % wait_time)

    def isInstrumentationInstalled(self, package_name, runner_name):
        """Checks if instrumentation is present on device."""
        instrumentation_path = "%s/%s" % (package_name, runner_name)
        command = "pm list instrumentation | grep %s" % instrumentation_path
        try:
            output = self.sendShellCommand(command)
            return output.startswith("instrumentation:")
        except AbortError:
            # command can return error code on failure
            return False

    def waitForProcess(self, name, wait_time=120):
        """Wait until a process is running on the device.

        Args:
            name: the process name as it appears in `ps`
            wait_time: time in seconds to wait

        Raises:
            WaitForResponseTimedOutError if wait_time elapses and the process is
                    still not running
        """
        logger.Log("Waiting for process %s" % name)
        self.sendCommand("wait-for-device")
        self._waitForShellCommandContents("ps", name, wait_time)

    def waitForProcessEnd(self, name, wait_time=120):
        """Wait until a process is no longer running on the device.

        Args:
            name: the process name as it appears in `ps`
            wait_time: time in seconds to wait

        Raises:
            WaitForResponseTimedOutError if wait_time elapses and the process is
                    still running
        """
        logger.Log("Waiting for process %s to end" % name)
        self._waitForShellCommandContents("ps", name, wait_time, invert=True)

    def _waitForShellCommandContents(self, command, expected, wait_time,
                                                                     raise_abort=True, invert=False):
        """Wait until the response to a command contains a given output.

        Assumes that a only successful execution of "adb shell <command>" contains
        the substring expected. Assumes that a device is present.

        Args:
            command: adb shell command to execute
            expected: the string that should appear to consider the
                    command successful.
            wait_time: time in seconds to wait
            raise_abort: if False, retry when executing the command raises an
                    AbortError, rather than failing.
            invert: if True, wait until the command output no longer contains the
                    expected contents.

        Raises:
            WaitForResponseTimedOutError: If wait_time elapses and the command has not
                    returned an output containing expected yet.
        """
        # Query the device with the command
        success = False
        attempts = 0
        wait_period = 5
        while not success and (attempts*wait_period) < wait_time:
            # assume the command will always contain expected in the success case
            try:
                output = self.sendShellCommand(command, retry_count=1)
                if ((not invert and expected in output)
                        or (invert and expected not in output)):
                    success = True
            except AbortError, e:
                if raise_abort:
                    raise
                # ignore otherwise

            if not success:
                time.sleep(wait_period)
                attempts += 1

        if not success:
            raise WaitForResponseTimedOutError()

    def waitForBootComplete(self, wait_time=120):
        """Waits for targeted device's bootcomplete flag to be set.

        Args:
            wait_time: time in seconds to wait

        Raises:
            WaitForResponseTimedOutError if wait_time elapses and pm still does not
            respond.
        """
        logger.Log("Waiting for boot complete...")
        self.sendCommand("wait-for-device")
        # Now the device is there, but may not be running.
        # Query the package manager with a basic command
        boot_complete = False
        attempts = 0
        wait_period = 5
        while not boot_complete and (attempts*wait_period) < wait_time:
            output = self.sendShellCommand("getprop dev.bootcomplete", retry_count=1)
            output = output.strip()
            if output == "1":
                boot_complete = True
            else:
                time.sleep(wait_period)
                attempts += 1
        if not boot_complete:
            raise WaitForResponseTimedOutError(
                    "dev.bootcomplete flag was not set after %s seconds" % wait_time)

    def sync(self, retry_count=3, runtime_restart=False):
        """Perform a adb sync.

        Blocks until device package manager is responding.

        Args:
            retry_count: number of times to retry sync before failing
            runtime_restart: stop runtime during sync and restart afterwards, useful
                for syncing system libraries (core, framework etc)

        Raises:
            WaitForResponseTimedOutError if package manager does not respond
            AbortError if unrecoverable error occurred
        """
        output = ""
        error = None
        if runtime_restart:
            self.sendShellCommand("setprop ro.test_harness 1", retry_count=retry_count)
            # manual rest bootcomplete flag
            self.sendShellCommand("setprop dev.bootcomplete 0",
                                                        retry_count=retry_count)
            self.sendShellCommand("stop", retry_count=retry_count)

        try:
            output = self.sendCommand("sync", retry_count=retry_count)
        except AbortError, e:
            error = e
            output = e.msg
        if "Read-only file system" in output:
            logger.SilentLog(output)
            logger.Log("Remounting read-only filesystem")
            self.sendCommand("remount")
            output = self.sendCommand("sync", retry_count=retry_count)
        elif "No space left on device" in output:
            logger.SilentLog(output)
            logger.Log("Restarting device runtime")
            self.sendShellCommand("stop", retry_count=retry_count)
            output = self.sendCommand("sync", retry_count=retry_count)
            self.sendShellCommand("start", retry_count=retry_count)
        elif error is not None:
            # exception occurred that cannot be recovered from
            raise error
        logger.SilentLog(output)
        if runtime_restart:
            # start runtime and wait till boot complete flag is set
            self.sendShellCommand("start", retry_count=retry_count)
            self.waitForBootComplete()
            # press the MENU key, this will disable key guard if runtime is started
            # with ro.monkey set to 1
            self.sendShellCommand("input keyevent 82", retry_count=retry_count)
        else:
            self.waitForDevicePm()
        return output

    def getSerialNumber(self):
        """Returns the serial number of the targeted device."""
        return self.sendCommand("get-serialno").strip()
    
    def getLogcat(self, tag = None, level = None):
#         logger.debug("Attaching to a logcat pipe...")
#         if not self.is_alive():
#             logger.error("The device [%s] is not running!" % self.device_name)
#             return None
        
#         if tag == None: tag = '*'
#         if level == None: level = 'V'
#         if level.upper() not in AdbInterface.LOG_LEVELS:
#             logger.error("The log level %s is not specified correctly!" % str(level))
#         
#         command = ['adb', '-s', self.device_name, 'logcat', '%s:%s' % (tag, level)]
#         if tag != '*':
#             command.append('*:S')
        
        cmd = "logcat %s:%s" % (tag, level)
        if tag != '*':
            # if we get only specified tag all others need to be suppressed
            cmd = ' '.join(cmd, "*:S")
        
        return self.sendCommand(cmd, timeout_time=None)
    
    
    def cleanLogcat(self):
#         logger.debug("Cleaning logcat...")
#         if not self.is_alive():
#             logger.error("The device [%s] is not running!" % self.device_name)
#             return
#         
#         try:
#             with open(os.devnull, 'w') as f_null:
#                 subprocess.check_call(['adb', '-s', self.device_name, 'logcat', '-c'], stderr=f_null)
#         except subprocess.CalledProcessError:
#             logger.error("Could not clean logcat!")
#             return
#         
#         logger.debug("Logcat is cleaned!")
        
        cmd = "logcat -c"
        runCommand(cmd=cmd, return_output=False)
            
    def getPackageUid(self, package_name):
        logger.debug("Getting UID of the package [%s]..." % package_name)
        uid = -1
        if not self.is_alive():
            logger.error("The device [%s] is not running!" % self.device_name)
            return uid
        if package_name == "":
            logger.warning("The name of the package is not specified!")
            return uid
        
        uid_lines = subprocess.check_output(['adb', '-s', self.device_name, 'shell', 'cat', '/data/system/packages.list'])
        lines = uid_lines.splitlines()
        for i in range(0,len(lines)): #first line just announces the list of devices
            words = lines[i].split(' ')
            if words[0].strip() == package_name:
                uid = int(words[1].strip())
                break
        
        logger.debug("The UID of the package [%s] is [%d]" % (package_name, uid))
        return uid
    
    def startActivityExplicitly(self, package_name, activity_name):
        #adb shell am start -n com.package.name/com.package.name.ActivityName 
        logger.debug("Starting activity [%s] of the package [%s]..." % (package_name, activity_name))
        
        if not package_name:
            logger.error("The name of the package is not specified!")
            return
        
        if not activity_name:
            logger.error("The name of the activity is not specified!")
            return
        
        run_string = package_name + '/' + activity_name
        cmd = "am start -n %s" % run_string
        self.sendShellCommand(cmd)
    
    def startActivityImplicitely(self, action=None, dataUri=None, mimeType=None, category=None, flags=0, extra={}):
        intent = self._createIntent(action=action, data_uri=dataUri, mime_type=mimeType, category=category, flags=flags, extra=extra)
        cmd = "am start %s" % intent
        self.sendShellCommand(cmd)
        
        
    def startServiceExplicitly(self, package_name, service_name):
        #adb shell am start -n com.package.name/com.package.name.ActivityName 
        logger.debug("Starting service [%s] from the package [%s]..." % (package_name, service_name))
        
        if not package_name:
            logger.error("The name of the package is not specified!")
            return
        
        if not service_name:
            logger.error("The name of the activity is not specified!")
            return
        
        run_string = package_name + '/' + service_name
        cmd = "am startservice -n %s" % run_string
        self.sendShellCommand(cmd)
        
    def startServiceImplicitely(self, action=None, dataUri=None, mimeType=None, category=None, flags=0, extra={}):
        intent = self._createIntent(action=action, data_uri=dataUri, mime_type=mimeType, category=category, flags=flags, extra=extra)
        cmd = "am startservice %s" % intent
        self.sendShellCommand(cmd)    
    
    
    def sendBroadcast(self, action=None, dataUri=None, mimeType=None, category=None, component=None, flags = 0, extra={}):
        intent = self._createIntent(action=action,
                                    data_uri=dataUri,
                                    mime_type=mimeType,
                                    category=category,
                                    component=component,
                                    flags=flags,
                                    extra=extra)
        cmd = "am broadcast %s" % intent
        self.sendShellCommand(cmd)
        
    def _createIntent(self, action=None, data_uri=None, mime_type=None, category=None, component=None, flags = 0, extra={}):
        intent =  ""
        if action:
            intent += " -a '%s'" % action
        if data_uri:
            intent += " -d '%s'" % data_uri
        if mime_type:
            intent += " -t '%s'" % mime_type
        if category:
            intent += " -c '%s'" % category
        if component:
            intent += " -n '%s'" % component
        if flags > 0:
            intent += " -f %d" % flags
        
        if extra:
            for entry in iteritems(extra):
                intent += " %s %s %s" % (TYPE_KEY.get(entry[1][0]), entry[0], entry[1][1]) 
        
        return intent
    
    def runMonkeyTest(self, timeout=None, packageName=None, verbosityLevel=0, 
            seed=None, throttle=0, eventsCount=500, dbgNoEvents=False, 
            hprof=False, ignoreCrashes=False, ignoreTimeouts=False, ignoreSecurityExceptions=False,
            killProcessAfterError=False, monitorNativeCrashes=False, waitDbg=False):
        
        options = ""
        if packageName:
            options += " -p %s" % packageName
        if verbosityLevel > 0:
            options += " -v"*verbosityLevel
        if seed:
            options += " -s %s" % str(seed) 
        if throttle > 0:
            options += " --throttle %d" % throttle
        if dbgNoEvents:
            options += " --dbg-no-events"
        if hprof:
            options += " --hprof"
        if ignoreCrashes:
            options += " --ignore-crashes"
        if ignoreTimeouts:
            options += " --ignore-timeouts"
        if ignoreSecurityExceptions:
            options += " --ignore-security-exceptions"
        if killProcessAfterError:
            options += " --kill-process-after-error"
        if monitorNativeCrashes:
            options += " --monitor-native-crashes"
        if waitDbg:
            options += " --wait-dbg"
        
        
        cmd = "monkey %s %d" % (options, eventsCount) 
        print cmd
        return self.sendShellCommand(cmd, timeout_time=timeout, retry_count=1)

def ParseAmInstrumentOutput(result):
    """Given the raw output of an "am instrument" command that targets and
    InstrumentationTestRunner, return structured data.

    Args:
        result (string): Raw output of "am instrument"

    Return
    (test_results, inst_finished_bundle)
    
    test_results (list of am_output_parser.TestResult)
    inst_finished_bundle (dict): Key/value pairs contained in the bundle that is
        passed into ActivityManager.finishInstrumentation(). Included in this bundle is the return
        code of the Instrumentation process, any error codes reported by the
        activity manager, and any results explicity added by the instrumentation
        code.
    """

    re_status_code = re.compile(r'INSTRUMENTATION_STATUS_CODE: (?P<status_code>-?\d)$')
    test_results = []
    inst_finished_bundle = {}

    result_block_string = ""
    for line in result.splitlines():
        result_block_string += line + '\n'

        if "INSTRUMENTATION_STATUS_CODE:" in line:
            test_result = TestResult(result_block_string)
            if test_result.GetStatusCode() == 1: # The test started
                pass
            elif test_result.GetStatusCode() in [0, -1, -2]:
                test_results.append(test_result)
            else:
                pass
            result_block_string = ""
        if "INSTRUMENTATION_CODE:" in line:
            inst_finished_bundle = _ParseInstrumentationFinishedBundle(result_block_string)
            result_block_string = ""

    return (test_results, inst_finished_bundle)


def _ParseInstrumentationFinishedBundle(result):
    """Given the raw output of "am instrument" returns a dictionary of the
    key/value pairs from the bundle passed into 
    ActivityManager.finishInstrumentation().

    Args:
        result (string): Raw output of "am instrument"

    Return:
    inst_finished_bundle (dict): Key/value pairs contained in the bundle that is
        passed into ActivityManager.finishInstrumentation(). Included in this bundle is the return
        code of the Instrumentation process, any error codes reported by the
        activity manager, and any results explicity added by the instrumentation
        code.
    """

    re_result = re.compile(r'INSTRUMENTATION_RESULT: ([^=]+)=(.*)$')
    re_code = re.compile(r'INSTRUMENTATION_CODE: (\-?\d)$')
    result_dict = {}
    key = ''
    val = ''
    last_tag = ''

    for line in result.split('\n'):
        line = line.strip(string.whitespace)
        if re_result.match(line):
            last_tag = 'INSTRUMENTATION_RESULT'
            key = re_result.search(line).group(1).strip(string.whitespace)
            if key.startswith('performance.'):
                key = key[len('performance.'):]
            val = re_result.search(line).group(2).strip(string.whitespace)
            try:
                result_dict[key] = float(val)
            except ValueError:
                result_dict[key] = val
            except TypeError:
                result_dict[key] = val
        elif re_code.match(line):
            last_tag = 'INSTRUMENTATION_CODE'
            key = 'code'
            val = re_code.search(line).group(1).strip(string.whitespace)
            result_dict[key] = val
        elif 'INSTRUMENTATION_ABORTED:' in line:
            last_tag = 'INSTRUMENTATION_ABORTED'
            key = 'INSTRUMENTATION_ABORTED'
            val = ''
            result_dict[key] = val
        elif last_tag == 'INSTRUMENTATION_RESULT':
            result_dict[key] += '\n' + line

    if not result_dict.has_key('code'):
        result_dict['code'] = '0'
        result_dict['shortMsg'] = "No result returned from instrumentation"

    return result_dict


class TestResult(object):
    """A class that contains information about a single test result."""

    def __init__(self, result_block_string):
        """
        Args:
            result_block_string (string): Is a single "block" of output. A single
            "block" would be either a "test started" status report, or a "test
            finished" status report.
        """

        self._test_name = None
        self._status_code = None
        self._failure_reason = None
        self._fields_map = {}

        re_status_code = re.search(r'INSTRUMENTATION_STATUS_CODE: '
                '(?P<status_code>1|0|-1|-2)', result_block_string)
        re_fields = re.compile(r'INSTRUMENTATION_STATUS: '
                '(?P<key>[\w.]+)=(?P<value>.*?)(?=\nINSTRUMENTATION_STATUS)', re.DOTALL)

        for field in re_fields.finditer(result_block_string):
            key, value = (field.group('key').strip(), field.group('value').strip())
            if key.startswith('performance.'):
                key = key[len('performance.'):]
            self._fields_map[key] = value
        self._fields_map.setdefault('class')
        self._fields_map.setdefault('test')

        self._test_name = '%s:%s' % (self._fields_map['class'],
                                                                 self._fields_map['test'])
        self._status_code = int(re_status_code.group('status_code'))
        if 'stack' in self._fields_map:
            self._failure_reason = self._fields_map['stack']

    def GetTestName(self):
        return self._test_name

    def GetStatusCode(self):
        return self._status_code

    def GetFailureReason(self):
        return self._failure_reason

    def GetResultFields(self):
        return self._fields_map
    
    
"""Defines common exception classes for this package."""
#TODO: put exceptions in a separate file

class MsgException(Exception):
  """Generic exception with an optional string msg."""
  def __init__(self, msg=""):
    self.msg = msg


class WaitForResponseTimedOutError(Exception):
  """We sent a command and had to wait too long for response."""


class DeviceUnresponsiveError(Exception):
  """Device is unresponsive to command."""


class InstrumentationError(Exception):
  """Failed to run instrumentation."""


class AbortError(MsgException):
  """Generic exception that indicates a fatal error has occurred and program
  execution should be aborted."""


class ParseError(MsgException):
  """Raised when xml data to parse has unrecognized format."""
  
  
  
_abort_on_error = False

def setAbortOnError(abort=True):
    """Sets behavior of runCommand to throw AbortError if command process returns
    a negative error code"""
    global _abort_on_error
    _abort_on_error = abort

def runCommand(cmd, timeout_time=None, retry_count=3, return_output=True,
                             stdin_input=None):
    """Spawn and retry a subprocess to run the given shell command.

    Args:
        cmd: shell command to run
        timeout_time: time in seconds to wait for command to run before aborting.
        retry_count: number of times to retry command
        return_output: if True return output of command as string. Otherwise,
            direct output of command to stdout.
        stdin_input: data to feed to stdin
    Returns:
        output of command
    """
    result = None
    while True:
        try:
            result = runOnce(cmd, timeout_time=timeout_time,
                                             return_output=return_output, stdin_input=stdin_input)
        except WaitForResponseTimedOutError:
            if retry_count == 0:
                raise
            retry_count -= 1
            logger.info("No response for %s, retrying" % cmd)
        else:
            # Success
            return result

def runOnce(cmd, timeout_time=None, return_output=True, stdin_input=None):
    """Spawns a subprocess to run the given shell command.

    Args:
        cmd: shell command to run
        timeout_time: time in seconds to wait for command to run before aborting.
        return_output: if True return output of command as string. Otherwise,
            direct output of command to stdout.
        stdin_input: data to feed to stdin
    Returns:
        output of command
    Raises:
        adb_interface_errors.WaitForResponseTimedOutError if command did not complete within
            timeout_time seconds.
        adb_interface_errors.AbortError is command returned error code and setAbortOnError is on.
    """
    start_time = time.time()
    so = []
    pid = []
    global _abort_on_error, error_occurred
    error_occurred = False

    def Run():
        global error_occurred
        if return_output:
            output_dest = subprocess.PIPE
        else:
            # None means direct to stdout
            output_dest = None
        if stdin_input:
            stdin_dest = subprocess.PIPE
        else:
            stdin_dest = None
        pipe = subprocess.Popen(
                cmd,
                executable='/bin/bash',
                stdin=stdin_dest,
                stdout=output_dest,
                stderr=subprocess.STDOUT,
                shell=True)
        pid.append(pipe.pid)
        try:
            output = pipe.communicate(input=stdin_input)[0]
            if output is not None and len(output) > 0:
                so.append(output)
        except OSError, e:
            logger.debug("failed to retrieve stdout from: %s" % cmd)
            logger.error(e)
            so.append("ERROR")
            error_occurred = True
        if pipe.returncode:
            logger.debug("Error: %s returned %d error code" %(cmd,
                    pipe.returncode))
            error_occurred = True

    t = threading.Thread(target=Run)
    t.start()

    break_loop = False
    while not break_loop:
        if not t.isAlive():
            break_loop = True

        # Check the timeout
        if (not break_loop and timeout_time is not None
                and time.time() > start_time + timeout_time):
            try:
                os.kill(pid[0], signal.SIGKILL)
            except OSError:
                # process already dead. No action required.
                pass

            logger.debug("about to raise a timeout for: %s" % cmd)
            raise WaitForResponseTimedOutError
        if not break_loop:
            time.sleep(0.1)

    t.join()
    output = "".join(so)
    if _abort_on_error and error_occurred:
        raise AbortError(msg=output)

    return "".join(so)
