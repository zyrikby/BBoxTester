package com.zhauniarovich.bbtester;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.Map;
import java.util.Set;

import android.app.Activity;
import android.app.Application;
import android.app.Instrumentation;
import android.app.Service;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Bundle;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.Looper;
import android.os.Message;
import android.util.Log;
import android.os.Process;

public class EmmaInstrumentation extends Instrumentation implements Handler.Callback {
	private static final String TAG = "EmmaInstrumentation";
    private static final boolean LOGD = true;
    
    private final static String DEFAULT_REPORT_ROOTDIR = "/mnt/sdcard";
    private static final String ERRORS_FILENAME = "errors.txt";
//    private static final int SHELL_UID = android.os.Process.getUidForName("shell");
    
    private static final String ACTION_FINISH_TESTING = "com.zhauniarovich.bbtester.finishtesting";
    
    private static final String PREFIX_ONSTOP = "onstop";
    private static final String PREFIX_ONERROR = "onerror";
    

    private final Bundle mResults = new Bundle();

    private static final String KEY_COVERAGE = "coverage";
    private static final String KEY_PROCEED_ON_ERROR = "proceedOnError";
    private static final String KEY_GENERATE_COVERAGE_REPORT_ON_ERROR = "generateCoverageReportOnError";
	private static final String KEY_REPORT_FOLDER = "coverageDir";
	private static final String KEY_CANCEL_ANALYSIS = "cancelAnalysis";
    
	private boolean mCoverage = true;
    private boolean generateCoverageOnError = true;
    private boolean proceedOnError = false;
    private boolean cancelAnalysis = false;
    
    private File reportDir = null;
    private File errorFile = null;
    
    private static int errorCounter = 0;
    
    
    private Handler handler;

    /**
     * Constructor
     */
    public EmmaInstrumentation() {
    	super();
    	if (LOGD) {
			Log.d(TAG, "Constructor Thread: " + Thread.currentThread().getName());
		}
    }

    @Override
    public void onCreate(Bundle arguments) {
    	super.onCreate(arguments);
    	if (LOGD) {
    		Log.d(TAG, "onCreate Thread: " + Thread.currentThread().getName());
    	}
    	if (arguments == null) {
    		Log.e(TAG, "Cannot start our instrumentation! Arguments are null!");
    		finish(Activity.RESULT_CANCELED, mResults);
    		return;
    	}
    	
    	String reportDirPath;
    	
    	mCoverage = getBooleanArgument(arguments, KEY_COVERAGE);
    	reportDirPath = arguments.getString(KEY_REPORT_FOLDER, null);
    	if (reportDirPath == null) {
    		reportDirPath = (new File(DEFAULT_REPORT_ROOTDIR, getComponentName().getPackageName())).getAbsolutePath();
    	}
    	proceedOnError = getBooleanArgument(arguments, KEY_PROCEED_ON_ERROR);
    	generateCoverageOnError = getBooleanArgument(arguments, KEY_GENERATE_COVERAGE_REPORT_ON_ERROR);
    	
    	
    	reportDir = new File(reportDirPath);
    	boolean success = reportDir.mkdirs();
    	if (LOGD) {
			Log.d(TAG, "ReportDir created: " + success);
		}
    	errorFile = new File(reportDir, ERRORS_FILENAME);
    	
    	if (LOGD) {
			Log.d(TAG, "Intent: " + arguments.toString());
		}
    	
    	HandlerThread handlerThread = new HandlerThread("MyNewThread");
    	handlerThread.start();
    	Looper looper = handlerThread.getLooper();
    	handler = new Handler(looper, this);
    	
        IntentFilter iFilter = new IntentFilter(ACTION_FINISH_TESTING);
        getContext().registerReceiver(mMessageReceiver, iFilter, null, handler);
        
        start();
        if (LOGD) {
			Log.d(TAG, "After start!");
		}
    }

    @Override
    public void onStart() {
        super.onStart();
        if (LOGD) {
    		Log.d(TAG, "onStart Thread: " + Thread.currentThread().getName());
    	}
        Looper.prepare();
    }
    
