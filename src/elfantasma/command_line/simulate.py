#
# elfantasma.command_line.simulate.py
#
# Copyright (C) 2019 Diamond Light Source and Rosalind Franklin Institute
#
# Author: James Parkhurst
#
# This code is distributed under the GPLv3 license, a copy of
# which is included in the root directory of this package.
#
import argparse
import logging
import numpy
import time
import elfantasma.io
import elfantasma.command_line
import elfantasma.config
import elfantasma.sample
from math import pi

# Get the logger
logger = logging.getLogger(__name__)


def projected_potential():
    """
    Simulate the projected potential from the sample

    """

    # Get the start time
    start_time = time.time()

    # Create the argument parser
    parser = argparse.ArgumentParser(
        description="Simulate the exit wave from the sample"
    )

    # Add some command line arguments
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default=None,
        dest="config",
        help="The yaml file to configure the simulation",
    )
    parser.add_argument(
        "-d",
        "--device",
        choices=["cpu", "gpu"],
        default=None,
        dest="device",
        help="Choose the device to use",
    )
    parser.add_argument(
        "--cluster.max_workers",
        type=int,
        default=None,
        dest="cluster_max_workers",
        help="The maximum number of worker processes",
    )
    parser.add_argument(
        "--cluster.method",
        type=str,
        choices=["sge"],
        default=None,
        dest="cluster_method",
        help="The cluster method to use",
    )
    parser.add_argument(
        "-s",
        "--sample",
        type=str,
        default="sample.h5",
        dest="sample",
        help="The filename for the sample",
    )

    # Parse the arguments
    args = parser.parse_args()

    # Configure some basic logging
    elfantasma.command_line.configure_logging()

    # Set the command line args in a dict
    command_line = {}
    if args.device is not None:
        command_line["device"] = args.device
    if args.cluster_max_workers is not None or args.cluster_method is not None:
        command_line["cluster"] = {}
    if args.cluster_max_workers is not None:
        command_line["cluster"]["max_workers"] = args.cluster_max_workers
    if args.cluster_method is not None:
        command_line["cluster"]["method"] = args.cluster_method

    # Load the full configuration
    config = elfantasma.config.load(args.config, command_line)

    # Print some options
    elfantasma.config.show(config)

    # Create the microscope
    microscope = elfantasma.microscope.new(**config["microscope"])

    # Create the sample
    logger.info(f"Loading sample from {args.sample}")
    sample = elfantasma.sample.load(args.sample)

    # Create the scan
    if config["scan"]["step_pos"] == "auto":
        radius = sample.shape_radius
        config["scan"]["step_pos"] = config["scan"]["step_angle"] * radius * pi / 180.0
    scan = elfantasma.scan.new(**config["scan"])
    if scan.positions[-1] > sample.containing_box[1][0]:
        raise RuntimeError("Scan goes beyond sample containing box")

    # Create the simulation
    simulation = elfantasma.simulation.projected_potential(
        microscope=microscope,
        sample=sample,
        scan=scan,
        device=config["device"],
        simulation=config["simulation"],
        cluster=config["cluster"],
    )

    # Run the simulation
    simulation.run()

    # Write some timing stats
    logger.info("Time taken: %.2f seconds" % (time.time() - start_time))


