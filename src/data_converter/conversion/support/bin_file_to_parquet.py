from pathlib import Path
from typing import Iterable
from data_converter.utilities.logging import set_up_file_logging
from data_converter.conversion.support.types import FolderResult, FileResult, Reason
from utilities.utilities.logging_helpers.setup_logger import cleanup_logger
import struct
import numpy as np
from io import BufferedReader
import pandas as pd

HEADER_PATTERN: bytes = b'\xe0\xca'
HEADER_BITMASK: bytes = b'\xf0\xff'
BYTEORDER = 'little'


def convert_bin_file_to_parquet(
    source_file: Path,
    destination: Path | Iterable[Path],
    logfile_path: Path,
    mem_use_threshold: int = 64*1024*1024
) -> FolderResult:
    """Converts CAEN binary (.BIN) format file to Parquet format

    Parameters
    ----------
    source_file : Path
        Path to source BIN file
    destination : Path | Iterable[Path]
        Desired path to converted Parquet file
    logfile_path : Path
        Path to log file used during conversion
    mem_use_threshold : int, optional
        memory use threshold in bytes, by default 64 MB
        Memory is used to store decoded rows during conversion. When memory use
        is over the set threshold, stored rows are collected and saved, so 
        memory is free for further use.

    Returns
    -------
    FileConversionResult
        _description_
    """
    # Even though psd data is smaller and could be framed less often,
    # indexing gets simpler when we do both at the same time
    max_count = 100_000
    new_logger, new_messenger = set_up_file_logging(source_file, logfile_path)

    with open(source_file, 'rb') as datafile:
        header = datafile.read(2)
        if not is_header_valid(header):
            cleanup_logger(new_logger)
            return False, source_file.name
        energy_flag = get_energy_flag(header)
        calib_energy_flag = get_calibrated_energy_flag(header)
        energyshort_flag = get_energyshort_flag(header)
        wave_samples_flag = get_waveform_samples_flag(header)
        flags = energy_flag, calib_energy_flag, energyshort_flag, wave_samples_flag

        # First record - set up buffer data structures
        idx = 0
        file_idx = 0
        # psd_df_idx_start = 0
        psd_struct = _get_psd_struct(*flags)
        psd_dtype = _get_psd_dtype(*flags)
        psd_array = _get_psd_array(max_count, psd_dtype)
        psd_df_list: list[pd.DataFrame] = []

        result, reason = _store_entry(idx, datafile, psd_struct, psd_array)
        if not result:
            return False, str(reason)  # TODO create better reason string

        if wave_samples_flag:
            n_samples = _get_n_samples(datafile)
        else:
            n_samples = 1

        # signals_df_idx_start = 0
        signals_struct = struct.Struct(f'{n_samples}h')
        signals_array = _get_signals_array(max_count, n_samples)
        signals_df_list: list[pd.DataFrame] = []

        if wave_samples_flag:
            result, reason = _store_entry(
                idx, datafile, signals_struct, signals_array)
            if not result:
                return False, str(reason)  # TODO better reason string

        done = False
        while not done:
            # TODO iterate over datafile, storing psd and signals each time
            idx += 1
            if idx >= max_count:
                _store_to_dataframe(
                    psd_df_list, signals_df_list, psd_array, signals_array)
                psd_array = _get_psd_array(max_count, psd_dtype)
                signals_array = _get_signals_array(max_count, n_samples)

            result, reason = _store_entry(
                idx, datafile, psd_struct, psd_array)
            if not result:
                if reason in [Reason.FILE_ENDS, Reason.INSUFFICIENT_BYTES]:
                    _store_to_dataframe(
                        psd_df_list, signals_df_list, psd_array, signals_array)
                    _save_dataframes(
                        destination, file_idx, psd_df_list, signals_df_list)
                    if reason == Reason.FILE_ENDS and not wave_samples_flag:
                        return True, ""
                        pass  # TODO check if file end is valid, return
                    pass  # TODO move all data to dataframes, save, return
                pass  # TODO check for end of file
            #  TODO check if n_samples matches
            if wave_samples_flag:
                result, reason = _store_entry(
                    idx, datafile, signals_struct, signals_array)
                if not result:
                    pass  # TODO check for end of file

    # use n_samples to read/decode samples, add to list
    # convert to DataFrame every X records, add to list
    # concat DataFrames every N DataFrame conversions
    cleanup_logger(new_logger)
    return False, ''  # STUB


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
    bitmask = int.from_bytes(HEADER_BITMASK, byteorder='little')
    masked_value = int.from_bytes(value, byteorder='little') & bitmask
    return masked_value == HEADER_PATTERN


