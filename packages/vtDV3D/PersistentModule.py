'''
Created on Dec 17, 2010

@author: tpmaxwel
'''

import vtk, sys, time, threading, inspect
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from core.modules.vistrails_module import Module, ModuleError
from packages.spreadsheet.spreadsheet_controller import spreadsheetController
from InteractiveConfiguration import *
from ColorMapManager import ColorMapManager 
from ModuleStore import ModuleStoreDatabase
from db.domain import DBModule, DBAnnotation
from vtUtilities import *

moduleInstances = {}

def CheckAbort(obj, event):
   if obj.GetEventPending() != 0:
       obj.SetAbortRender(1)
       
def IsListType( val ):
    valtype = type(val)
    return ( valtype ==type(list()) ) or  ( valtype ==type(tuple()) )

def ExtendClassDocumentation( klass ):
    instance = klass()
    default_doc = "" if ( klass.__doc__ == None ) else klass.__doc__ 
    klass.__doc__ = " %s\n %s " % ( default_doc, instance.getConfigurationHelpText() )
 
################################################################################      

class AlgorithmOutputModule( Module ):
    
    def __init__( self, **args ):
        Module.__init__(self) 
        self.algoOutput = args.get('output',None)  
        self.algoOutputPort = args.get('port',None)
        
    def getOutput(self): 
        if self.algoOutput <> None: return self.algoOutput
        if self.algoOutputPort <> None: return self.algoOutputPort.GetProducer().GetOutput() 
        return None
                
    def getOutputPort(self): 
        return self.algoOutputPort 
    
    def inputToAlgorithm( self, algorithm, iPort = -1 ):
        if self.algoOutputPort <> None: 
            if iPort < 0:   algorithm.SetInputConnection( self.algoOutputPort )
            else:           algorithm.SetInputConnection( iPort, self.algoOutputPort )
        else: algorithm.SetInput( self.getOutput() )

class AlgorithmOutputModule3D( AlgorithmOutputModule ):
    
    def __init__( self, renderer, **args ):
        AlgorithmOutputModule.__init__( self, **args ) 
        self.renderer = renderer 
    
    def getRenderer(self): 
        return self.renderer
   
class PersistentModule( QObject ):
    '''
    <H2> Interactive Configuration</H2>
    All vtDV3D Workflow Module support interactive configuration functions that 
    are used to configure parameters for colormaps, transfer functions, and other display options. 
    All configuration  functions are invoked using command keys and saved as provenance upon completion.   
    Consult the 'modules' tab of the help widget for a list of available command keys for the current cell. <P>
        There are two types of configuration functions: gui functions and leveling functions.  
        <h3> GUI Functions </h3>
        GUI functions facilitate interactive parameter configurations that require a choice from a discreet set of possible values
        ( e.g. choosing a colormap or the number of contour levels ). Typing the the gui command code pops up a gui widget.  
        All gui function command codes are lower case.
        <h3> Leveling Functions </h3>
        Leveling functions facilitate interactive configuration of continuously varying parameters  ( e.g. scaling a colormap or 
        configuring a transfer function ). Typing the leveling command code puts the cell into leveling mode.  Leveling is initiated
        when the user left-clicks in the cell while it is in leveling mode.  Mouse drag operations (while leveling) generate
        leveling configurations.  When the (left) mouse button is release the leveling configuration is saved as provenance and the
        cell returns to normal (non-leveling) mode.   
    '''          
    def __init__( self, mid, **args ):
        QObject.__init__(self)
        self.moduleID = mid
        self.initVersionMap()
        self.datasetId = None
        self.fieldData = None
        self.rangeBounds = None
        self.newDataset = False
        self.wmod = None
        self.allowMultipleInputs = False
        self.newLayerConfiguration = False
        self.inputModuleList = None
        self.nonFunctionLayerDepParms = args.get( 'layerDepParms', [] )
        self.input =  None
        self.roi = None 
        self.activeLayer = None
        self.configurableFunctions = {}
        self.configuring = False
        self.InteractionState = None
        self.requiresPrimaryInput = args.get( 'requiresPrimaryInput', True )
        self.createColormap = args.get( 'createColormap', True )
        self.parmUpdating = {}
        self.ndims = args.get( 'ndims', 3 ) 
        self.primaryInputPort = 'slice' if (self.ndims == 2) else 'volume' 
        self.primaryMetaDataPort = self.primaryInputPort
        self.documentation = None
        self.parameterCache = {}
        self.taggedVersionMap = {}
        self.iTimestep = 0
        if self.createColormap:
            self.addConfigurableGuiFunction( 'colormap', ColormapConfigurationDialog, 'c', setValue=self.setColormap, getValue=self.getColormap, layerDependent=True )
        self.addConfigurableGuiFunction( 'timestep', AnimationConfigurationDialog, 'a', setValue=self.setTimestep, getValue=self.getTimestep )