def exit_wave():
    """
    Simulate the exit wave from the sample

    """

    # Get the start time
    start_time = time.time()

    # Create the argument parser
    parser = argparse.ArgumentParser(
        description="Simulate the exit wave from the sample"
    )

    # Add some command line arguments
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default=None,
        dest="config",
        help="The yaml file to configure the simulation",
    )
    parser.add_argument(
        "-d",
        "--device",
        choices=["cpu", "gpu"],
        default=None,
        dest="device",
        help="Choose the device to use",
    )
    parser.add_argument(
        "--cluster.max_workers",
        type=int,
        default=None,
        dest="cluster_max_workers",
        help="The maximum number of worker processes",
    )
    parser.add_argument(
        "--cluster.method",
        type=str,
        choices=["sge"],
        default=None,
        dest="cluster_method",
        help="The cluster method to use",
    )
    parser.add_argument(
        "-s",
        "--sample",
        type=str,
        default="sample.h5",
        dest="sample",
        help="The filename for the sample",
    )
    parser.add_argument(
        "-e",
        "--exit_wave",
        type=str,
        default="exit_wave.h5",
        dest="exit_wave",
        help="The filename for the exit wave",
    )

    # Parse the arguments
    args = parser.parse_args()

    # Configure some basic logging
    elfantasma.command_line.configure_logging()

    # Set the command line args in a dict
    command_line = {}
    if args.device is not None:
        command_line["device"] = args.device
    if args.cluster_max_workers is not None or args.cluster_method is not None:
        command_line["cluster"] = {}
    if args.cluster_max_workers is not None:
        command_line["cluster"]["max_workers"] = args.cluster_max_workers
    if args.cluster_method is not None:
        command_line["cluster"]["method"] = args.cluster_method

    # Load the full configuration
    config = elfantasma.config.load(args.config, command_line)

    # Print some options
    elfantasma.config.show(config)

    # Create the microscope
    microscope = elfantasma.microscope.new(**config["microscope"])

    # Create the sample
    logger.info(f"Loading sample from {args.sample}")
    sample = elfantasma.sample.load(args.sample)

    # Create the scan
    if config["scan"]["step_pos"] == "auto":
        radius = sample.shape_radius
        config["scan"]["step_pos"] = config["scan"]["step_angle"] * radius * pi / 180.0
    scan = elfantasma.scan.new(**config["scan"])
    if scan.positions[-1] > sample.containing_box[1][0]:
        raise RuntimeError("Scan goes beyond sample containing box")

    # Create the simulation
    simulation = elfantasma.simulation.exit_wave(
        microscope=microscope,
        sample=sample,
        scan=scan,
        device=config["device"],
        simulation=config["simulation"],
        cluster=config["cluster"],
    )

    # Create the writer
    logger.info(f"Opening file: {args.exit_wave}")
    writer = elfantasma.io.new(
        args.exit_wave, shape=simulation.shape, dtype=numpy.complex64
    )

    # Run the simulation
    simulation.run(writer)

    # Write some timing stats
    logger.info("Time taken: %.2f seconds" % (time.time() - start_time))


def optics():
    """
    Simulate the optics

    """

    # Get the start time
    start_time = time.time()

    # Create the argument parser
    parser = argparse.ArgumentParser(description="Simulate the optics")

    # Add some command line arguments
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default=None,
        dest="config",
        help="The yaml file to configure the simulation",
    )
    parser.add_argument(
        "-d",
        "--device",
        choices=["cpu", "gpu"],
        default=None,
        dest="device",
        help="Choose the device to use",
    )
    parser.add_argument(
        "--cluster.max_workers",
        type=int,
        default=None,
        dest="cluster_max_workers",
        help="The maximum number of worker processes",
    )
    parser.add_argument(
        "--cluster.method",
        type=str,
        choices=["sge"],
        default=None,
        dest="cluster_method",
        help="The cluster method to use",
    )
    parser.add_argument(
        "-e",
        "--exit_wave",
        type=str,
        default="exit_wave.h5",
        dest="exit_wave",
        help="The filename for the exit wave",
    )
    parser.add_argument(
        "-o",
        "--optics",
        type=str,
        default="optics.h5",
        dest="optics",
        help="The filename for the optics",
    )

    # Parse the arguments
    args = parser.parse_args()

    # Configure some basic logging
    elfantasma.command_line.configure_logging()

    # Set the command line args in a dict
    command_line = {}
    if args.device is not None:
        command_line["device"] = args.device
    if args.cluster_max_workers is not None or args.cluster_method is not None:
        command_line["cluster"] = {}
    if args.cluster_max_workers is not None:
        command_line["cluster"]["max_workers"] = args.cluster_max_workers
    if args.cluster_method is not None:
        command_line["cluster"]["method"] = args.cluster_method

    # Load the full configuration
    config = elfantasma.config.load(args.config, command_line)

    # Print some options
    elfantasma.config.show(config)

    # Create the microscope
    microscope = elfantasma.microscope.new(**config["microscope"])

    # Create the exit wave data
    logger.info(f"Loading sample from {args.exit_wave}")
    exit_wave = elfantasma.io.open(args.exit_wave)

    # Create the scan
    config["scan"]["start_angle"] = exit_wave.start_angle
    config["scan"]["start_pos"] = exit_wave.start_position
    config["scan"]["step_angle"] = exit_wave.step_angle
    config["scan"]["stop_angle"] = exit_wave.stop_angle
    config["scan"]["step_pos"] = exit_wave.step_position
    scan = elfantasma.scan.new(**config["scan"])

    # Create the simulation
    simulation = elfantasma.simulation.optics(
        microscope=microscope,
        exit_wave=exit_wave,
        scan=scan,
        device=config["device"],
        simulation=config["simulation"],
        cluster=config["cluster"],
    )

    # Create the writer
    logger.info(f"Opening file: {args.optics}")
    writer = elfantasma.io.new(args.optics, shape=simulation.shape, dtype=numpy.float32)

    # Run the simulation
    simulation.run(writer)

    # Write some timing stats
    logger.info("Time taken: %.2f seconds" % (time.time() - start_time))


