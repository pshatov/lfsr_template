# ---------------------------------------------------------------------------------------------------------------------
# lfsr_math.py
# ---------------------------------------------------------------------------------------------------------------------
# LFSR Math Module
# ---------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------------------------------------------------
import numpy
import sympy  # type: ignore


# ---------------------------------------------------------------------------------------------------------------------
# More Imports
# ---------------------------------------------------------------------------------------------------------------------
from numpy import ndarray
from lfsr_enum import FeedbackModeEnum
from typing import Tuple
from sympy.ntheory import is_mersenne_prime  # type: ignore


# ---------------------------------------------------------------------------------------------------------------------
class LFSR_Math:

    # -----------------------------------------------------------------------------------------------------------------
    @staticmethod
    def period(width: int) -> int:
        return 2 ** width - 1
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    @staticmethod
    def get_int_bit(value: int, index: int) -> int:
        return (value & (1 << index)) >> index
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    @classmethod
    def matrix_gf2(cls, mtx: ndarray, width: int) -> None:
        for x in range(width):
            cls.column_gf2(mtx, width, col=x)
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    @classmethod
    def column_gf2(cls, mtx: ndarray, width: int, col: int = 0) -> None:
        for row in range(width):
            cls._element_gf2(mtx, row, col)
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _element_gf2(mtx: ndarray, row: int, col: int) -> None:
        mtx[row][col] %= 2
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    @classmethod
    def matrix_exponentiate_gf2(cls, mtx: ndarray, pwr: int, width: int) -> ndarray:

        # start with identity matrix
        result = numpy.identity(width, dtype=int)

        base = mtx
        for i in range(width):

            # next exponent bit
            ei = cls.get_int_bit(pwr, i)

            # do the schoolbook right-to-left "square and multiply" exponentiation
            if ei > 0:
                result = numpy.matmul(result, base)
                cls.matrix_gf2(result, width)

            # square the base
            base = numpy.matmul(base, base)
            cls.matrix_gf2(base, width)

        return result
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    @classmethod
    def fast_forward_poly_fibonacci(cls, poly: ndarray, init: ndarray, steps: int, width: int) -> numpy.ndarray:

        # prepare initial value
        init_t = numpy.transpose(init)

        # prepare matrix
        mtx = numpy.zeros([width, width], dtype=int)
        for i in range(0, width - 1):
            mtx[i + 1][i] = 1
        mtx[0] = poly[0]

        # raise matrix to target power
        mtx_pow = cls.matrix_exponentiate_gf2(mtx, steps, width)

        # compute return value
        last = numpy.matmul(mtx_pow, init_t)
        cls.column_gf2(last, width)

        # transpose
        last_t = numpy.transpose(last)
        return last_t
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    @classmethod
    def fast_forward_poly_galois(cls, poly: ndarray, init: ndarray, steps: int, width: int) -> numpy.ndarray:
        raise NotImplementedError
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    @classmethod
    def int2row(cls, value: int, width: int) -> numpy.ndarray:
        ret = numpy.zeros([1, width], dtype=int)
        for index in range(width):
            ret[0][index] = cls.get_int_bit(value, index)
        return ret
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    @staticmethod
    def validate_init_value_int(feedback_mode: FeedbackModeEnum, init_value: int, width: int) -> Tuple[bool, str]:

        if feedback_mode == FeedbackModeEnum.Fibonacci and init_value == 0:
            return False, "All-zeroes state is prohibited in Fibonacci mode!"

        if feedback_mode == FeedbackModeEnum.Galois and init_value == (2 ** width - 1):
            return False, "All-ones state is prohibited in Galois mode!"

        return True, ""
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    @staticmethod
    def validate_poly_numpy(poly: numpy.ndarray, width: int) -> Tuple[bool, str]:

        # highest power must be present
        if poly[0][width - 1] == 0:
            return False, "Polynomial does not have nonzero coefficient for the largest power of x"

        # must have at least two taps
        if numpy.sum(poly[0]) < 2:
            return False, "Polynomial must have at least two feedback taps"

        # number of taps must be even
        if numpy.sum(poly[0]) % 2 > 0:
            return False, "Polynomial must have an even number of feedback taps"

        return True, ""
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    @classmethod
    def fast_forward_poly_wrapper(cls,
                                  feedback_mode: FeedbackModeEnum,
                                  poly: numpy.ndarray, width: int,
                                  init_value: numpy.ndarray,
                                  count: int) -> numpy.ndarray:

        ff_args = poly, init_value, count, width

        if feedback_mode == FeedbackModeEnum.Fibonacci:
            return cls.fast_forward_poly_fibonacci(*ff_args)

        elif feedback_mode == FeedbackModeEnum.Galois:
            return cls.fast_forward_poly_galois(*ff_args)

        else:
            raise RuntimeError
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------
    @classmethod
    def check_poly_max_length(cls,
                              feedback_mode: FeedbackModeEnum,
                              poly: numpy.ndarray, width: int,
                              init_value: numpy.ndarray) -> Tuple[bool, str]:

        period = cls.period(width)

        # compute value after one full period
        last = cls.fast_forward_poly_wrapper(feedback_mode, poly, width, init_value, period)

        # compare
        if not numpy.array_equal(last, init_value):
            return False, "Value after full period doesn't match initial value, not max length"

        else:
            msg = "Value after full period matches initial value (OK)"

        # check sub-periods (if necessary)
        if is_mersenne_prime(period):
            msg += "\nPeriod is prime, no further checks needed"

        else:
            msg += "\nChecking sub-periods..."

            divisors = sympy.divisors(period)[1:-1]
            for d in divisors:
                msg += "  Checking sub-period of %d" % d
                last = cls.fast_forward_poly_wrapper(feedback_mode, poly, width, init_value, d)
                if numpy.array_equal(last, init_value):
                    msg += "    Value after sub-period matches initial value, not max length"
                    return False, msg
                else:
                    msg += "    Value after sub-period doesn't match initial value (OK)"

        return True, ""
    # -----------------------------------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------------
# End of File
# ---------------------------------------------------------------------------------------------------------------------
