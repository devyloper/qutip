__all__ = ['file_data_store', 'file_data_read', 'qsave', 'qload']

import pickle
import numpy as np
import sys
from .core import Qobj
from pathlib import Path


# -----------------------------------------------------------------------------
# Write matrix data to a file
#
def file_data_store(filename, data, numtype="complex", numformat="decimal",
                    sep=","):
    """Stores a matrix of data to a file to be read by an external program.

    Parameters
    ----------
    filename : str or pathlib.Path
        Name of data file to be stored, including extension.
    data: array_like
        Data to be written to file.
    numtype : str {'complex, 'real'}
        Type of numerical data.
    numformat : str {'decimal','exp'}
        Format for written data.
    sep : str
        Single-character field seperator.  Usually a tab, space, comma,
        or semicolon.

    """
    if filename is None or data is None:
        raise ValueError("filename or data is unspecified")

    M, N = np.shape(data)

    f = open(filename, "w")

    f.write("# Generated by QuTiP: %dx%d %s matrix " % (M, N, numtype) +
            "in %s format ['%s' separated values].\n" % (numformat, sep))

    if numtype == "complex":

        if numformat == "exp":

            for m in range(M):
                for n in range(N):
                    if np.imag(data[m, n]) >= 0.0:
                        f.write("%.10e+%.10ej" % (np.real(data[m, n]),
                                                  np.imag(data[m, n])))
                    else:
                        f.write("%.10e%.10ej" % (np.real(data[m, n]),
                                                 np.imag(data[m, n])))
                    if n != N - 1:
                        f.write(sep)
                f.write("\n")

        elif numformat == "decimal":

            for m in range(M):
                for n in range(N):
                    if np.imag(data[m, n]) >= 0.0:
                        f.write("%.10f+%.10fj" % (np.real(data[m, n]),
                                                  np.imag(data[m, n])))
                    else:
                        f.write("%.10f%.10fj" % (np.real(data[m, n]),
                                                 np.imag(data[m, n])))
                    if n != N - 1:
                        f.write(sep)
                f.write("\n")

        else:
            raise ValueError("Illegal numformat value (should be " +
                             "'exp' or 'decimal')")

    elif numtype == "real":

        if numformat == "exp":

            for m in range(M):
                for n in range(N):
                    f.write("%.10e" % (np.real(data[m, n])))
                    if n != N - 1:
                        f.write(sep)
                f.write("\n")

        elif numformat == "decimal":

            for m in range(M):
                for n in range(N):
                    f.write("%.10f" % (np.real(data[m, n])))
                    if n != N - 1:
                        f.write(sep)
                f.write("\n")

        else:
            raise ValueError("Illegal numformat value (should be " +
                             "'exp' or 'decimal')")

    else:
        raise ValueError("Illegal numtype value (should be " +
                         "'complex' or 'real')")

    f.close()


# -----------------------------------------------------------------------------
# Read matrix data from a file
#
def file_data_read(filename, sep=None):
    """Retrieves an array of data from the requested file.

    Parameters
    ----------
    filename : str or pathlib.Path
        Name of file containing reqested data.
    sep : str
        Seperator used to store data.

    Returns
    -------
    data : array_like
        Data from selected file.

    """
    if filename is None:
        raise ValueError("filename is unspecified")

    f = open(filename, "r")

    #
    # first count lines and numbers of
    #
    M = N = 0
    for line in f:
        # skip comment lines
        if line[0] == '#' or line[0] == '%':
            continue
        # find delim
        if N == 0 and sep is None:
            if len(line.rstrip().split(",")) > 1:
                sep = ","
            elif len(line.rstrip().split(";")) > 1:
                sep = ";"
            elif len(line.rstrip().split(":")) > 1:
                sep = ":"
            elif len(line.rstrip().split("|")) > 1:
                sep = "|"
            elif len(line.rstrip().split()) > 1:
                # sepical case for a mix of white space deliminators
                sep = None
            else:
                raise ValueError("Unrecognized column deliminator")
        # split the line
        line_vec = line.split(sep)
        n = len(line_vec)
        if N == 0 and n > 0:
            N = n
            # check type
            if ("j" in line_vec[0]) or ("i" in line_vec[0]):
                numtype = "complex"
            else:
                numtype = "np.real"

            # check format
            if ("e" in line_vec[0]) or ("E" in line_vec[0]):
                numformat = "exp"
            else:
                numformat = "decimal"

        elif N != n:
            raise ValueError("Badly formatted data file: " +
                             "unequal number of columns")
        M += 1

    #
    # read data and store in a matrix
    #
    f.seek(0)

    if numtype == "complex":
        data = np.zeros((M, N), dtype="complex")
        m = n = 0
        for line in f:
            # skip comment lines
            if line[0] == '#' or line[0] == '%':
                continue
            n = 0
            for item in line.rstrip().split(sep):
                data[m, n] = complex(item)
                n += 1
            m += 1

    else:
        data = np.zeros((M, N), dtype="float")
        m = n = 0
        for line in f:
            # skip comment lines
            if line[0] == '#' or line[0] == '%':
                continue
            n = 0
            for item in line.rstrip().split(sep):
                data[m, n] = float(item)
                n += 1
            m += 1

    f.close()

    return data


def qsave(data, name='qutip_data'):
    """
    Saves given data to file named 'filename.qu' in current directory.

    Parameters
    ----------
    data : instance/array_like
        Input Python object to be stored.
    filename : str or pathlib.Path
        Name of output data file.

    """
    # open the file for writing
    path = Path(name)
    path = path.with_suffix(path.suffix + ".qu")

    with open(path, "wb") as fileObject:
        # this writes the object a to the file named 'filename.qu'
        pickle.dump(data, fileObject)


def qload(name):
    """
    Loads data file from file named 'filename.qu' in current directory.

    Parameters
    ----------
    name : str or pathlib.Path
        Name of data file to be loaded.

    Returns
    -------
    qobject : instance / array_like
        Object retrieved from requested file.

    """
    path = Path(name)
    path = path.with_suffix(path.suffix + ".qu")

    with open(path, "rb") as fileObject:
        if sys.version_info >= (3, 0):
            out = pickle.load(fileObject, encoding='latin1')
        else:
            out = pickle.load(fileObject)

    return out