def image():
    """
    Simulate the image with noise

    """

    # Get the start time
    start_time = time.time()

    # Create the argument parser
    parser = argparse.ArgumentParser(description="Simulate the image")

    # Add some command line arguments
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default=None,
        dest="config",
        help="The yaml file to configure the simulation",
    )
    parser.add_argument(
        "-o",
        "--optics",
        type=str,
        default="optics.h5",
        dest="optics",
        help="The filename for the optics",
    )
    parser.add_argument(
        "-i",
        "--exit_wave",
        type=str,
        default="image.h5",
        dest="image",
        help="The filename for the exit wave",
    )

    # Parse the arguments
    args = parser.parse_args()

    # Configure some basic logging
    elfantasma.command_line.configure_logging()

    # Load the full configuration
    config = elfantasma.config.load(args.config)

    # Print some options
    elfantasma.config.show(config)

    # Create the microscope
    microscope = elfantasma.microscope.new(**config["microscope"])

    # Create the exit wave data
    logger.info(f"Loading sample from {args.optics}")
    optics = elfantasma.io.open(args.optics)

    # Create the scan
    config["scan"]["start_angle"] = optics.start_angle
    config["scan"]["start_pos"] = optics.start_position
    config["scan"]["step_angle"] = optics.step_angle
    config["scan"]["stop_angle"] = optics.stop_angle
    config["scan"]["step_pos"] = optics.step_position
    scan = elfantasma.scan.new(**config["scan"])

    # Create the simulation
    simulation = elfantasma.simulation.image(
        microscope=microscope,
        optics=optics,
        scan=scan,
        device=config["device"],
        simulation=config["simulation"],
        cluster=config["cluster"],
    )

    # Create the writer
    logger.info(f"Opening file: {args.image}")
    writer = elfantasma.io.new(args.image, shape=simulation.shape, dtype=numpy.int32)

    # Run the simulation
    simulation.run(writer)

    # Write some timing stats
    logger.info("Time taken: %.2f seconds" % (time.time() - start_time))


def simple():
    """
    Simulate the image

    """

    # Get the start time
    start_time = time.time()

    # Create the argument parser
    parser = argparse.ArgumentParser(description="Simulate the image")

    # Add some command line arguments
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default=None,
        dest="config",
        help="The yaml file to configure the simulation",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="output.h5",
        dest="output",
        help="The filename for the output",
    )
    parser.add_argument(
        "atoms",
        type=str,
        default=None,
        nargs="?",
        help="The filename for the input atoms",
    )

    # Parse the arguments
    args = parser.parse_args()

    # Configure some basic logging
    elfantasma.command_line.configure_logging()

    # Load the full configuration
    config = elfantasma.config.load(args.config)

    # Print some options
    elfantasma.config.show(config)

    # Create the microscope
    microscope = elfantasma.microscope.new(**config["microscope"])

    # Create the exit wave data
    logger.info(f"Loading sample from {args.atoms}")
    atoms = elfantasma.sample.AtomData.from_text_file(args.atoms)

    # Create the simulation
    simulation = elfantasma.simulation.simple(
        microscope=microscope,
        atoms=atoms,
        device=config["device"],
        simulation=config["simulation"],
    )

    # Create the writer
    logger.info(f"Opening file: {args.output}")
    writer = elfantasma.io.new(
        args.output, shape=simulation.shape, dtype=numpy.complex64
    )

    # Run the simulation
    simulation.run(writer)

    # Write some timing stats
    logger.info("Time taken: %.2f seconds" % (time.time() - start_time))