def get_energy_flag(header: bytes) -> bool:
    return _get_flag(header, '0b0001')


def get_calibrated_energy_flag(header: bytes) -> bool:
    return _get_flag(header, '0b0010')


def get_energyshort_flag(header: bytes) -> bool:
    return _get_flag(header, '0b0100')


def get_waveform_samples_flag(header: bytes) -> bool:
    return _get_flag(header, '0b1000')


def _get_psd_struct(
    energy_flag: bool,
    calib_energy_flag: bool,
    energyshort_flag: bool,
    wave_samples_flag: bool
) -> struct.Struct:
    en = 'h' if energy_flag else ''
    ce = 'd' if calib_energy_flag else ''
    es = 'h' if energyshort_flag else ''
    wf = 'B' if wave_samples_flag else ''
    format_string = f'<HHQ{en}{ce}{es}L{wf}'
    return struct.Struct(format_string)


def _get_psd_dtype(
    energy_flag: bool,
    calib_energy_flag: bool,
    energyshort_flag: bool,
    wave_samples_flag: bool
) -> np.dtype:
    dtype_list = [('BOARD', np.uint8), ('CHANNEL', np.uint8),
                  ('TIMESTAMP', np.uint64)]
    if energy_flag:
        dtype_list.append([('ENERGY', np.int16)])
    if calib_energy_flag:
        dtype_list.append([('CALIB_ENERGY', np.float64)])
    if energyshort_flag:
        dtype_list.append([('ENERGYSHORT', np.int16)])
    dtype_list.append([('FLAGS', np.uint32)])
    if wave_samples_flag:
        dtype_list.append([('WAVEFORM_CODE', np.uint8)])
    return np.dtype(dtype_list)


def _get_psd_array(count: int,
                   dtype: np.dtype) -> np.ndarray:
    psd_array = np.zeros(count, dtype=dtype)
    return psd_array


def _store_entry(index: int,
                 data_file: BufferedReader,
                 data_struct: struct.Struct,
                 data_array: np.ndarray) -> FileResult:
    b = data_file.read(data_struct.size)
    if b:
        try:
            decoded = data_struct.unpack(b)
            data_array[index] = decoded
        except struct.error:
            return False, Reason.INSUFFICIENT_BYTES
        except IndexError:
            return False, Reason.OUT_OF_RANGE
        return True, Reason.OK
    else:
        return False, Reason.FILE_ENDS


def _store_to_dataframe(
    psd_df_list: list[pd.DataFrame],
    signals_df_list: list[pd.DataFrame],
    psd_array: np.ndarray,
    signals_array: np.ndarray
):
    psd_df_list.append(pd.DataFrame(psd_array))
    signals_df_list.append(pd.DataFrame(signals_array))


def _save_dataframes(
    destination: Path | Iterable[Path],
    file_idx: int,
    psd_df_list: list[pd.DataFrame],
    signals_df_list: list[pd.DataFrame]
):
    # concats dataframes in list, saves to parquet
    pass  # STUB


def _get_n_samples(data_file: BufferedReader) -> int:
    n_samples_struct = struct.Struct('<L')
    b = data_file.read(n_samples_struct.size)
    n_samples = n_samples_struct.unpack(b)[0]
    return n_samples


def _get_signals_array(count: int, n_samples: int) -> np.ndarray:
    signals_dtype_list = [(str(i), np.int16) for i in range(n_samples)]
    signals_dtype = np.dtype(signals_dtype_list)
    signals_array = np.zeros(100_000, dtype=signals_dtype)
    return signals_array


def _get_flag(header: bytes, mask: str) -> bool:
    mask_int = int(mask, 2)
    return int.from_bytes(header, byteorder=BYTEORDER) & mask_int == mask_int