#        self.addConfigurableGuiFunction( 'layer', LayerConfigurationDialog, 'l', setValue=self.setLayer, getValue=self.getLayer )

    def invalidateWorkflowModule( self, workflowModule ):
        if (self.wmod == workflowModule): self.wmod = None

    def setWorkflowModule( self, workflowModule ):
        self.wmod = workflowModule

    def initiateParameterUpdate( self, parmName ):
        self.parmUpdating[parmName] = True     
     
    def addAnnotation( self, id, note ):  
        controller, module = self.getRegisteredModule() 
        controller.add_annotation( (id, str(note)), module.id ) 
    
    def setLabel( self, label ):      
        controller, module = self.getRegisteredModule() 
        controller.add_annotation( ('__desc__', str(label)), module.id ) 
        controller.current_pipeline_view.recreate_module( controller.current_pipeline, module.id )
        pass
        
    def setNewConfiguration(self, **args ):
        self.newLayerConfiguration = args.get( 'newLayerConfig', False )

    def clearNewConfiguration(self):
        self.newLayerConfiguration = False
    
    def generateDocumentation(self):
        self.documentation = "\n <h2>Module %s</h2> \n" % ( self.__class__.__name__ )
        if self.__class__.__doc__ <> None: self.documentation += self.__class__.__doc__
        self.documentation += self.getConfigurationHelpText()

    def getCachedParameter(self, parameter_name ):
        layerCache = self.parameterCache.setdefault( self.getParameterId(), {} )
        return layerCache.get( parameter_name )
        
    def getParameter(self, parameter_name, default_value = None ):
        paramVal = self.getCachedParameter( parameter_name  )
        if paramVal == None:
            paramVal = self.getTaggedParameterValue( parameter_name )
            if paramVal <> None: self.setParameter( parameter_name, paramVal )
        return paramVal if paramVal else default_value
                
    def setParameter(self, parameter_name, value, parameter_id = None ):
        if parameter_id == None: parameter_id = self.getParameterId()
        layerCache = self.parameterCache.setdefault( parameter_id, {} )
        layerCache[parameter_name] = value 

    def getTaggedParameterValue(self, parameter_name ):
        import api
        tag = self.getParameterId()
        ctrl = api.get_current_controller()
        pval = None
        if tag <> None: 
            try:
                tagged_version_number = self.getTaggedVersion( tag )
                if tagged_version_number >= 0:
                    functionID = getFunctionId( self.moduleID, parameter_name, ctrl )
                    if functionID >= 0:
                        tagged_pipeLine =  ctrl.vistrail.getPipeline( tagged_version_number )
                        tagged_module = tagged_pipeLine.modules[ self.moduleID ]
                        tagged_function = tagged_module.functions[functionID]
                        parameterList = tagged_function.parameters
                        pval = [ translateToPython( parmRec ) for parmRec in parameterList ]
#                        print " --- getTaggedParameterValue[%s]: tag=%s, version=%d, value=%s " % ( parameter_name, tag, tagged_version_number, str(pval) )
            except Exception, err:
                print>>sys.stderr, " Exception in getTaggedParameterValue: %s " % str( err )
        return pval
                
        
    def is_cacheable(self):
        return False
    
    def updateTextDisplay( self, text = None ):
        pass
            
    def getName(self):
        return str( self.__class__.__name__ )
        
    def dvCompute( self, **args ):
        self.initializeInputs( **args )     
        if self.input or self.inputModuleList or not self.requiresPrimaryInput:
            self.execute()
            self.initializeConfiguration()
        elif self.requiresPrimaryInput:
            print>>sys.stderr, " Error, no input to module %s " % ( self.__class__.__name__ )
        self.persistLayerDependentParameters()

    def dvUpdate(self):
        self.initializeInputs()     
        self.execute()
 
    def getRangeBounds(self): 
        return self.rangeBounds
    
    def getScalarRange(self): 
        return self.scalarRange

    def getParameterDisplay( self, parmName, parmValue ):
        if parmName == 'timestep':
            return str( self.iTimestep ), 1
        return None, 1
          
    def getPrimaryInput( self, **args ):
        return self.getInputValue( self.primaryInputPort, **args )
    
    def getPrimaryInputList(self, **args ):
        return self.getInputList( self.primaryInputPort, **args  )
    
    def isLayerDependentParameter( self, parmName ):
        cf = self.configurableFunctions.get( parmName, None )
        if cf: return cf.isLayerDependent
        try:
            pindex = self.nonFunctionLayerDepParms.index( parmName )
            return True
        except: return False 
       
    def getInputList( self, inputName, **args ):
        inputList = None
        portInputIsValid = not ( self.newLayerConfiguration and self.isLayerDependentParameter(inputName) )
        if portInputIsValid: 
#            wmod = args.get( 'wmod', self.getWorkflowModule() )
            if self.wmod:  inputList = self.wmod.forceGetInputListFromPort( inputName )
        if inputList == None:         
            inputList = self.getParameter( inputName, None )
        return inputList  
      
    def getInputValue( self, inputName, default_value = None, **args ):
        inputVal = None
        portInputIsValid = not ( self.newLayerConfiguration and self.isLayerDependentParameter(inputName) )
        if portInputIsValid: 
#            self.wmod = args.get( 'wmod', self.getWorkflowModule() )
            if self.wmod:  inputVal = self.wmod.forceGetInputFromPort( inputName, None )
            else:     inputVal = getFunctionParmStrValues( args.get( 'dbmod', None ), inputName  )
#                print " %s ---> getInputValueFromPort( %s ) : %s " % ( self.getName(), inputName, str(inputVal) )
        if inputVal == None:         
            inputVal = self.getParameter( inputName, default_value )
#            print " %s ---> getInputValueFromCache( %s ) : %s " % ( self.getName(), inputName, str(inputVal) )
        return inputVal
    
    def setResult( self, outputName, value ): 
#        wmod = self.getWorkflowModule()   
        if self.wmod <> None:       self.wmod.setResult( outputName, value )
        self.setParameter( outputName, value )
                    
    def initializeLayers( self, scalars ):
#        activeLayerInput = self.getInputValue( 'layer' )
#        if activeLayerInput == None: activeLayerInput = self.getParameter( 'layer' ) 
#        print " initializeLayers: activeLayerInput = %s " % str( activeLayerInput )
#        if activeLayerInput:
#            newActiveLayer = getItem(  activeLayerInput )
#            if  newActiveLayer <> self.activeLayer:
#                self.activeLayer = newActiveLayer
##                self.setParameterInputsEnabled( False ) 
        if self.activeLayer == None: 
            self.activeLayer =self.getAnnotation( 'activeLayer' )
        if self.input and not scalars:
            scalarsArray = self.input.GetPointData().GetScalars()
            if scalarsArray <> None:
                scalars = scalarsArray.GetName() 
            else:
                layerList = self.getLayerList()
                if len( layerList ): scalars = layerList[0] 
        if self.activeLayer <> scalars:
            self.updateLayerDependentParameters( self.activeLayer, scalars )
            self.activeLayer = scalars 
            self.addAnnotation( 'activeLayer', self.activeLayer  ) 

    
    def getLayerList(self):
        layerList = []
        pointData = self.input.GetPointData()
        for iA in range( pointData.GetNumberOfArrays() ):
            array_name = pointData.GetArrayName(iA)
            if array_name: layerList.append( array_name )
        return layerList
    
    def setLayer( self, layer ):
        self.activeLayer = getItem( layer )

    def getLayer( self ):
        return [ self.activeLayer, ]
    
    def updateMetadata(self):
        scalars = None
        self.newDataset = False
        if self.input <> None:
            fd = self.input.GetFieldData() 
