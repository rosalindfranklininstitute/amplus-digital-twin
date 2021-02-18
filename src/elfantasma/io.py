#
# elfantasma.io.py
#
# Copyright (C) 2019 Diamond Light Source and Rosalind Franklin Institute
#
# Author: James Parkhurst
#
# This code is distributed under the GPLv3 license, a copy of
# which is included in the root directory of this package.
#
import h5py
import numpy
import mrcfile
import os
import PIL.Image

try:
    FEI_EXTENDED_HEADER_DTYPE = mrcfile.dtypes.FEI1_EXTENDED_HEADER_DTYPE
except Exception:
    FEI_EXTENDED_HEADER_DTYPE = mrcfile.dtypes.FEI_EXTENDED_HEADER_DTYPE


class Writer(object):
    """
    Interface to write the simulated data

    """

    @property
    def shape(self):
        """
        The shape property

        """
        return self._data.shape

    @property
    def dtype(self):
        """
        The dtype property

        """
        return self._data.dtype

    @property
    def data(self):
        """
        The data property

        """
        return self._data

    @property
    def angle(self):
        """
        The angle property

        """
        return self._angle

    @property
    def position(self):
        """
        The position property

        """
        return self._position

    @property
    def shift(self):
        """
        The shift property

        """
        return self._shift

    @property
    def pixel_size(self):
        """
        The pixel size property

        """
        return self._pixel_size

    @property
    def is_mrcfile_writer(self):
        """
        Return if is mrcfile

        """
        return isinstance(self, MrcFileWriter)

    @property
    def is_nexus_writer(self):
        """
        Return if is nexus

        """
        return isinstance(self, NexusWriter)

    @property
    def is_image_writer(self):
        """
        Return if is image

        """
        return isinstance(self, ImageWriter)

    def update(self):
        """
        Update if anything needs to be done

        """
        pass


class MrcFileWriter(Writer):
    """
    Write to an mrcfile

    """

    class AngleProxy(object):
        """
        Proxy interface to angles

        """

        def __init__(self, handle):
            self.handle = handle

        def __setitem__(self, item, data):
            self.handle.extended_header[item]["Alpha tilt"] = data

    class PositionProxy(object):
        """
        Proxy interface to positions

        """

        def __init__(self, handle):
            self.handle = handle
            n = len(self.handle.extended_header)
            self.x, self.y = numpy.meshgrid(numpy.arange(0, 3), numpy.arange(0, n))

        def __setitem__(self, item, data):

            # Set the items
            def setitem_internal(j, i, d):
                if i == 0:
                    self.handle.extended_header[j]["Shift X"] = d
                elif i == 1:
                    self.handle.extended_header[j]["Shift Y"] = d

            # Get the indices from the item
            x = self.x[item]
            y = self.y[item]

            # Set the item
            if isinstance(x, numpy.ndarray):
                for j, i, d in zip(y, x, data):
                    setitem_internal(j, i, d)
            else:
                setitem_internal(y, x, data)

    def __init__(self, filename, shape, pixel_size, dtype="uint8"):
        """
        Initialise the writer

        Args:
            filename (str): The filename
            shape (tuple): The shape of the data
            pixel_size (float): The pixel size
            dtype (str): The data type

        """
        # Get the dtype
        dtype = numpy.dtype(dtype)

        # Convert 32bit int and 64bit float
        if dtype == "int32":
            dtype = numpy.dtype(numpy.int16)
        elif dtype == "uint32":
            dtype = numpy.dtype(numpy.uint16)
        elif dtype == "float64":
            dtype = numpy.dtype(numpy.float32)
        elif dtype == "complex128":
            dtype = numpy.dtype(numpy.complex64)

        # Open the handle to the mrcfile
        self.handle = mrcfile.new_mmap(
            filename,
            shape=(0, 0, 0),
            mrc_mode=mrcfile.utils.mode_from_dtype(dtype),
            overwrite=True,
        )

        # Setup the extended header
        extended_header = numpy.zeros(shape=shape[0], dtype=FEI_EXTENDED_HEADER_DTYPE)

        # Set the extended header
        self.handle._check_writeable()
        self.handle._close_data()
        self.handle._extended_header = extended_header
        self.handle.header.nsymbt = extended_header.nbytes
        self.handle.header.exttyp = "FEI1"
        self.handle._open_memmap(dtype, shape)
        self.handle.update_header_from_data()
        self.handle.flush()

        # Set the pixel size
        self.handle.voxel_size = pixel_size
        for i in range(self.handle.extended_header.shape[0]):
            self.handle.extended_header[i]["Pixel size X"] = pixel_size * 1e-10
            self.handle.extended_header[i]["Pixel size Y"] = pixel_size * 1e-10
            self.handle.extended_header[i]["Application"] = "RFI Simulation"

        # Set the data array
        self._data = self.handle.data
        self._angle = MrcFileWriter.AngleProxy(self.handle)
        self._position = MrcFileWriter.PositionProxy(self.handle)

    @property
    def pixel_size(self):
        """
        The pixel size

        """
        return self.handle.voxel_size[0]

    def update(self):
        """
        Update before closing

        """
        self.handle.update_header_stats()


