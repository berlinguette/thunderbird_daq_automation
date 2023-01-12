import re
import struct
from io import BufferedReader
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from data_converter.conversion.support.types import (FileResult, FolderResult,
                                                     Reason)
from data_converter.utilities.logging import set_up_file_logging
from utilities.utilities.logging_helpers.setup_logger import cleanup_logger

HEADER_PATTERN: bytes = b'\xe0\xca'
HEADER_BITMASK: bytes = b'\xf0\xff'
BYTEORDER = 'little'
END_NUMBER_PATTERN = r'^(.*_)(\d+)$'


def convert_bin_file_to_parquet(
    source_file: Path,
    destination: Path | Iterable[Path],
    logfile_path: Path,
    mem_use_threshold: int | None = None
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
        memory use threshold in MB, by default 512 MB
        Memory is used to store decoded rows during conversion. When memory use
        is over the set threshold, stored rows are collected and saved, so 
        memory is free for further use.

    Returns
    -------
    FolderResult
        whether the conversion was successful (as boolean), 
        and a explanatory success/failure message
    """
    # Even though psd data is smaller and could be framed less often,
    # indexing gets simpler when we do both at the same time
    if mem_use_threshold is None:
        mem_use_threshold = 512

    if not source_file.suffix.lower() == '.bin':
        return False, f"File {source_file.name} is not a BIN file"
    max_count = 100_000
    new_logger, new_messenger = set_up_file_logging(source_file, logfile_path)
    source_file_name = _get_destination_file_name(source_file)
    psd_dest_folder, signals_dest_folder = _get_split_data_destinations(
        destination)
    file_result = False
    file_reason = "Not yet set"

    with open(source_file, 'rb') as datafile:
        header = datafile.read(2)
        if not is_header_valid(header):
            cleanup_logger(new_logger)
            return False, source_file.name
        flags = get_header_flags(header)
        wave_samples_flag = flags[3]
        if wave_samples_flag:
            psd_dest_name, signals_dest_name = _get_split_parquet_names(
                source_file_name)
            file_destination = (psd_dest_folder / psd_dest_name,
                                signals_dest_folder / signals_dest_name)
        else:
            psd_dest_name = f"caen_{source_file_name}.parquet"
            file_destination = psd_dest_folder / psd_dest_name

        # First record - set up buffer data structures
        record_array_idx = 0  # current record index in array, reset on array reset
        # current starting record index for next dataframe, reset on file save, used in df indexing
        dataframe_start_idx = 0
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
                mem_used_bytes = sum(
                    [df.memory_usage(deep=True).sum()
                     for df in psd_df_list+signals_df_list]
                )
                mem_used_MB = mem_used_bytes / (1024*1024)
                if mem_used_MB >= mem_use_threshold:
                    file_name_idx = _save_dataframes(
                        file_destination, file_name_idx, wave_samples_flag,
                        psd_df_list, signals_df_list)
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
                    file_destination, file_name_idx, wave_samples_flag,
                    psd_df_list, signals_df_list)
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
                            destination, file_name_idx, wave_samples_flag,
                            psd_df_list, signals_df_list)
                        if reason == Reason.FILE_ENDS:
                            # File ended after PSD data, but signals expected
                            # Invalid end state!
                            file_result = False
                            file_reason = "File ended early"
                            new_messenger.debug(
                                f"File {source_file.name} ended early")
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
                        "Record at expected index " +
                        f"{record_array_idx+dataframe_start_idx} " +
                        f"has {current_n_samples} samples, " +
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
    bitmask = int.from_bytes(HEADER_BITMASK, byteorder=BYTEORDER)
    masked_value = int.from_bytes(value, byteorder=BYTEORDER) & bitmask
    return masked_value.to_bytes(2, BYTEORDER) == HEADER_PATTERN


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
    names = ['BOARD', 'CHANNEL', 'TIMESTAMP']
    formats = [np.uint8, np.uint8, np.uint64]
    if energy_flag:
        names.append('ENERGY')
        formats.append(np.int16)
    if calib_energy_flag:
        names.append('CALIB_ENERGY')
        formats.append(np.float64)
    if energyshort_flag:
        names.append('ENERGYSHORT')
        formats.append(np.int16)
    names.append('FLAGS')
    formats.append(np.uint32)
    if wave_samples_flag:
        names.append('WAVEFORM_CODE')
        formats.append(np.uint8)
    return np.dtype({'names': names, 'formats': formats})


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
    index = pd.RangeIndex(dataframe_start_idx,
                          dataframe_start_idx+records_count)
    psd_df_list.append(pd.DataFrame(psd_array[:records_count], index=index))
    signals_df_list.append(pd.DataFrame(
        signals_array[:records_count], index=index))
    return dataframe_start_idx + records_count


def _save_dataframes(
    destination: Path | Iterable[Path],
    file_idx: int,
    wave_samples_flag: bool,
    psd_df_list: list[pd.DataFrame],
    signals_df_list: list[pd.DataFrame]
) -> int:
    psd_concat = pd.concat(psd_df_list)
    signals_concat = pd.concat(signals_df_list)
    psd_path, signals_path = _get_save_file_names(destination, file_idx)
    psd_concat.to_parquet(psd_path)
    if wave_samples_flag:
        signals_concat.to_parquet(signals_path)
    return file_idx + 1


def _get_save_file_names(
    destination: Path | Iterable[Path],
    file_idx: int
) -> tuple[Path, Path]:
    idx_length = 2
    padded_idx = str(file_idx).zfill(idx_length)
    if isinstance(destination, Path):
        stem = destination.stem
        psd_stem = f"{stem}_{padded_idx}"
        psd_path = destination.with_stem(psd_stem)
        signals_path = destination.with_stem(psd_stem)
    else:
        psd_filename, signals_filename, *_ = destination
        psd_stem = f"{psd_filename.stem}_{padded_idx}"
        signals_stem = f"{signals_filename.stem}_{padded_idx}"
        psd_path = psd_filename.with_stem(psd_stem)
        signals_path = signals_filename.with_stem(signals_stem)
    return psd_path, signals_path


def _get_destination_file_name(source_file: Path) -> str:
    file_number_length = 5  # i.e. run_00000, supports 100,000 files
    pattern = r'.+_\d{' + re.escape(str(file_number_length)) + r'}'
    source_file_name = source_file.stem
    if not re.match(pattern, source_file_name):
        match = re.match(END_NUMBER_PATTERN, source_file_name)
        if match:
            start, number = match.group(1, 2)
            fixed_number = str(number).zfill(file_number_length)
            source_file_name = str(start) + fixed_number
        else:
            starting_file_number = '0'.zfill(file_number_length)
            # source_file_name = source_file_name + '_00000'
            source_file_name = f"{source_file_name}_{starting_file_number}"
    return source_file_name


def _get_split_data_destinations(destination: Path | Iterable[Path]):
    if isinstance(destination, Path):
        # put everything in the same folder, even if signals exists
        psd_destination = destination
        signals_destination = destination
    else:
        psd_destination, *rest = destination
        try:
            signals_destination, *_ = rest
        except ValueError:
            signals_destination = psd_destination
    return psd_destination, signals_destination


def _get_split_parquet_names(source_file_name: str) -> tuple[str, str]:
    psd_dest_name = f"caen_psd_{source_file_name}.parquet"
    signals_dest_name = f"caen_samples_{source_file_name}.parquet"
    return psd_dest_name, signals_dest_name


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