#            print " %s:initMetadata---> # Arrays = %d" % ( self.__class__.__name__, fd.GetNumberOfArrays() )
            self.input.Update()
            self.fieldData = self.input.GetFieldData() 
#            print " %s:updateMetadata---> # Arrays = %d" % ( self.__class__.__name__, self.fieldData.GetNumberOfArrays() )
            self.rangeBounds = None
            metadata = self.getMetadata()
            if metadata <> None: 
                self.setParameter( 'metadata', metadata )
                self.roi = metadata.get( 'bounds', None )
                
                dsetId = metadata.get( 'datasetId', None )
                if self.datasetId <> dsetId:
                    self.pipelineBuilt = False
                    if self.datasetId <> None: self.newDataset = True
                    self.datasetId = dsetId
                               
                dtype =  metadata.get( 'datatype', None )
                scalars =  metadata.get( 'scalars', None )
                self.rangeBounds = getRangeBounds( dtype )
                self.scalarRange = None
                if scalars <> None:
                    var_md = metadata.get( scalars , None )
                    if var_md <> None:
                        range = var_md.get( 'range', None )
                        if range: 
                            self.scalarRange = list( range )
                            self.scalarRange.append( 1 )
        return scalars
           
    def setActiveScalars( self ):
        pass
#        pointData = self.input.GetPointData()
#        if self.activeLayer:  
#            pointData.SetActiveScalars( self.activeLayer )
#            print " SetActiveScalars on pointData %d: %s" % ( id(pointData), self.activeLayer )
           
                                   
#    def transferInputLayer( self, imageData ):
#        oldPointData = imageData.GetPointData() 
#        array_names = [ oldPointData.GetArrayName(iP) for iP in range( oldPointData.GetNumberOfArrays() ) ]
#        for array_name in array_names: oldPointData.RemoveArray( array_name )
#        pointData = self.input.GetPointData()
#        activeArray = None
#        if self.activeLayer <> None:  activeArray = pointData.GetArray( self.activeLayer )
#        else:                         activeArray = pointData.GetArray( 0 )
#        if activeArray <> None:       imageData.GetPointData().SetScalars( activeArray )
                               

#        if self.input <> None:
#            pointData = self.input.GetPointData() 
#            scalars = pointData.GetScalars() 
#            i0 = scalars.GetNumberOfTuples()/2
#            datavalues = [ scalars.GetTuple1(i0+100*i) for i in range(3) ]      
#            print "%s.updateMetadata: scalars= %s, i0=%d, sample values= %s" % ( self.__class__.__name__, str(id(scalars)), i0, str(datavalues) )

    def getInputCopy(self):
        image_data = vtk.vtkImageData() 
        gridSpacing = self.input.GetSpacing()
        gridOrigin = self.input.GetOrigin()
        gridExtent = self.input.GetExtent()
        image_data.SetScalarType( self.input.GetScalarType() )  
        image_data.SetOrigin( gridOrigin[0], gridOrigin[1], gridOrigin[2] )
        image_data.SetSpacing( gridSpacing[0], gridSpacing[1], gridSpacing[2] )
        image_data.SetExtent( gridExtent[0], gridExtent[1], gridExtent[2], gridExtent[3], gridExtent[4], gridExtent[5] )
        return image_data

    def initializeInputs( self, **args ):
        if self.allowMultipleInputs:
            try:
                self.inputModuleList = self.getPrimaryInputList( **args )
                self.inputModule = self.inputModuleList[0]
            except Exception, err:
                raise ModuleError( self, 'Broken pipeline at input to module %s:\n (%s)' % ( self.__class__.__name__, str(err) ) )
        else:
            self.inputModule = self.getPrimaryInput( **args )
            if self.inputModule == None: print " ---- No input to module %s ---- " % ( self.__class__.__name__ )
#        print " %s.initializeInputs: input Module= %s " % ( self.__class__.__name__, str( input_id ) )
        if  self.inputModule <> None: 
            self.input =  self.inputModule.getOutput() 
            print " --- %s:initializeInputs---> # Arrays = %d " % ( self.__class__.__name__,  ( self.input.GetFieldData().GetNumberOfArrays() if self.input else -1 ) )   
            scalars = self.updateMetadata()            
            self.initializeLayers( scalars )
#            self.setActiveScalars()
            
        elif ( self.fieldData == None ): 
            self.initializeMetadata()

    def getDataValue( self, image_value):
        if not self.scalarRange: raise ModuleError( self, "ERROR: no variable selected in dataset input to module %s" % str( self.__class__.__name__ ) )
        valueRange = self.scalarRange
        sval = ( image_value - self.rangeBounds[0] ) / ( self.rangeBounds[1] - self.rangeBounds[0] )
        dataValue = valueRange[0] + sval * ( valueRange[1] - valueRange[0] ) 
        return dataValue

    def getDataValues( self, image_value_list ):
        if not self.scalarRange: raise ModuleError( self, "ERROR: no variable selected in dataset input to module %s" % str( self.__class__.__name__ ) )
        valueRange = self.scalarRange
        data_values = []
        for image_value in image_value_list:
            sval = ( image_value - self.rangeBounds[0] ) / ( self.rangeBounds[1] - self.rangeBounds[0] )
            dataValue = valueRange[0] + sval * ( valueRange[1] - valueRange[0] ) 
            data_values.append( dataValue )
        return data_values

    def getImageValue( self, data_value ):
        if not self.scalarRange: raise ModuleError( self, "ERROR: no variable selected in dataset input to module %s" % str( self.__class__.__name__ ) )
        valueRange = self.scalarRange
        sval = ( data_value - valueRange[0] ) / ( valueRange[1] - valueRange[0] )
        imageValue = self.rangeBounds[0] + sval * ( self.rangeBounds[1] - self.rangeBounds[0] ) 
        return imageValue

    def getImageValues( self, data_value_list ):
        if not self.scalarRange: raise ModuleError( self, "ERROR: no variable selected in dataset input to module %s" % str( self.__class__.__name__ ) )
        valueRange = self.scalarRange
        imageValues = []
        for data_value in data_value_list:
            sval = ( data_value - valueRange[0] ) / ( valueRange[1] - valueRange[0] )
            imageValue = self.rangeBounds[0] + sval * ( self.rangeBounds[1] - self.rangeBounds[0] ) 
            imageValues.append( imageValue )
        return imageValues

    def set2DOutput( self, **args ):
