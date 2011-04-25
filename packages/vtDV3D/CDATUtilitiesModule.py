'''
Created on Mar 22, 2011

@author: tpmaxwel
'''
import vtk, sys, os, copy, time
from InteractiveConfiguration import *
from core.modules.vistrails_module import Module, ModuleError
from WorkflowModule import WorkflowModule 
from ModuleStore import ModuleStoreDatabase
from core.vistrail.port_spec import PortSpec
from vtUtilities import *
from PersistentModule import * 
from CDATTaskDefinitions import TaskManager
import numpy.ma as ma
from vtk.util.misc import vtkGetDataRoot
import cdms2 
from PyQt4 import QtCore, QtGui
from core.modules.module_registry import get_module_registry
from core.vistrail.port import PortEndPoint

class PM_CDMS_CDATUtilities( PersistentModule ):

    def __init__(self, mid):
        PersistentModule.__init__( self, mid, createColormap=False )
        self.completedTaskRecs = {}
        self.task = None
        self.updateLabel()
        
    def setTaskCompleted( self, task_key ):
        tsCompletedTasks = self.completedTaskRecs.setdefault( self.iTimestep, {} )
        tsCompletedTasks[ task_key  ] = True

    def getTaskCompleted( self, task_key ):
#        wmod = self.getWorkflowModule()  
#        if wmod == None: return False
        tsCompletedTasks = self.completedTaskRecs.get( self.iTimestep, {} )
        return tsCompletedTasks.get( task_key, False )
                
    def updateLabel( self, recreate = False ):
        controller, module = self.getRegisteredModule()
        if module.has_annotation_with_key('__desc__'):
            label = module.get_annotation_by_key('__desc__').value.strip()
            controller.add_annotation( ('__desc__', str(label)), module.id ) 
            if recreate: controller.current_pipeline_view.recreate_module( controller.current_pipeline, module.id )
            
    def executeTask(self, skipCompletedTasks, **args):
        cdmsDataset = self.getInputValue( "dataset"  ) 
        taskInputData = self.getInputValue( "task"  ) 
        taskMap =  decodeFromString( getItem( taskInputData ) ) if taskInputData else None   
        taskData =  taskMap.get( cdmsDataset.id, None ) if taskMap else None
        if taskData:
            taskName = taskData[0]
            if taskName:
                taskClass = TaskManager.getTask( taskName )
                task = taskClass( cdmsDataset )
                task_key = task.getInputMap( self )
                if ( skipCompletedTasks and self.getTaskCompleted( task_key ) ):   print " Skipping completed task: %s " % task_key
                else:  task.compute( self.iTimestep, **args )
                self.setTaskCompleted( task_key )
            else:
                print>>sys.stderr, "Error, no task defined in CDATUtilities module"  
        self.setResult( 'dataset', cdmsDataset )
        
    def dvCompute(self, **args ):
        self.initializeInputs( **args )
        self.executeTask( False, **args)     
        self.initializeConfiguration()            
        self.persistLayerDependentParameters()
        
    def dvUpdate(self, **args ):
        self.executeTask( True, **args)     

#    def processParameterChange( self, parameter_name, new_parameter_value ):
#        PersistentModule.processParameterChange( self, parameter_name, new_parameter_value )
#        if parameter_name == 'task': self.setLabel( new_parameter_value )
        
class CDMS_CDATUtilities(WorkflowModule):
    
    PersistentModuleClass = PM_CDMS_CDATUtilities
    
    def __init__( self, **args ):
        WorkflowModule.__init__(self, **args)     

def getVariableSelectionLabel( varName, ndims ):
    if ndims == 2:  return '%s (slice)' % varName 
    if ndims == 3:  return '%s (volume)' % varName 
    return ''

