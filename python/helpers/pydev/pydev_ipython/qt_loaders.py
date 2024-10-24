"""
This module contains factory functions that attempt
to return Qt submodules from the various python Qt bindings.

It also protects against double-importing Qt with different
bindings, which is unstable and likely to crash

This is used primarily by qt and qt_for_kernel, and shouldn't
be accessed directly from the outside
"""
import sys
from functools import partial
import importlib.util

from pydev_ipython.version import check_version

# Available APIs.
QT_API_PYQT = 'pyqt'
QT_API_PYQTv1 = 'pyqtv1'
QT_API_PYQT_DEFAULT = 'pyqtdefault' # don't set SIP explicitly
QT_API_PYSIDE = 'pyside'
QT_API_PYQT5 = 'pyqt5'
QT_API_PYQT6 = 'pyqt6'


def find_module(module_name, path=None, parent_name=None):
    spec = importlib.util.find_spec(module_name, path)
    if spec is None:
        if parent_name is not None:
            spec = importlib.util.find_spec(parent_name + '.' + module_name, path)
        if spec is None:
            raise ImportError


class ImportDenier(object):
    """Import Hook that will guard against bad Qt imports
    once IPython commits to a specific binding
    """

    def __init__(self):
        self.__forbidden = set()

    def forbid(self, module_name):
        sys.modules.pop(module_name, None)
        self.__forbidden.add(module_name)

    def find_module(self, fullname, path=None):
        if path:
            return
        if fullname in self.__forbidden:
            return self

    def load_module(self, fullname):
        raise ImportError("""
    Importing %s disabled by IPython, which has
    already imported an Incompatible QT Binding: %s
    """ % (fullname, loaded_api()))

ID = ImportDenier()
sys.meta_path.append(ID)


def commit_api(api):
    """Commit to a particular API, and trigger ImportErrors on subsequent
       dangerous imports"""

    if api == QT_API_PYSIDE:
        ID.forbid('PyQt4')
        ID.forbid('PyQt5')
        ID.forbid('PyQt6')
    else:
        ID.forbid('PySide6')


def loaded_api():
    """Return which API is loaded, if any

    If this returns anything besides None,
    importing any other Qt binding is unsafe.

    Returns
    -------
    None, 'pyside', 'pyqt', or 'pyqtv1'
    """
    if 'PyQt4.QtCore' in sys.modules:
        if qtapi_version() == 2:
            return QT_API_PYQT
        else:
            return QT_API_PYQTv1
    elif 'PySide6.QtCore' in sys.modules:
        return QT_API_PYSIDE
    elif 'PyQt5.QtCore' in sys.modules:
        return QT_API_PYQT5
    elif 'PyQt6.QtCore' in sys.modules:
        return QT_API_PYQT6
    return None


def has_binding(api):
    """Safely check for PyQt4 or PySide6, without importing
       submodules

       Parameters
       ----------
       api : str [ 'pyqtv1' | 'pyqt' | 'pyside' | 'pyqtdefault']
            Which module to check for

       Returns
       -------
       True if the relevant module appears to be importable
    """
    # we can't import an incomplete pyside and pyqt4
    # this will cause a crash in sip (#1431)
    # check for complete presence before importing
    module_name = {QT_API_PYSIDE: 'PySide6',
                   QT_API_PYQT: 'PyQt4',
                   QT_API_PYQTv1: 'PyQt4',
                   QT_API_PYQT_DEFAULT: 'PyQt4',
                   QT_API_PYQT5: 'PyQt5',
                   QT_API_PYQT6: 'PyQt6',
                   }
    module_name = module_name[api]

    try:
        #importing top level PyQt4/PySide6 module is ok...
        mod = __import__(module_name)
        #...importing submodules is not
        find_module('QtCore', mod.__path__, mod.__name__)
        find_module('QtGui', mod.__path__, mod.__name__)
        find_module('QtSvg', mod.__path__, mod.__name__)

        #we can also safely check PySide6 version
        if api == QT_API_PYSIDE:
            return check_version(mod.__version__, '6.0.0')
        else:
            return True
    except ImportError:
        return False


def qtapi_version():
    """Return which QString API has been set, if any

    Returns
    -------
    The QString API version (1 or 2), or None if not set
    """
    try:
        import sip
    except ImportError:
        return
    try:
        return sip.getapi('QString')
    except ValueError:
        return


