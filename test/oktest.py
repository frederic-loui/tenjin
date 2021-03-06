# -*- coding: utf-8 -*-

###
### oktest.py -- new style test utility
###
### $Release: 0.11.0 $
### $Copyright: copyright(c) 2010-2011 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

__all__ = ('ok', 'NOT', 'NG', 'not_ok', 'run', 'spec', 'test', 'fail', 'skip', 'todo', 'subject', 'situation', 'main')
__version__ = "$Release: 0.11.0 $".split()[1]

import sys, os, re, types, traceback, time, linecache

python2 = sys.version_info[0] == 2
python3 = sys.version_info[0] == 3
if python2:
    from cStringIO import StringIO
if python3:
    xrange = range
    from io import StringIO


def _new_module(name, local_vars, util=None):
    try:
        mod = type(sys)(name)
    except:
        # The module creation above does not work for Jython 2.5.2
        import imp
        mod = imp.new_module(name)
    sys.modules[name] = mod
    mod.__dict__.update(local_vars)
    if util and getattr(mod, '__all__', None):
        for k in mod.__all__:
            util.__dict__[k] = mod.__dict__[k]
        util.__all__ += mod.__all__
    return mod


__unittest = True    # see unittest.TestResult._is_relevant_tb_level()


config = _new_module('oktest.config', {
    "debug": False,
    #"color_enabled": _sys.platform.startswith(('darwin', 'linux', 'freebsd', 'netbsd'))  # not work on Python2.4
    #"color_enabled": any(lambda x: _sys.platform.startswith(x), ('darwin', 'linux', 'freebsd', 'netbsd'))  # not work on Python2.4
    "color_available": bool([ 1 for p in ('darwin', 'linux', 'freebsd', 'netbsd') if sys.platform.startswith(p) ]),
    "color_enabled":  None,    # None means detect automatiallly
    "TARGET_PATTERN": '.*(Test|TestCase|_TC)$',   # class name pattern of test case
})


## not used for compatibility with unittest
#class TestFailed(AssertionError):
#
#    def __init__(self, mesg, file=None, line=None, diff=None):
#        AssertionError.__init__(self, mesg)
#        self.file = file
#        self.line = line
#        self.diff = diff
#

ASSERTION_ERROR = AssertionError


def _diff_p(target, op, other):
    if op != '==':             return False
    if target == other:        return False
    #if not util._is_string(target): return False
    #if not util._is_string(other):  return False
    if not DIFF:               return False
    is_a = isinstance
    if is_a(target, str) and is_a(other, str):
        return True
    if python2 and is_a(target, unicode) and is_a(other, unicode):
        return True
    return False


def _truncated_repr(obj, max=80+15):
    s = repr(obj)
    if len(s) > max:
        return s[:max - 15] + ' [truncated]...'
    return s


def _msg(target, op, other=None):
    if   op.endswith('()'):   msg = '%r%s'     % (target, op)
    elif op.startswith('.'):  msg = '%r%s(%r)' % (target, op, other)
    else:                     msg = '%r %s %r' % (target, op, other)
    msg += " : failed."
    return msg


def _msg2(target, op, other=None):
    diff_str = _diff_p(target, op, other) and _diff(target, other) or ''
    if diff_str:
        #msg = "actual %s expected : failed.\n" % (op,)
        msg = "%s == %s : failed." % (_truncated_repr(target), _truncated_repr(other))
        return (msg, diff_str)
    else:
        return _msg(target, op, other)


DIFF = True

def _diff(target, other):
    from difflib import unified_diff
    if hasattr(DIFF, '__call__'):
        expected = [ DIFF(line) + "\n" for line in other.splitlines(True) ]
        actual   = [ DIFF(line) + "\n" for line in target.splitlines(True) ]
    else:
        if other.find("\n") == -1 and target.find("\n") == -1:
            expected, actual = [other + "\n"], [target + "\n"]
        else:
            expected, actual = other.splitlines(True), target.splitlines(True)
            if not expected: expected.append('')
            if not actual:   actual.append('')
            for lines in (expected, actual):
                if not lines[-1].endswith("\n"):
                    lines[-1] += "\n\\ No newline at end of string\n"
    return ''.join(unified_diff(expected, actual, 'expected', 'actual', n=2))


def assertion(func):
    """decorator to declare assertion function.
       ex.
         @oktest.assertion
         def startswith(self, arg):
           boolean = self.target.startswith(arg)
           if boolean != self.boolean:
             self.failed("%r.startswith(%r) : failed." % (self.target, arg))
         #
         ok ("Sasaki").startswith("Sas")
    """
    def deco(self, *args):
        self._tested = True
        return func(self, *args)
    deco.__name__ = func.__name__
    deco.__doc__ = func.__doc__
    setattr(AssertionObject, func.__name__, deco)
    return deco


#def deprecated(f):
#    return f


class AssertionObject(object):

    def __init__(self, target, boolean=True):
        self.target = target
        self.boolean = boolean
        self._tested = False
        self._location = None

    def __del__(self):
        if self._tested is False:
            msg = "%s() is called but not tested." % (self.boolean and 'ok' or 'not_ok')
            if self._location:
                msg += " (file '%s', line %s)" % self._location
            #import warnings; warnings.warn(msg)
            sys.stderr.write("*** warning: oktest: %s\n" % msg)

    #def not_(self):
    #    self.boolean = not self.boolean
    #    return self

    def failed(self, msg, depth=2, boolean=None):
        file, line = util.get_location(depth + 1)
        diff = None
        if isinstance(msg, tuple):
            msg, diff = msg
        if boolean is None: boolean = self.boolean
        if boolean is False:
            msg = 'not ' + msg
        raise self._assertion_error(msg, file, line, diff)

    def _assertion_error(self, msg, file, line, diff):
        #return TestFailed(msg, file=file, line=line, diff=diff)
        ex = ASSERTION_ERROR(diff and msg + "\n" + diff or msg)
        ex.file = file;  ex.line = line;  ex.diff = diff;  ex.errmsg = msg
        ex._raised_by_oktest = True
        return ex

    @property
    def should(self):           # UNDOCUMENTED
        """(experimental) allows user to call True/False method as assertion.
           ex.
             ok ("SOS").should.startswith("S")   # same as ok ("SOS".startswith("S")) == True
             ok ("123").should.isdigit()         # same as ok ("123".isdigit()) == True
        """
        return Should(self, self.boolean)

    @property
    def should_not(self):       # UNDOCUMENTED
        """(experimental) allows user to call True/False method as assertion.
           ex.
             ok ("SOS").should_not.startswith("X")   # same as ok ("SOS".startswith("X")) == False
             ok ("123").should_not.isalpha()         # same as ok ("123".isalpha()) == False
        """
        return Should(self, not self.boolean)


def _f():

    @assertion
    def __eq__(self, other):
        boolean = self.target == other
        if boolean == self.boolean:  return self
        #self.failed(_msg(self.target, '==', other))
        self.failed(_msg2(self.target, '==', other))

    @assertion
    def __ne__(self, other):
        boolean = self.target != other
        if boolean == self.boolean:  return self
        self.failed(_msg(self.target, '!=', other))

    @assertion
    def __gt__(self, other):
        boolean = self.target > other
        if boolean == self.boolean:  return self
        self.failed(_msg(self.target, '>', other))

    @assertion
    def __ge__(self, other):
        boolean = self.target >= other
        if boolean == self.boolean:  return self
        self.failed(_msg(self.target, '>=', other))

    @assertion
    def __lt__(self, other):
        boolean = self.target < other
        if boolean == self.boolean:  return self
        self.failed(_msg(self.target, '<', other))

    @assertion
    def __le__(self, other):
        boolean = self.target <= other
        if boolean == self.boolean:  return self
        self.failed(_msg(self.target, '<=', other))

    @assertion
    def in_delta(self, other, delta):
        boolean = self.target > other - delta
        if boolean != self.boolean:
            self.failed(_msg(self.target, '>', other - delta))
        boolean = self.target < other + delta
        if boolean != self.boolean:
            self.failed(_msg(self.target, '<', other + delta))
        return self

