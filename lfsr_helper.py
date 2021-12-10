# ---------------------------------------------------------------------------------------------------------------------
# lfsr_helper.py
# ---------------------------------------------------------------------------------------------------------------------
# LFSR Helper Module
# ---------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------------------------------------------------
import math
import sys
import numpy
import random


# ---------------------------------------------------------------------------------------------------------------------
# More Imports
# ---------------------------------------------------------------------------------------------------------------------
from enum import Enum, auto
from argparse import Namespace
from lfsr_math import LFSR_Math
from typing import Tuple
from lfsr_enum import FeedbackModeEnum, ResetTypeEnum


# ---------------------------------------------------------------------------------------------------------------------
class LFSR_Params:

    RNG_Seed = 1  # internal rng seed
    MinWidth = 3

    # -----------------------------------------------------------------------------------------------------------------
    def __init__(self, args: Namespace, default_module_name: str) -> None:

        # sanity check
        if args.width < self.MinWidth:
            self._exit_failure("Width must be >= %d, was given %d" % (self.MinWidth, args.width))

        # remember verbosity level
        self.verbose = args.verbose

        # prepare rng
        self._print_verbose("Seeding RNG...")
        random.seed(self.RNG_Seed)

        # parse simple parameters
        self.width = args.width
        self.width1 = self.width - 1
        self.width2 = self.width - 2
        self.period = LFSR_Math.period(self.width)
        self.feedback_mode = args.feedback_mode
        self.reset_type = ResetTypeEnum(args.reset_type)
        self.reset_port_name = args.reset_type

        # format module name
        self.module_name = self._format_module_name(args, default_module_name)

        # print some info
        self._print_verbose("Generating %d-bit LFSR named '%s'..." % (self.width, self.module_name))

        # parse clock enable parameters
        self.clock_enable_port_declaration = self._format_ce_port_declaration(args.clock_enable)
        self.clock_enable_condition = self._format_ce_condition(args.clock_enable)
        self.tb_clock_enable = self._format_tb_ce(args.clock_enable)

        # parse and format initial value
        self.init_value_numpy = self._process_init_value(args)
        self.init_value_bin = self._format_init_value_bin()

        # format remaining fields
        self.sensitivity_list = self._format_sensitivity_list()
        self.reset_signal = self._format_reset_signal()
        self.tb_reset_active, self.tb_reset_inactive = self._format_testbench_resets()

        # handle and format polynomial function
        if args.poly is not None:

            # user requested specific polynomial
            self._print_verbose("Using user-supplied polynomial...")

            # try to parse user-supplied polynomial
            user_poly = self._parse_user_poly_arg(args)
            self.poly_numpy = LFSR_Math.int2row(user_poly, self.width)

            user_poly_ok, user_poly_msg = LFSR_Math.validate_poly_numpy(self.poly_numpy, self.width)
            if not user_poly_ok:
                self._print_verbose(user_poly_msg)
                self._exit_failure("User-supplied polynomial is invalid!")

            user_poly_ok, user_poly_msg = LFSR_Math.check_poly_max_length(self.feedback_mode,
                                                                          self.poly_numpy, self.width,
                                                                          self.init_value_numpy)
            if not user_poly_ok:
                self._print_verbose(user_poly_msg)
                self._exit_failure("User-supplied polynomial is not maximum length!")

        else:

            # try to generate a polynomial on the fly
            self._print_verbose("Trying to generate a random polynomial...")

            poly_found = False
            while not poly_found:
                random_poly = random.getrandbits(self.width)
                poly_width_hex = math.ceil(self.width / 4)
                self._print_verbose("  RNG returned 0x%%0%dx" % poly_width_hex % random_poly)

                self.poly_numpy = LFSR_Math.int2row(random_poly, self.width)
                random_poly_ok, _ = LFSR_Math.validate_poly_numpy(self.poly_numpy, self.width)
                if random_poly_ok:
                    poly_found, _ = LFSR_Math.check_poly_max_length(self.feedback_mode,
                                                                    self.poly_numpy, self.width,
                                                                    self.init_value_numpy)

            # done
            self._print_verbose("    OK")

        # format feedback function
        self.poly_func = self._process_poly_func_wrapper()
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    def _process_init_value(self, args: Namespace) -> numpy.ndarray:

        if args.init_random:

            # generate random initial value
            self._print_verbose("Generating random initial value...")
            init_value = random.getrandbits(self.width)
            self._print_verbose("  RNG returned %d" % init_value)

            # rng might have generated invalid initial value (all zeroes or ones), take care of that
            ok, _ = LFSR_Math.validate_init_value_int(self.feedback_mode, init_value, self.width)
            while not ok:  # don't complain
                init_value = random.getrandbits(self.width)
                self._print_verbose("  Trying again, RNG returned %d" % init_value)
                ok, _ = LFSR_Math.validate_init_value_int(self.feedback_mode, init_value, self.width)

            # done
            self._print_verbose("    OK")

        else:

            # parse what the user told us to
            self._print_verbose("Parsing initial value...")
            init_value = self._parse_init_value_arg(args)

        return LFSR_Math.int2row(init_value, self.width)
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    def _process_poly_func_wrapper(self) -> str:

        if self.feedback_mode == FeedbackModeEnum.Fibonacci:
            return self._process_poly_func_fibonacci()

        elif self.feedback_mode == FeedbackModeEnum.Galois:
            return self._process_poly_func_galois()

        else:
            raise RuntimeError
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    def _process_poly_func_fibonacci(self) -> str:

        poly_func = "lfsr_value_next = {lfsr_value_current[%d:0], " % (self.width - 2)
        poly_func_offset = 8 + len(poly_func)
        poly_func += "lfsr_value_current[%d] ^" % (self.width - 1)

        seen_taps = 1
        total_taps = self.poly_numpy.sum()

        for i in range(self.width - 2, -1, -1):
            if self.poly_numpy[0][i] == 1:
                poly_func += "\n" + " " * poly_func_offset + "lfsr_value_current[%d]" % i
                seen_taps += 1
                if seen_taps < total_taps:
                    poly_func += " ^"
                else:
                    poly_func += "};"

        return poly_func
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    def _process_poly_func_galois(self) -> str:
        raise NotImplementedError
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    def _parse_init_value_arg(self, args: Namespace) -> int:

        init_value = None

        try:

            # try to convert
            init_value = self._int0x16(args.init_value)

        except ValueError:
            LFSR_Params._exit_failure("Can't parse initial value ('%s'), specify as hex number, eg. 0x4321" %
                                      args.init_value)

        assert init_value is not None
        init_value_width = len(bin(init_value)[2:])
        if init_value_width > self.width:
            LFSR_Params._exit_failure("Initial value '%s' is too large (%d bits), must fit in only %d bits" %
                                      (args.init_value, init_value_width, self.width))

        ok, msg = LFSR_Math.validate_init_value_int(self.feedback_mode, init_value, self.width)
        if not ok:
            self._print_verbose(msg)
            LFSR_Params._exit_failure("Initial value '%s' is prohibited for the specified LFSR mode" %
                                      args.init_value)

        return init_value
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    def _parse_user_poly_arg(self, args: Namespace) -> int:

        user_poly = None

        try:

            # try to parse
            user_poly = self._int0x16(args.poly)

        except ValueError:
            self._exit_failure("Can't parse polynomial ('%s'), please specify it as hex number with the highest power "
                               "on the left, eg. 0xC means x^4 + x^3 + 1" % args.poly)

        assert user_poly is not None
        user_poly_width = len(bin(user_poly)[2:])

        if user_poly_width > self.width:
            self._exit_failure("Polynomial '%s' is too large (largest power is %d), must have largest nonzero power "
                               "of %d" % (args.poly, user_poly_width, self.width))

        return user_poly
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    def _format_sensitivity_list(self) -> str:
        sensitivity_list = "posedge clk"
        if self.reset_type == ResetTypeEnum.AsyncHigh:
            sensitivity_list += " or posedge %s" % self.reset_port_name
        elif self.reset_type == ResetTypeEnum.AsyncLow:
            sensitivity_list += " or negedge %s" % self.reset_port_name
        return sensitivity_list
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    def _format_reset_signal(self) -> str:
        reset_signal = self.reset_port_name
        if self.reset_type == ResetTypeEnum.SyncLow:
            reset_signal = "!" + reset_signal
        elif self.reset_type == ResetTypeEnum.AsyncLow:
            reset_signal = "!" + reset_signal
        return reset_signal
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    def _format_testbench_resets(self) -> Tuple[str, str]:  # (active, inactive)
        if self.reset_type == ResetTypeEnum.SyncHigh or self.reset_type == ResetTypeEnum.AsyncHigh:
            return "1'b1", "1'b0"
        else:
            return "1'b0", "1'b1"
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    def _format_init_value_bin(self) -> str:
        init_value_bin = ""
        for i in range(self.width - 1, -1, -1):
            init_value_bin += "%d" % self.init_value_numpy[0][i]
        return init_value_bin
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _format_tb_ce(ce: bool) -> str:
        return "\n        .ce(1'b1)," if ce else ""
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _format_ce_condition(ce: bool) -> str:
        return " if (ce)" if ce else ""
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _format_ce_port_declaration(ce: bool) -> str:
        return "\n    input ce," if ce else ""
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    def _format_module_name(self, args: Namespace, default_module_name: str) -> str:
        return args.module_name if args.module_name is not None else "%s_%d" % (default_module_name, self.width)
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    def _print_verbose(self, msg: str) -> None:
        if self.verbose:
            print(msg)
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _int0x16(s: str) -> int:
        s = s.lower()  # just in case
        if not s.startswith('0x'):
            raise ValueError
        return int(s, 16)  # can also raise ValueError
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _exit_failure(msg: str) -> None:
        sys.exit(msg)  # this sets the exit code to 1
    # -----------------------------------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------------