class NexusWriter(Writer):
    """
    Write to a nexus file

    """

    class ShiftProxy(object):
        """
        Proxy interface to positions

        """

        def __init__(self, handle):
            self.handle = handle
            n = self.handle["x_shift"].shape[0]
            self.x, self.y = numpy.meshgrid(numpy.arange(0, 2), numpy.arange(0, n))

        def __setitem__(self, item, data):

            # Set the items
            def setitem_internal(j, i, d):
                if i == 0:
                    self.handle["x_shift"][j] = d
                elif i == 1:
                    self.handle["y_shift"][j] = d

            # Get the indices from the item
            x = self.x[item]
            y = self.y[item]

            # Set the item
            if isinstance(x, numpy.ndarray):
                for j, i, d in zip(y, x, data):
                    setitem_internal(j, i, d)
            else:
                setitem_internal(y, x, data)

    class PositionProxy(object):
        """
        Proxy interface to positions

        """

        def __init__(self, handle):
            self.handle = handle
            n = self.handle["x_translation"].shape[0]
            self.x, self.y = numpy.meshgrid(numpy.arange(0, 3), numpy.arange(0, n))

        def __setitem__(self, item, data):

            # Set the items
            def setitem_internal(j, i, d):
                if i == 0:
                    self.handle["x_translation"][j] = d
                elif i == 1:
                    self.handle["y_translation"][j] = d
                elif i == 2:
                    self.handle["z_translation"][j] = d

            # Get the indices from the item
            x = self.x[item]
            y = self.y[item]

            # Set the item
            if isinstance(x, numpy.ndarray):
                for j, i, d in zip(y, x, data):
                    setitem_internal(j, i, d)
            else:
                setitem_internal(y, x, data)

    def __init__(self, filename, shape, pixel_size, dtype="float32"):
        """
        Initialise the writer

        Args:
            filename (str): The filename
            shape (tuple): The shape of the data
            pixel_size (float): The pixel size
            dtype (object): The data type of the data

        """

        # Open the file for writing
        self.handle = h5py.File(filename, "w")

        # Create the entry
        entry = self.handle.create_group("entry")
        entry.attrs["NX_class"] = "NXentry"
        entry["definition"] = "NXtomo"

        # Create the instrument
        instrument = entry.create_group("instrument")
        instrument.attrs["NX_class"] = "NXinstrument"

        # Create the detector
        detector = instrument.create_group("detector")
        detector.attrs["NX_class"] = "NXdetector"
        detector.create_dataset("data", shape=shape, dtype=dtype)
        detector["image_key"] = numpy.zeros(shape=shape[0])
        detector["x_pixel_size"] = numpy.full(shape=shape[0], fill_value=pixel_size)
        detector["y_pixel_size"] = numpy.full(shape=shape[0], fill_value=pixel_size)

        # Create the sample
        sample = entry.create_group("sample")
        sample.attrs["NX_class"] = "NXsample"
        sample["name"] = "elfantasma-simulation"
        sample.create_dataset("rotation_angle", shape=(shape[0],), dtype=numpy.float32)
        sample.create_dataset("x_translation", shape=(shape[0],), dtype=numpy.float32)
        sample.create_dataset("y_translation", shape=(shape[0],), dtype=numpy.float32)
        sample.create_dataset("z_translation", shape=(shape[0],), dtype=numpy.float32)
        sample.create_dataset("x_shift", shape=(shape[0],), dtype=numpy.float32)
        sample.create_dataset("y_shift", shape=(shape[0],), dtype=numpy.float32)

        # Create the data
        data = entry.create_group("data")
        data["data"] = detector["data"]
        data["rotation_angle"] = sample["rotation_angle"]
        data["x_translation"] = sample["x_translation"]
        data["y_translation"] = sample["y_translation"]
        data["z_translation"] = sample["z_translation"]
        data["x_shift"] = sample["x_shift"]
        data["y_shift"] = sample["y_shift"]
        data["image_key"] = detector["image_key"]

        # Set the data ptr
        self._data = data["data"]
        self._angle = data["rotation_angle"]
        self._position = NexusWriter.PositionProxy(data)
        self._shift = NexusWriter.ShiftProxy(data)

    @property
    def pixel_size(self):
        """
        Return the pixel size

        """
        return self.handle["instrument"]["detector"]["x_pixel_size"][0]


