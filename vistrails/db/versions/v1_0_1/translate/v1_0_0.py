############################################################################
##
## Copyright (C) 2006-2008 University of Utah. All rights reserved.
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

import copy
from db.versions.v1_0_1.domain import DBVistrail, DBWorkflow, DBLog, \
    DBRegistry, DBModuleDescriptor, DBGroup

def translateVistrail(_vistrail):
    def update_workflow(old_obj, translate_dict):
        return DBWorkflow.update_version(old_obj.db_workflow, translate_dict)
    translate_dict = {'DBGroup': {'workflow': update_workflow}}
    vistrail = DBVistrail.update_version(_vistrail, translate_dict)
    vistrail.db_version = '1.0.1'
    return vistrail

def translateWorkflow(_workflow):
    def update_workflow(old_obj, translate_dict):
        return DBWorkflow.update_version(old_obj.db_workflow, translate_dict)
    translate_dict = {'DBGroup': {'workflow': update_workflow}}
    workflow = DBWorkflow.update_version(_workflow, translate_dict)
    workflow.db_version = '1.0.1'
    return workflow

def translateLog(_log):
    translate_dict = {}
    log = DBLog.update_version(_log, translate_dict)
    log.db_version = '1.0.1'
    return log

def translateRegistry(_registry):
    def update_descriptors(old_obj, translate_dict):
        def get_update_method(package_version):
            def update_package_version(old_desc, t_dict):
                return package_version
            return update_package_version

        descriptors = []
        for descriptor in old_obj.db_module_descriptors:
            new_t_dict = {'DBModuleDescriptor': 
                          {'package_version': \
                               get_update_method(old_obj.db_version)}}
            d = DBModuleDescriptor.update_version(descriptor, new_t_dict)
            descriptors.append(d)
        return descriptors

    translate_dict = {'DBPackage': {'module_descriptors': update_descriptors}}
    registry = DBRegistry.update_version(_registry, translate_dict)
    registry.db_version = '1.0.1'
    return registry