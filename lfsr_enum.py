# ---------------------------------------------------------------------------------------------------------------------
# lfsr_enum.py
# ---------------------------------------------------------------------------------------------------------------------
# LFSR Enum Module
# ---------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------------
# More Imports
# ---------------------------------------------------------------------------------------------------------------------
from enum import Enum


# ---------------------------------------------------------------------------------------------------------------------
class FeedbackModeEnum(Enum):

    Fibonacci = 'Fibonacci'
    Galois = 'Galois'
# ---------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------------
# noinspection SpellCheckingInspection
class ResetTypeEnum(Enum):

    SyncHigh = 'srst'
    SyncLow = 'srstn'
    AsyncHigh = 'arst'
    AsyncLow = 'arstn'
# ---------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------------
# End of File
# ---------------------------------------------------------------------------------------------------------------------
