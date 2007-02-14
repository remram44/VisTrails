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
import core.modules
import core.modules.module_registry
from core.modules.vistrails_module import Module, ModuleError
from SciPy import SciPy
from Matrix import *
from MatlabReader import MatlabReader
from MatrixInfo import MatrixInfo
from MatrixConvert import MatrixConvert
from MatrixOperations import *
from DSP import *
import core.modules.basic_modules

from scipy import sparse

def initialize(*args, **keywords):
    reg = core.modules.module_registry
    basic = core.modules.basic_modules

    reg.addModule(SciPy)
    reg.addModule(Matrix)
    reg.addModule(MatrixOperation)
    reg.addModule(DSP)
    
    reg.addModule(SparseMatrix)
    reg.addInputPort(SparseMatrix, "size", (basic.Integer, 'Matrix Size'))
    reg.addOutputPort(SparseMatrix, "output", (SparseMatrix, 'Output Matrix'))

    reg.addModule(PrintMatrix)
    reg.addInputPort(PrintMatrix, "InputMatrix", (Matrix, 'Matrix'))
    reg.addOutputPort(PrintMatrix, "Output", (basic.String, 'Output String'))

    reg.addModule(MatrixConvert)
    reg.addInputPort(MatrixConvert, "InputMatrix", (Matrix, 'Matrix'))
    reg.addInputPort(MatrixConvert, "OutputType", (basic.String, 'Output Type'))
    reg.addOutputPort(MatrixConvert, "SparseOutput", (SparseMatrix, 'Output Sparse Matrix'))
#    reg.addOutputPort(MatrixConvert, "COOOutput", (COOMatrix, 'Output COO Matrix'))
#    reg.addOutputPort(MatrixConvert, "CSCOutput", (CSCMatrix, 'Output CSC Matrix'))

    reg.addModule(MatlabReader)
    reg.addInputPort(MatlabReader, "Filename", (basic.String, 'Filename'))
    reg.addOutputPort(MatlabReader, "sparseoutput", (SparseMatrix, 'Output Sparse Matrix'))

    reg.addModule(MatrixInfo)
    reg.addInputPort(MatrixInfo, "InputMatrix", (Matrix, 'Matrix'))
    reg.addOutputPort(MatrixInfo, "output", (basic.String, 'Output String'))

    reg.addModule(GetReals)
    reg.addInputPort(GetReals, "InputMatrix", (SparseMatrix, 'Input Matrix'))
    reg.addOutputPort(GetReals, "OutputMatrix", (SparseMatrix, 'Result'))

    reg.addModule(GetImaginaries)
    reg.addInputPort(GetImaginaries, "InputMatrix", (SparseMatrix, 'Input Matrix'))
    reg.addOutputPort(GetImaginaries, "OutputMatrix", (SparseMatrix, 'Result'))

    reg.addModule(Conjugate)
    reg.addInputPort(Conjugate, "InputMatrix", (SparseMatrix, 'Input Matrix'))
    reg.addOutputPort(Conjugate, "OutputMatrix", (SparseMatrix, 'Result'))

    reg.addModule(GetRow)
    reg.addInputPort(GetRow, "InputMatrix", (Matrix, 'Input Matrix'))
    reg.addInputPort(GetRow, "RowIndex", (basic.Integer, 'Row Index'))
    reg.addOutputPort(GetRow, "OutputMatrix", (SparseMatrix, 'Result'))

    reg.addModule(GetCol)
    reg.addInputPort(GetCol, "InputMatrix", (Matrix, 'Input Matrix'))
    reg.addInputPort(GetCol, "ColIndex", (basic.Integer, 'Col Index'))
    reg.addOutputPort(GetCol, "OutputMatrix", (SparseMatrix, 'Result'))

    reg.addModule(GetColumnRange)
    reg.addInputPort(GetColumnRange, "InputMatrix", (SparseMatrix, 'Input Matrix'))
    reg.addInputPort(GetColumnRange, "StartIndex", (basic.Integer, 'Start Index'))
    reg.addInputPort(GetColumnRange, "EndIndex", (basic.Integer, 'End Index'))
    reg.addOutputPort(GetColumnRange, "Output", (SparseMatrix, 'Result'))
    
    reg.addModule(ScalarMultiply)
    reg.addInputPort(ScalarMultiply, "InputMatrix", (Matrix, 'Input Matrix'))
    reg.addInputPort(ScalarMultiply, "Scalar", (basic.Float, 'Scalar'))
    reg.addOutputPort(ScalarMultiply, "OutputMatrix", (SparseMatrix, 'Result'))

    reg.addModule(Transpose)
    reg.addInputPort(Transpose, "InputMatrix", (Matrix, 'Input Matrix'))
    reg.addOutputPort(Transpose, "OutputMatrix", (Matrix, 'Output Matrix'))

    reg.addModule(MatrixMultiply)
    reg.addInputPort(MatrixMultiply, "InputMatrix1", (Matrix, 'Input Matrix 1'))
    reg.addInputPort(MatrixMultiply, "InputMatrix2", (Matrix, 'Input Matrix 2'))
    reg.addOutputPort(MatrixMultiply, "OutputMatrix", (Matrix, 'Output Matrix'))

    reg.addModule(ElementMultiply)
    reg.addInputPort(ElementMultiply, "InputMatrix1", (Matrix, 'Input Matrix 1'))
    reg.addInputPort(ElementMultiply, "InputMatrix2", (Matrix, 'Input Matrix 2'))
    reg.addOutputPort(ElementMultiply, "OutputMatrix", (SparseMatrix, 'Output Matrix'))

    reg.addModule(FFT)
    reg.addInputPort(FFT, "Signals", (Matrix, 'Input Signal Matrix'))
    reg.addInputPort(FFT, "FFT Samples", (basic.Integer, 'FFT Samples'))
    reg.addOutputPort(FFT, "FFT Output", (SparseMatrix, 'FFT Output'))