#    @assertion
#    def __contains__(self, other):
#        boolean = self.target in other
#        if boolean == self.boolean:  return self
#        self.failed(_msg(self.target, 'in', other))

    @assertion
    def in_(self, other):
        boolean = self.target in other
        if boolean == self.boolean:  return self
        self.failed(_msg(self.target, 'in', other))

    @assertion
    def not_in(self, other):
        boolean = self.target not in other
        if boolean == self.boolean:  return self
        self.failed(_msg(self.target, 'not in', other))

    @assertion
    def contains(self, other):
        boolean = other in self.target
        if boolean == self.boolean:  return self
        self.failed(_msg(other, 'in', self.target))

    @assertion
    def not_contain(self, other):  # DEPRECATED
        boolean = other in self.target
        if boolean == self.boolean:  return self
        self.failed(_msg(other, 'not in', self.target))

    @assertion
    def is_(self, other):
        boolean = self.target is other
        if boolean == self.boolean:  return self
        self.failed(_msg(self.target, 'is', other))

    @assertion
    def is_not(self, other):
        boolean = self.target is not other
        if boolean == self.boolean:  return self
        self.failed(_msg(self.target, 'is not', other))

    @assertion
    def is_a(self, other):
        boolean = isinstance(self.target, other)
        if boolean == self.boolean:  return self
        self.failed("isinstance(%r, %s) : failed." % (self.target, other.__name__))

    @assertion
    def is_not_a(self, other):
        boolean = not isinstance(self.target, other)
        if boolean == self.boolean:  return self
        self.failed("not isinstance(%r, %s) : failed." % (self.target, other.__name__))

    @assertion
    def has_attr(self, name):
        boolean = hasattr(self.target, name)
        if boolean == self.boolean:  return self
        self.failed("hasattr(%r, %r) : failed." % (self.target, name))

    @assertion
    def attr(self, name, expected):
        if not hasattr(self.target, name):
            self.failed("hasattr(%r, %r) : failed." % (self.target, name), boolean=True)
        boolean = getattr(self.target, name) == expected
        if boolean == self.boolean:  return self
        prefix = 'attr(%r): ' % name
        msg = _msg2(getattr(self.target, name), "==", expected)
        if isinstance(msg, tuple):
            msg = (prefix + msg[0], msg[1])
        else:
            msg = prefix + msg
        self.failed(msg)

    @assertion
    def matches(self, pattern, flags=0):
        if isinstance(pattern, type(re.compile('x'))):
            boolean = bool(pattern.search(self.target))
            if boolean == self.boolean:  return self
            self.failed("re.search(%r, %r) : failed." % (pattern.pattern, self.target))
        else:
            rexp = re.compile(pattern, flags)
            boolean = bool(rexp.search(self.target))
            if boolean == self.boolean:  return self
            self.failed("re.search(%r, %r) : failed." % (pattern, self.target))

    @assertion
    def not_match(self, pattern, flag=0):
        if isinstance(pattern, type(re.compile('x'))):
            boolean = not pattern.search(self.target)
            if boolean == self.boolean:  return self
            self.failed("not re.search(%r, %r) : failed." % (pattern.pattern, self.target))
        else:
            rexp = re.compile(pattern, flag)
            boolean = not rexp.search(self.target)
            if boolean == self.boolean:  return self
            self.failed("not re.search(%r, %r) : failed." % (pattern, self.target))

    @assertion
    def length(self, n):
        boolean = len(self.target) == n
        if boolean == self.boolean:  return self
        self.failed("len(%r) == %r : failed." % (self.target, n))

    @assertion
    def is_file(self):
        boolean = os.path.isfile(self.target)
        if boolean == self.boolean:  return self
        self.failed('os.path.isfile(%r) : failed.' % self.target)

    @assertion
    def not_file(self):
        boolean = not os.path.isfile(self.target)
        if boolean == self.boolean:  return self
        self.failed('not os.path.isfile(%r) : failed.' % self.target)

    @assertion
    def is_dir(self):
        boolean = os.path.isdir(self.target)
        if boolean == self.boolean:  return self
        self.failed('os.path.isdir(%r) : failed.' % self.target)

    @assertion
    def not_dir(self):
        boolean = not os.path.isdir(self.target)
        if boolean == self.boolean:  return self
        self.failed('not os.path.isdir(%r) : failed.' % self.target)

    @assertion
    def exists(self):
        boolean = os.path.exists(self.target)
        if boolean == self.boolean:  return self
        self.failed('os.path.exists(%r) : failed.' % self.target)

    @assertion
    def not_exist(self):
        boolean = not os.path.exists(self.target)
        if boolean == self.boolean:  return self
        self.failed('not os.path.exists(%r) : failed.' % self.target)

    @assertion
    def raises(self, exception_class, errmsg=None):
        return self._raise_or_not(exception_class, errmsg, self.boolean)

    @assertion
    def not_raise(self, exception_class=Exception):
        return self._raise_or_not(exception_class, None, not self.boolean)

    def _raise_or_not(self, exception_class, errmsg, flag_raise):
        ex = None
        try:
            self.target()
        except:
            ex = sys.exc_info()[1]
            if isinstance(ex, AssertionError) and not hasattr(ex, '_raised_by_oktest'):
                raise
            self.target.exception = ex
            if flag_raise:
                if not isinstance(ex, exception_class):
                    self.failed('%s%r is kind of %s : failed.' % (ex.__class__.__name__, ex.args, exception_class.__name__), depth=3)
                    #raise
                if errmsg is None:
                    pass
                elif isinstance(errmsg, _rexp_type):
                    if not errmsg.search(str(ex)):
                        self.failed("error message %r is not matched to pattern." % str(ex), depth=3)   # don't use ex2msg(ex)!
                else:
                    if str(ex) != errmsg:   # don't use ex2msg(ex)!
                        #self.failed("expected %r but got %r" % (errmsg, str(ex)))
                        self.failed("%r == %r : failed." % (str(ex), errmsg), depth=3)   # don't use ex2msg(ex)!
            else:
                if isinstance(ex, exception_class):
                    self.failed('%s should not be raised : failed, got %r.' % (exception_class.__name__, ex), depth=3)
        else:
            if flag_raise and ex is None:
                self.failed('%s should be raised : failed.' % exception_class.__name__, depth=3)
        return self

    AssertionObject._raise_or_not = _raise_or_not
    AssertionObject.hasattr = has_attr      # for backward compatibility
    AssertionObject.is_not_file = not_file  # for backward compatibility
    AssertionObject.is_not_dir  = not_dir   # for backward compatibility

_f()
del _f

_rexp_type = type(re.compile('x'))

ASSERTION_OBJECT = AssertionObject


def ok(target):
    obj = ASSERTION_OBJECT(target, True)
    obj._location = util.get_location(1)
    return obj

def NG(target):
    obj = ASSERTION_OBJECT(target, False)
    obj._location = util.get_location(1)
    return obj

def not_ok(target):  # for backward compatibility
    obj = ASSERTION_OBJECT(target, False)
    obj._location = util.get_location(1)
    return obj

def NOT(target):     # experimental. prefer to NG()?
    obj = ASSERTION_OBJECT(target, False)
    obj._location = util.get_location(1)
    return obj

def fail(desc):
    raise AssertionError(desc)


class Should(object):

    def __init__(self, assertion_object, boolean=None):
        self.assertion_object = assertion_object
        if boolean is None:
            boolean = assertion_object.boolean
        self.boolean = boolean

    def __getattr__(self, key):
        ass = self.assertion_object
        tested = ass._tested
        ass._tested = True
        val = getattr(ass.target, key)
        if not hasattr(val, '__call__'):
            msg = "%s.%s: not a callable." % (type(ass.target).__name__, key)
            raise ValueError(msg)   # or TypeError?
        ass._tested = tested
        def f(*args, **kwargs):
            ass._tested = True
            ret = val(*args, **kwargs)
            if ret not in (True, False):
                msg = "%r.%s(): expected to return True or False but it returned %r." \
                      % (ass.target, val.__name__, ret)
                raise ValueError(msg)
            if ret != self.boolean:
                buf = [ repr(arg) for arg in args ]
                buf.extend([ "%s=%r" % (k, kwargs[k]) for k in kwargs ])
                msg = "%r.%s(%s) : failed." % (ass.target, val.__name__, ", ".join(buf))
                if self.boolean is False:
                    msg = "not " + msg
                ass.failed(msg)
        return f


class SkipTest(Exception):
    pass

try:
    from unittest import SkipTest
except ImportError:
    if python2:
        sys.exc_clear()


class SkipObject(object):

    def __call__(self, reason):
        raise SkipTest(reason)

    def when(self, condition, reason):
        if condition:
            def deco(func):
                def fn(self):
                    raise SkipTest(reason)
                fn.__name__ = func.__name__
                fn.__doc__  = func.__doc__
                fn._firstlineno = util._func_firstlineno(func)
                return fn
        else:
            def deco(func):
                return func
        return deco

    #def unless(self, condition, reason):
    #    if not condition:
    #        raise SkipException(reason)

skip = SkipObject()


def todo(func):
    def deco(*args, **kwargs):
        exc_info = None
        try:
            func(*args, **kwargs)
            raise _UnexpectedSuccess("test should be failed (because not implemented yet), but passed unexpectedly.")
        except AssertionError:
            raise _ExpectedFailure(sys.exc_info())
    deco.__name__ = func.__name__
    deco.__doc__  = func.__doc__
    return deco

class _ExpectedFailure(Exception):

    def __init__(self, exc_info=None):
        Exception.__init__(self, "expected failure")
        if exc_info:
            self.exc_info = exc_info

class _UnexpectedSuccess(Exception):
    pass

try:
    from unittest.case import _ExpectedFailure, _UnexpectedSuccess
except ImportError:
    if python2:
        sys.exc_clear()



ST_PASSED  = "passed"
ST_FAILED  = "failed"
ST_ERROR   = "error"
ST_SKIPPED = "skipped"
ST_TODO    = "todo"
#ST_UNEXPECTED = "unexpected"


class TestRunner(object):

    _filter_test = _filter_key = _filter_val = None

    def __init__(self, reporter=None, filter=None):
        self._reporter = reporter
        self.filter = filter
        filter = filter and filter.copy() or {}
        if filter:
            self._filter_test = filter.pop('test', None)
        if filter:
            self._filter_key  = list(filter.keys())[0]
            self._filter_val  = filter.pop(self._filter_key)

    def __get_reporter(self):
        if self._reporter is None:
            self._reporter = REPORTER()
        return self._reporter

    def __set_reporter(self, reporter):
        self._reporter = reporter

    reporter = property(__get_reporter, __set_reporter)

    def _test_name(self, name):
        return re.sub(r'^test_?', '', name)

    def get_testnames(self, klass):
        #names = [ name for name in dir(klass) if name.startswith('test') ]
        #names.sort()
        #return names
        testnames = [ k for k in dir(klass) if k.startswith('test') and hasattr(getattr(klass, k), '__class__') ]
        ## filter by test name or user-defined options
        pattern, key, val = self._filter_test, self._filter_key, self._filter_val
        if pattern or key:
            testnames = [ s for s in testnames
                              if _filtered(klass, getattr(klass, s), s, pattern, key, val) ]
        ## filter by $TEST environment variable
        pattern = os.environ.get('TEST')
        if pattern:
            rexp  = re.compile(pattern)
            testnames = [ s for s in testnames
                              if rexp.search(self._test_name(s)) ]
        ## sort by linenumber
        def fn(testname, klass=klass):
            func = getattr(klass, testname)
            lineno = getattr(func, '_firstlineno', None) or util._func_firstlineno(func)
            return (lineno, testname)
        testnames.sort(key=fn)
        return testnames

    def _invoke(self, obj, method1, method2):
        meth = getattr(obj, method1, None) or getattr(obj, method2, None)
        if not meth: return None, None
        try:
            meth()
            return meth, None
        except KeyboardInterrupt:
            raise
        except Exception:
            return meth.__name__, sys.exc_info()

    def run_class(self, klass, testnames=None):
        self._enter_testclass(klass)
        try:
            method_name, exc_info = self._invoke(klass, 'before_all', 'setUpClass')
            if not exc_info:
                try:
                    self.run_testcases(klass, testnames)
                finally:
                    method_name, exc_info = self._invoke(klass, 'after_all', 'tearDownClass')
        finally:
            if not exc_info: method_name = None
            self._exit_testclass(klass, method_name, exc_info)

    def run_testcases(self, klass, testnames=None):
        if testnames is None:
            testnames = self.get_testnames(klass)
        context_list = getattr(klass, '_context_list', None)
        if context_list:
            items = []
            for tname in testnames:
                meth = getattr(klass, tname)
                if not hasattr(meth, '_test_context'):
                    items.append((tname, meth))
            items.extend(context_list)
            TestContext._sort_items(items)
            allowed = dict.fromkeys(testnames)
            self._run_items(klass, items, allowed)
        else:
            for testname in testnames:
                testcase = self._new_testcase(klass, testname)
                self.run_testcase(testcase, testname)

    def _run_items(self, klass, items, allowed):
        for item in items:
            if isinstance(item, tuple):
                testname = item[0]
                if testname in allowed:
                    testcase = self._new_testcase(klass, testname)
                    self.run_testcase(testcase, testname)
            else:
                assert isinstance(item, TestContext)
                context = item
                self._enter_testcontext(context)
                try:
                    self._run_items(klass, context.items, allowed)
                finally:
                    self._exit_testcontext(context)

    def _new_testcase(self, klass, method_name):
        try:
            obj = klass()
        except ValueError:     # unittest.TestCase raises ValueError
            obj = klass(method_name)
        meth = getattr(obj, method_name)
        obj.__name__ = self._test_name(method_name)
        obj._testMethodName = method_name    # unittest.TestCase compatible
        obj._testMethodDoc  = meth.__doc__   # unittest.TestCase compatible
        obj._run_by_oktest  = True
        obj._oktest_specs   = []
        return obj

    def run_testcase(self, testcase, testname):
        self._enter_testcase(testcase, testname)
        try:
            _, exc_info = self._invoke(testcase, 'before', 'setUp')
            if exc_info:
                status = ST_ERROR
            else:
                try:
                    status = None
                    try:
                        status, exc_info = self._run_testcase(testcase, testname)
                    except:
                        status, exc_info = ST_ERROR, sys.exc_info()
                finally:
                    _, ret = self._invoke(testcase, 'after', 'tearDown')
                    if ret:
                        status, exc_info = ST_ERROR, ret
                    #else:
                        #assert status is not None
        finally:
            self._exit_testcase(testcase, testname, status, exc_info)

    def _run_testcase(self, testcase, testname):
        try:
            meth = getattr(testcase, testname)
            meth()
        except KeyboardInterrupt:
            raise
        except AssertionError:
            return ST_FAILED, sys.exc_info()
        except SkipTest:
            return ST_SKIPPED, sys.exc_info()
        except _ExpectedFailure:   # when failed expectedly
            return ST_TODO, ()
        except _UnexpectedSuccess: # when passed unexpectedly
            #return ST_UNEXPECTED, ()
            ex = sys.exc_info()[1]
            if not ex.args:
                ex.args = ("test should be failed (because not implemented yet), but passed unexpectedly.",)
            return ST_FAILED, sys.exc_info()
        except Exception:
            return ST_ERROR, sys.exc_info()
        else:
            specs = getattr(testcase, '_oktest_specs', None)
            arr = specs and [ spec for spec in specs if spec._exception ]
            if arr: return ST_FAILED, arr
            return ST_PASSED, ()

    def _enter_testclass(self, testclass):
        self.reporter.enter_testclass(testclass)

    def _exit_testclass(self, testclass, method_name, exc_info):
        self.reporter.exit_testclass(testclass, method_name, exc_info)

    def _enter_testcase(self, testcase, testname):
        self.reporter.enter_testcase(testcase, testname)

    def _exit_testcase(self, testcase, testname, status, exc_info):
        self.reporter.exit_testcase(testcase, testname, status, exc_info)

    def _enter_testcontext(self, context):
        self.reporter.enter_testcontext(context)

    def _exit_testcontext(self, context):
        self.reporter.exit_testcontext(context)

    def __enter__(self):
        self.reporter.enter_all()
        return self

    def __exit__(self, *args):
        self.reporter.exit_all()


