'''
Created on Dec 2, 2010

@author: tpmaxwel
'''
import vtk, math
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import core.modules.module_registry
from core.modules.vistrails_module import Module, ModuleError
from core.modules.module_registry import get_module_registry
from core.interpreter.default import get_default_interpreter as getDefaultInterpreter
from core.modules.basic_modules import Integer, Float, String, File, Variant, Color
from packages.vtk.base_module import vtkBaseModule
from ColorMapManager import ColorMapManager 
from WorkflowModule import WorkflowModule 
from PersistentModule import * 
from vtUtilities import *
        
class PM_VolumeSlicer(PersistentVisualizationModule):
    """
        This module generates dragable slices through 3D volumetric (<i>vtkImagedata</i>) data.  Three slice planes are provided 
        ( perpendicular to the three axes ) which are dragable along the corresponding axis (by default) with a right mouse click.
        More general plane orientations are possible by enabling margins (see command keys).  Colormap scaling is controlled using 
        the <b>colorRangeScale</b> leveling function.  Left clicking on a slice plane displays the coordinates and data value at the picked point.
        <h3>  Command Keys </h3> 
        <table border="2" bordercolor="#336699" cellpadding="2" cellspacing="2" width="100%">  
        <tr> <th> Command Key </th> <th> Function </th> </tr> 
        <tr> <td> l </td> <td> Toggle show colorbar. </td>
        <tr> <td> x </td> <td> Snap the 'x' slice back to its default (perpendicular to 'x' axis) position. </td>
        <tr> <td> y </td> <td> Snap the 'y' slice back to its default (perpendicular to 'y' axis) position. </td>
        <tr> <td> z </td> <td> Snap the 'z' slice back to its default (perpendicular to 'z' axis) position. </td>
        <tr> <td> m </td> <td> Enable margins. Right-clicking and dragging the slice margins enables rotations and translations of the planes </td>
        </table>
    """
    def __init__( self, mid, **args ):
        self.imageRange = None
        PersistentVisualizationModule.__init__( self, mid, **args )
        self.addConfigurableLevelingFunction( 'colorScale', 'C', setLevel=self.scaleColormap, getLevel=self.getDataRangeBounds, layerDependent=True )
        self.addConfigurableLevelingFunction( 'opacity', 'O',    setLevel=self.setOpacity,    getLevel=self.getOpacity, isDataValue=False, layerDependent=True )
        self.sliceOutputShape = args.get( 'slice_shape', [ 100, 50 ] )
        self.opacity = 1.0
        self.updatingPlacement = False
        self.planeWidgetX = None
        self.planeWidgetY = None
        self.planeWidgetZ = None
        self.imageRescale = None
        print " Volume Slicer init, id = %s " % str( id(self) )

    def getRangeBounds(self): 
        return self.rangeBounds 

    def getDataRangeBounds(self): 
        range = self.getDataValues( self.rangeBounds[0:2] ) 
        range.append( self.rangeBounds[2] )
        return range
    
    def getOpacity(self):
        return [ self.opacity, self.opacity ]
    
    def setOpacity(self, range ):
        rop = math.fabs( range[0] )
        iop = int( rop )
        self.opacity = (rop-iop) if ( (iop%2) == 0 ) else 1.0 - (rop-iop)
        printArgs( " Leveling: ", opacity=self.opacity ) 
        self.updateOpacity() 

    def updateOpacity(self):
        self.lut.SetAlpha( self.opacity ) 
#        self.UpdateWidgetPlacement()
        