#        wmod = args.get( 'wmod', self.getWorkflowModule()  )  
        if self.wmod:
            portName = args.get( 'name', 'slice' )
            outputModule = AlgorithmOutputModule( **args )
            output =  outputModule.getOutput() 
            fd = output.GetFieldData() 
            fd.PassData( self.fieldData )                      
            self.wmod.setResult( portName, outputModule ) 
        else: print " Missing wmod in %s.set2DOutput" % self.__class__.__name__

    def setOutputModule( self, outputModule, portName = 'volume', **args ): 
#        self.wmod = args.get( 'wmod', self.getWorkflowModule()  ) 
        if self.wmod:  
            output =  outputModule.getOutput() 
            fd = output.GetFieldData()  
            fd.PassData( self.fieldData )                
            self.wmod.setResult( portName, outputModule ) 
        else: print " Missing wmod in %s.set2DOutput" % self.__class__.__name__
        
    def getFieldData( self, id, fd=None ): 
        fdata = self.fieldData if fd==None else fd
        dataVector = fdata.GetAbstractArray( id ) 
        if dataVector == None: return None
        nd = dataVector.GetNumberOfTuples()
        return [ dataVector.GetValue(id) for id in range( nd ) ]         

    def setFieldData( self, id, data ): 
        dataVector = self.fieldData.GetAbstractArray( id ) 
        if dataVector == None: return False
        for id in range(len(data)): dataVector.SetValue( id, data[id] )         
 
    def applyFieldData( self, props ): 
        pass
#        position = self.getFieldData( 'position' ) 
#        if position <> None:  
#            for prop in props: 
#                prop.SetPosition( position )
#        scale = self.getFieldData( 'scale' ) 
#        if scale <> None: 
#            for prop in props: 
#                prop.SetScale( scale )
#        print " applyFieldData, pos = %s" % ( str(position) )

    def addMetadata( self, metadata ):
        dataVector = self.fieldData.GetAbstractArray( 'metadata' ) 
        if dataVector == None:   
            print " Can't get Metadata for class %s " % ( self.__class__.__name__ )
        else:
            enc_mdata = encodeToString( metadata )
            dataVector.InsertNextValue( enc_mdata  )

    def getMetadata( self, metadata = {}, port=None  ):
        if self.fieldData:
            md = extractMetadata( self.fieldData )
            if md: metadata.update( md )
        return metadata
        
    def addMetadataObserver( self, caller, event ):
        fd = caller.GetOutput().GetFieldData()
        fd.ShallowCopy( self.fieldData )
        pass

    def initializeMetadata( self ):
        self.fieldData = vtk.vtkDataSetAttributes()
        self.fieldData.AddArray( getStringDataArray( 'metadata' ) )
#        print " %s:initializeMetadata---> # FieldData Arrays = %d " % ( self.__class__.__name__, self.fieldData.GetNumberOfArrays() )
#        self.fieldData.AddArray( getFloatDataArray( 'position', [  0.0, 0.0, 0.0 ] ) )
#        self.fieldData.AddArray( getFloatDataArray( 'scale',    [  1.0, 1.0, 1.0 ] ) ) 
           
    def addConfigurableFunction(self, name, function_args, **args):
        self.configurableFunctions[name] = ConfigurableFunction( name, function_args, None, **args )

    def addConfigurableLevelingFunction(self, name, key, **args):
        self.configurableFunctions[name] = WindowLevelingConfigurableFunction( name, key, **args )

    def addConfigurableGuiFunction(self, name, guiClass, key, **args):
        guiCF = GuiConfigurableFunction( name, guiClass, key, start=self.startConfigurationObserver, update=self.updateConfigurationObserver, finalize=self.finalizeConfigurationObserver, **args )
        self.configurableFunctions[name] = guiCF

    def addConfigurableWidgetFunction(self, name, signature, widgetWrapper, key, **args):
        wCF = WidgetConfigurableFunction( name, signature, widgetWrapper, key, **args )
        self.configurableFunctions[name] = wCF
    
    def getConfigurationHelpText(self):
        lines = []
        lines.append( '\n <h3>Configuration Command Keys:</h3>\n' )
        lines.append(  '<table border="2" bordercolor="#336699" cellpadding="2" cellspacing="2" width="100%">\n' )
        lines.append( '<tr> <th> Command Key </th> <th> Configuration </th> <th> Type </th> </tr>' )
        lines.append( ''.join( [ configFunct.getHelpText() for configFunct in self.configurableFunctions.values() ] ) )
        lines.append( '</table>' )
        return ''.join( lines ) 
          
    def initializeConfiguration(self):
        for configFunct in self.configurableFunctions.values():
            configFunct.init( self )
            
    def applyConfiguration(self):
        for configFunct in self.configurableFunctions.values():
            configFunct.applyParameter( self )
            