def _filtered(klass, meth, tname, pattern, key, val, _rexp=re.compile(r'^test(_|_\d\d\d(_|: ))?')):
    from fnmatch import fnmatch
    if pattern:
        if not fnmatch(_rexp.sub('', tname), pattern):
            return False   # skip testcase
    if key:
        if not meth: meth = getattr(klass, tname)
        d = getattr(meth, '_options', None)
        if not (d and isinstance(d, dict) and fnmatch(str(d.get(key)), val)):
            return False   # skip testcase
    return True   # invoke testcase


TEST_RUNNER = TestRunner


def run(*targets, **kwargs):
    out    = kwargs.pop('out', None)
    color  = kwargs.pop('color', None)
    filter = kwargs.pop('filter', {})
    style  = kwargs.pop('style', None)
    klass  = kwargs.pop('reporter_class', None)
    #
    if not klass:
        if style:
            klass = BaseReporter.get_registered_class(style)
            if not klass:
                raise ValueError("%r: unknown report style." % style)
        else:
            klass = REPORTER
    #
    reporter = klass(out=out, color=color)
    runner = TEST_RUNNER(reporter=reporter, filter=filter)
    #
    if len(targets) == 0:
        targets = (config.TARGET_PATTERN, )
    #
    runner.__enter__()
    try:
        for klass in _target_classes(targets):
            runner.run_class(klass)
    finally:
        runner.__exit__(sys.exc_info())
    counts = runner.reporter.counts
    get = counts.get
    #return get(ST_FAILED, 0) + get(ST_ERROR, 0) + get(ST_UNEXPECTED, 0)
    return get(ST_FAILED, 0) + get(ST_ERROR, 0)


def _target_classes(targets):
    target_classes = []
    rexp_type = type(re.compile('x'))
    vars = None
    for arg in targets:
        if util._is_class(arg):
            klass = arg
            target_classes.append(klass)
        elif util._is_string(arg) or isinstance(arg, rexp_type):
            rexp = util._is_string(arg) and re.compile(arg) or arg
            if vars is None: vars = sys._getframe(2).f_locals
            klasses = [ vars[k] for k in vars if rexp.search(k) and util._is_class(vars[k]) ]
            if TESTCLASS_SORT_KEY:
                klasses.sort(key=TESTCLASS_SORT_KEY)
            target_classes.extend(klasses)
        else:
            raise ValueError("%r: not a class nor pattern string." % (arg, ))
    return target_classes


def _min_firstlineno_of_methods(klass):
    func_types = (types.FunctionType, types.MethodType)
    d = klass.__dict__
    linenos = [ util._func_firstlineno(d[k]) for k in d
                if k.startswith('test') and type(d[k]) in func_types ]
    return linenos and min(linenos) or -1

TESTCLASS_SORT_KEY = _min_firstlineno_of_methods


##
## Reporter
##

class Reporter(object):

    def enter_all(self): pass
    def exit_all(self):  pass
    def enter_testclass(self, testclass): pass
    def exit_testclass (self, testclass, method_name, exc_info): pass
    def enter_testcase (self, testcase, testname): pass
    def exit_testcase  (self, testcase, testname, status, exc_info): pass
    def enter_testcontext (self, context): pass
    def exit_testcontext  (self, context): pass