#    def UpdateWidgetPlacement(self):
#        self.updatingPlacement = True
#        self.planeWidgetX.UpdatePlacement() 
#        self.planeWidgetX.PlaceWidget()
#        self.planeWidgetY.UpdatePlacement() 
#        self.planeWidgetY.PlaceWidget()
#        self.planeWidgetZ.UpdatePlacement() 
#        self.planeWidgetZ.PlaceWidget()
#        self.updatingPlacement = False
                                                  
    def buildPipeline(self):
        """ execute() -> None
        Dispatch the vtkRenderer to the actual rendering widget
        """           
        # The 3 image plane widgets are used to probe the dataset. 
        wmod = self.getWorkflowModule()      
        print " Volume Slicer buildPipeline, id = %s " % str( id(self) )
        self.sliceOutput = vtk.vtkImageData()  
        xMin, xMax, yMin, yMax, zMin, zMax = self.input.GetWholeExtent()       
        self.slicePosition = [ (xMax-xMin)/2, (yMax-yMin)/2, (zMax-zMin)/2  ]       
        dataType = self.input.GetScalarTypeAsString()
        bounds = list(self.input.GetBounds()) 
        origin = self.input.GetOrigin()
        if (dataType <> 'float') and (dataType <> 'double'):
             self.setMaxScalarValue( self.input.GetScalarType() )
        print "Data Type = %s, range = (%f,%f), extent = %s, origin = %s, bounds=%s" % ( dataType, self.rangeBounds[0], self.rangeBounds[1], str(self.input.GetWholeExtent()), str(origin), str(bounds) )
      
        # The shared picker enables us to use 3 planes at one time
        # and gets the picking order right
        picker = vtk.vtkCellPicker()
        picker.SetTolerance(0.005) 
         
        self.planeWidgetX = vtk.vtkImagePlaneWidget()
        self.planeWidgetX.DisplayTextOn()
        self.planeWidgetX.SetInput( self.input )
        self.planeWidgetX.SetPlaneOrientationToXAxes()
        self.planeWidgetX.SetSliceIndex( self.slicePosition[0] )
        self.planeWidgetX.SetPicker(picker)
        self.planeWidgetX.SetRightButtonAction( VTK_SLICE_MOTION_ACTION )
        self.planeWidgetX.SetDisplayText( 1 )
        prop1 = self.planeWidgetX.GetPlaneProperty()
        prop1.SetColor(1, 0, 0)
        self.planeWidgetX.SetUserControlledLookupTable(1)
        self.planeWidgetX.SetLookupTable( self.lut )
        self.planeWidgetX.AddObserver( 'EndInteractionEvent', self.SliceObserver )
        self.planeWidgetX.AddObserver( 'InteractionEvent', callbackWrapper( self.PickObserver, 0 ) )
        self.planeWidgetX.AddObserver( 'StartInteractionEvent', callbackWrapper( self.PickObserver, 0 ) )
        self.planeWidgetX.PlaceWidget(  bounds[0], bounds[1], bounds[2], bounds[3], bounds[4], bounds[5]   )
#        if bounds[0] < 0.0: self.planeWidgetX.GetProp3D().AddPosition ( 360.0, 0.0, 0.0 )
#        self.planeWidgetX.SetOrigin( self.input.GetOrigin() )
        self.planeWidgetX.AddObserver( 'AnyEvent', self.TestObserver )
                
        self.planeWidgetY = vtk.vtkImagePlaneWidget()
        self.planeWidgetY.DisplayTextOn()
        self.planeWidgetY.SetInput( self.input )
        self.planeWidgetY.SetPlaneOrientationToYAxes()
        self.planeWidgetY.SetUserControlledLookupTable(1)
        self.planeWidgetY.SetSliceIndex( self.slicePosition[1] )
        self.planeWidgetY.SetRightButtonAction( VTK_SLICE_MOTION_ACTION )
        self.planeWidgetY.SetPicker(picker)
        self.planeWidgetY.AddObserver( 'EndInteractionEvent', self.SliceObserver )
        self.planeWidgetY.AddObserver( 'InteractionEvent', callbackWrapper( self.PickObserver, 1 ) )
        self.planeWidgetY.AddObserver( 'StartInteractionEvent', callbackWrapper( self.PickObserver, 1 ) )
        self.planeWidgetY.AddObserver( 'AnyEvent', self.TestObserver )
        self.planeWidgetY.SetDisplayText( 1 )
        prop2 = self.planeWidgetY.GetPlaneProperty()
        prop2.SetColor(1, 1, 0)
