import re
from pathlib import Path
from typing import Iterable, Optional, Union

from data_converter.conversion.support.abstract_folder_converter import (
    AbstractFolderConverter,
)
from data_converter.conversion.support.bin_folder_to_parquet import (
    BINtoParquetFolderConverter,
)
from data_converter.conversion.support.constants import (
    DUAL_CHANNEL_DATA_PREFIX,
    SINGLE_CHANNEL_DATA_PREFIX,
)
from data_converter.conversion.support.csv_folder_to_parquet import (
    AbstractCSVtoParquetFolderConverter,
    DualChannelCSVConverter,
    SingleChannelCSVConverter,
)
from data_converter.conversion.support.csv_folder_to_parquet_polars import (
    AbstractCSVtoParquetPolarsFolderConverter,
    DualChannelCSVPolarsConverter,
    SingleChannelCSVPolarsConverter,
)
from data_converter.conversion.support.enums import CAENDataFormat, CAENChannelFormat
from utilities.utilities.configuration.configuration import Config


class CSVConverterFactory:
    def make_csv_converter(
        self,
        folder: Path,
        destination: Union[Path, Iterable[Path]],
        config: Config,
        logfile_path: Path,
    ) -> AbstractCSVtoParquetFolderConverter:
        csv_format = self._single_or_dual_channel(folder)
        if csv_format == CAENChannelFormat.SINGLE:
            return SingleChannelCSVConverter(folder, destination, config, logfile_path)
        elif csv_format == CAENChannelFormat.DUAL:
            return DualChannelCSVConverter(folder, destination, config, logfile_path)
        else:
            raise ValueError(
                f"Folder {folder.name} channel type (single/dual) could not be determined"
            )

    def _single_or_dual_channel(self, folder: Path) -> Optional[CAENChannelFormat]:
        single_pattern = re.compile(f"{SINGLE_CHANNEL_DATA_PREFIX}.*")
        dual_pattern = re.compile(f"{DUAL_CHANNEL_DATA_PREFIX}.*")
        contains_single = any(
            (single_pattern.fullmatch(file.name) for file in folder.iterdir())
        )
        contains_dual = any(
            (dual_pattern.fullmatch(file.name) for file in folder.iterdir())
        )
        if contains_single:
            return CAENChannelFormat.SINGLE
        if contains_dual:
            return CAENChannelFormat.DUAL
        return None
    

class CSVPolarsConverterFactory:
    def make_csv_converter(
        self,
        folder: Path,
        destination: Union[Path, Iterable[Path]],
        config: Config,
        logfile_path: Path,
    ) -> AbstractCSVtoParquetPolarsFolderConverter:
        csv_format = self._single_or_dual_channel(folder)
        if csv_format == CAENChannelFormat.SINGLE:
            return SingleChannelCSVPolarsConverter(folder, destination, config, logfile_path)
        elif csv_format == CAENChannelFormat.DUAL:
            return DualChannelCSVPolarsConverter(folder, destination, config, logfile_path)
        else:
            raise ValueError(
                f"Folder {folder.name} channel type (single/dual) could not be determined"
            )

    def _single_or_dual_channel(self, folder: Path) -> Optional[CAENChannelFormat]:
        single_pattern = re.compile(f"{SINGLE_CHANNEL_DATA_PREFIX}.*")
        dual_pattern = re.compile(f"{DUAL_CHANNEL_DATA_PREFIX}.*")
        contains_single = any(
            (single_pattern.fullmatch(file.name) for file in folder.iterdir())
        )
        contains_dual = any(
            (dual_pattern.fullmatch(file.name) for file in folder.iterdir())
        )
        if contains_single:
            return CAENChannelFormat.SINGLE
        if contains_dual:
            return CAENChannelFormat.DUAL
        return None


class FolderConverterFactory:
    def make_folder_converter(
        self,
        folder: Path,
        destination: Union[Path, Iterable[Path]],
        config: Config,
        logfile_path: Path,
    ) -> AbstractFolderConverter:
        folder_format = self._determine_folder_contents(folder)
        if folder_format == CAENDataFormat.CSV:
            return CSVConverterFactory().make_csv_converter(
                folder, destination, config, logfile_path
            )
            # return CSVPolarsConverterFactory().make_csv_converter(
            #     folder, destination, config, logfile_path
            # )
        elif folder_format == CAENDataFormat.BIN:
            return BINtoParquetFolderConverter(
                folder, destination, config, logfile_path
            )
        else:
            raise ValueError(f"Folder {folder.name} contained unsupported file type")

    def _determine_folder_contents(self, folder: Path) -> Optional[CAENDataFormat]:
        bin_pattern = re.compile(r".*\.bin", flags=re.IGNORECASE)
        csv_pattern = re.compile(r".*\.csv", flags=re.IGNORECASE)
        contains_bin = any(
            (bin_pattern.fullmatch(file.name) for file in folder.iterdir())
        )
        contains_csv = any(
            (csv_pattern.fullmatch(file.name) for file in folder.iterdir())
        )
        if contains_bin:
            return CAENDataFormat.BIN
        if contains_csv:
            return CAENDataFormat.CSV
        return None  # STUB