class BaseReporter(Reporter):

    INDICATOR = {
        ST_PASSED:  "passed",          # or "ok" ?
        ST_FAILED:  "Failed",
        ST_ERROR:   "ERROR",
        ST_SKIPPED: "skipped",
        ST_TODO:    "TODO",
        #ST_UNEXPECTED: "Unexpected",
    }

    separator =  "-" * 70

    def __init__(self, out=None, color=None):
        self._color = color
        self.out = out
        self.counts = {}
        self._context_stack = []

    def _set_color(self, color=None):
        if color is not None:
            self._color = color
        elif config.color_enabled is not None:
            self._color = config.color_enabled
        elif not config.color_available:
            self._color = False
        else:
            self._color = is_tty(self._out)

    def __get_out(self):
        if not self._out:
            self.out = sys.stdout
        return self._out

    def __set_out(self, out):
        self._out = out
        if out is not None and self._color is None:
            self._set_color(None)

    out = property(__get_out, __set_out)

    def clear_counts(self):
        self.counts = {
            ST_PASSED:     0,
            ST_FAILED:     0,
            ST_ERROR:      0,
            ST_SKIPPED:    0,
            ST_TODO:       0,
            #ST_UNEXPECTED: 0,
        }

    _counts2str_table = [
        (ST_PASSED,     "passed",     True),
        (ST_FAILED,     "failed",     True),
        (ST_ERROR,      "error",      True),
        (ST_SKIPPED,    "skipped",    True),
        (ST_TODO,       "todo",       True),
        #(ST_UNEXPECTED, "unexpected", False),
    ]

    def counts2str(self):
        buf = [None]; add = buf.append
        total = 0
        for word, status, required in self._counts2str_table:
            n = self.counts.get(status, 0)
            s = "%s:%s" % (word, n)
            if n: s = self.colorize(s, status)
            if required or n:
                add(s)
            total += n
        buf[0] = "total:%s" % total
        return ", ".join(buf)

    def enter_all(self):
        self.clear_counts()
        self._start_time = time.time()

    def exit_all(self):
        dt = time.time() - self._start_time
        min = int(int(dt) / 60)     # int / int is float on Python3
        sec = dt - (min * 60)
        elapsed = min and "%s:%06.3f" % (min, sec) or "%.3f" % sec
        self.out.write("## %s  (%s sec)\n" % (self.counts2str(), elapsed))
        self.out.flush()

    def enter_testclass(self, testclass):
        self._exceptions = []

    def exit_testclass(self, testclass, method_name, exc_info):
        for tupl in self._exceptions:
            self.report_exceptions(*tupl)
        if exc_info:
            self.report_exception(testclass, method_name, ST_ERROR, exc_info, None)
        if self._exceptions or exc_info:
            self.write_separator()
        self.out.flush()

    def enter_testcase(self, testcase, testname):
        pass

    def exit_testcase(self, testcase, testname, status, exc_info):
        self.counts[status] = self.counts.setdefault(status, 0) + 1
        if exc_info and status != ST_SKIPPED:
            context = self._context_stack and self._context_stack[-1] or None
            self._exceptions.append((testcase, testname, status, exc_info, context))

    def enter_testcontext(self, context):
        self._context_stack.append(context)

    def exit_testcontext(self, context):
        popped = self._context_stack.pop()
        assert popped is context

    def indicator(self, status):
        indicator = self.INDICATOR.get(status) or '???'
        if self._color:
            indicator = self.colorize(indicator, status)
        return indicator

    def get_testclass_name(self, testclass):
        subject = testclass.__dict__.get('SUBJECT') or testclass
        return getattr(subject, '__name__', None) or str(subject)

    def get_testcase_desc(self, testcase, testname):
        meth = getattr(testcase, testname)
        return meth and meth.__doc__ and meth.__doc__ or testname

    def report_exceptions(self, testcase, testname, status, exc_info, context):
        if isinstance(exc_info, list):
            specs = exc_info
            for spec in specs:
                self.report_spec_esception(testcase, testname, status, spec, context)
        else:
            self.report_exception(testcase, testname, status, exc_info, context)

    def report_exception(self, testcase, testname, status, exc_info, context):
        self.report_exception_header(testcase, testname, status, exc_info, context)
        self.report_exception_body  (testcase, testname, status, exc_info, context)
        self.report_exception_footer(testcase, testname, status, exc_info, context)

    def report_exception_header(self, testcase, testname, status, exc_info, context):
        if isinstance(testcase, type):
            klass, method = testcase, testname
            title = "%s > %s()" % (self.get_testclass_name(klass), method)
            desc   = None
        else:
            parent, child, desc = self._get_testcase_header_items(testcase, testname)
            items = [child]
            c = context
            while c:
                items.append(c.desc)
                c = c.parent
            items.append(parent)
            items.reverse()
            title = " > ".join(items)
        indicator = self.indicator(status)
        self.write_separator()
        self.out.write("[%s] %s\n" % (indicator, title))
        if desc: self.out.write(desc + "\n")

    def _get_testcase_header_items(self, testcase, testname):
        parent = self.get_testclass_name(testcase.__class__)
        if re.match(r'^test_\d\d\d: ', testname):
            child = testname[5:]
            desc  = None
        else:
            child = testname + '()'
            desc  = getattr(testcase, testname).__doc__
        return parent, child, desc

    def _filter(self, tb, filename, linenum, funcname):
        #return not filename.startswith(_oktest_filepath)
        return "__unittest" not in tb.tb_frame.f_globals

    def report_exception_body(self, testcase, testname, status, exc_info, context):
        assert exc_info
        ex_class, ex, ex_traceback = exc_info
        filter = not config.debug and self._filter or None
        arr = format_traceback(ex, ex_traceback, filter=filter)
        for x in arr:
            self.out.write(x)
        errmsg = "%s: %s" % (ex_class.__name__, ex)
        tupl = errmsg.split("\n", 1)
        if len(tupl) == 1:
            first_line, rest = tupl[0], None
        else:
            first_line, rest = tupl
        self.out.write(self.colorize(first_line, status) + "\n")
        if rest:
            self.out.write(rest)
            if not rest.endswith("\n"): self.out.write("\n")
        self.out.flush()

    def report_exception_footer(self, testcase, testname, status, exc_info, context):
        pass

    def _print_temporary_str(self, string):
        if is_tty(self.out):
            #self.__string = string
            self.out.write(string)
            self.out.flush()

    def _erase_temporary_str(self, _eraser="\b"*255):
        if is_tty(self.out):
            #n = len(self.__string) + 1    # why '+1' ?
            #self.out.write("\b" * n)      # not work with wide-chars
            #self.out.flush()
            #del self.__string
            self.out.write(_eraser)
            self.out.flush()

    def report_spec_esception(self, testcase, testname, status, spec, context):
        ex = spec._exception
        exc_info = (ex.__class__, ex, spec._traceback)
        #self.report_exception_header(testcase, testname, status, exc_info, context)
        parent, child, desc = self._get_testcase_header_items(testcase, testname)
        indicator = self.indicator(status)
        self.write_separator()
        self.out.write("[%s] %s > %s > %s\n" % (indicator, parent, child, spec.desc))
        if desc: self.out.write(desc + "\n")
        #
        stacktrace = self._filter_stacktrace(spec._stacktrace, spec._traceback)
        self._print_stacktrace(stacktrace)
        #
        self.report_exception_body(testcase, testname, status, exc_info, context)
        self.report_exception_footer(testcase, testname, status, exc_info, context)

    def _filter_stacktrace(self, stacktrace, traceback_):
        entries = traceback.extract_tb(traceback_)
        file, line, func, text = entries[0]
        i = len(stacktrace) - 1
        while i >= 0 and not (stacktrace[i][0] == file and stacktrace[i][2] == func):
            i -= 1
        bottom = i
        while i >= 0 and not _is_oktest_py(stacktrace[i][0]):
            i -= 1
        top = i + 1
        return stacktrace[top:bottom]

    def _print_stacktrace(self, stacktrace):
        for file, line, func, text in stacktrace:
            self.out.write('  File "%s", line %s, in %s\n' % (file, line, func))
            self.out.write('    %s\n' % text)

    def colorize(self, string, kind):
        if not self._color:
            return string
        if kind == ST_PASSED:  return util.Color.green(string, bold=True)
        if kind == ST_FAILED:  return util.Color.red(string, bold=True)
        if kind == ST_ERROR:   return util.Color.red(string, bold=True)
        if kind == ST_SKIPPED: return util.Color.yellow(string, bold=True)
        if kind == ST_TODO:    return util.Color.yellow(string, bold=True)
        #if kind == ST_UNEXPECTED: return util.Color.red(string, bold=True)
        if kind == "topic":    return util.Color.bold(string)
        if kind == "sep":      return util.Color.red(string)
        if kind == "context":  return util.Color.bold(string)
        return util.Color.yellow(string)

    def write_separator(self):
        self.out.write(self.colorize(self.separator, "sep") + "\n")

    def status_char(self, status):
        if not hasattr(self, '_status_chars'):
            self._status_chars = {
                ST_PASSED : ".",
                ST_FAILED : self.colorize("f", ST_FAILED ),
                ST_ERROR  : self.colorize("E", ST_ERROR  ),
                ST_SKIPPED: self.colorize("s", ST_SKIPPED),
                ST_TODO   : self.colorize("t", ST_TODO),
                #ST_UNEXPECTED: self.colorize("u", ST_UNEXPECTED),
                None      : self.colorize("?", None),
            }
        return self._status_chars.get(status) or self._status_chars.get(None)

    _registered = {}

    @classmethod
    def register_class(cls, name, klass):
        cls._registered[name] = klass

    @classmethod
    def get_registered_class(cls, name):
        return cls._registered.get(name)


def _is_oktest_py(filepath, _dirpath=os.path.dirname(__file__)):
    #return re.search(r'oktest.py[co]?$', filepath)
    return filepath.startswith(_dirpath)


def is_tty(out):
    return hasattr(out, 'isatty') and out.isatty()


def traceback_formatter(file, line, func, linestr):
    text = linestr.strip()
    return func and '  File "%s", line %s, in %s\n    %s\n' % (file, line, func, text) \
                or  '  File "%s", line %s\n    %s\n'        % (file, line,       text)


def format_traceback(exception, traceback, filter=None, formatter=traceback_formatter):
    limit = getattr(sys, 'tracebacklimit', 200)
    if not formatter:
        formatter = lambda *args: args
    pos = -1
    if hasattr(exception, '_raised_by_oktest'):
        _file, _line = exception.file, exception.line
    else:
        _file, _line = False, -1
    tb = traceback
    arr = []; add = arr.append
    i = 0
    while tb and i < limit:
        linenum  = tb.tb_lineno
        filename = tb.tb_frame.f_code.co_filename
        funcname = tb.tb_frame.f_code.co_name
        if not filter or filter(tb, linenum, filename, funcname):
            linecache.checkcache(filename)
            linestr = linecache.getline(filename, linenum)
            add(formatter(filename, linenum, funcname, linestr))
            if linenum == _line and filename == _file:
                pos = i
            i += 1
        tb = tb.tb_next
    if pos >= 0:
        arr[pos+1:] = []
    return arr


class VerboseReporter(BaseReporter):

    _super = BaseReporter

    def __init__(self, *args, **kwargs):
        self._super.__init__(self, *args, **kwargs)
        self.depth = 1

    def enter_testclass(self, testclass):
        self._super.enter_testclass(self, testclass)
        self.out.write("* %s\n" % self.colorize(self.get_testclass_name(testclass), "topic"))
        self.out.flush()

    def enter_testcase(self, testcase, testname):
        desc = self.get_testcase_desc(testcase, testname)
        self._print_temporary_str("  " * self.depth + "- [      ] " + desc)

    def exit_testcase(self, testcase, testname, status, exc_info):
        s = ""
        if status == ST_SKIPPED:
            ex = exc_info[1]
            #reason = getattr(ex, 'reason', '')
            reason = ex.args[0]
            s = " (reason: %s)" % (reason, )
            exc_info = ()
        self._super.exit_testcase(self, testcase, testname, status, exc_info)
        self._erase_temporary_str()
        indicator = self.indicator(status)
        desc = self.get_testcase_desc(testcase, testname)
        self.out.write("  " * self.depth + "- [%s] %s%s\n" % (indicator, desc, s))
        self.out.flush()

    def enter_testcontext(self, context):
        self._super.enter_testcontext(self, context)
        s = context.desc
        if not (s.startswith("when ") or s == "else:"):
            s = self.colorize(s, "context")
        self.out.write("  " * self.depth + "+ %s\n" % s)
        self.depth += 1

    def exit_testcontext(self, context):
        self._super.exit_testcontext(self, context)
        self.depth -= 1

BaseReporter.register_class("verbose", VerboseReporter)


class SimpleReporter(BaseReporter):

    _super = BaseReporter

    def __init__(self, *args, **kwargs):
        self._super.__init__(self, *args, **kwargs)

    def enter_testclass(self, testclass):
        self._super.enter_testclass(self, testclass)
        self.out.write("* %s: " % self.colorize(self.get_testclass_name(testclass), "topic"))
        self.out.flush()

    def exit_testclass(self, *args):
        self.out.write("\n")
        self._super.exit_testclass(self, *args)

    def exit_testcase(self, testcase, testname, status, exc_info):
        self._super.exit_testcase(self, testcase, testname, status, exc_info)
        self.out.write(self.status_char(status))
        self.out.flush()

BaseReporter.register_class("simple", SimpleReporter)


class PlainReporter(BaseReporter):

    _super = BaseReporter

    def __init__(self, *args, **kwargs):
        self._super.__init__(self, *args, **kwargs)

    def exit_testclass(self, testclass, method_name, exc_info):
        if self._exceptions or exc_info:
            self.out.write("\n")
        self._super.exit_testclass(self, testclass, method_name, exc_info)

    def exit_testcase(self, testcase, testname, status, exc_info):
        self._super.exit_testcase(self, testcase, testname, status, exc_info)
        self.out.write(self.status_char(status))
        self.out.flush()

    def exit_all(self):
        self.out.write("\n")
        self._super.exit_all(self)

BaseReporter.register_class("plain", PlainReporter)


class UnittestStyleReporter(BaseReporter):

    _super = BaseReporter

    def __init__(self, *args, **kwargs):
        self._super.__init__(self, *args, **kwargs)
        self._color = False
        self.separator = "-" * 70

    def enter_testclass(self, testclass):
        if getattr(self, '_exceptions', None) is None:
            self._exceptions = []

    def exit_testclass(self, testclass, method_name, exc_info):
        if exc_info:
            self._exceptions.append((testclass, method_name, ST_ERROR, exc_info))

    def enter_testcase(self, *args):
        self._super.enter_testcase(self, *args)

    def exit_testcase(self, testcase, testname, status, exc_info):
        self._super.exit_testcase(self, testcase, testname, status, exc_info)
        self.out.write(self.status_char(status))
        self.out.flush()

    def exit_all(self):
        self.out.write("\n")
        for tupl in self._exceptions:
            self.report_exceptions(*tupl)
        self._super.exit_all(self)

    def report_exception_header(self, testcase, testname, status, exc_info, context):
        if isinstance(testcase, type):
            klass, method = testcase, testname
            parent = self.get_testclass_name(klass)
            child  = method
        else:
            parent = testcase.__class__.__name__
            child  = testname
        indicator = self.INDICATOR.get(status) or '???'
        self.out.write("=" * 70 + "\n")
        self.out.write("%s: %s#%s()\n" % (indicator, parent, child))
        self.out.write("-" * 70 + "\n")

