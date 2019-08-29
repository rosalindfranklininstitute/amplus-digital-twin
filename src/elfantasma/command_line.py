#
# elfantasma.command_line.py
#
# Copyright (C) 2019 Diamond Light Source
#
# Author: James Parkhurst
#
# This code is distributed under the GPLv3 license, a copy of
# which is included in the root directory of this package.
#
import argparse
import pickle
import gemmi
import elfantasma.sample
import elfantasma.simulation


def show_input(args):
    """
    Print the command line arguments

    Args:
        args (object): The arguments object

    """
    print("Command line arguments:")
    for key, value in vars(args).items():
        print(f"  {key} = {value}")


def main():
    """
    The main interface to elfantasma

    """
    # Create the argument parser
    parser = argparse.ArgumentParser(description="Generate EM phantoms")

    # Add some command line arguments
    parser.add_argument(
        "-d,--device",
        choices=["cpu", "gpu"],
        default="gpu",
        dest="device",
        help="Choose the device to use",
    )
    parser.add_argument(
        "-o,--output",
        type=str,
        default="output.pickle",
        dest="output",
        help="The filename for the simulation results",
    )
    parser.add_argument(
        "-p,--phantom",
        choices=["4v5d"],
        default="4v5d",
        dest="phantom",
        help="Choose the phantom to generate",
    )

    # Parse the arguments
    args = parser.parse_args()

    # Print some options
    show_input(args)

    # Create the sample
    sample = elfantasma.sample.create_sample(args.phantom)

    # Create the simulation
    simulation = elfantasma.simulation.create_simulation(sample, args.device)

    # Run the simulation
    simulation.run()

    # Save the output to file
    print("Saving simulation results to %s" % args.output)
    with open(args.output, "wb") as outfile:
        pickle.dump(simulation.asdict(), outfile, protocol=2)


def read_pdb():
    """
    Read the given PDB file and show the atom positions

    """

    # Create the argument parser
    parser = argparse.ArgumentParser(description="Read a PDB file")

    # Add an argument for the filename
    parser.add_argument(
        "-f,--filename",
        type=str,
        default=None,
        dest="filename",
        help="The path to the PDB file",
    )

    # Parse the arguments
    args = parser.parse_args()

    # Check a filename has been given
    if args.filename == None:
        parser.print_help()
        exit(0)

    # Read the structure
    structure = gemmi.read_structure(args.filename)

    # Iterate through atoms
    prefix = " " * 4
    print("Structure: %s" % structure.name)
    for model in structure:
        print("%sModel: %s" % (prefix, model.name))
        for chain in model:
            print("%sChain: %s" % (prefix * 2, chain.name))
            for residue in chain:
                print("%sResidue: %s" % (prefix * 3, residue.name))
                for atom in residue:
                    print(
                        "%sAtom: %s, %f, %f, %f, %f, %f"
                        % (
                            prefix * 4,
                            atom.element.name,
                            atom.pos.x,
                            atom.pos.y,
                            atom.pos.z,
                            atom.occ,
                            atom.charge,
                        )
                    )


if __name__ == "__main__":
    main()