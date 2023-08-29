"""
To generate a wrapper around a c-based library, ctypesgen is a greate resource.
To use this package, install it through pip, and make sure your computer can compile
code with gcc (for linux and macOS should be already available, for Windows you
have to download something like MinGW-W64-64bit. One example download can be found
[here](https://github.com/niXman/mingw-builds-binaries).

To generate code based on mycode.dll which is related to the mycode.h header file,
simply type on a terminal `ctypesgen -l mycode.dll mycode.h -o mycode.py`.
This file will include all the code included in ctypesgen.printer_python.preamble
and ctypesgen.libraryloader, and then it will include library-related content.

Here, we will import load_library function that allows us to import dll files.
To make our code clean, we will only include a modified version of the generated *.py,
and import the preamble (if needed) and library loader through this file. For example,
see qt3-utils/spectrometers/atspectrograph.py.

"""
import ctypes
import functools
import os
from ctypes import CDLL, pointer, c_int, c_char_p
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeVar, Sequence, Type, Callable

from ctypesgen.libraryloader import load_library as _library_loader, LibraryLoader
from ctypesgen.printer_python.preamble import String

from qt3utils.errors import QT3Error

# TODO: Add search paths such as default installation folders, program folders, and environments in _library_loader


PathType = TypeVar('PathType', str, Path)
DEFAULT_ENV_KEYS_OF_INSTALLATION_FOLDERS = ['ProgramFiles', 'ProgramFiles(X86)', 'ProgramW6432']


@dataclass
class Library:
    """
    Wrapper function for ctypesgen.LibraryLoader.Lookup, which is a wrapper for Type[ctypes.CDLL] function.
    Each library created with this class will be added in the library_registry.
    You can access the library methods (e.g. MyCMethod) by simply calling it through the Library object
    (Library.MyCMethod). Alternatively, you can use the lookup functionality to choose between `cdecl` and `stdcall`
    calling conventions (Library.lib.get('MyCMethod', 'cdecl')).
    """
    registry_name: str
    """ Name used in library registry. """
    lib: LibraryLoader.Lookup
    """ A ctypesgen object used for easy access lookup of 
    library methods. Can either use the getter method to get
    a library method (e.g. lib.get('MyCMethod', cdecl)(),
    or directly call a method same as one would do with 
    CDLL objects (e.g. lib.MyCMethod()).
    """
    name: str = field(init=False)
    """ Filename of library. """
    path: Path = field(init=False)
    """ Absolute path where library was found. """
    lib_access: dict[str, Type[CDLL]] = field(init=False)
    """ Dictionary with library object(s). If on Windows, 
    two items will exist depending on the calling convention used, 
    with keys 'cdecl' (ctypes.CDLL) and 'stdcall' (ctypes.WinDLL). 
    If not on Windows, only 'cdecl' will exist. """

    def __post_init__(self):
        self.lib_access = self.lib.access
        full_name = Path(self.lib_access['cdecl']._name)
        self.path = full_name.parent
        self.name = full_name.name
        self._append_to_registry()

    def _append_to_registry(self):
        if self.registry_name not in library_registry:
            library_registry[self.registry_name] = self

    def __getattr__(self, item):
        if item not in dir(self):
            return getattr(self.lib, item)
        else:
            return getattr(self, item)

    def get(self, name: str, calling_convention: str = 'cdecl'):
        return self.lib.get(name, calling_convention)

    def has(self, name: str, calling_convention: str = 'cdecl') -> bool:
        return self.lib.has(name, calling_convention)


library_registry: dict[str, Library] = {}


def _add_library_search_dirs(other_dirs: Sequence[str]):
    """
    Add potential user-defined library paths to library loader.
    If library paths are relative, convert them to absolute with respect to this
    file's directory.

    Note
    ----
    Modified version of add_library_search_dirs from ctypesgen.libraryloader.
    """
    for path in other_dirs:
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        if path not in _library_loader.other_dirs:
            _library_loader.other_dirs.append(path)


def _remove_library_search_dirs(other_dirs: Sequence[str]):
    """
    Remove potential user-defined library paths from library loader.
    """
    for path in other_dirs:
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        if path in _library_loader.other_dirs:
            _library_loader.other_dirs.remove(path)


def get_potential_paths_via_environment(
        installation_folders: Sequence[PathType],
        environment_keys: Sequence[str] = None
):
    """
    Combine all possible installation folders (package/library-based)
    and all the environment-specific folders, to find all potential library folders.
    """
    if environment_keys is None:
        environment_keys = DEFAULT_ENV_KEYS_OF_INSTALLATION_FOLDERS

    return [Path(env_path).joinpath(inst_path) for inst_path in installation_folders
            for env_path_key, env_path in os.environ.items() if env_path_key in environment_keys]