#        if bounds[0] < 0.0: self.planeWidgetY.GetProp3D().AddPosition ( 360.0, 0.0, 0.0 )
        self.planeWidgetX.PlaceWidget(  bounds[0], bounds[1], bounds[2], bounds[3], bounds[4], bounds[5]   )        
        self.planeWidgetY.SetUserControlledLookupTable(1)
        self.planeWidgetY.SetLookupTable( self.lut )
        
        self.planeWidgetZ = vtk.vtkImagePlaneWidget()
        self.planeWidgetZ.DisplayTextOn()
        self.planeWidgetZ.SetInput( self.input )
        self.planeWidgetZ.SetPlaneOrientationToZAxes()
        self.planeWidgetZ.SetSliceIndex( self.slicePosition[2] )
        self.planeWidgetZ.SetRightButtonAction( VTK_SLICE_MOTION_ACTION )
        self.planeWidgetZ.SetPicker(picker)
        self.planeWidgetZ.AddObserver( 'EndInteractionEvent', self.SliceObserver )
        self.planeWidgetZ.AddObserver( 'InteractionEvent', callbackWrapper( self.PickObserver, 2 ) )
        self.planeWidgetZ.AddObserver( 'StartInteractionEvent', callbackWrapper( self.PickObserver, 2 ) )
        self.planeWidgetZ.AddObserver( 'AnyEvent', self.TestObserver )
        self.planeWidgetZ.SetDisplayText( 1 )
                
        prop3 = self.planeWidgetZ.GetPlaneProperty()
        prop3.SetColor(0, 0, 1)
#        if bounds[0] < 0.0: self.planeWidgetZ.GetProp3D().AddPosition ( 360.0, 0.0, 0.0 )
        self.planeWidgetX.PlaceWidget(  bounds[0], bounds[1], bounds[2], bounds[3], bounds[4], bounds[5]   )

        self.planeWidgetZ.SetUserControlledLookupTable(1)
        self.planeWidgetZ.SetLookupTable( self.lut )
        self.setMarginSize( 0.0 )  
        self.renderer.SetBackground(0.1, 0.1, 0.2)  
        self.lut.SetAlpha( self.opacity ) 
        self.imageRescale = vtk.vtkImageReslice() 
        self.imageRescale.SetOutputDimensionality(2) 
        self.imageRescale.SetInterpolationModeToLinear() 
        self.imageRescale.SetResliceAxesDirectionCosines( [1, 0, 0], [0, -1, 0], [0, 0, 1] )

        self.set2DOutput( port=self.imageRescale.GetOutputPort(), name='slice', wmod = wmod ) 
        self.set3DOutput(wmod = wmod) 
         
#    def updateModule1(self):
#        self.transferInputLayer( self.sliceInput ) 
#        self.SliceObserver( self.planeWidgetZ ) 

    def updateModule(self):
        print " Volume Slicer: updateModule, cachable: %s " % str( self.is_cacheable() )
        print " ******** Input extent: %s, origin: %s, spacing: %s " % ( self.input.GetExtent(), self.input.GetOrigin(), self.input.GetSpacing() )

        self.planeWidgetX.SetInput( self.input ) 
        self.planeWidgetX.SetSliceIndex( self.slicePosition[0] )
        
        self.planeWidgetY.SetInput( self.input ) 
        self.planeWidgetY.SetSliceIndex( self.slicePosition[1] )
        
        self.planeWidgetZ.SetInput( self.input ) 
        self.planeWidgetZ.SetSliceIndex( self.slicePosition[2] )

#        na1 = self.input.GetPointData().GetNumberOfArrays()
#        self.setActiveScalars()
#        na2 = self.input.GetPointData().GetNumberOfArrays()
        self.SliceObserver( self.planeWidgetZ )
        
#    def InputModifiedObserver( self, caller, event = None ):
#        if not self.updatingPlacement:
#            self.UpdateWidgetPlacement()
           
    def TestObserver( self, caller=None, event = None ):
        pass
#        print " TestObserver: event = %s, " % ( event )

    def PickObserver( self, iAxis, caller, event = None ):
        image_value = caller.GetCurrentImageValue() 
        spos = caller.GetSlicePosition()
        dataValue = self.getDataValue( image_value )