#    def setParameterInputsEnabled( self, isEnabled ):
#        for configFunct in self.configurableFunctions.values():
#            configFunct.setParameterInputEnabled( isEnabled )
# TBD: integrate
    def startConfigurationObserver( self, parameter_name, *args ):
        self.textActor.VisibilityOn() 
    
    def startLevelingEvent( self, caller, event ):    
        x, y = caller.GetEventPosition()
        self.startLeveling( x, y )
                  
    def startLeveling( self, x, y ):
        if (self.InteractionState <> None) and not self.configuring:
            configFunct = self.configurableFunctions[ self.InteractionState ]
            if configFunct.type == 'leveling':
                self.configuring = True
                configFunct.start( self.InteractionState, x, y )
                if self.ndims == 3: 
                    self.iren.SetInteractorStyle( self.configurationInteractorStyle )
                    self.textActor.VisibilityOn()
    
    def isActive( self ):
        import api
        controller = api.get_current_controller()
        return ( self.moduleID in controller.current_pipeline.modules )
               
    def updateConfigurationObserver( self, parameter_name, new_parameter_value, *args ):
#        print " updateConfigurationObserver[%s], class = %s " % ( parameter_name, self.__class__.__name__ )
        try:
            self.setResult( parameter_name, new_parameter_value )
            configFunct = self.configurableFunctions[ parameter_name ]
            configFunct.setValue( new_parameter_value )
            self.processParameterChange( parameter_name, new_parameter_value )
            textDisplay = configFunct.getTextDisplay()
            if textDisplay <> None:  
                self.updateTextDisplay( textDisplay )
        except KeyError:
            print>>sys.stderr, " Can't find configuration function for parameter update: %s " % str( parameter_name )
                
    def updateLayerDependentParameters( self, old_layer, new_layer ):
#       print "updateLayerDependentParameters"
       self.newLayerConfiguration = True
#       for configFunct in self.configurableFunctions.values():
#            if configFunct.isLayerDependent:  
#                self.persistParameter( configFunct.name, None )     

    def refreshParameters( self, useInitialValue = False ):
        if useInitialValue:
           for configFunct in self.configurableFunctions.values():
               if configFunct.isLayerDependent:
                   pass        
        else:
#            wmod = self.getWorkflowModule( False )
            if self.wmod:    
                for configFunct in self.configurableFunctions.values():
                    value = self.wmod.forceGetInputFromPort( configFunct.name, None )
                    if value: self.setParameter( configFunct.name, value )
            else: print " Missing wmod in %s.refreshParameters" % self.__class__.__name__
                    
#            for configFunct in self.configurableFunctions.values():
#                    
#                    self.persistParameter( configFunct.name, value ) 
#                configFunct.init( self )
                
                
                
#            function = getFunction( configFunct.name, functionList )
    def persistParameters( self ):
       for configFunct in self.configurableFunctions.values():
            value = self.getCachedParameter( configFunct.name, self.activeLayer ) 
            if value:
                self.persistParameter( configFunct.name, value )
                configFunct.init( self )    


    def persistLayerDependentParameters( self ):
       if self.newLayerConfiguration:
           for configFunct in self.configurableFunctions.values():
                if configFunct.isLayerDependent: 
                    value = self.getCachedParameter( configFunct.name ) 
                    if value: self.persistParameter( configFunct.name, value ) 
           self.newLayerConfiguration = False    
                
    def processParameterChange( self, parameter_name, new_parameter_value ):
        if parameter_name == 'timestep':
#            printTime( 'ProcessParameterChange[ %s ]' % self.__class__.__name__ )
            self.dvUpdate()
            
        self.parmUpdating[ parameter_name ] = False 
#            self.updateFunction( parameter_name, new_parameter_value )
#            if self.ndims == 3: self.render()
#        if parameter_name == 'layer':
#            if self.pipelineBuilt:
#                print " &&&& Process Layer change: %s " % new_parameter_value                
#                executeWorkflow()
#                self.compute()               
        
#        print "%s.processParameterChange" % ( self.__class__.__name__ )                  
                    
    def parameterUpdating( self, parmName ):
        parm_update = self.parmUpdating [parmName] 
#        print "%s- check parameter updating: %s " % ( self.__class__.__name__, str(parm_update) )
        return parm_update
   
    def updateLevelingEvent( self, caller, event ):
        x, y = caller.GetEventPosition()
        wsize = caller.GetRenderWindow().GetSize()
        self.updateLeveling( x, y, wsize )
                
    def updateLeveling( self, x, y, wsize, **args ):
        if self.configuring:
            configFunct = self.configurableFunctions[ self.InteractionState ]
            if configFunct.type == 'leveling':
                configData = configFunct.update( self.InteractionState, x, y, wsize )
                if configData <> None:
#                    self.wmod = args.get( 'wmod', self.getWorkflowModule( False )  )  
                    if self.wmod: self.wmod.setResult( configFunct.name, configData )
                    self.setParameter( configFunct.name, configData ) 
                    textDisplay = configFunct.getTextDisplay()
                    if textDisplay <> None:  self.updateTextDisplay( textDisplay )
                                     
    def getInteractionState( self, key ):
        for configFunct in self.configurableFunctions.values():
            if ( configFunct.key == key ): return configFunct.name
        return None    
    
