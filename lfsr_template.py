# ---------------------------------------------------------------------------------------------------------------------
# lfsr_template.py
# ---------------------------------------------------------------------------------------------------------------------
# Generate Verilog LFSR module and testbench
# ---------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------------
# More Imports
# ---------------------------------------------------------------------------------------------------------------------
from argparse import ArgumentParser, Namespace
from lfsr_helper import FeedbackModeEnum, ResetTypeEnum, LFSR_Formatter, LFSR_Params


# ---------------------------------------------------------------------------------------------------------------------
class Defaults:

    FeedbackMode = FeedbackModeEnum.Fibonacci
    InitValue = "0x1"
    ResetType = ResetTypeEnum.SyncHigh
    ModuleName = 'lfsr'
# ---------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------------
def parse_args() -> Namespace:

    # create parser
    parser = ArgumentParser(description="Generate Verilog LFSR module and testbench")

    # configure feedback_mode
    feedback_mode_parent = parser.add_argument_group('Feedback mode selection',
                                                     'default is %s' % Defaults.FeedbackMode.value)

    feedback_mode_group = feedback_mode_parent.add_mutually_exclusive_group()

    feedback_mode_group.add_argument('-f', '--fibonacci', action='store_const', const=FeedbackModeEnum.Fibonacci,
                                     dest='feedback_mode', help="Generate Fibonacci LFSR")

    feedback_mode_group.add_argument('-g', '--galois', action='store_const', const=FeedbackModeEnum.Galois,
                                     dest='feedback_mode', help="Generate Galois LFSR")

    parser.set_defaults(feedback_mode=Defaults.FeedbackMode)

    # configure init_mode
    init_mode_parent = parser.add_argument_group('Initial value selection',
                                                 'default is %s' % Defaults.InitValue)

    init_mode_group = init_mode_parent.add_mutually_exclusive_group()

    init_mode_group.add_argument("-i", "--init-value", default=Defaults.InitValue,
                                 help="Initial value of LFSR shift register (specify as hex number,"
                                      " can also be random, see below)")

    init_mode_group.add_argument("-j", "--init-random", action='store_true', help="Generate random initial value")

    # configure reset_type
    parser.add_argument("-r", "--reset-type", default=Defaults.ResetType.value,
                        choices=[rst.value for rst in ResetTypeEnum],
                        help="Type of reset to use (default is '%s')" % Defaults.ResetType.value)

    # configure other arguments
    parser.add_argument("-p", "--poly", default=None,
                        help="Feedback polynomial to use (specify as hex number, default is to generate a random one)")

    parser.add_argument("-m", "--module-name", default=None,
                        help="Name of module to generate (default is '%s<width>')" % Defaults.ModuleName)

    parser.add_argument("-c", "--clock-enable", action='store_true',
                        help="Add clock enable port (default is no clock enable)")

    parser.add_argument("-v", "--verbose", action='store_true',
                        help="Be verbose and print internal operation details")

    # configure width
    parser.add_argument('width', type=int, help="Width of LFSR in bits")

    # TODO: Add argument to decide what to generate. Default is both targets, but someone might need just the module
    #       itself or only the testbench (why?)

    # TODO: Add argument to print what was generated instead of always writing to files.

    # TODO: Consider refusing to overwrite already existing output files. Maybe add an argument to force overwrite.

    # parse command line
    return parser.parse_args()
# ---------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------------
def main() -> None:

    # create lfsr generator instance
    lfsr = LFSR_Formatter()

    # parse arguments and turn them into parameters
    args = parse_args()
    params = LFSR_Params(args, Defaults.ModuleName)

    # generate and save output products (module and testbench)
    for output in lfsr.OutputEnum:
        verilog = lfsr.generate_output(output, params)
        lfsr.write_output(output, verilog, params)
# ---------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
# ---------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------------
# End of File
# ---------------------------------------------------------------------------------------------------------------------