#        textDisplay = None
#        if (self.currentButton == self.LEFT_BUTTON):  textDisplay = " value: %s." % str( spos )
#        if (self.currentButton == self.RIGHT_BUTTON): textDisplay = " value: %.5G %s." % ( dataValue, units )
        textDisplay = " pos: %.2f, value: %.3G %s." % ( spos, dataValue, self.units )
        self.slicePosition[iAxis] = caller.GetSliceIndex() 
#        print " Event %s: caller: %s, interaction: %d " % ( str(event), dir( caller ), caller.GetInteraction() )
#        print "textDisplay: '%s' " % textDisplay
        if textDisplay: self.updateTextDisplay( textDisplay )
#        print " -- PickObserver: axis %d, dataValue = %f " % ( iAxis, dataValue )
                      
    def SliceObserver( self, caller, event = None ):
        import api
        iOrientation = caller.GetPlaneOrientation()
        resliceOutput = caller.GetResliceOutput()
        resliceOutput.Update()
        self.imageRescale.SetInput( resliceOutput )
        output_slice_extent = self.getAdjustedSliceExtent( iOrientation )
        self.imageRescale.SetOutputExtent( output_slice_extent )
        output_slice_spacing = self.getAdjustedSliceSpacing( iOrientation, resliceOutput )
        self.imageRescale.SetOutputSpacing( output_slice_spacing )
        self.updateSliceOutput()
        self.endInteraction()
        
    def updateSliceOutput(self):
        sliceOutput = self.imageRescale.GetOutput()
        sliceOutput.Update()
        self.set2DOutput( name='slice', output=sliceOutput )
        sliceOutput.InvokeEvent("RenderEvent")
        self.refreshCells()
#        imageWriter = vtk.vtkJPEGWriter()
#        imageWriter.SetFileName ("~/sliceImage.jpg")
#        imageWriter.SetInput( sliceOutput )
#        imageWriter.Write()    
        print " Slice Output: extent: %s, spacing: %s " % ( str( sliceOutput.GetExtent() ), str( sliceOutput.GetSpacing() ) )
        pass

    def getColormapSpec(self): 
        value_range = self.lut.GetTableRange() 
