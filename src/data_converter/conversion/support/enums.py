from enum import Enum


class ExperimentType(Enum):
    CAEN = "CAEN"
    WENDI = "WENDI II"


class CAENDataFormat(Enum):
    CSV = ".csv"
    BIN = ".bin"


class Reason(Enum):
    OK = 'OK'
    FILE_ENDS = 'File ends'
    OUT_OF_RANGE = 'Index out of range'
    INSUFFICIENT_BYTES = 'Not enough bytes read'
