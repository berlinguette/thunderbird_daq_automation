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
    mem_use_threshold: int = 14*1024*1024
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
    file_result = False
    file_reason = "Not yet set"

    with open(source_file, 'rb') as datafile:
        header = datafile.read(2)
        if not is_header_valid(header):
            cleanup_logger(new_logger)
            return False, source_file.name
        flags = get_header_flags(header)
        wave_samples_flag = flags[3]

        # First record - set up buffer data structures
        record_array_idx = 0  # current record index in array, reset on array reset
        dataframe_start_idx = 0  # current starting record index for next dataframe, reset on file save, used in df indexing
        file_name_idx = 0  # current file index over all records, incr. on new file
        
        # PSD buffer structures
        psd_struct = _get_psd_struct(*flags)
        psd_dtype = _get_psd_dtype(*flags)
        psd_array = _get_psd_array(max_count, psd_dtype)
        psd_df_list: list[pd.DataFrame] = []

        # Read and store first PSD entry
        result, reason = _store_entry(
            record_array_idx, datafile, psd_struct, psd_array)
        if not result:
            return False, str(reason)  # TODO create better reason string

        # Creating dummy signals buffers simplifies later code
        if wave_samples_flag:
            n_samples = _get_n_samples(datafile)
        else:
            n_samples = 1

        # Signals buffer structures
        signals_struct = struct.Struct(f'{n_samples}h')
        signals_array = _get_signals_array(max_count, n_samples)
        signals_df_list: list[pd.DataFrame] = []

        # Read and store first signals entry
        if wave_samples_flag:
            result, reason = _store_entry(
                record_array_idx, datafile, signals_struct, signals_array)
            if not result:
                return False, str(reason)  # TODO better reason string

        # Loop to read all following entries
        done = False
        while not done:
            record_array_idx += 1  # index now = number of added elements
            if record_array_idx >= max_count:  # need to clear array
                dataframe_start_idx = _store_to_dataframe(
                    dataframe_start_idx, record_array_idx, 
                    psd_df_list, signals_df_list, 
                    psd_array, signals_array)
                psd_array = _get_psd_array(max_count, psd_dtype)
                signals_array = _get_signals_array(max_count, n_samples)
                record_array_idx = record_array_idx % max_count
                # Save to disk if too much memory used
                mem_used = sum(
                    [df.memory_usage(deep=True).sum()
                     for df in psd_df_list+signals_df_list]
                    )
                if mem_used >= mem_use_threshold:
                    file_name_idx = _save_dataframes(
                        destination, file_name_idx, psd_df_list, signals_df_list)
                    psd_df_list = []
                    signals_df_list = []

            # Store PSD entry and handle result
            result, reason = _store_entry(
                record_array_idx, datafile, psd_struct, psd_array)
            if not result:
                done = True
                dataframe_start_idx = _store_to_dataframe(
                    dataframe_start_idx, record_array_idx, 
                    psd_df_list, signals_df_list,
                    psd_array, signals_array)
                file_name_idx = _save_dataframes(
                    destination, file_name_idx, psd_df_list, signals_df_list)
                if reason == Reason.FILE_ENDS:
                    # File ended at end of last record, so valid end state!
                    file_result = True
                    file_reason = "OK"
                    new_messenger.debug(f"Finished reading {source_file.name}")
                elif reason == Reason.INSUFFICIENT_BYTES:
                    file_result = False
                    file_reason = "Insufficient bytes found for last record"
                    new_messenger.debug(file_reason)
                elif reason == Reason.OUT_OF_RANGE:
                    file_result = False
                    file_reason = (
                        f"Tried to store record index {record_array_idx} " + 
                        f"in storage array of length {max_count}"
                        )
                    new_messenger.debug(file_reason)
                else:
                    file_result = False
                    file_reason = f"Unexpected failure reason: {str(reason)}"
                    new_messenger.debug(file_reason)
                continue  # since done = True, loop completes

            # Store wave samples entry and handle result
            if wave_samples_flag:
                # Each entry stores number of signal samples, 
                # but this should be consistent across entries
                # No idea why CAEN does this. Thanks for the complication! >_<
                current_n_samples = _get_n_samples(datafile)
                if current_n_samples == n_samples:
                    result, reason = _store_entry(
                        record_array_idx, datafile, signals_struct, signals_array)
                    if not result:
                        done = True
                        dataframe_start_idx = _store_to_dataframe(
                            dataframe_start_idx, record_array_idx, 
                            psd_df_list, signals_df_list,
                            psd_array, signals_array)
                        file_name_idx = _save_dataframes(
                            destination, file_name_idx, psd_df_list, signals_df_list)
                        if reason == Reason.FILE_ENDS:
                            # File ended after PSD data, but signals expected
                            # Invalid end state!
                            file_result = False
                            file_reason = "File ended early"
                            new_messenger.debug(f"File {source_file.name} ended early")
                        elif reason == Reason.INSUFFICIENT_BYTES:
                            file_result = False
                            file_reason = "Insufficient bytes found for last record"
                            new_messenger.debug(file_reason)
                        elif reason == Reason.OUT_OF_RANGE:
                            file_result = False
                            file_reason = (
                                f"Tried to store record index {record_array_idx} " + 
                                f"in storage array of length {max_count}"
                                )
                            new_messenger.debug(file_reason)
                        else:
                            file_result = False
                            file_reason = f"Unexpected failure reason: {str(reason)}"
                            new_messenger.debug(file_reason)
                        continue  # since done = True, loop completes
                else:
                    # Incorrect number of samples, skip this entry entirely
                    new_messenger.debug(
                        "Record at expected index "+
                        f"{record_array_idx+dataframe_start_idx} "+
                        f"has {current_n_samples} samples, "+
                        f"expected {n_samples}; record was skipped")
                    temp_struct = struct.Struct(f'{current_n_samples}h')
                    datafile.read(temp_struct.size)
                    record_array_idx -= 1  # so next entry overwrites this one

    cleanup_logger(new_logger)
    return file_result, file_reason


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