#    def finalizeConfigurations( self ):
#        parameter_changes = []
#        wmod = self.getWorkflowModule() 
#        for parameter_name in self.configurableFunctions.keys():
#            outputModule = wmod.get_output( parameter_name )
#            output = outputModule.getOutput()
#            self.persistParameter( parameter_name, output )    

    def finalizeLevelingEvent( self, caller, event ):
        return self.finalizeLeveling()  
                                    
    def finalizeLeveling( self ):
        if self.ndims == 3: self.textActor.VisibilityOff()
        isLeveling = self.isLeveling()
        if isLeveling: 
            self.finalizeConfigurationObserver( self.InteractionState )            
            if self.ndims == 3: self.iren.SetInteractorStyle( self.navigationInteractorStyle )
            self.configuring = False
            self.InteractionState = None
        return isLeveling
     
    def isLeveling( self ):
        if self.InteractionState <> None: 
            configFunct = self.configurableFunctions[ self.InteractionState ]
            if configFunct.type == 'leveling':
                return True
        return False
    
    def updateFunction(self, parameter_name, output ):
        import api 
        param_values_str = [ str(x) for x in output ] if isList(output) else str( output )     
        controller = api.get_current_controller()
        module = controller.current_pipeline.modules[ self.moduleID ]
        try:
            controller.update_function( module, parameter_name, param_values_str, -1L, []  )
        except IndexError, err:
            print "Error updating parameter %s on module %s: %s" % ( parameter_name, self.__class__.__name__, str(err) )
            pass 
        return controller
    
    def getParameterId( self, parmName = None ):
        parmIdList = []
        if self.datasetId: parmIdList.append( self.datasetId )
        if self.activeLayer: parmIdList.append( self.activeLayer )
        if parmName: parmIdList.append( parmName )
        if parmIdList: return '.'.join( parmIdList )
        return 'all' 
    
    def tagCurrentVersion( self, tag ):
        import api
        ctrl = api.get_current_controller()  
        versionList = self.taggedVersionMap.setdefault( tag, [] )
        if (not versionList) or (versionList[-1] < ctrl.current_version):
            versionList.append( ctrl.current_version )
        return ctrl.current_version

    def getTaggedVersionList( self, tag ):
        return self.taggedVersionMap.get( tag, None )
    
    def persistVersionMap( self ): 
        serializedVersionMap = encodeToString( self.taggedVersionMap ) 
        self.addAnnotation( 'taggedVersionMap', serializedVersionMap )
        
    def getAnnotation( self, key, default_value = None ):
        controller, module = self.getRegisteredModule()
        if module.has_annotation_with_key(key): return module.get_annotation_by_key(key).value
        return default_value

    def initVersionMap( self ): 
        if self.moduleID > 0:
            serializedVersionMap = self.getAnnotation('taggedVersionMap')
            if serializedVersionMap: self.taggedVersionMap = decodeFromString( serializedVersionMap.strip() ) 
                
    def getTaggedVersion( self, tag ):
        versionList = self.taggedVersionMap.get( tag, None )
        return versionList[-1] if versionList else -1                     

    def persistParameter( self, parameter_name, output, processChange = False, **args ):
        if output <> None: 
            import api
            ctrl = api.get_current_controller()
            param_values_str = [ str(x) for x in output ] if isList(output) else str( output )  
            v0 = ctrl.current_version
            api.change_parameter( self.moduleID, parameter_name, param_values_str )
            v1 = ctrl.current_version
            tag = self.getParameterId()             
            taggedVersion = self.tagCurrentVersion( tag )
            new_parameter_id = args.get( 'parameter_id', tag )
            self.setParameter( parameter_name, output, new_parameter_id )
            if processChange: self.processParameterChange( parameter_name, output )
            print " PM: Persist Parameter %s -> %s, tag = %s, taggedVersion=%d, new_id = %s, version => ( %d -> %d ), module = %s" % ( parameter_name, str(output), tag, taggedVersion, new_parameter_id, v0, v1, self.__class__.__name__ )
                          
    def finalizeParameter(self, parameter_name, *args ):
        try:
            output = self.getParameter( parameter_name )
            assert (output <> None), "Attempt to finalize parameter that has not been cached." 
            self.persistParameter( parameter_name, output )  
        except Exception, err:
            print "Error changing parameter for %s module: %s", ( self.__class__.__name__, str(err) )
           
    def finalizeConfigurationObserver( self, parameter_name, *args ):
        self.finalizeParameter( parameter_name, *args )    
        for parameter_name in self.getModuleParameters(): self.finalizeParameter( parameter_name, *args )           

    def setActivation( self, name, value ):
        bval = bool(value)  
        self.activation[ name ] = bval
        print "Set activation for %s[%s] to %s "% ( self.getName(), name, bval ) 
        
    def getActivation( self, name ): 
        return self.activation.get( name, True )

    def getRegisteredModule(self):
        import api
        controller = api.get_current_controller() 
        mid = self.moduleID
        module = controller.current_pipeline.modules[ mid ]
        return controller, module
    
    def getWorkflowModule(self, forceGet=True ):
        try:
            return getPersistentModule( self.moduleID, forceGet )
        except Exception, err:
            print "Exception in getWorkflowModule[%d]: %s" % ( self.moduleID, str(err) )
        
    def updateModule(self):
        pass
    
    def getOutputModules( self, port ):
        import api
        controller = api.get_current_controller() 
        mid = self.moduleID
        modules = controller.current_pipeline.get_outputPort_modules( mid, port )
        return modules
 
    def getRegisteredDescriptor( self ):       
        registry = get_module_registry()
        controller, module = self.getRegisteredModule()
        descriptor = registry.get_descriptor_by_name( module.package, module.name, module.namespace )
        return controller, module, descriptor        
        
    def getModuleParameters( self ):
        return []

    def setTimestep( self, data ):
        self.iTimestep = getItem( data )
        self.onNewTimestep()
            
    def getTimestep( self ):
        return self.iTimestep

    def onNewTimestep(self):
        pass                                              
      
class PersistentVisualizationModule( PersistentModule ):

    NoModifier = 0
    ShiftModifier = 1
    CtrlModifier = 2
    AltModifier = 3
    
    LEFT_BUTTON = 0
    RIGHT_BUTTON = 1
    
    
    moduleDocumentationDialog = None 

    def __init__( self, mid, **args ):
        self.currentButton = None
        PersistentModule.__init__(self, mid, **args  )
        self.modifier = self.NoModifier
        self._max_scalar_value = None
        self.colormapManager = None
        self.colormapName = 'Spectral'
        self.invertColormap = 1
        self.renderer = None
        self.iren = None 
        self.gui = None
        self.pipelineBuilt = False
        self.activation = {}
        self.navigationInteractorStyle = None
        self.textActor = None
                                
    def TestObserver( self, caller=None, event = None ):
        pass 
    
#        print "%s.processParameterChange" % ( self.__class__.__name__ )                  

#    def setLayer( self, layer ):
#        PersistentModule.setLayer( self, layer )
#        if self.pipelineBuilt: executeWorkflow()

    def set3DOutput( self, **args ):  
        portName = args.get( 'name', 'volume' )