def can_import(api):
    """Safely query whether an API is importable, without importing it"""
    if not has_binding(api):
        return False

    current = loaded_api()
    if api == QT_API_PYQT_DEFAULT:
        return current in [QT_API_PYQT, QT_API_PYQTv1, QT_API_PYQT5, QT_API_PYQT6, None]
    else:
        return current in [api, None]


def import_pyqt4(version=2):
    """
    Import PyQt4

    Parameters
    ----------
    version : 1, 2, or None
      Which QString/QVariant API to use. Set to None to use the system
      default

    ImportErrors raised within this function are non-recoverable
    """
    # The new-style string API (version=2) automatically
    # converts QStrings to Unicode Python strings. Also, automatically unpacks
    # QVariants to their underlying objects.
    import sip

    if version is not None:
        sip.setapi('QString', version)
        sip.setapi('QVariant', version)

    from PyQt4 import QtGui, QtCore, QtSvg

    if not check_version(QtCore.PYQT_VERSION_STR, '4.7'):
        raise ImportError("IPython requires PyQt4 >= 4.7, found %s" %
                          QtCore.PYQT_VERSION_STR)

    # Alias PyQt-specific functions for PySide6 compatibility.
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot

    # query for the API version (in case version == None)
    version = sip.getapi('QString')
    api = QT_API_PYQTv1 if version == 1 else QT_API_PYQT
    return QtCore, QtGui, QtSvg, api

def import_pyqt5():
    """
    Import PyQt5

    ImportErrors raised within this function are non-recoverable
    """
    from PyQt5 import QtGui, QtCore, QtSvg

    # Alias PyQt-specific functions for PySide6 compatibility.
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot

    return QtCore, QtGui, QtSvg, QT_API_PYQT5

def import_pyqt6():
    from PyQt6 import QtGui, QtCore, QtSvg

    # Alias PyQt-specific functions for PySide6 compatibility.
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot

    return QtCore, QtGui, QtSvg, QT_API_PYQT6


def import_pyside():
    """
    Import PySide6

    ImportErrors raised within this function are non-recoverable
    """
    from PySide6 import QtGui, QtCore, QtSvg  # @UnresolvedImport
    return QtCore, QtGui, QtSvg, QT_API_PYSIDE


def load_qt(api_options):
    """
    Attempt to import Qt, given a preference list
    of permissible bindings

    It is safe to call this function multiple times.

    Parameters
    ----------
    api_options: List of strings
        The order of APIs to try. Valid items are 'pyside',
        'pyqt', and 'pyqtv1'

    Returns
    -------

    A tuple of QtCore, QtGui, QtSvg, QT_API
    The first three are the Qt modules. The last is the
    string indicating which module was loaded.

    Raises
    ------
    ImportError, if it isn't possible to import any requested
    bindings (either becaues they aren't installed, or because
    an incompatible library has already been installed)
    """
    loaders = {QT_API_PYSIDE: import_pyside,
               QT_API_PYQT: import_pyqt4,
               QT_API_PYQTv1: partial(import_pyqt4, version=1),
               QT_API_PYQT_DEFAULT: partial(import_pyqt4, version=None),
               QT_API_PYQT5: import_pyqt5,
               QT_API_PYQT6: import_pyqt6,
               }

    for api in api_options:

        if api not in loaders:
            raise RuntimeError(
                "Invalid Qt API %r, valid values are: %r, %r, %r, %r, %r, %r" %
                (api, QT_API_PYSIDE, QT_API_PYQT,
                 QT_API_PYQTv1, QT_API_PYQT_DEFAULT, QT_API_PYQT5, QT_API_PYQT6))

        if not can_import(api):
            continue

        #cannot safely recover from an ImportError during this
        result = loaders[api]()
        api = result[-1]  # changed if api = QT_API_PYQT_DEFAULT
        commit_api(api)
        return result
    else:
        raise ImportError("""
    Could not load requested Qt binding. Please ensure that
    PyQt4 >= 4.7 or PySide6 >= 6.0.0 is available,
    and only one is imported per session.

    Currently-imported Qt library:   %r
    PyQt4 installed:                 %s
    PyQt5 installed:                 %s
    PyQt6 installed:                 %s
    PySide6 >= 6.0.0 installed:      %s
    Tried to load:                   %r
    """ % (loaded_api(),
           has_binding(QT_API_PYQT),
           has_binding(QT_API_PYQT5),
           has_binding(QT_API_PYQT6),
           has_binding(QT_API_PYSIDE),
           api_options))