    private boolean getBooleanArgument(Bundle arguments, String tag) {
        String tagString = arguments.getString(tag);
        return tagString != null && Boolean.parseBoolean(tagString);
    }

    private void generateCoverageReport(String filename) {
    	if (LOGD) {
			Log.d(TAG, "");
		}
        java.io.File coverageFile = new java.io.File(reportDir, filename);
        if (LOGD)
            Log.d(TAG, "generateCoverageReport(): " + coverageFile.getAbsolutePath());
        // We may use this if we want to avoid reflection and we include
        // emma.jar
        // RT.dumpCoverageData(coverageFile, false, false);

        // Use reflection to call emma dump coverage method, to avoid
        // always statically compiling against emma jar
        try {
            Class<?> emmaRTClass = Class.forName("com.vladium.emma.rt.RT");
            Method dumpCoverageMethod = emmaRTClass.getMethod(
                    "dumpCoverageData", coverageFile.getClass(), boolean.class,
                    boolean.class);
            dumpCoverageMethod.invoke(null, coverageFile, false, false);
        } catch (ClassNotFoundException e) {
            reportEmmaError("Is emma jar on classpath?", e);
        } catch (SecurityException e) {
            reportEmmaError(e);
        } catch (NoSuchMethodException e) {
            reportEmmaError(e);
        } catch (IllegalArgumentException e) {
            reportEmmaError(e);
        } catch (IllegalAccessException e) {
            reportEmmaError(e);
        } catch (InvocationTargetException e) {
            reportEmmaError(e);
        }
    }

    private void reportEmmaError(Exception e) {
        reportEmmaError("", e);
    }

    private void reportEmmaError(String hint, Exception e) {
        String msg = "Failed to generate emma coverage. " + hint;
        Log.e(TAG, msg, e);
        mResults.putString(Instrumentation.REPORT_KEY_STREAMRESULT, "\nError: "
                + msg);
    }



    /**
     * BroadcastReceiver handler for intent sending to finish testing of application.
     */
    private BroadcastReceiver mMessageReceiver = new BroadcastReceiver() {
    	@Override
    	public void onReceive(Context context, Intent intent) {
    		// TODO: Check this code later
    		//checking that the intent is sent from the adb shell
//    		final int callingUid = Binder.getCallingUid();
//    		if (callingUid != SHELL_UID) {
//    			return;
//    		}
        	if (LOGD) {
        		Log.d(TAG, "onReceive Thread: " + Thread.currentThread().getName());
        	}
    		
    		final Bundle arguments = intent.getExtras();
    		if (arguments != null) {
    			cancelAnalysis = arguments.getBoolean(KEY_CANCEL_ANALYSIS, false);
            }
    		
    		if (cancelAnalysis) {
    			removeDirectory(reportDir);
    			handler.sendEmptyMessage(0);
    			return;
    		}
    		
    		if (mCoverage) {
    			final long currentTime = System.currentTimeMillis();
    			String filename = PREFIX_ONSTOP  + "_coverage_" + String.valueOf(currentTime) + ".ec";
    			generateCoverageReport(filename);
    		}
    		
    		handler.sendEmptyMessage(0);
    	}
    };

	@Override
	public void finish(int resultCode, Bundle results) {
		if (LOGD) {
			Log.d(TAG, "Finish Thread: " + Thread.currentThread().getName());
		}
		super.finish(resultCode, results);
	}

	@Override
	public void onDestroy() {
		if (LOGD) {
			Log.d(TAG, "OnDestroy Thread: " + Thread.currentThread().getName());
		}
		getContext().unregisterReceiver(mMessageReceiver);
		handler = null;
		super.onDestroy();
	}

	@Override
	public boolean onException(Object obj, Throwable e) {
		if (LOGD) {
			Log.d(TAG, "OnException Thread: " + Thread.currentThread().getName());
		}

		long currentTimeMillis = System.currentTimeMillis();
		String coverageFileName = null;
		if (generateCoverageOnError) {
			coverageFileName = PREFIX_ONERROR + "_coverage_" + String.valueOf(currentTimeMillis) + ".ec";
			generateCoverageReport(coverageFileName);
		}
		
		try {
			appendError(currentTimeMillis, coverageFileName, obj, e);
		}
		catch(IOException exc) {
			exc.printStackTrace();
		}
		
		//true - continue to execute tests, false - let the exception to be fired
		return proceedOnError;
	}