# noinspection SpellCheckingInspection
class LFSR_Formatter:

    _template_module = """module {p.module_name} #
(
    parameter [{p.width1}:0] INIT = {p.width}'b{p.init_value_bin}
)
(
    input clk,
    input {p.reset_port_name},{p.clock_enable_port_declaration}
    output [{p.width1}:0] value
);

    reg [{p.width1}:0] lfsr_value = INIT;

    assign value = lfsr_value;

    function  [{p.width1}:0] lfsr_value_next;
        input [{p.width1}:0] lfsr_value_current;
        {p.poly_func}
    endfunction

    always @({p.sensitivity_list})
        //
        if ({p.reset_signal}) lfsr_value <= INIT;
        else{p.clock_enable_condition} lfsr_value <= lfsr_value_next(lfsr_value);

endmodule
"""

    _template_testbench = """`timescale 1ns / 1ps

module tb_{p.module_name};


    //
    // Clock
    //
    reg clk = 1'b0;
    localparam CLOCK_PERIOD = 10.0; // 100 MHz
    initial forever #(0.5 * CLOCK_PERIOD) clk = ~clk;


    //
    // Reset
    //
    reg {p.reset_port_name} = {p.tb_reset_active};


    //
    // UUT
    //
    wire [{p.width1}:0] uut_dout;
    reg  [{p.width1}:0] uut_dout_init;
    {p.module_name} uut
    (
        .clk(clk),
        .{p.reset_port_name}({p.reset_port_name}),{p.tb_clock_enable}
        .value(uut_dout)
    );


    //
    // Script
    //
    integer i;
    initial begin
        $dumpfile("tb_{p.module_name}.vcd");
        $dumpvars(0);
        #(100.0 * CLOCK_PERIOD);
        uut_dout_init = uut_dout;
        #(100.0 * CLOCK_PERIOD);
        {p.reset_port_name} = {p.tb_reset_inactive};
        for (i=0; i<{p.period}; i=i+1)
            #(1.0 * CLOCK_PERIOD);
        if (uut_dout == uut_dout_init)
            $display("Output value after full period matches the initial value - OK");
        else
            $display("Output value after full period doesn't match the initial value - ERROR");
        $finish;
    end


endmodule
    """

    # -----------------------------------------------------------------------------------------------------------------
    class OutputEnum(Enum):
        Module = auto()
        Testbench = auto()
    # -----------------------------------------------------------------------------------------------------------------

    _TemplateDict = {OutputEnum.Module: _template_module,
                     OutputEnum.Testbench: _template_testbench}

    # -----------------------------------------------------------------------------------------------------------------
    @classmethod
    def generate_output(cls, output: OutputEnum, params: LFSR_Params) -> str:
        return cls._TemplateDict[output].format(p=params)
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    @classmethod
    def write_output(cls, output: OutputEnum, verilog: str, params: LFSR_Params) -> None:
        tb_prefix = "tb_" if output == cls.OutputEnum.Testbench else ""
        filename = "%s%s.v" % (tb_prefix, params.module_name)
        with open(filename, 'w') as f:
            f.write(verilog)
    # -----------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------------
# End of File
# ---------------------------------------------------------------------------------------------------------------------