def load_library(
        name: PathType,
        paths: Sequence[PathType] | PathType = None,
        registry_name: str = None
) -> Library:
    if isinstance(paths, str | Path):
        paths = [paths]
    elif paths is None:
        paths = []

    if registry_name is None:
        registry_name = Path(name).stem

    if registry_name in library_registry:
        # TODO: Add warning of multiple library initializations
        # TODO: Check that paths match
        return library_registry[registry_name]

    paths = [Path(path).joinpath(name).name for path in paths]
    _add_library_search_dirs(paths)
    try:
        new_lib: LibraryLoader.Lookup = _library_loader(name)
        new_lib_entry = Library(registry_name, new_lib)
        _remove_library_search_dirs(paths)
        return new_lib_entry
    except ImportError:
        _remove_library_search_dirs(paths)
        raise QT3Error()  # TODO: Change error message.


PyCPointerType = ctypes._Pointer.__class__


def getitem(var: Sequence, item, default=...):
    """ Safely retrieves item from Sequence, without raising an error if default is provided. """
    if default is ...:
        return var.__getitem__(item)

    try:
        return var.__getitem__(item)
    except IndexError:
        return default


def pythonify(c_func: ctypes._CFuncPtr = None, *, string_buffer_size=1024):
    """
    A decorator that converts C/C++ function calls to Python function calls.
    """
    if c_func is None:
        # If the decorator is used without arguments, it returns a partially applied version of itself.
        return functools.partial(pythonify, string_buffer_size=string_buffer_size)

    @functools.wraps(c_func)
    def wrapper(*py_args):
        arg_types = getattr(c_func, 'argtypes', [])
        # res_type = getattr(c_func, 'restype', c_int)

        # Indexes of C arguments that are pointers and should have their values from C to Python after calling c_func.
        py_res_from_c_arg_index = []

        c_args: list[PyCPointerType] = []  # List to store C arguments.
        c_return_args = []  # List to store "returnable" C arguments that can be altered within the c_func call
        # (i.e., are pointers).

        py_args_iter = iter(py_args)  # Iterator for the end-user Python arguments
        py_args_idx = -1  # Counter for the current Python argument.

        skip_next = False
        for i, arg_type in enumerate(arg_types):
            if skip_next:
                skip_next = False
                continue

            if isinstance(arg_type, PyCPointerType):
                # If the argument type is a C pointer type, store the pointer-index and prepare for conversion.
                py_res_from_c_arg_index.append(i)
                return_arg_type = arg_type._type_
                return_arg = return_arg_type()
                c_return_args.append(return_arg)
                c_args.append(pointer(return_arg))

            elif arg_type == c_char_p or arg_type == String:
                if isinstance(getitem(py_args, py_args_idx + 1, None), str):
                    # If the argument type is a C string type, handle it as either input
                    py_str = next(py_args_iter)
                    py_args_idx += 1
                    c_str = c_char_p(py_str.encode('utf-8'))
                    c_args.append(c_str)

                # Following custom that has the string buffer size after the string...
                else:
                    if not isinstance(getitem(py_args, py_args_idx + 1, None), int):
                        # If the next Python argument is not an integer (i.e., definitely not a string buffer size,
                        # use the default buffer size
                        buffer_size = string_buffer_size
                    elif getitem(arg_types, i + 1, None) == c_int:
                        # If the next argument type is c_int, treat the string as an output buffer and the
                        # next argument as the buffer size
                        buffer_size = next(py_args_iter)
                    else:
                        # If the string handling logic doesn't apply, raise an error.
                        # TODO: Change error
                        raise ValueError(f'Implementation of c-string did not work successfully for c-argument {i} in '
                                         f'{c_func.__name__}.')

                    c_str_buffer = ctypes.create_string_buffer(buffer_size)
                    c_return_args.append(c_str_buffer)
                    c_args.append(c_str_buffer)
                    c_args.append(buffer_size)
                    skip_next = True

            else:
                # For other argument types, simply add the corresponding Python arguments to the C arguments list.
                try:
                    c_args.append(next(py_args_iter))
                    py_args_idx += 1
                except StopIteration:
                    # TODO: Change error
                    raise ValueError("The number of Python args doesn't match non-pointer C inputs.")

        # Call the original C function with the converted C arguments.
        c_result = c_func(*c_args)

        # Prepare Python results from the C result and C returnable arguments (pointers).
        py_results = [c_result]
        for return_arg in c_return_args:
            py_result = return_arg.value
            if isinstance(py_result, bytes):
                py_result = py_result.decode('utf-8')
            py_results.append(py_result)

        return tuple(py_results)

    return wrapper
