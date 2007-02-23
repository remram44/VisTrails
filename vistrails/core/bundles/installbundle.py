############################################################################
##
## Copyright (C) 2006-2007 University of Utah. All rights reserved.
##
## This file is part of VisTrails.
##
## This file may be used under the terms of the GNU General Public
## License version 2.0 as published by the Free Software Foundation
## and appearing in the file LICENSE.GPL included in the packaging of
## this file.  Please review the following to ensure GNU General Public
## Licensing requirements will be met:
## http://www.opensource.org/licenses/gpl-license.php
##
## If you are unsure which license is appropriate for your use (for
## instance, you are interested in developing a commercial derivative
## of VisTrails), please contact us at vistrails@sci.utah.edu.
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
##
############################################################################

"""Module with utilities to try and install a bundle if possible."""

from core.bundles.utils import guess_system, guess_graphical_sudo
import core.bundles.installbundle # this is on purpose
import os

##############################################################################

def linux_ubuntu_install(package_name):
    # HACK, otherwise splashscreen stays in front of screens
    try:
        import PyQt4.QtCore
        PyQt4.QtCore.QCoreApplication.instance().splashScreen.hide()
    except:
        pass

    cmd = core.system.visTrailsRootDirectory()
    cmd += '/core/bundles/linux_ubuntu_install.py '
    cmd += package_name

    sucmd = guess_graphical_sudo() + " '" + cmd + "'"
    result = os.system(sucmd)

    return (result == 0) # 0 indicates success

def install(dependency_dictionary):
    """Tries to import a python module. If unsuccessful, tries to install
the appropriate bundle and then reimport. py_import tries to be smart
about which system it runs on."""
    distro = guess_system()
    if not dependency_dictionary.has_key(distro):
        return False
    else:
        callable_ = getattr(core.bundles.installbundle,
                            distro.replace('-', '_') + '_install')
        return callable_(dependency_dictionary[distro])