class CDATUtilitiesModuleConfigurationWidget(DV3DConfigurationWidget):

    def __init__(self, module, controller, parent=None):
        self.serializedTaskData = None
        self.variableList = None
        self.outputNames = None
        self.task = None
        self.taskMap = {}
        self.inputMap = None
        self.outputMap = {}
        self.timeRange = None
        self.datasetId = None
        self.inputTabIndex = -1
        self.outputTabIndex = -1
        DV3DConfigurationWidget.__init__(self, module, controller, 'CDMS Data Reader Configuration', parent)
        if module.has_annotation_with_key('__desc__'):
            label = module.get_annotation_by_key('__desc__').value.strip()
            title = '%s (%s) Module Configuration'%(label, module.name)
        else:
            title = '%s Module Configuration'%module.name
        self.setWindowTitle(title)
        self.setupTabs()

    def getParameters( self, module ):
        ( self.variableList, self.datasetId, self.cdmsFile, self.timeRange ) = DV3DConfigurationWidget.getVariableList( module.id )
        taskData = getFunctionParmStrValues( module, "task" )
        if taskData: self.processTaskData( getItem( taskData ) )
#        if taskData: self.serializedTaskData = taskData[0]          

    def processTaskData( self, taskData ):
        taskMapInput = decodeFromString( taskData ) 
        if taskMapInput:
            self.taskMap = taskMapInput         
            taskRecord = self.taskMap.get( self.datasetId, None )
            if taskRecord:
                self.task = taskRecord[0]
                inputs = taskRecord[1].split(';')
                self.inputMap = {}
                for input in inputs:
                    inputData = input.split(',')
                    if len(inputData) > 1:
                        self.inputMap[ inputData[0] ] = ( inputData[1], int(inputData[2]) )
                outputs = taskRecord[2].split(';')
                self.outputMap = {}
                for output in outputs:
                    outputData = output.split(',')
                    if len(outputData) > 1:
                        self.outputMap[ outputData[0] ] = outputData[1]
        
    def buildTaskList( self ):
        taskList = TaskManager.getTaskList()
        for taskName in taskList:
            self.taskCombo.addItem( taskName )
        if self.task:
            currentIndex = self.taskCombo.findText( self.task )
            self.taskCombo.setCurrentIndex( currentIndex )
                        
    def updateTask( self, qtask ):
        taskName = str( qtask )
        if self.outputTabIndex >= 0: self.tabbedWidget.removeTab( self.outputTabIndex )
        if self.inputTabIndex  >= 0: self.tabbedWidget.removeTab( self.inputTabIndex )
        inputsTab = QWidget()        
        self.inputTabIndex = self.tabbedWidget.addTab( inputsTab, 'inputs' )                 
        outputsTab = QWidget()        
        self.outputTabIndex = self.tabbedWidget.addTab( outputsTab, 'outputs' ) 

        taskClass = TaskManager.getTask( taskName )
        inputs_layout = QVBoxLayout()
        inputsTab.setLayout( inputs_layout ) 
        inputs_layout.setMargin(10)
        inputs_layout.setSpacing(10)
        self.varCombos = {}
        inputVar = None
        firstVar = None
        for input in taskClass.inputs:
            input_selection_layout = QHBoxLayout()
            input_selection_label = QLabel( "%s:" % str(input) )
            input_selection_layout.addWidget( input_selection_label ) 
    
            varCombo =  QComboBox ( self.parent() )
            input_selection_label.setBuddy( varCombo )
            varCombo.setMaximumHeight( 30 )
            input_selection_layout.addWidget( varCombo  )
            for ( var, ndims ) in self.variableList: 
                if ndims == 2: 
                    varCombo.addItem( getVariableSelectionLabel( var, ndims ) )
                    if not firstVar: firstVar = var
            for ( var, ndims ) in self.variableList: 
                if ndims == 3: 
                    varCombo.addItem( getVariableSelectionLabel( var, ndims ) )
                    if not firstVar: firstVar = var
            self.varCombos[input] = varCombo
            self.connect( varCombo, SIGNAL("currentIndexChanged(QString)"), self.updateOutputs ) 
            inputs_layout.addLayout(input_selection_layout)
            if self.inputMap:
                ( varValue, ndim ) = self.inputMap.get( input, ( None, None ) )
                if varValue:
                    varLabel = getVariableSelectionLabel( varValue, ndim )
                    currentIndex = varCombo.findText( varLabel )
                    varCombo.setCurrentIndex( currentIndex )
                    if not inputVar: inputVar = varValue
        if not inputVar: inputVar = firstVar
        

        outputs_layout = QVBoxLayout()
        outputsTab.setLayout( outputs_layout ) 
        outputs_layout.setMargin(10)
        outputs_layout.setSpacing(10)
        self.outputNames = {}
        for output in taskClass.outputs:
            output_selection_layout = QHBoxLayout()
            output_selection_label = QLabel( "%s:" % str(output) )
            output_selection_layout.addWidget( output_selection_label ) 
    
            outputEdit =  QLineEdit ( self.parent() )
            output_selection_label.setBuddy( outputEdit )
            output_selection_layout.addWidget( outputEdit  )
            self.outputNames[output] = outputEdit
            outputs_layout.addLayout(output_selection_layout)
            outputValue = self.outputMap.get( output, None )
            if not outputValue:
                outputValue = "%s.%s.%s" % ( inputVar, taskName, output ) if inputVar else "%s.%s" % ( taskName, output )
                self.outputMap[output] = outputValue
            outputEdit.setText( outputValue )
            
    def updateOutputs( self, arg ):
        if self.outputNames <> None:
#            print " updateOutputs: arg = %s " % str( arg )
            nameList = []
            for varCombo in self.varCombos.values():
                comboText = varCombo.currentText()
                varData = str( comboText ).split('(')
                varName = varData[0].strip()
                nameList.append( varName )
            taskName = str( self.taskCombo.currentText() )
            nameList.append( taskName )
            nameListText = '.'.join( nameList )            
            for output in self.outputNames:
                outputValue = "%s.%s" % ( nameListText, output )
                outputEdit = self.outputNames[ output ]
                outputEdit.setText( outputValue )                
           
    def getSerializedTaskData(self, taskName ):  
        serializedInputs, serializedOutputs = self.getSerializedIOData( taskName ) 
        self.taskMap[ self.datasetId ] = [ taskName, serializedInputs, serializedOutputs ]
        return encodeToString( self.taskMap )
        
    def getSerializedIOData( self, taskName ):
        ioData = []
        varDimMap = {}
        for input in self.varCombos:
            var = self.varCombos[input].currentText() 
            varData = var.split('(')
            if len( varData ) > 1:
                varType = str(varData[1]).strip()
                ndim = 3 if ( varType[0] == 'v' ) else 2
                varDimMap[ input ] = ndim
                ioData.append( '%s,%s,%d' % ( str(input), str(varData[0]).strip(), ndim ) )
        serializedInputs = ';'.join( ioData )
        ioData = []
        taskClass = TaskManager.getTask( taskName )
        for output in self.outputNames:
            var = self.outputNames[output].text() 
            ndim = taskClass.getOutputDimensionality( output, varDimMap )
            if ndim: ioData.append( '%s,%s,%d' % ( str(output), str(var), ndim ) )
        serializedOutputs = ';'.join( ioData )
        return serializedInputs, serializedOutputs 
                          
    def setupTabs(self):
        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setMargin(0)
        self.layout().setSpacing(0)
        self.tabbedWidget = QTabWidget()
        self.layout().addWidget( self.tabbedWidget ) 
        
        tasksTab = QWidget()        
        self.tabbedWidget.addTab( tasksTab, 'tasks' )                 
        tasks_layout = QVBoxLayout()
        tasksTab.setLayout( tasks_layout ) 
        
        task_selection_layout = QHBoxLayout()
        task_selection_label = QLabel( "Tasks:"  )
        task_selection_layout.addWidget( task_selection_label ) 

        self.taskCombo =  QComboBox ( self.parent() )
        task_selection_label.setBuddy( self.taskCombo )
        self.taskCombo.setMaximumHeight( 30 )
        task_selection_layout.addWidget( self.taskCombo  )
        self.buildTaskList()
        self.connect( self.taskCombo, SIGNAL("currentIndexChanged(QString)"), self.updateTask ) 
        tasks_layout.addLayout(task_selection_layout)
        
        self.updateTask( self.taskCombo.currentText() )