#        print " -- getColormapSpec: ( %f %f ) " % ( value_range[0], value_range[1] )
        return '%s,%d,%f,%f' % ( self.colormapName, self.invertColormap, value_range[0], value_range[1] )
       
    def getAdjustedSliceExtent( self, iOrientation ):
        return [ 0, self.sliceOutputShape[0]-1,  0, self.sliceOutputShape[1]-1, 0, 0 ]          

    def getAdjustedSliceSpacing( self, iOrientation, outputData ):
        padded_extent = outputData.GetWholeExtent()
        padded_shape = [ padded_extent[1]-padded_extent[0]+1, padded_extent[3]-padded_extent[2]+1, 1 ]
        padded_spacing = outputData.GetSpacing()
        scale_factor = [ padded_shape[0]/float(self.sliceOutputShape[0]), padded_shape[1]/float(self.sliceOutputShape[1]) ]
        return [ padded_spacing[0]*scale_factor[0], padded_spacing[1]*scale_factor[1], 1.0 ]
                
    def activateWidgets( self, iren ):
        self.planeWidgetX.SetInteractor( iren )
        self.planeWidgetX.On()
        self.planeWidgetY.SetInteractor( iren )
        self.planeWidgetY.On() 
        self.planeWidgetZ.SetInteractor( iren )     
        self.planeWidgetZ.On() 
        print "Initial Camera Position = %s\n Origins: " % str( self.renderer.GetActiveCamera().GetPosition() )
        for widget in [ self.planeWidgetX, self.planeWidgetY, self.planeWidgetZ ]: 
            print " slice-%d: %s %s %s %s " % ( widget.GetPlaneOrientation(), str( widget.GetOrigin() ), str( widget.GetPoint1 () ), str( widget.GetPoint2 () ), str( widget.GetCenter() ) )
       
    def initColorScale( self, caller, event ): 
        x, y = caller.GetEventPosition()
        self.ColorLeveler.startWindowLevel( x, y )

    def scaleColormap( self, ctf_data ):
        self.imageRange = self.getImageValues( ctf_data[0:2] ) 
        self.lut.SetTableRange( self.imageRange[0], self.imageRange[1] ) 
        self.addMetadata( { 'colormap' : self.getColormapSpec() } )
        print " Volume Slicer: Scale Colormap: [ %.2f, %.2f ] " % ( self.imageRange[0], self.imageRange[1] )
        
    def finalizeLeveling( self ):
        isLeveling =  PersistentVisualizationModule.finalizeLeveling( self )
        if isLeveling:
            self.addMetadata( { 'colormap' : self.getColormapSpec() } ) 
            self.updateSliceOutput()

    def setColormap( self, data ):
        PersistentVisualizationModule.setColormap( self, data )
        self.updateSliceOutput()

    def updateColorScale( self, caller, event ):
        x, y = caller.GetEventPosition()
        wsize = self.renderer.GetSize()
        range = self.ColorLeveler.windowLevel( x, y, wsize )
        return range
              
    def onKeyPress( self, caller, event ):
        key = caller.GetKeyCode() 
        keysym = caller.GetKeySym()
        alt = ( keysym.lower().find('alt') == 0 )
        ctrl = caller.GetControlKey() 
        shift = caller.GetShiftKey() 
        print " -- Key Press: %c ( %d: %s ), ctrl: %s, shift: %s, alt: %s, event = %s " % ( key, ord(key), str(keysym), bool(ctrl), bool(shift), bool(alt), str( event ) )
        if ( key == 'm' ):  self.setMarginSize( 0.05 ) 
        elif ( key == 'x' ): 
            self.planeWidgetX.SetPlaneOrientationToXAxes() 
            self.planeWidgetX.SetSliceIndex( 0 ) #self.slicePosition[0] )
            self.render()      
        elif ( key == 'y' ):  
            self.planeWidgetY.SetPlaneOrientationToYAxes()
            self.planeWidgetY.SetSliceIndex( 0 ) #self.slicePosition[1] )
            self.render()       
        elif ( key == 'z' ):  
            self.planeWidgetZ.SetPlaneOrientationToZAxes()
            self.planeWidgetZ.SetSliceIndex( 0 ) #self.slicePosition[2] )
            self.render() 
             
              
    def onKeyRelease( self, caller, event ):
        key = caller.GetKeyCode()
        if ( key == 'm' ):  self.setMarginSize( 0.0 )  
                
    def setMarginSize(self, msize ):    
        self.planeWidgetX.SetMarginSizeX( msize ) 
        self.planeWidgetX.SetMarginSizeY( msize ) 
        self.planeWidgetY.SetMarginSizeX( msize ) 
        self.planeWidgetY.SetMarginSizeY( msize ) 
        self.planeWidgetZ.SetMarginSizeX( msize ) 
        self.planeWidgetZ.SetMarginSizeY( msize ) 

class VolumeSlicer(WorkflowModule):
    
    PersistentModuleClass = PM_VolumeSlicer
    
    def __init__( self, **args ):
        WorkflowModule.__init__(self, **args)    
              
if __name__ == '__main__':
    executeVistrail( 'VolumeSlicerDemo' )
    
    
    
#        self.spacing = self.input.GetSpacing()
#        sx, sy, sz = self.spacing       
#        origin = self.input.GetOrigin()
#        ox, oy, oz = origin
#        center = [ origin[0] + self.spacing[0] * 0.5 * (xMin + xMax), origin[1] + self.spacing[1] * 0.5 * (yMin + yMax), origin[2] + self.spacing[2] * 0.5 * (zMin + zMax)]
#        self.sliceMatrix = [ vtk.vtkMatrix4x4(), vtk.vtkMatrix4x4(), vtk.vtkMatrix4x4() ]
#        self.sliceMatrix[0].DeepCopy( (0, 1, 0, center[0],    0,  0, 1, center[1],     1, 0, 0, center[2],    0, 0, 0, 1) )
#        self.sliceMatrix[1].DeepCopy( (1, 0, 0, center[0],    0,  0, 1, center[1],     0, 1, 0, center[2],    0, 0, 0, 1) )
#        self.sliceMatrix[2].DeepCopy( (1, 0, 0, center[0],    0, -1, 0, center[1],     0, 0, 1, center[2],    0, 0, 0, 1) )
         
#        self._range = self.rangeBounds[0:2]           