	private void appendError(long timeMillis, String coverageFileName, Object obj, Throwable e) throws IOException  {
		String errorComp;
		if (obj == null) {
			errorComp = "null";
		}
		else if (obj instanceof Application) {
			errorComp = "Application";
		}
		else if (obj instanceof Activity) {
			errorComp = "Activity";
		}
		else if (obj instanceof Service) {
			errorComp = "Service";
		}
		else if (obj instanceof BroadcastReceiver) {
			errorComp = "BroadcastReceiver";
		}
		else {
			errorComp = obj.getClass().getSimpleName();
		}
		
		String errorSource = "null";
		if (obj != null) {
			errorSource = obj.getClass().getName();
		}
		
		
		StringBuffer errorStr = new StringBuffer();
		
		errorStr.append("ErrorCount: ").append(errorCounter++).append("\n");
		errorStr.append("Time: ").append(timeMillis).append("\n");
		errorStr.append("CoverageFile: ").append(coverageFileName != null ? coverageFileName : "").append("\n");
		errorStr.append("PackageName: ").append(getComponentName().getPackageName()).append("\n");
		errorStr.append("ProcessPid: ").append(Process.myPid()).append("\n");
		errorStr.append("ErrorComponent: ").append(errorComp).append("\n");
		errorStr.append("ErrorSource: ").append(errorSource).append("\n");
		errorStr.append("ShortMsg: ").append(e.toString()).append("\n");
		errorStr.append("LongMsg: ").append(e.getMessage()).append("\n");
		errorStr.append("Stack: \n").append(getStackTrace(e)).append("\n");
//		errorStr.append("------------------------------------------------------------").append("\n");
//		errorStr.append("THREAD_STATE: \n").append(getThreadState()).append("\n");
		errorStr.append("============================================================").append("\n\n");
		
		if (LOGD) {
			Log.d(TAG, "Error:\n" + errorStr.toString());
		}
		
		if (!errorFile.exists()) {
			errorFile.createNewFile();
		}
		FileWriter fileWritter = new FileWriter(errorFile, true);
        BufferedWriter bufferWritter = new BufferedWriter(fileWritter);
        bufferWritter.write(errorStr.toString());
        bufferWritter.close();
	}
	
	private String getStackTrace(Throwable e) {
		StringWriter sw = new StringWriter();
		PrintWriter pw = new PrintWriter(sw);
		e.printStackTrace(pw);
		return sw.toString(); // stack trace as a string;
	}
	
//	private static String getThreadState() {
//		Set<Map.Entry<Thread, StackTraceElement[]>> threads = Thread.getAllStackTraces().entrySet();
//		StringBuilder threadState = new StringBuilder();
//		for (Map.Entry<Thread, StackTraceElement[]> threadAndStack : threads) {
//			StringBuilder threadMessage = new StringBuilder("  ").append(threadAndStack.getKey());
//			threadMessage.append("\n");
//			for (StackTraceElement ste : threadAndStack.getValue()) {
//				threadMessage.append("    ");
//				threadMessage.append(ste.toString());
//				threadMessage.append("\n");
//			}
//			threadMessage.append("\n");
//			threadState.append(threadMessage.toString());
//		}
//		return threadState.toString();
//	}

	private static void removeDirectory(File dir) {
	    if (dir.isDirectory()) {
	        File[] files = dir.listFiles();
	        if (files != null && files.length > 0) {
	            for (File aFile : files) {
	                removeDirectory(aFile);
	            }
	        }
	        dir.delete();
	    } else {
	        dir.delete();
	    }
	}

	@Override
	public boolean handleMessage(Message msg) {
		if (LOGD) {
			Log.d(TAG, "handleMessage Thread: " + Thread.currentThread().getName());
		}
		finish(Activity.RESULT_OK, mResults);
		return false;
	}
}