class ImageWriter(Writer):
    """
    Write to a images

    """

    class DataProxy(object):
        """
        A proxy interface for the data

        """

        def __init__(self, template, shape=None, vmin=None, vmax=None):
            self.template = template
            self.shape = shape
            self.vmin = vmin
            self.vmax = vmax

        def __setitem__(self, item, data):

            # Check the input
            assert isinstance(item, tuple)
            assert isinstance(item[1], slice)
            assert isinstance(item[2], slice)
            assert item[1].start is None
            assert item[1].stop is None
            assert item[1].step is None
            assert item[2].start is None
            assert item[2].stop is None
            assert item[2].step is None
            assert len(data.shape) == 2
            assert data.shape[0] == self.shape[1]
            assert data.shape[1] == self.shape[2]

            # Convert to squared amplitude
            if numpy.iscomplexobj(data):
                data = numpy.abs(data) ** 2
                self.vmin = None
                self.vmax = None

            # Compute scale factors to put between 0 and 255
            if self.vmin is None:
                vmin = numpy.min(data)
            else:
                vmin = self.vmin
            if self.vmax is None:
                vmax = numpy.max(data)
            else:
                vmax = self.vmax
            s1 = 255.0 / (vmax - vmin)
            s0 = -s1 * vmin

            # Save the image to file
            filename = self.template % (item[0] + 1)
            image = (data * s1 + s0).astype(numpy.uint8)
            PIL.Image.fromarray(image).save(filename)

    def __init__(self, template, shape=None, vmin=None, vmax=None):
        """
        Initialise the writer

        Args:
            filename (str): The filename
            shape (tuple): The shape of the data

        """

        # Set the proxy data interface
        self._data = ImageWriter.DataProxy(template, shape, vmin, vmax)

        # Create dummy arrays for angle and position
        self._angle = numpy.zeros(shape=shape[0], dtype=numpy.float32)
        self._position = numpy.zeros(shape=(shape[0], 3), dtype=numpy.float32)
        self._pixel_size = 0

    @property
    def vmin(self):
        """
        The vmin property

        """
        return self._data.vmin

    @property
    def vmax(self):
        """
        The vmax property

        """
        return self._data.vmax

    @vmin.setter
    def vmin(self, vmin):
        """
        The vmin propety setter

        """
        self._data.vmin = vmin

    @vmax.setter
    def vmax(self, vmax):
        """
        The vmax property setter

        """
        self._data.vmax = vmax


