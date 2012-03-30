from core.bundles import py_import

#vtk = py_import('vtk', {'linux-ubuntu': 'python-vtk',
#                        'linux-fedora': 'vtk-python'})

from core.utils import all, any, VistrailsInternalError, InstanceObject
from core.debug import debug
from core.modules.basic_modules import Integer, Float, String, File, \
     Variant, Color, Boolean, identifier as basic_pkg
from core.modules.module_registry import get_module_registry
from core.modules.vistrails_module import new_module, ModuleError

def initialize():
    registry = get_module_registry()

    #import visitvariable
    #visitvariable.initialize()

    if registry.has_module('edu.utah.sci.vistrails.spreadsheet',
                           'SpreadsheetCell'):                
        import visitcell        
        visitcell.registerSelf()
    else:
        print 'Spreadsheet not found!'