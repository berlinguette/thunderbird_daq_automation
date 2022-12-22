from enum import Enum

class Reason(Enum):
    OK = 'OK'
    FILE_ENDS = 'File ends'
    OUT_OF_RANGE = 'Index out of range'
    INSUFFICIENT_BYTES = 'Not enough bytes read'
    