BaseReporter.register_class("unittest", SimpleReporter)


class OldStyleReporter(BaseReporter):

    _super = BaseReporter

    def enter_all(self):
        pass

    def exit_all(self):
        pass

    def enter_class(self, testcase, testname):
        pass

    def exit_class(self, testcase, testname):
        pass

    def enter_testcase(self, testcase, testname):
        self.out.write("* %s.%s ... " % (testcase.__class__.__name__, testname))

    def exit_testcase(self, testcase, testname, status, exc_info):
        if status == ST_PASSED:
            self.out.write("[ok]\n")
        elif status == ST_FAILED:
            ex_class, ex, ex_traceback = exc_info
            flag = hasattr(ex, '_raised_by_oktest')
            self.out.write("[NG] %s\n" % (flag and ex.errmsg or util.ex2msg(ex)))
            def formatter(filepath, lineno, funcname, linestr):
                return "   %s:%s: %s\n" % (filepath, lineno, linestr.strip())
            arr = format_traceback(ex, ex_traceback, filter=self._filter, formatter=formatter)
            for x in arr:
                self.out.write(x)
            if flag and getattr(ex, 'diff', None):
                self.out.write(ex.diff)
        elif status == ST_ERROR:
            ex_class, ex, ex_traceback = exc_info
            self.out.write("[ERROR] %s: %s\n" % (ex_class.__name__, util.ex2msg(ex)))
            def formatter(filepath, lineno, funcname, linestr):
                return "  - %s:%s:  %s\n" % (filepath, lineno, linestr.strip())
            arr = format_traceback(ex, ex_traceback, filter=self._filter, formatter=formatter)
            for x in arr:
                self.out.write(x)
        elif status == ST_SKIPPED:
            self.out.write("[skipped]\n")
        elif status == ST_TODO:
            self.out.write("[TODO]\n")
        #elif status == ST_UNEXPECTED:
        #    self.out.write("[Unexpected]\n")
        else:
            assert False, "UNREACHABLE: status=%r" % (status,)

BaseReporter.register_class("oldstyle", SimpleReporter)


REPORTER = VerboseReporter
#REPORTER = SimpleReporter
#REPORTER = PlainReporter
#REPORTER = OldStyleReporter
if os.environ.get('OKTEST_REPORTER'):
    REPORTER = globals().get(os.environ.get('OKTEST_REPORTER'))
    if not REPORTER:
        raise ValueError("%s: reporter class not found." % os.environ.get('OKTEST_REPORTER'))


##
## util
##
def _dummy():

    __all__ = ('chdir', 'rm_rf')

    if python2:
        def _is_string(val):
            return isinstance(val, (str, unicode))
        def _is_class(obj):
            return isinstance(obj, (types.TypeType, types.ClassType))
        def _is_unbound(method):
            return not method.im_self
        def _func_name(func):
            return func.func_name
        def _func_firstlineno(func):
            func = getattr(func, 'im_func', func)
            return func.func_code.co_firstlineno
    if python3:
        def _is_string(val):
            return isinstance(val, (str, bytes))
        def _is_class(obj):
            return isinstance(obj, (type, ))
        def _is_unbound(method):
            return not method.__self__
        def _func_name(func):
            return func.__name__
        def _func_firstlineno(func):
            return func.__code__.co_firstlineno

    ##
    ## _Context
    ##
    class Context(object):

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None


    class RunnableContext(Context):

        def run(self, func, *args, **kwargs):
            self.__enter__()
            try:
                return func(*args, **kwargs)
            finally:
                self.__exit__(*sys.exc_info())

        def deco(self, func):
            def f(*args, **kwargs):
                return self.run(func, *args, **kwargs)
            return f

        __call__ = run    # for backward compatibility


    class Chdir(RunnableContext):

        def __init__(self, dirname):
            self.dirname = dirname
            self.path    = os.path.abspath(dirname)
            self.back_to = os.getcwd()

        def __enter__(self, *args):
            os.chdir(self.path)
            return self

        def __exit__(self, *args):
            os.chdir(self.back_to)


    class Using(Context):
        """ex.
             class MyTest(object):
                pass
             with oktest.util.Using(MyTest):
                def test_1(self):
                  ok (1+1) == 2
             if __name__ == '__main__':
                oktest.run(MyTest)
        """
        def __init__(self, klass):
            self.klass = klass

        def __enter__(self):
            localvars = sys._getframe(1).f_locals
            self._start_names = localvars.keys()
            if python3: self._start_names = list(self._start_names)
            return self

        def __exit__(self, *args):
            localvars  = sys._getframe(1).f_locals
            curr_names = localvars.keys()
            diff_names = list(set(curr_names) - set(self._start_names))
            for name in diff_names:
                setattr(self.klass, name, localvars[name])


    def chdir(path, func=None):
        cd = Chdir(path)
        return func is not None and cd.run(func) or cd

    def using(klass):                       ## undocumented
        return Using(klass)


    def ex2msg(ex):
        #return ex.message   # deprecated since Python 2.6
        #return str(ex)      # may be empty
        #return ex.args[0]   # ex.args may be empty (ex. AssertionError)
        #return (ex.args or ['(no error message)'])[0]
        return str(ex) or '(no error message)'

    def flatten(arr, type=(list, tuple)):   ## undocumented
        L = []
        for x in arr:
            if isinstance(x, type):
                L.extend(flatten(x))
            else:
                L.append(x)
        return L

    def rm_rf(*fnames):
        for fname in flatten(fnames):
            if os.path.isfile(fname):
                os.unlink(fname)
            elif os.path.isdir(fname):
                from shutil import rmtree
                rmtree(fname)

    def get_location(depth=0):
        frame = sys._getframe(depth+1)
        return (frame.f_code.co_filename, frame.f_lineno)

    def read_binary_file(fname):
        f = open(fname, 'rb')
        try:
            b = f.read()
        finally:
            f.close()
        return b

    if python2:
        _rexp = re.compile(r'(?:^#!.*?\r?\n)?#.*?coding:[ \t]*([-\w]+)')
        def read_text_file(fname,  _rexp=_rexp, _read_binary_file=read_binary_file):
            b = _read_binary_file(fname)
            m = _rexp.match(b)
            encoding = m and m.group(1) or 'utf-8'
            u = b.decode(encoding)
            assert isinstance(u, unicode)
            return u
    if python3:
        _rexp = re.compile(r'(?:^#!.*?\r?\n)?#.*?coding:[ \t]*([-\w]+)'.encode('us-ascii'))
        def read_text_file(fname,  _rexp=_rexp, _read_binary_file=read_binary_file):
            b = _read_binary_file(fname)
            m = _rexp.match(b)
            encoding = m and m.group(1).decode('us-ascii') or 'utf-8'
            u = b.decode(encoding)
            assert isinstance(u, str)
            return u

    from types import MethodType as _MethodType

    if python2:
        def func_argnames(func):
            if isinstance(func, _MethodType):
                codeobj = func.im_func.func_code
                index = 1
            else:
                codeobj = func.func_code
                index = 0
            return codeobj.co_varnames[index:codeobj.co_argcount]
        def func_defaults(func):
            if isinstance(func, _MethodType):
                return func.im_func.func_defaults
            else:
                return func.func_defaults
    if python3:
        def func_argnames(func):
            if isinstance(func, _MethodType):
                codeobj = func.__func__.__code__
                index = 1
            else:
                codeobj = func.__code__
                index = 0
            return codeobj.co_varnames[index:codeobj.co_argcount]
        def func_defaults(func):
            if isinstance(func, _MethodType):
                return func.__func__.__defaults__
            else:
                return func.__defaults__

    ##
    ## color
    ##
    class Color(object):

        @staticmethod
        def bold(s):
            return "\033[0;1m" + s + "\033[22m"

        @staticmethod
        def black(s, bold=False):
            return "\033[%s;30m%s\033[0m" % (bold and 1 or 0, s)

        @staticmethod
        def red(s, bold=False):
            return "\033[%s;31m%s\033[0m" % (bold and 1 or 0, s)

        @staticmethod
        def green(s, bold=False):
            return "\033[%s;32m%s\033[0m" % (bold and 1 or 0, s)

        @staticmethod
        def yellow(s, bold=False):
            return "\033[%s;33m%s\033[0m" % (bold and 1 or 0, s)

        @staticmethod
        def blue(s, bold=False):
            return "\033[%s;34m%s\033[0m" % (bold and 1 or 0, s)

        @staticmethod
        def magenta(s, bold=False):
            return "\033[%s;35m%s\033[0m" % (bold and 1 or 0, s)

        @staticmethod
        def cyan(s, bold=False):
            return "\033[%s;36m%s\033[0m" % (bold and 1 or 0, s)

        @staticmethod
        def white(s, bold=False):
            return "\033[%s;37m%s\033[0m" % (bold and 1 or 0, s)

        @staticmethod
        def _colorize(s):
            s = re.sub(r'<b>(.*?)</b>', lambda m: Color.bold(m.group(1)), s)
            s = re.sub(r'<R>(.*?)</R>', lambda m: Color.red(m.group(1), bold=True), s)
            s = re.sub(r'<r>(.*?)</r>', lambda m: Color.red(m.group(1), bold=False), s)
            s = re.sub(r'<G>(.*?)</G>', lambda m: Color.green(m.group(1), bold=True), s)
            s = re.sub(r'<Y>(.*?)</Y>', lambda m: Color.yellow(m.group(1), bold=True), s)
            return s


    return locals()

util = _new_module('oktest.util', _dummy())
del _dummy

helper = util  ## 'help' is an alias of 'util' (for backward compatibility)
sys.modules['oktest.helper'] = sys.modules['oktest.util']


