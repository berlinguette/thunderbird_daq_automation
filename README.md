# Thunderbird DAQ Automation

This code is designed to automate general data collection and conversion.

## Installation

This program has been tested with Python 3.10.5.

We recommend using a virtual environment for the required Python packages.

To create a virtual environment run:

```shell
$ python -m venv .venv
```

which will create a new virtual environment at `.venv`.

For Linux/macOS, activate the virtual environment with:

```shell
$ source .venv/bin/activate
```

or for Windows, activate with:

```
> .venv\Scripts\activate
```

Then install the required packages with:

```
$ pip install -r requirements.txt
```

To convert PicoScope data, the PicoScope software must be installed separately.

To more easily install submodules, use the `--recursive` option when using `git clone`.

If cloning normally, set up submodules as follows:

```shell
git submodule init
git submodule update
```

## Utilities Updating

To get all updates to the `utilities` submodule:

```shell
git submodule update --remote --rebase
```

## Running

To run the main data converter program, use the `src/data_converter.py` program.

On Windows, just run the `tbird_data_converter.bat` executable.

For Linux, first activate the virtual environment before running the program:

```shell
$ source .venv/bin/activate
$ python src/data_converter.py
```

## Documentation

Sphinx documentation is located in the `src/docs/` folder. To build the documentation,
navigate to the folder and run:

```
$ make html
```

or 

```
> make.bat
```

for Linux/macOS and Windows, respectively.
Generated documentation will be in the `src/docs/_build` folder, where you can
find the entry point under `_build/html/index.html`.

## Packaging

To package the converter to a Windows executable, just run `src/data_converter_packager.bat` on a Windows machine.