#        portsTab = QWidget()        
#        self.tabbedWidget.addTab( portsTab, 'parameters' )                 
#        ports_layout = QVBoxLayout()
#        portsTab.setLayout( ports_layout ) 
# 
#        self.scrollArea = QtGui.QScrollArea(self)
#        ports_layout.addWidget(self.scrollArea)
#        self.scrollArea.setFrameStyle(QtGui.QFrame.NoFrame)
#        self.listContainer = QtGui.QWidget(self.scrollArea)
#        self.listContainer.setLayout(QtGui.QGridLayout(self.listContainer))
#        self.inputPorts = self.module.destinationPorts()
#        self.inputDict = {}
#        self.outputPorts = self.module.sourcePorts()
#        self.outputDict = {}
#        self.constructList()
        
        self.buttonLayout = QtGui.QHBoxLayout()
        self.buttonLayout.setMargin(5)
        self.okButton = QtGui.QPushButton('&OK', self)
        self.okButton.setFixedWidth(100)
        self.buttonLayout.addWidget(self.okButton)
        self.cancelButton = QtGui.QPushButton('&Cancel', self)
        self.cancelButton.setShortcut('Esc')
        self.cancelButton.setFixedWidth(100)
        self.buttonLayout.addWidget(self.cancelButton)
        self.layout().addLayout(self.buttonLayout)
        self.connect(self.okButton, QtCore.SIGNAL('clicked(bool)'), self.okTriggered)
        self.connect(self.cancelButton, QtCore.SIGNAL('clicked(bool)'), self.close )

#    def checkBoxFromPort(self, port, input_=False):
#        checkBox = QtGui.QCheckBox(port.name)
#        if input_:
#            pep = PortEndPoint.Destination
#        else:
#            pep = PortEndPoint.Source
#        if not port.optional or (pep, port.name) in self.module.portVisible:
#            checkBox.setCheckState(QtCore.Qt.Checked)
#        else:
#            checkBox.setCheckState(QtCore.Qt.Unchecked)
#        if not port.optional or (input_ and port.sigstring=='()'):
#            checkBox.setEnabled(False)
#        return checkBox

#    def constructList(self):
#        label = QtGui.QLabel('Input Ports')
#        label.setAlignment(QtCore.Qt.AlignHCenter)
#        label.font().setBold(True)
#        label.font().setPointSize(12)
#        self.listContainer.layout().addWidget(label, 0, 0)
#        label = QtGui.QLabel('Output Ports')
#        label.setAlignment(QtCore.Qt.AlignHCenter)
#        label.font().setBold(True)
#        label.font().setPointSize(12)
#        self.listContainer.layout().addWidget(label, 0, 1)
#
#        for i in xrange(len(self.inputPorts)):
#            port = self.inputPorts[i]
#            checkBox = self.checkBoxFromPort(port, True)
#            self.inputDict[port.name] = checkBox
#            self.listContainer.layout().addWidget(checkBox, i+1, 0)
#        
#        for i in xrange(len(self.outputPorts)):
#            port = self.outputPorts[i]
#            checkBox = self.checkBoxFromPort(port)
#            self.outputDict[port.name] = checkBox
#            self.listContainer.layout().addWidget(checkBox, i+1, 1)
#        
#        self.listContainer.adjustSize()
#        self.listContainer.setFixedHeight(self.listContainer.height())
#        self.scrollArea.setWidget(self.listContainer)
#        self.scrollArea.setWidgetResizable(True)

    def sizeHint(self):
        return QtCore.QSize( 350, 250 )

    def okTriggered(self, checked = False):
#        for port in self.inputPorts:
#            entry = (PortEndPoint.Destination, port.name)
#            if (port.optional and
#                self.inputDict[port.name].checkState()==QtCore.Qt.Checked):
#                self.module.portVisible.add(entry)
#            else:
#                self.module.portVisible.discard(entry)
#            
#        for port in self.outputPorts:
#            entry = (PortEndPoint.Source, port.name)
#            if (port.optional and
#                self.outputDict[port.name].checkState()==QtCore.Qt.Checked):
#                self.module.portVisible.add(entry)
#            else:
#                self.module.portVisible.discard(entry)
        task = str( self.taskCombo.currentText() )
        self.persistParameter( 'task', [ self.getSerializedTaskData( task ) ] )
        self.pmod.persistVersionMap()   
        if self.pmod:  
            self.pmod.addAnnotation( 'datasetId', self.datasetId  )
            self.pmod.setLabel( task )
        self.close()

if __name__ == '__main__':
    executeVistrail( 'TestPipeline1', 'TestPipeline2' )