#        wmod = args.get( 'wmod', self.getWorkflowModule()  )  
        outputModule = AlgorithmOutputModule3D( self.renderer, **args )
        output =  outputModule.getOutput() 
        oid = id( outputModule )
        if output <> None:
            fd = output.GetFieldData() 
            fd.PassData( self.fieldData ) 
        if self.wmod == None:
            print>>sys.stderr, "Missing wmod in set3DOutput for class %s" % ( self.__class__.__name__ )
        else:
            self.wmod.setResult( portName, outputModule )
            print "set3DOutput for class %s" % ( self.__class__.__name__ ) 

    def updateTextDisplay( self, text = None ):
        if text <> None: self.textBuff = text
        if (self.ndims == 3) and self.textActor:
            self.textActor.SetInput( self.textBuff )
            self.textActor.Modified()
            self.textActor.VisibilityOn()
            
    def UpdateCamera(self):
        pass
            
    def isBuilt(self):
        return self.pipelineBuilt

    def execute(self):
        initConfig = False
        if not self.isBuilt():
            if self.ndims == 3: self.initializeRendering()
            
            self.buildPipeline()
            
            if self.ndims == 3: self.finalizeRendering() 
            self.pipelineBuilt = True
            initConfig = True
            
        if not initConfig: self.applyConfiguration()   
                           
        self.updateModule() 
        
        if initConfig:  self.initializeConfiguration()  
        else:           self.applyConfiguration()
              
        
    def buildPipeline(self): 
        pass 
    
    def getColormapSpec(self):
        return '%s,%d' % ( self.colormapName, self.invertColormap )
    
    def buildColormap(self):
        if self.colormapManager <> None:
            self.colormapManager.reverse_lut = self.invertColormap
            self.colormapManager.load_lut( self.colormapName )
#            print " >>> LoadColormap:  %s " % self.colormapName
            return True
        else:
            print " >>> LoadColormap:  Colormap Manager not defined"
            return False
        
    def setColormap( self, data ):
        self.colormapName = str(data[0])
        self.invertColormap = data[1]
        self.addMetadata( { 'colormap' : self.getColormapSpec() } )
#        print ' ~~~~~~~ SET COLORMAP:  --%s--  ' % self.colormapName
        if self.buildColormap(): 
            self.rebuildColorTransferFunction()
            self.render() 
            
    def rebuildColorTransferFunction( self ):
        pass 
            
    def getColormap(self):
        reverse = 0 if ( self.colormapManager <> None ) and self.colormapManager.reverse_lut else 1
        return [ self.colormapName, reverse ]

    def render( self ):   
        rw = self.renderer.GetRenderWindow()
        if rw <> None: rw.Render()
       
    def setMaxScalarValue(self, iDType ):  
        if iDType   == vtk.VTK_UNSIGNED_CHAR:   self._max_scalar_value = 255
        elif iDType == vtk.VTK_UNSIGNED_SHORT:  self._max_scalar_value = 256*256-1
        elif iDType == vtk.VTK_SHORT:           self._max_scalar_value = 256*128-1
        else:                                   self._max_scalar_value = self.rangeBounds[1]  
                
    def initializeRendering(self):
        inputModule = self.getPrimaryInput()
        renderer_import = inputModule.getRenderer() if  inputModule <> None else None 
        self.renderer = vtk.vtkRenderer() if renderer_import == None else renderer_import
        self.renderer.AddObserver( 'ModifiedEvent', self.activateEvent )
        self.createTextActor()
        if self.createColormap: 
            self.createColorBarActor()
        
    def getProp( self, ptype ):
      props = self.renderer.GetViewProps()
      nitems = props.GetNumberOfItems()
      for iP in range(nitems):
          prop = props.GetItemAsObject(iP)
          if prop.IsA( ptype ): return prop
      return None
  
    def createColorBarActor( self ):
        self.colorBarActor = self.getProp( 'vtkScalarBarActor' )
        if self.colorBarActor == None:
            self.lut = vtk.vtkLookupTable()
            self.colorBarActor = vtk.vtkScalarBarActor()
            self.colorBarActor.SetLookupTable( self.lut )
            self.colorBarActor.SetVisibility(0)
            self.renderer.AddActor( self.colorBarActor )
        else:
            self.lut = self.colorBarActor.GetLookupTable()
        self.colormapManager = ColorMapManager( self.lut ) 

    def createTextActor( self ):
      self.textBuff = "NA                           "
      self.textActor = self.getProp( 'vtkTextActor' )
      if self.textActor == None:
          self.textActor = vtk.vtkTextActor()  
          self.textActor.SetInput( self.textBuff )
          self.textActor.SetTextScaleModeToNone()
        
          textprop = self.textActor.GetTextProperty()
          textprop.SetColor(1,1,1)
          textprop.SetFontFamilyToArial()
          textprop.SetFontSize(18)
          textprop.BoldOff()
          textprop.ItalicOff()
          textprop.ShadowOff()
          textprop.SetJustificationToLeft()
          textprop.SetVerticalJustificationToBottom()
        
          coord = self.textActor.GetPositionCoordinate()
          coord.SetCoordinateSystemToNormalizedViewport()
          coord.SetValue( .4, .01 )
        
          self.textActor.VisibilityOff()
          self.renderer.AddViewProp( self.textActor )


    def finalizeRendering(self):
        pass

    def refreshCells(self):
        spreadsheetWindow = spreadsheetController.findSpreadsheetWindow()
        spreadsheetWindow.repaint()
      
    def activateEvent( self, caller, event ):
        self.renwin = self.renderer.GetRenderWindow( )
        if self.renwin <> None:
            iren = self.renwin.GetInteractor() 
            if ( iren <> None ):
                if ( iren <> self.iren ):
                    if self.iren == None: 
                        self.renwin.AddObserver("AbortCheckEvent", CheckAbort)
                        self.configurationInteractorStyle = vtk.vtkInteractorStyleUser()
                    self.iren = iren
                    self.activateWidgets( self.iren )                                  
                    self.iren.AddObserver( 'CharEvent', self.setInteractionState )                   
                    self.iren.AddObserver( 'MouseMoveEvent', self.updateLevelingEvent )
                    self.iren.AddObserver( 'LeftButtonReleaseEvent', self.finalizeLevelingEvent )
