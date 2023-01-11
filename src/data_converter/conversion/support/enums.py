from enum import Enum


class ExperimentType(Enum):
    PICO = "PicoScope"
    CAEN = "CAEN"
    WENDI = "WENDI II"


class Reason(Enum):
    OK = 'OK'
    FILE_ENDS = 'File ends'
    OUT_OF_RANGE = 'Index out of range'
    INSUFFICIENT_BYTES = 'Not enough bytes read'
