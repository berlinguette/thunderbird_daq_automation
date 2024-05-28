# Thunderbird Data Analyzer Frontend

This is the frontend interface for the Thunderbird automatic data analyzer.
It gives users visibility into the conversion/processing status of all experiments stored on the QMI data drive,
as well as allowing them to easily run conversion/processing scripts. The frontend is meant to interface with the backend API server which manages the inventory of experiments.

## Installation

To install dependencies, run `npm install`. The program needs a `.env` file in the root directory - use the provided `.env_example` as a template.

## Running

To start the dev server, run `npm run dev`.

To build for production, run `npm run build` and use `npm run preview` to preview the production build.

## Usage

### Overview

The program automatically keeps track of the analysis status of all experiments in the QMI data drive directory.
Upon navigating to the homepage, users will be presented with a table of all experiments that have been found, as
well as the last-modified times of the folders in each directory.

For example, an experiment may be present in
the `1-Unconverted_Data` directory but not in the `2-Converted_Data` or `3-Output` directories. In this case,
its ID will display the last-modified time of the ID folder in `1-Unconverted_Data` and display "Not Found" for
the other two directories.

### Analyzing

The program is also capable of automatically running analysis scripts for conversion and processing.
Users have the option to analyze all experiment or to select a subset of experiments in the table to analyze.
Furthermore, users can choose to only convert, only process, or do both for the experiments to be analyzed.
The program will attempt to perform the selected operation on the given experiments.


However, if unconverted data for an experiment does not exist or converted data already exists, conversion will be skipped.
Likewise, if converted data for an experiment does not exist or processed data already exists, processing will be skipped.

### Overrides

In order to account for experiment edge cases, overrides can be configured to in order to ignore certain experiments.
For example, experiments matching a certain pattern like `ID-EJ-309-.*` can be overridden so that they always
appear to be present in the inventory no matter what their actual stage of conversion is.
This can allow us to prevent certain experiments from being analyzed.

### Queue

Upon starting analysis for experiments, users can navigate to the Queue page in order to view the current analysis progress.
The queue will display the current experiment being analyzed as well as what stage of analysis it is in (converting/processing). It will also display all experiments that are being queued for analysis.

The Queue page also displays live logs from the backend, which can be used to see details of the experiment analysis.
The logs can be filtered by log level for more or less detail.