#                    self.iren.AddObserver( 'AnyEvent', self.onAnyEvent )        
                    self.iren.AddObserver( 'CharEvent', self.onKeyPress )
                    self.iren.AddObserver( 'KeyReleaseEvent', self.onKeyRelease )
                    self.iren.AddObserver( 'LeftButtonPressEvent', self.onLeftButtonPress )
                    self.iren.AddObserver( 'ModifiedEvent', self.onModified )
                    self.iren.AddObserver( 'RenderEvent', self.onRender )                   
                    self.iren.AddObserver( 'LeftButtonReleaseEvent', self.onLeftButtonRelease )
                    self.iren.AddObserver( 'RightButtonReleaseEvent', self.onRightButtonRelease )
                    self.iren.AddObserver( 'LeftButtonPressEvent', self.startLevelingEvent )
                    self.iren.AddObserver( 'RightButtonPressEvent', self.onRightButtonPress )
                    for configurableFunction in self.configurableFunctions.values():
                        configurableFunction.activateWidget( iren )
                if ( self.iren.GetInteractorStyle() <> self.navigationInteractorStyle ):               
                    self.navigationInteractorStyle = self.iren.GetInteractorStyle()  
                    
    def setInteractionState(self, caller, event):
        key = caller.GetKeyCode() 
        keysym = caller.GetKeySym()
        ctrl = caller.GetControlKey()
        self.processKeyEvent( key, caller, event )
#        if key == self.current_key:
#            t = time.time()
#            if( ( t - self.event_time ) < 0.01 ): return
#        self.event_time = time.time()
#        self.current_key = key

    def processKeyEvent( self, key, caller=None, event=None ):
#        print "Interaction event, key = %s" % ( key )
        if key == 'h': 
            if  PersistentVisualizationModule.moduleDocumentationDialog == None:
                modDoc = ModuleDocumentationDialog()
                modDoc.addDocument( 'configuration', PersistentModule.__doc__ )
                PersistentVisualizationModule.moduleDocumentationDialog = modDoc
            if self.documentation == None:
                self.generateDocumentation()           
                PersistentVisualizationModule.moduleDocumentationDialog.addDocument( 'modules', self.documentation )
                PersistentVisualizationModule.moduleDocumentationDialog.addCloseObserver( self.clearDocumenation )
                PersistentVisualizationModule.moduleDocumentationDialog.show()
        elif ( self.createColormap and ( key == 'l' ) ): 
            if  self.colorBarActor.GetVisibility():  
                  self.colorBarActor.VisibilityOff()  
            else: self.colorBarActor.VisibilityOn() 
            self.render() 
        elif (  key == 'z'  ): 
            if self.InteractionState <> None: 
                configFunct = self.configurableFunctions[ self.InteractionState ]
                configFunct.reset( )
        elif (  key == 'r'  ): 
            ModuleStoreDatabase.refreshParameters()
        else:
            state =  self.getInteractionState( key )
#            print " %s Set Interaction State: %s ( currently %s) " % ( str(self.__class__), state, self.InteractionState )
            if state <> None:
                if self.InteractionState <> None: 
                    configFunct = self.configurableFunctions[ self.InteractionState ]
                    configFunct.close()
                if self.InteractionState == state:
                    self.endInteraction()             
                else:
                    self.InteractionState = state
                    configFunct = self.configurableFunctions[ self.InteractionState ]
                    configFunct.open( self.InteractionState )
                    
    def endInteraction( self ):
        self.InteractionState = None 
        self.configuring = False 
        if self.ndims == 3:
            self.textActor.VisibilityOff()              
#            self.render()
        
    def onLeftButtonRelease( self, caller, event ):
        self.currentButton = None 
    
    def onRightButtonRelease( self, caller, event ):
        self.currentButton = None 
               
    def onKeyRelease( self, caller, event ):
        pass

    def setModifiers(self, caller, event):
        key = caller.GetKeyCode() 
        keysym = caller.GetKeySym()
        if ( ord(key) == 0 ):
            if  ( keysym.lower().find('alt') == 0 ): 
                self.modifier = self.AltModifier
            elif  ( keysym.lower().find('shift') == 0 ): 
                self.modifier = self.ShiftModifier
            else: 
                self.modifier = self.CtrlModifier
    
    def unsetModifiers( self, caller, event ):
        self.modifier = self.NoModifier
 

            
#    def checkFunctionName( self, module, parameter_name ):
#            old_id = -1
#            function = None
#            for old_function in module.functions:
#                if old_function.name == parameter_name:
#                    old_id = old_function.real_id
#            if old_id >= 0:
#                function = module.function_idx[old_id]
#            if function <> None:
#                print>>sys.stderr, "  \n  !! Warning: Configurable Function Name Clash in %s Module: %s !! \n " % ( str(self.__class__), parameter_name )

        
#        if provType == self.ColorMapScaling: 
#            output = self.get_output( 'colorScale' )
#            controller.update_function( module, 'colorScale', output )
#        if provType == self.TransferFunctionScaling: 
#            output = self.get_output( 'functionScale' )
#            controller.update_function( module, 'functionScale', output )
#        if provType == self.OpacityScaling: 
#            output = self.get_output( 'opacityScale' )
#            controller.update_function( module, 'opacityScale', output )
                
    def activateWidgets(self, iren):
        return 0
    
    def onLeftButtonPress( self, caller, event ):
        self.currentButton = self.LEFT_BUTTON
        self.UpdateCamera()    
        return 0

    def onRightButtonPress( self, caller, event ):
        self.currentButton = self.RIGHT_BUTTON
        self.UpdateCamera()
        return 0

    def onModified( self, caller, event ):
        return 0

    def onRender( self, caller, event ):
        return 0
             
    def onKeyPress( self, caller, event ):
        return 0
    
    def onAnyEvent(self, caller, event ):
        print " >> %s Event: %s " % ( str(caller.__class__), event )
        return 0
    
    def clearDocumenation(self):
        PersistentVisualizationModule.moduleDocumentationDialog.clearTopic( 'modules' )
        self.documentation = None


        
