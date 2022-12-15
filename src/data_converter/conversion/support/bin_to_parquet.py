# read header (16 bits)
# fail if not 0xCAEx
# read last bits to get signal save settings
#   bit 0: Energy saved
#   bit 1: Calib_energy saved
#   bit 2: Energyshort saved
#   bit 3: Waveform samples saved
# create struct/np_array for non-sample data
# create 
# calculate total bit size of these fields:
#   board, channel, timestamp, energy, calib_energy, energyshort, flags, waveform code
# read non-sample bits, decode to struct, add to list
# read n_samples, decode
# use n_samples to read/decode samples, add to list
# convert to DataFrame every X records, add to list
# concat DataFrames every N DataFrame conversions

HEADER_PATTERN = b'\xe0\xca'
HEADER_UPPER_BITMASK = b'\xf0\xff'

def is_header_valid(value: bytes) -> bool:
    """Checks if header follows CAEN binary save file pattern (0xCAE?)

    Parameters
    ----------
    value : bytes
        Header bytes

    Returns
    -------
    bool
        True if header follows expected pattern
    """
    return False  # STUB

def get_energy_flag(header: bytes) -> bool:
    return False  # STUB

def get_calibrated_energy_flag(header: bytes) -> bool:
    return False  # STUB

def get_energyshort_flag(header: bytes) -> bool:
    return False  # STUB

def get_waveform_samples_flag(header: bytes) -> bool:
    return False  # STUB