##
## spec()   # deprecated
##
class Spec(util.Context):   # deprecated

    _exception  = None
    _traceback  = None
    _stacktrace = None

    def __init__(self, desc):
        self.desc = desc
        self._testcase = None

    def __enter__(self):
        self._testcase = tc = self._find_testcase_object()
        if getattr(tc, '_run_by_oktest', None):
            tc._oktest_specs.append(self)
        return self

    def _find_testcase_object(self):
        max_depth = 10
        for i in xrange(2, max_depth):
            try:
                frame = sys._getframe(i)   # raises ValueError when too deep
            except ValueError:
                break
            method = frame.f_code.co_name
            if method.startswith("test"):
                arg_name = frame.f_code.co_varnames[0]
                testcase = frame.f_locals.get(arg_name, None)
                if hasattr(testcase, "_testMethodName") or hasattr(testcase, "_TestCase__testMethodName"):
                    return testcase
        return None

    def __exit__(self, *args):
        ex = args[1]
        tc = self._testcase
        if ex and hasattr(ex, '_raised_by_oktest') and hasattr(tc, '_run_by_oktest'):
            self._exception  = ex
            self._traceback  = args[2]
            self._stacktrace = traceback.extract_stack()
            return True

    def __iter__(self):
        self.__enter__()
        #try:
        #    yield self  # (Python2.4) SyntaxError: 'yield' not allowed in a 'try' block with a 'finally' clause
        #finally:
        #    self.__exit__(*sys.exc_info())
        ex = None
        try:
            yield self
        except:
            ex = None
        self.__exit__(*sys.exc_info())
        if ex:
            raise ex

    def __call__(self, func):
        self.__enter__()
        try:
            func()
        finally:
            self.__exit__(*sys.exc_info())

    def __bool__(self):       # for Pyton3
        filter = os.environ.get('SPEC')
        return not filter or (filter in self.desc)

    __nonzero__ = __bool__    # for Python2


def spec(desc):   # deprecated
    #if not os.getenv('OKTEST_WARNING_DISABLED'):
    #    import warnings
    #    warnings.warn("oktest.spec() is deprecated.", DeprecationWarning, 2)
    return Spec(desc)


##
## @test() decorator
##

def test(description_text=None, **options):
    frame = sys._getframe(1)
    localvars  = frame.f_locals
    globalvars = frame.f_globals
    n = localvars.get('__n', 0) + 1
    localvars['__n'] = n
    def deco(orig_func):
        argnames = util.func_argnames(orig_func)
        fixture_names = argnames[1:]   # except 'self'
        if fixture_names:
            def newfunc(self):
                self._options = options
                self._description = description_text
                return fixture_injector.invoke(self, orig_func, globalvars)
        else:
            def newfunc(self):
                self._options = options
                self._description = description_text
                return orig_func(self)
        orig_name = orig_func.__name__
        if orig_name.startswith('test'):
            newfunc.__name__ = orig_name
        else:
            newfunc.__name__ = "test_%03d: %s" % (n, description_text)
            localvars[newfunc.__name__] = newfunc
        newfunc.__doc__  = orig_func.__doc__ or description_text
        newfunc._options = options
        newfunc._firstlineno = getattr(orig_func, '_firstlineno', None) or util._func_firstlineno(orig_func)
        return newfunc
    return deco


##
## fixture manager and injector
##

class FixtureManager(object):

    def provide(self, name):
        raise NameError("Fixture provider for '%s' not found." % (name,))

    def release(self, name, value):
        pass

fixture_manager = FixtureManager()


class FixtureInjector(object):

    def invoke(self, object, func, *opts):
        """invoke function with fixtures."""
        releasers = {"self": None}     # {"arg_name": releaser_func()}
        resolved  = {"self": object}   # {"arg_name": arg_value}
        in_progress = []
        ##
        arg_names = util.func_argnames(func)
        ## default arg values of test method are stored into 'resolved' dict
        ## in order for providers to access to them
        defaults = util.func_defaults(func)
        if defaults:
            idx = - len(defaults)
            for aname, default in zip(arg_names[idx:], defaults):
                resolved[aname] = default
            arg_names = arg_names[:idx]
        ##
        def _resolve(arg_name):
            aname = arg_name
            if aname not in resolved:
                pair = self.find(aname, object, *opts)
                if pair:
                    provider, releaser = pair
                    resolved[aname] = _call(provider, aname)
                    releasers[aname] = releaser
                else:
                    resolved[aname] = fixture_manager.provide(aname)
            return resolved[aname]
        def _call(provider, resolving_arg_name):
            arg_names = util.func_argnames(provider)
            if not arg_names:
                return provider()
            in_progress.append(resolving_arg_name)
            defaults = util.func_defaults(provider)
            if not defaults:
                arg_values = [ _get_value(aname) for aname in arg_names ]
            else:
                idx  = - len(defaults)
                arg_values = [ _get_value(aname) for aname in arg_names[:idx] ]
                for aname, default in zip(arg_names[idx:], defaults):
                    arg_values.append(resolved.get(aname, default))
            in_progress.remove(resolving_arg_name)
            return provider(*arg_values)
        def _get_value(arg_name):
            if arg_name in resolved:        return resolved[arg_name]
            if arg_name not in in_progress: return _resolve(arg_name)
            raise self._looped_dependency_error(arg_name, in_progress, object)
        ##
        arguments = [ _resolve(aname) for aname in arg_names ]
        assert not in_progress
        try:
            #return func(object, *arguments)
            return func(*arguments)
        finally:
            self._release_fixtures(resolved, releasers)

    def _release_fixtures(self, resolved, releasers):
        for name in resolved:
            if name in releasers:
                releaser = releasers[name]
                if releaser:
                    names = util.func_argnames(releaser)
                    if names and names[0] == "self":
                        releaser(resolved["self"], resolved[name])
                    else:
                        releaser(resolved[name])
            else:
                fixture_manager.release(name, resolved[name])

    def find(self, name, object, *opts):
        """return provide_xxx() and release_xxx() functions."""
        globalvars = opts[0]
        provider_name = 'provide_' + name
        releaser_name = 'release_' + name
        meth = getattr(object, provider_name, None)
        if meth:
            provider = meth
            if python2:
                if hasattr(meth, 'im_func'):  provider = meth.im_func
            elif python3:
                if hasattr(meth, '__func__'): provider = meth.__func__
            releaser = getattr(object, releaser_name, None)
            return (provider, releaser)
        elif provider_name in globalvars:
            provider = globalvars[provider_name]
            if not isinstance(provider, types.FunctionType):
                raise TypeError("%s: expected function but got %s." % (provider_name, type(provider)))
            releaser = globalvars.get(releaser_name)
            return (provider, releaser)
        #else:
        #    raise NameError("%s: no such fixture provider for '%s'." % (provider_name, name))
            return None

    def _looped_dependency_error(self, aname, in_progress, object):
        names = in_progress + [aname]
        pos   = names.index(aname)
        loop  = '=>'.join(names[pos:])
        if pos > 0:
            loop = '->'.join(names[0:pos]) + '->' + loop
        classname = object.__class__.__name__
        testdesc  = object._description
        return LoopedDependencyError("fixture dependency is looped: %s (class: %s, test: '%s')" % (loop, classname, testdesc))


fixture_injector = FixtureInjector()


class LoopedDependencyError(ValueError):
    pass


##
## test context
##
def context():

    __all__ = ('subject', 'situation', )
    global TestContext

    class TestContext(object):
        """grouping test methods.

        normally created with subject() or situation() helpers.

        ex::
            class HelloClassTest(unittest.TestCase):
                SUBJECT = Hello
                with subject('#method1()'):
                    @test("spec1")
                    def _(self):
                        ...
                    @test("spec2")
                    def _(self):
                        ...
                with subject('#method2()'):
                    with situation('when condition:'):
                        @test("spec3")
                        def _(self):
                    with situation('else:')
                        @test("spec3")
                        def _(self):
                        ...
        """

        def __init__(self, desc, _lineno=None):
            self.desc = desc
            self.items = []
            self.parent = None
            self._lineno = _lineno

        def __repr__(self):
            return "<TestContext desc=%r items=[%s]>" % \
                       (self.desc, ','.join(repr(x) for x in self.items))

        def __enter__(self):
            f_locals = sys._getframe(1).f_locals
            self._f_locals = f_locals
            self._varnames = set(f_locals.keys())
            stack = f_locals.setdefault('_context_stack', [])
            if not stack:
                f_locals.setdefault('_context_list', []).append(self)
            else:
                self.parent = stack[-1]
                self.parent.items.append(self)
            stack.append(self)
            return self

        def __exit__(self, *args):
            f_locals = self._f_locals
            popped = f_locals['_context_stack'].pop()
            assert popped is self
            newvars = set(f_locals.keys()) - self._varnames
            for name in newvars:
                if name.startswith('test'):
                    func = f_locals[name]
                    if not hasattr(func, '_test_context'):
                        func._test_context = self.desc
                        self.items.append((name, func))
            self._sort_items(self.items)
            del self._f_locals
            del self._varnames

        @staticmethod
        def _sort_items(items):
            def fn(item):
                if isinstance(item, tuple):
                    return getattr(item[1], '_firstlineno', None) or \
                           util._func_firstlineno(item[1])
                elif isinstance(item, TestContext):
                    return item._lineno or 0
                else:
                    assert False, "** item=%r" % (item, )
            items.sort(key=fn)

        @staticmethod
        def _inspect_items(items):
            def _inspect(items, depth, add):
                for item in items:
                    if isinstance(item, tuple):
                        add("  " * depth + "- %s()\n" % item[0])
                    else:
                        add("  " * depth + "- Context: %r\n" % item.desc)
                        _inspect(item.items, depth+1, add)
            buf = []
            _inspect(items, 0, buf.append)
            return "".join(buf)


    def subject(desc):
        """helper to group test methods by subject"""
        lineno = sys._getframe(1).f_lineno
        return TestContext(desc, _lineno=lineno)

    def situation(desc):
        """helper to group test methods by situation or condition"""
        lineno = sys._getframe(1).f_lineno
        return TestContext(desc, _lineno=lineno)


    return locals()

context = _new_module("oktest.context", context())
context.TestContext = TestContext
subject   = context.subject
situation = context.situation