class Reader(object):
    """
    Interface to write the simulated data

    """

    def __init__(self, handle, data, angle, position, pixel_size):
        """
        Initialise the data

        Args:
            data (array): The data array
            angle (array): The angle array
            position (array): The position array
            pixel_size (float): The pixel size array

        """
        # Check the size
        assert len(angle) == data.shape[0], "Inconsistent dimensions"
        assert len(position) == data.shape[0], "Inconsistent dimensions"

        # Set the array
        self.handle = handle
        self.data = data
        self.angle = angle
        self.position = position
        self.pixel_size = pixel_size
        self.shape = data.shape
        self.dtype = data.dtype

    @property
    def start_angle(self):
        """
        Returns:
            float: the start angle

        """
        return self.angle[0]

    @property
    def stop_angle(self):
        """
        Returns:
            float: The stop angle

        """
        return self.angle[-1]

    @property
    def step_angle(self):
        """
        Returns:
            float: The stop angle

        """
        tol = 1e-7
        if len(self.angle) == 1:
            step = 1
        else:
            step = (self.angle[-1] - self.angle[0]) / (len(self.angle) - 1)
        # assert all(
        #     abs((b - a) - step) < tol for a, b in zip(self.angle[0:-1], self.angle[1:])
        # )
        return step

    @property
    def start_position(self):
        """
        Returns:
            float: the start position

        """
        return self.position[0][1]

    @property
    def stop_position(self):
        """
        Returns:
            float: The stop position

        """
        return self.position[-1][1]

    @property
    def step_position(self):
        """
        Returns:
            float: The stop position

        """
        tol = 1e-7
        if self.position.shape[0] > 1:
            step = (self.position[-1, 1] - self.position[0, 1]) / (
                self.position.shape[0] - 1
            )
            assert all(
                abs((b - a) - step) < tol
                for a, b in zip(self.position[0:-1, 1], self.position[1:1])
            )
        else:
            step = 0
        return step

    @property
    def num_images(self):
        """
        Returns:
            int: The number of images

        """
        return len(self.angle)

    @classmethod
    def from_mrcfile(Class, filename):
        """
        Read the simulated data from a mrc file

        Args:
            filename (str): The input filename

        """

        # Read the data
        handle = mrcfile.mmap(filename, "r")

        # Check the header info
        if handle.header.exttyp == b"FEI1":
            assert handle.extended_header.dtype == FEI_EXTENDED_HEADER_DTYPE
            assert len(handle.extended_header.shape) == 1
            assert handle.extended_header.shape[0] == handle.data.shape[0]

            # Read the angles
            angle = numpy.zeros(handle.data.shape[0], dtype=numpy.float32)
            for i in range(handle.extended_header.shape[0]):
                angle[i] = handle.extended_header[i]["Alpha tilt"]

            # Read the positions
            position = numpy.zeros(shape=(handle.data.shape[0], 3), dtype=numpy.float32)
            for i in range(handle.extended_header.shape[0]):
                position[i, 0] = handle.extended_header[i]["Shift X"]
                position[i, 1] = handle.extended_header[i]["Shift Y"]
                position[i, 2] = 0
        else:
            angle = numpy.zeros(handle.data.shape[0], dtype=numpy.float32)
            position = numpy.zeros(shape=(handle.data.shape[0], 3), dtype=numpy.float32)

        # Get the pixel size
        pixel_size = handle.voxel_size["x"]

        # Create the reader
        return Reader(handle, handle.data, angle, position, pixel_size)

    @classmethod
    def from_nexus(Class, filename):
        """
        Read the simulated data from a nexus file

        Args:
            filename (str): The input filename

        """

        # Read the data from disk
        handle = h5py.File(filename, "r")

        # Get the entry
        entry = handle["entry"]
        assert entry.attrs["NX_class"] == "NXentry"
        definition = entry["definition"][()]
        if isinstance(definition, bytes):
            definition = definition.decode("utf-8")
        assert definition == "NXtomo"

        # Get the data and detector
        data = entry["data"]
        detector = entry["instrument"]["detector"]

        # Get the positions
        position = numpy.array(
            (data["x_translation"], data["y_translation"], data["z_translation"])
        ).T

        # Get the pixel size
        pixel_size = detector["x_pixel_size"][0]

        # Create the reader
        return Reader(
            handle, data["data"], data["rotation_angle"], position, pixel_size
        )

    @classmethod
    def from_file(Class, filename):
        """
        Read the simulated data from file

        Args:
            filename (str): The output filename

        """
        extension = os.path.splitext(filename)[1].lower()
        if extension in [".mrc"]:
            return Class.from_mrcfile(filename)
        elif extension in [".h5", ".hdf5", ".nx", ".nxs", ".nexus", "nxtomo"]:
            return Class.from_nexus(filename)
        else:
            raise RuntimeError(f"File with unknown extension: {filename}")


def new(filename, shape=None, pixel_size=None, dtype=None, vmin=None, vmax=None):
    """
    Create a new file for writing

    Args:
        filename (str): The output filename
        shape (tuple): The output shape
        pixel_size (tuple): The pixel size
        dtype (object): The data type (only used with NexusWriter)
        vmin (int): The minimum value (only used in ImageWriter)
        vmax (int): The maximum value (only used in ImageWriter)

    Returns:
        object: The file writer

    """
    extension = os.path.splitext(filename)[1].lower()
    if extension in [".mrc"]:
        return MrcFileWriter(filename, shape, pixel_size, dtype)
    elif extension in [".h5", ".hdf5", ".nx", ".nxs", ".nexus", "nxtomo"]:
        return NexusWriter(filename, shape, pixel_size, dtype)
    elif extension in [".png", ".jpg", ".jpeg", ".tif", ".tiff"]:
        return ImageWriter(filename, shape, vmin, vmax)
    else:
        raise RuntimeError(f"File with unknown extension: {filename}")


def open(filename):
    """
    Read the simulated data from file

    Args:
        filename (str): The output filename

    """
    return Reader.from_file(filename)
