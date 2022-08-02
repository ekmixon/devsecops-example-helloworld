#!/usr/local/bin/python2.6
# encoding: utf-8
'''
BrowserTest -- shortdesc

BrowserTest is a description

It defines classes_and_methods

@author:     user_name
'''


import sys
import os
import re
import unittest
import __main__ as main

from webdriver.browsertest.Result import Result
from webdriver.browsertest.Reporter import Reporter
from webdriver.browsertest.Bootstrap import Bootstrap
from webdriver.browsertest.Container import Container 

class TestSuite:

    webDriver = None
    reporter = None

    def __init__(self, top = None, pattern = None, verbose = None, clazz = None):
        self._verbose = self._verbose(verbose)
        self._convertArguments()
        if clazz is None:
            self._pattern = pattern or "test_.*\.py$"
            self._testSuite = self._createSuite(top)
        else:
            self._testSuite = self._createSuiteFromTestCase(clazz)
        TestSuite.reporter = self._reporter()
        self._inputEncoding = os.getenv("INPUT_ENCODING", 'utf-8')

    def run(self, verbosity = 2, runner = None):
        reload(sys)
        #sys.setdefaultencoding(self._inputEncoding)
        if TestSuite.reporter:
            TestSuite.reporter.openResultsFile()
        if not runner:
            testReportsDir = os.getenv("TEST_REPORTS_DIR")
            if testReportsDir is None:
                runner = unittest.TextTestRunner(verbosity = verbosity)
            else:
                import xmlrunner
                self._log("Sending XML output to '{0}' (encoding={1})".format(testReportsDir,\
                        self._inputEncoding))
                runner = xmlrunner.XMLTestRunner(verbosity = verbosity, output = testReportsDir)
        reload(sys)
        if os.getenv("REUSE_DRIVER") is not None:
            self._log("Reuse WebDriver for all tests")
            TestSuite.webDriver = Container()
        else:
            self._log("Create a new WebDriver for each test")
        self._log("About to run test")
        successful = self.isSuccessful(runner.run(self._testSuite))
        self._log("Test suite successful:{0}".format(successful))
        if TestSuite.webDriver is not None:
            TestSuite.webDriver.teardownDriver(successful)
        if TestSuite.reporter:
            TestSuite.reporter.closeResultsFile()

    def isSuccessful(self, result):
        return Result.convert(result) == Result.PASS

    def _verbose(self, verbose):
        if (verbose == True):
            return True
        for arg in sys.argv:
            if arg == "--verbose":
                return True
        return os.getenv("VERBOSE") is not None

    def _log(self, message):
        if self._verbose:
            print message
            #time.sleep(1)
    def _createSuiteFromTestCase(self, clazz):
        testSuite = unittest.TestSuite()
        testSuite.addTests(unittest.TestLoader().loadTestsFromTestCase(clazz))
        return testSuite

    def _createSuite(self, top):
        directories = self._findDirectories(top)
        #sys.path.insert(1, top)
        loader = unittest.TestLoader()
        suiteList = [self._discover(loader, directory) for directory in directories]
        directories = self._findDirectories(top)
        return unittest.TestSuite(suiteList)

    def _discover(self, loader, directory, prefix = None):
        directory = directory or "."
        self._log("Discovering test cases in {0}".format(directory))

        testSuite = unittest.TestSuite()
        pattern = re.compile(self._pattern)
        moduleName = self._moduleName(directory)
        if moduleName != "":
            sys.path.insert(1, directory)
        files = os.listdir(directory)
        files = sorted(files)
        for f in files:
            if pattern.match(f):
                self._log(f"Checking {f} for {self._pattern}")
                testName = self._testName(f)
                if testName != "":
                    self._log("Found test {0} in {1}".format(testName, f"{directory}/{f}"))
                    testSuite.addTests(loader.loadTestsFromName(testName))
        return testSuite

    def _moduleName(self, directory):
        path = directory
        path = path[1:] if path.startswith(".") else path
        path = path[1:] if path.startswith("/") else path
        return ".".join(path.split("/"))

    def _testName(self, f):
        return f[:-3] if f.endswith(".py") else f

    def _findDirectories(self, top = None, prefix = None):
        #self._log("Running - {0} -".format(main.__file__))
        top = top or os.path.dirname(main.__file__)
        self._log("Checking {0} for directories".format(top if prefix is None else prefix))
        prefix = "" if prefix is None else prefix
        directories = [top]
        entries = os.listdir(top)
        for entry in entries:
            if os.path.isdir(f"{top}/{entry}"):
                entryDir = f"/{entry}"
                self._log("Adding directory {0} ".format(prefix + entryDir ))
                directories += self._findDirectories(top + entryDir , prefix = entryDir )
        return directories

    def _convertArguments(self):
        parameters = [ "execution-id", "test-reports-dir", "verbose", "implicit-wait", \
            "environment", "reuse-driver", "results-file",\
            "base-url", "cookie", "step-delay", "default-wait", \
            "webdriver-class", "webdriver-capabilities", \
            "location", "remote-username", "remote-accesskey", "remote-url", \
            "remote-test-id", "build", "default-window-width"]
        Bootstrap.convertArgumentsToVariables(parameters)

    def _reporter(self):
        return Reporter(resultsFile) if (resultsFile := self._resultsFile()) else None

    def _resultsFile(self):
        return os.getenv("RESULTS_FILE")