##
## dummy
##
def _dummy():

    __all__ = ('dummy_file', 'dummy_dir', 'dummy_values', 'dummy_attrs', 'dummy_environ_vars', 'dummy_io')


    class DummyFile(util.RunnableContext):

        def __init__(self, filename, content):
            self.filename = filename
            self.path     = os.path.abspath(filename)
            self.content  = content

        def __enter__(self, *args):
            f = open(self.path, 'w')
            try:
                f.write(self.content)
            finally:
                f.close()
            return self

        def __exit__(self, *args):
            os.unlink(self.path)


    class DummyDir(util.RunnableContext):

        def __init__(self, dirname):
            self.dirname = dirname
            self.path    = os.path.abspath(dirname)

        def __enter__(self, *args):
            os.mkdir(self.path)
            return self

        def __exit__(self, *args):
            import shutil
            shutil.rmtree(self.path)


    class DummyValues(util.RunnableContext):

        def __init__(self, dictionary, items_=None, **kwargs):
            self.dict = dictionary
            self.items = {}
            if isinstance(items_, dict):
                self.items.update(items_)
            if kwargs:
                self.items.update(kwargs)

        def __enter__(self):
            self.original = d = {}
            for k in self.items:
                if k in self.dict:
                    d[k] = self.dict[k]
            self.dict.update(self.items)
            return self

        def __exit__(self, *args):
            for k in self.items:
                if k in self.original:
                    self.dict[k] = self.original[k]
                else:
                    del self.dict[k]
            self.__dict__.clear()


    class DummyIO(util.RunnableContext):

        def __init__(self, stdin_content=None):
            self.stdin_content = stdin_content

        def __enter__(self):
            self.stdout, sys.stdout = sys.stdout, StringIO()
            self.stderr, sys.stderr = sys.stderr, StringIO()
            self.stdin,  sys.stdin  = sys.stdin,  StringIO(self.stdin_content or "")
            return self

        def __exit__(self, *args):
            sout, serr = sys.stdout.getvalue(), sys.stderr.getvalue()
            sys.stdout, self.stdout = self.stdout, sys.stdout.getvalue()
            sys.stderr, self.stderr = self.stderr, sys.stderr.getvalue()
            sys.stdin,  self.stdin  = self.stdin,  self.stdin_content

        def __call__(self, func, *args, **kwargs):
            self.returned = self.run(func, *args, **kwargs)
            return self

        def __iter__(self):
            yield self.stdout
            yield self.stderr


    def dummy_file(filename, content):
        return DummyFile(filename, content)

    def dummy_dir(dirname):
        return DummyDir(dirname)

    def dummy_values(dictionary, items_=None, **kwargs):
        return DummyValues(dictionary, items_, **kwargs)

    def dummy_attrs(object, items_=None, **kwargs):
        return DummyValues(object.__dict__, items_, **kwargs)

    def dummy_environ_vars(**kwargs):
        return DummyValues(os.environ, **kwargs)

    def dummy_io(stdin_content="", func=None, *args, **kwargs):
        obj = dummy.DummyIO(stdin_content)
        if func is None:
            return obj    # for with-statement
        obj.__enter__()
        try:
            func(*args, **kwargs)
        finally:
            obj.__exit__(*sys.exc_info())
        #return obj.stdout, obj.stderr
        return obj


    return locals()


dummy = _new_module('oktest.dummy', _dummy(), util)
del _dummy



##
## Tracer
##
def _dummy():

    __all__ = ('Tracer', )


    class Call(object):

        __repr_style = None

        def __init__(self, receiver=None, name=None, args=None, kwargs=None, ret=None):
            self.receiver = receiver
            self.name   = name     # method name
            self.args   = args
            self.kwargs = kwargs
            self.ret    = ret

        def __repr__(self):
            #return '%s(args=%r, kwargs=%r, ret=%r)' % (self.name, self.args, self.kwargs, self.ret)
            if self.__repr_style == 'list':
                return repr(self.list())
            if self.__repr_style == 'tuple':
                return repr(self.tuple())
            buf = []; a = buf.append
            a("%s(" % self.name)
            for arg in self.args:
                a(repr(arg))
                a(", ")
            for k in self.kwargs:
                a("%s=%s" % (k, repr(self.kwargs[k])))
                a(", ")
            if buf[-1] == ", ":  buf.pop()
            a(") #=> %s" % repr(self.ret))
            return "".join(buf)

        def __iter__(self):
            yield self.receiver
            yield self.name
            yield self.args
            yield self.kwargs
            yield self.ret

        def list(self):
            return list(self)

        def tuple(self):
            return tuple(self)

        def __eq__(self, other):
            if isinstance(other, list):
                self.__repr_style = 'list'
                return list(self) == other
            elif isinstance(other, tuple):
                self.__repr_style = 'tuple'
                return tuple(self) == other
            elif isinstance(other, self.__class__):
                return self.name == other.name and self.args == other.args \
                    and self.kwargs == other.kwargs and self.ret == other.ret
            else:
                return False

        def __ne__(self, other):
            return not self.__eq__(other)


    class FakeObject(object):

        def __init__(self, **kwargs):
            self._calls = self.__calls = []
            for name in kwargs:
                setattr(self, name, self.__new_method(name, kwargs[name]))

        def __new_method(self, name, val):
            fake_obj = self
            if isinstance(val, types.FunctionType):
                func = val
                def f(self, *args, **kwargs):
                    r = Call(fake_obj, name, args, kwargs, None)
                    fake_obj.__calls.append(r)
                    r.ret = func(self, *args, **kwargs)
                    return r.ret
            else:
                def f(self, *args, **kwargs):
                    r = Call(fake_obj, name, args, kwargs, val)
                    fake_obj.__calls.append(r)
                    return val
            f.func_name = f.__name__ = name
            if python2: return types.MethodType(f, self, self.__class__)
            if python3: return types.MethodType(f, self)


    class Tracer(object):
        """trace function or method call to record arguments and return value.
           see README.txt for details.
        """

        def __init__(self):
            self.calls = []

        def __getitem__(self, index):
            return self.calls[index]

        def __len__(self):
            return len(self.calls)

        def __iter__(self):
            return self.calls.__iter__()

        def _copy_attrs(self, func, newfunc):
            for k in ('func_name', '__name__', '__doc__'):
                if hasattr(func, k):
                    setattr(newfunc, k, getattr(func, k))

        def _wrap_func(self, func, block):
            tr = self
            def newfunc(*args, **kwargs):                # no 'self'
                call = Call(None, util._func_name(func), args, kwargs, None)
                tr.calls.append(call)
                if block:
                    ret = block(func, *args, **kwargs)
                else:
                    ret = func(*args, **kwargs)
                #newfunc._return = ret
                call.ret = ret
                return ret
            self._copy_attrs(func, newfunc)
            return newfunc

        def _wrap_method(self, method_obj, block):
            func = method_obj
            tr = self
            def newfunc(self, *args, **kwargs):          # has 'self'
                call = Call(self, util._func_name(func), args, kwargs, None)
                tr.calls.append(call)
                if util._is_unbound(func): args = (self, ) + args   # call with 'self' if unbound method
                if block:
                    ret = block(func, *args, **kwargs)
                else:
                    ret = func(*args, **kwargs)
                call.ret = ret
                return ret
            self._copy_attrs(func, newfunc)
            if python2:  return types.MethodType(newfunc, func.im_self, func.im_class)
            if python3:  return types.MethodType(newfunc, func.__self__)

        def trace_func(self, func):
            newfunc = self._wrap_func(func, None)
            return newfunc

        def fake_func(self, func, block):
            newfunc = self._wrap_func(func, block)
            return newfunc

        def trace_method(self, obj, *method_names):
            for method_name in method_names:
                method_obj = getattr(obj, method_name, None)
                if method_obj is None:
                    raise NameError("%s: method not found on %r." % (method_name, obj))
                setattr(obj, method_name, self._wrap_method(method_obj, None))
            return None

        def fake_method(self, obj, **kwargs):
            def _new_block(ret_val):
                def _block(*args, **kwargs):
                    return ret_val
                return _block
            def _dummy_method(obj, name):
                fn = lambda *args, **kwargs: None
                fn.__name__ = name
                if python2: fn.func_name = name
                if python2: return types.MethodType(fn, obj, type(obj))
                if python3: return types.MethodType(fn, obj)
            for method_name in kwargs:
                method_obj = getattr(obj, method_name, None)
                if method_obj is None:
                    method_obj = _dummy_method(obj, method_name)
                block = kwargs[method_name]
                if not isinstance(block, types.FunctionType):
                    block = _new_block(block)
                setattr(obj, method_name, self._wrap_method(method_obj, block))
            return None

        def trace(self, target, *args):
            if type(target) is types.FunctionType:       # function
                func = target
                return self.trace_func(func)
            else:
                obj = target
                return self.trace_method(obj, *args)

        def fake(self, target, *args, **kwargs):
            if type(target) is types.FunctionType:       # function
                func = target
                block = args and args[0] or None
                return self.fake_func(func, block)
            else:
                obj = target
                return self.fake_method(obj, **kwargs)

        def fake_obj(self, **kwargs):
            obj = FakeObject(**kwargs)
            obj._calls = obj._FakeObject__calls = self.calls
            return obj


    return locals()


tracer = _new_module('oktest.tracer', _dummy(), util)
del _dummy



##
## mainapp
##
import unittest

def load_module(mod_name, filepath, content=None):
    mod = type(os)(mod_name)
    mod.__dict__["__name__"] = mod_name
    mod.__dict__["__file__"] = filepath
    #mod.__dict__["__file__"] = os.path.abspath(filepath)
    if content is None:
        if python2:
            content = util.read_binary_file(filepath)
        if python3:
            content = util.read_text_file(filepath)
    if filepath:
        code = compile(content, filepath, "exec")
        exec(code, mod.__dict__, mod.__dict__)
    else:
        exec(content, mod.__dict__, mod.__dict__)
    return mod

def rglob(dirpath, pattern, _entries=None):
    import fnmatch
    if _entries is None: _entries = []
    isdir, join = os.path.isdir, os.path.join
    add = _entries.append
    if isdir(dirpath):
        items = os.listdir(dirpath)
        for item in fnmatch.filter(items, pattern):
            path = join(dirpath, item)
            add(path)
        for item in items:
            path = join(dirpath, item)
            if isdir(path) and not item.startswith('.'):
                rglob(path, pattern, _entries)
    return _entries