def get_header_flags(header: bytes) -> tuple[bool, bool, bool, bool]:
    energy_flag = get_energy_flag(header)
    calib_energy_flag = get_calibrated_energy_flag(header)
    energyshort_flag = get_energyshort_flag(header)
    waveform_flag = get_waveform_samples_flag(header)
    return energy_flag, calib_energy_flag, energyshort_flag, waveform_flag


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
    dataframe_start_idx: int, 
    records_count: int, 
    psd_df_list: list[pd.DataFrame],
    signals_df_list: list[pd.DataFrame],
    psd_array: np.ndarray,
    signals_array: np.ndarray
) -> int:
    if records_count == 0:
        return dataframe_start_idx
    index = pd.RangeIndex(dataframe_start_idx, dataframe_start_idx+records_count)
    psd_df_list.append(pd.DataFrame(psd_array[:records_count], index=index))
    signals_df_list.append(pd.DataFrame(signals_array[:records_count], index=index))
    return dataframe_start_idx + records_count


def _save_dataframes(
    destination: Path | Iterable[Path],
    file_idx: int,
    psd_df_list: list[pd.DataFrame],
    signals_df_list: list[pd.DataFrame]
) -> int:
    psd_concat = pd.concat(psd_df_list)
    signals_concat = pd.concat(signals_df_list)
    if isinstance(destination, Path):
        stem = destination.stem
        psd_stem = f"{stem}_psd_{file_idx}"
        signals_stem = f"{stem}_signals_{file_idx}"
        psd_path = destination.with_stem(psd_stem)
        signals_path = destination.with_stem(signals_stem)
    else:
        psd_filename, signals_filename, *_ = destination
        psd_stem = f"{psd_filename.stem}_{file_idx}"
        signals_stem = f"{signals_filename.stem}_{file_idx}"
        psd_path = psd_filename.with_stem(psd_stem)
        signals_path = signals_filename.with_stem(signals_stem)
        pass # TODO handle separate psd/signals filenames
    psd_concat.to_parquet(psd_path)
    signals_concat.to_parquet(signals_path)
    return file_idx + 1


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
