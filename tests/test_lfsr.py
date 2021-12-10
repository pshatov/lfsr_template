# ---------------------------------------------------------------------------------------------------------------------
# test_lfsr.py
# ---------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------------------------------------------------
import pytest


# ---------------------------------------------------------------------------------------------------------------------
# More Imports
# ---------------------------------------------------------------------------------------------------------------------
from pytest import fixture
from lfsr_enum import FeedbackModeEnum
from lfsr_math import LFSR_Math


# ---------------------------------------------------------------------------------------------------------------------
@fixture
def load_polys():

    def _load_polys_helper(width):
        polys = []
        with open('tests/%d.txt' % width) as f:
            f_lines = f.readlines()
        for fl in f_lines:
            polys.append(int(fl.strip(), 16))
        return polys

    return _load_polys_helper
# ---------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------------
def _test_check_poly_max_length_helper(feedback_mode, width, load_polys):

    all_polys = load_polys(width)

    for p in range(2 ** (width - 1), 2 ** width):

        p_numpy = LFSR_Math.int2row(p, width)

        p_ok, _ = LFSR_Math.validate_poly_numpy(p_numpy, width)
        if not p_ok:
            continue

        # TODO: Randomize initial value?

        p_valid, _ = LFSR_Math.check_poly_max_length(feedback_mode, p_numpy, width, LFSR_Math.int2row(1, width))

        # missed max length?
        if not p_valid and p in all_polys:
            return False

        # bogus max length?
        if p_valid and p not in all_polys:
            return False

        # delete
        if p_valid:
            all_polys.remove(p)

    # check, that all polys have been found
    if len(all_polys) > 0:
        return False

    return True
# ---------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------------
def test_helper_check_poly_max_length_8bit(load_polys):
    for f in FeedbackModeEnum:

        # skip galois mode
        if f == FeedbackModeEnum.Galois:
            with pytest.raises(NotImplementedError):
                _test_check_poly_max_length_helper(f, 8, load_polys)
            continue

        _test_check_poly_max_length_helper(f, 8, load_polys)
# ---------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------------
# End of File
# ---------------------------------------------------------------------------------------------------------------------