def _dummy():

    global optparse
    import optparse

    class MainApp(object):

        debug = False

        def __init__(self, command=None):
            self.command = command

        def _new_cmdopt_parser(self):
            #import cmdopt
            #parser = cmdopt.Parser()
            #parser.opt("-h").name("help")                         .desc("show help")
            #parser.opt("-v").name("version")                      .desc("version of oktest.py")
            ##parser.opt("-s").name("testdir").arg("DIR[,DIR2,..]") .desc("test directory (default 'test' or 'tests')")
            #parser.opt("-p").name("pattern").arg("PAT[,PAT2,..]") .desc("test script pattern (default '*_test.py,test_*.py')")
            #parser.opt("-x").name("exclude").arg("PAT[,PAT2,..]") .desc("exclue file pattern")
            #parser.opt("-D").name("debug")                        .desc("debug mode")
            #return parser
            parser = optparse.OptionParser(conflict_handler="resolve")
            parser.add_option("-h", "--help",       action="store_true",     help="show help")
            parser.add_option("-v", "--version",    action="store_true",     help="verion of oktest.py")
            parser.add_option("-s", dest="style",   metavar="STYLE",         help="reporting style (plain/simple/verbose, or p/s/v)")
            parser.add_option(      "--color",      metavar="true|false",    help="enable/disable output color")
            parser.add_option("-K", dest="encoding", metavar="ENCODING",     help="output encoding (utf-8 when system default is US-ASCII)")
            parser.add_option("-p", dest="pattern", metavar="PAT[,PAT2,..]", help="test script pattern (default '*_test.py,test_*.py')")
            #parser.add_option("-x", dest="exclude", metavar="PAT[,PAT2,..]", help="exclue file pattern")
            parser.add_option("-U", dest="unittest", action="store_true",    help="run testcases with unittest.main instead of oktest.run")
            parser.add_option("-D", dest="debug",   action="store_true",     help="debug mode")
            parser.add_option("-f", dest="filter",  metavar="FILTER",        help="filter (class=xxx/test=xxx/useroption=xxx)")
            return parser

        def _load_modules(self, filepaths, pattern=None):
            from fnmatch import fnmatch
            modules = []
            for fpath in filepaths:
                mod_name = os.path.basename(fpath).replace('.py', '')
                if pattern and not fnmatch(mod_name, pattern):
                    continue
                mod = load_module(mod_name, fpath)
                modules.append(mod)
            self._trace("modules: ", modules)
            return modules

        def _load_classes(self, modules, pattern=None):
            from fnmatch import fnmatch
            testclasses = []
            unittest_testclasses = []
            oktest_testclasses   = []
            for mod in modules:
                for k in dir(mod):
                    #if k.startswith('_'): continue
                    v = getattr(mod, k)
                    if not isinstance(v, type): continue
                    klass = v
                    if pattern and not fnmatch(klass.__name__, pattern):
                        continue
                    if issubclass(klass, unittest.TestCase):
                        testclasses.append(klass)
                        unittest_testclasses.append(klass)
                    elif re.search(config.TARGET_PATTERN, klass.__name__):
                        testclasses.append(klass)
                        oktest_testclasses.append(klass)
            return testclasses, unittest_testclasses, oktest_testclasses

        def _run_unittest(self, klasses, pattern=None, filters=None):
            self._trace("test_pattern: %r" % (pattern,))
            self._trace("unittest_testclasses: ", klasses)
            loader = unittest.TestLoader()
            the_suite = unittest.TestSuite()
            rexp = re.compile(r'^test(_|_\d\d\d(_|: ))?')
            if filters:
                key = list(filters.keys())[0]
                val = filters[key]
            else:
                key = val = None
            for klass in klasses:
                if pattern or filters:
                    testnames = loader.getTestCaseNames(klass)
                    testcases = [ klass(tname) for tname in testnames
                                      if _filtered(klass, None, tname, pattern, key, val) ]
                    suite = loader.suiteClass(testcases)
                else:
                    suite = loader.loadTestsFromTestCase(klass)
                the_suite.addTest(suite)
            #runner = unittest.TextTestRunner()
            runner = unittest.TextTestRunner(stream=sys.stderr)
            result = runner.run(the_suite)
            n_errors = len(result.errors) + len(result.failures)
            return n_errors

        def _run_oktest(self, klasses, pattern, kwargs):
            self._trace("test_pattern: %r" % (pattern,))
            self._trace("oktest_testclasses: ", klasses)
            if pattern:
                kwargs.setdefault('filter', {})['test'] = pattern
            import oktest; run = oktest.run    # don't remove!
            n_errors = run(*klasses, **kwargs)
            return n_errors

        def _trace(self, msg, items=None):
            write = sys.stderr.write
            if items is None:
                write("** DEBUG: %s\n" % msg)
            else:
                write("** DEBUG: %s[\n" % msg)
                for item in items:
                    write("**   %r,\n" % (item,))
                write("** ]\n")

        def _help_message(self, parser):
            buf = []; add = buf.append
            add("Usage: python -m oktest [options] file_or_directory...\n")
            #add(parser.help_message(20))
            add(re.sub(r'^.*\n.*\n[oO]ptions:\n', '', parser.format_help()))
            add("Example:\n")
            add("   ## run test scripts in plain format\n")
            add("   $ python -m oktest -sp tests/*_test.py\n")
            add("   ## run test scripts in 'tests' dir with pattern '*_test.py'\n")
            add("   $ python -m oktest -p '*_test.py' tests\n")
            add("   ## filter by class name\n")
            add("   $ python -m oktest -f class='ClassName*' tests\n")
            add("   ## filter by test method name\n")
            add("   $ python -m oktest -f '*method*' tests   # or -f test='*method*'\n")
            add("   ## filter by user-defined option added by @test decorator\n")
            add("   $ python -m oktest -f tag='*value*' tests\n")
            return "".join(buf)

        def _version_info(self):
            buf = []; add = buf.append
            add("oktest: " + __version__)
            add("python: " + sys.version.split("\n")[0])
            add("")
            return "\n".join(buf)

        def _get_files(self, args, pattern):
            filepaths = []
            for arg in args:
                if os.path.isfile(arg):
                    filepaths.append(arg)
                elif os.path.isdir(arg):
                    files = self._find_files_recursively(arg, pattern)
                    filepaths.extend(files)
                else:
                    raise ValueError("%s: file or directory expected." % (arg,))
            return filepaths

        def _find_files_recursively(self, testdir, pattern):
            isdir = os.path.isdir
            assert isdir(testdir)
            filepaths = []
            for pat in pattern.split(","):
                files = rglob(testdir, pat)
                if files:
                    filepaths.extend(files)
                    self._trace("testdir: %r, pattern: %r, files: " % (testdir, pat), files)
            return filepaths

        #def _exclude_files(self, filepaths, pattern):
        #    from fnmatch import fnmatch
        #    _trace = self._trace
        #    basename = os.path.basename
        #    original = filepaths[:]
        #    for pat in pattern.split(","):
        #        filepaths = [ fpath for fpath in filepaths
        #                          if not fnmatch(basename(fpath), pat) ]
        #    _trace("excluded: %r" % (list(set(original) - set(filepaths)), ))
        #    return filepaths

        def _get_filters(self, opts_filter):
            filters = {}
            if opts_filter:
                pair = opts_filter.split('=', 2)
                if len(pair) != 2:
                    pair = ('test', pair[0])
                filters[pair[0]] = pair[1]
            return filters

        def _handle_opt_report(self, opt_report, parser):
            key = None
            d = {"p": "plain", "s": "simple", "v": "verbose"}
            key = d.get(opt_report, opt_report)
            self._trace("reporter: %s" % key)
            if not BaseReporter.get_registered_class(key):
                #raise optparse.OptionError("%r: unknown report sytle (plain/simple/verbose, or p/s/v)" % opt_report)
                parser.error("%r: unknown report sytle (plain/simple/verbose, or p/s/v)" % opt_report)
            return key

        def _handle_opt_color(self, opt_color, parser):
            import oktest.config
            if   opt_color in ('true', 'yes', 'on'):
                oktest.config.color_enabled = True
            elif opt_color in ('false', 'no', 'off'):
                oktest.config.color_enabled = False
            else:
                #raise optparse.OptionError("--color=%r: 'true' or 'false' expected" % opt_color)
                parser.error("--color=%r: 'true' or 'false' expected" % opt_color)
            return oktest.config.color_enabled

        def _get_output_writer(self, encoding):
            self._trace('output encoding: ' + encoding)
            if python2:
                import codecs
                return codecs.getwriter(encoding)(sys.stdout)
            if python3:
                import io
                return io.TextIOWrapper(sys.stdout.buffer, encoding=encoding)

        def run(self, args=None, **kwargs):
            if args is None: args = sys.argv[1:]
            parser = self._new_cmdopt_parser()
            #opts = parser.parse(args)
            opts, args = parser.parse_args(args)
            if opts.debug:
                self.debug = True
                _trace = self._trace
                import oktest.config
                oktest.config.debug = True
            else:
                _trace = self._trace = lambda msg, items=None: None
            _trace("python: " + sys.version.split()[0])
            _trace("oktest: " + __version__)
            _trace("opts: %r" % (opts,))
            _trace("args: %r" % (args,))
            if opts.help:
                print(self._help_message(parser))
                return
            if opts.version:
                print(self._version_info())
                return
            #
            if opts.style:
                kwargs['style'] = self._handle_opt_report(opts.style, parser)
            if opts.color:
                kwargs['color'] = self._handle_opt_color(opts.color, parser)
            if 'out' not in kwargs:
                if opts.encoding:
                    kwargs['out'] = self._get_output_writer(opts.encoding)
                elif not hasattr(sys.stdout, 'encoding') or sys.stdout.encoding == 'US-ASCII':
                    kwargs['out'] = self._get_output_writer('utf-8')
            #
            pattern = opts.pattern or '*_test.py,test_*.py'
            filepaths = self._get_files(args, pattern)
            #if opts.exclude:
            #    filepaths = self._exclude_files(filepaths, opts.exclude)
            filters = self._get_filters(opts.filter)
            fval = lambda key, filters=filters: filters.pop(key, None)
            modules = self._load_modules(filepaths, fval('module'))
            tupl = self._load_classes(modules, fval('class'))
            testclasses, unittest_testclasses, oktest_testclasses = tupl
            kwargs['filter'] = filters
            if opts.unittest:
                n_errors = 0
                if unittest_testclasses:
                    n_errors += self._run_unittest(unittest_testclasses, fval('test'), filters)
                if oktest_testclasses:
                    n_errors += self._run_oktest(oktest_testclasses, fval('test'), kwargs)
            else:
                n_errors = self._run_oktest(testclasses, fval('test'), kwargs)
            return n_errors

        @classmethod
        def main(cls, sys_argv=None):
            #import cmdopt
            if sys_argv is None: sys_argv = sys.argv
            #app = cls(sys_argv[0])
            #try:
            #    app.run(sys_argv[1:])
            #    sys.exit(0)
            #except cmdopt.ParseError:
            #    ex = sys.exc_info()[1]
            #    sys.stderr.write("%s" % (ex, ))
            #    sys.exit(1)
            app = cls(sys_argv[0])
            n_errors = app.run(sys_argv[1:])
            sys.exit(n_errors)

    return locals()


mainapp = _new_module('oktest.mainapp', _dummy(), util)
del _dummy


def main(*args):
    sys_argv = [__file__] + sys.argv + list(args)
    mainapp.MainApp.main(sys_argv)


if __name__ == '__main__':
    mainapp.MainApp.main()
