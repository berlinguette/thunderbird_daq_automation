# Thunderbird DAQ Automation

This code is designed to automate general data collection and conversion.

## Installation

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

## Packaging

To package the converter to a Windows executable, just run `src/data_converter_packager.bat` on a Windows machine.
