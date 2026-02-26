# Thunderbird DAQ Automation

## Overview

This code is designed to convert neutron detector data into Parquet format for easier data processing.

### Supported formats

- CAEN CoMPASS:
  - Binary (.bin)
  - Comma-separated values (.csv)

## System Requirements

### Hardware requirements

The converter requires only a standard computer with sufficient RAM to support in-memory operation on a data set file.

The converter has been successfully run on the following computer configuration:

- Processor: AMD Ryzen 9 5950X 16-core 3.40 GHz
- RAM: 32 GB

### Software requirements

#### OS requirements

The converter is officially supported for Windows. It has been tested on Windows 10 Enterprise version 22H2.

#### Python dependencies

This converter has been tested on Python version 3.10.5. Python package dependencies are given in requirements.txt.

#### Other dependencies

Installation of this code requires git, and has been tested with version 2.42.0.windows.2.

The converter has been tested with data files from the following:

- CAEN CoMPASS version 2.1.0

## Installation

The code lines given for each step must be entered on the Windows command line.

1. Clone the source code
    - `git clone --recursive https://github.com/berlinguette/thunderbird_daq_automation.git`
    - `cd thunderbird_daq_automation`
2. [OPTIONAL] Set up git submodules (only if you omit the `--recursive` flag in Step 1)
    - `git submodule init`
    - `git submodule update`
3. Create and activate Python virtual environment
    - `python -m venv .venv`
    - `.\.venv\Scripts\activate`
4. Install Python dependencies
    - `pip install -r requirements.txt`
5. Create start-up shortcut
    a. Find code folder in File Explorer
        - `start .`
    b. Find file `tbird_data_converter.bat`
    c. Create shortcut
        - Drag file to desired destination while holding down the ALT key, or...
        - Right-click file and choose `Create shortcut`

Installation should typically take 5-10 minutes on a "normal" desktop computer.

## Demo

TODO make demo GIF and add here

## Use instructions

1. Open converter UI (using the shortcut)
   - You will see a blank terminal window for a moment until the UI loads
2. [OPTIONAL] Change settings
   - Click the `Settings` button to open the Settings dialog.
   - In the dialog:
     - Click the `Save` button to save the current settings.
     - Click the `Load` button to load a settings file.
     - Click the `OK` button to confirm settings changes, or the `Cancel` button to discard those changes.
3. Select input data sources
   - Click the `+📁` button to open the Folder Select dialog, where you can select the desired data folders
4. [OPTIONAL] Remove input data sources
   - On the main screen, click a data source in the list, then click the `-` button to remove it.
5. Select output destination
   - Click the `Set Destination` button to open the Destination Select dialog, where you can select the desired destination folder
   - Each converted data source will be saved here in a separate folder per source
6. Start conversion
   - Click the `Start Conversion` button to start conversion
   - The UI will close, and conversion process will be shown on the terminal window
