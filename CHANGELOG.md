# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [TODO]

### Functionality
 - make length of predefined pulse sequences On, Off and Trigger variable

### Bugs
 - Parameters do not refresh when adding parameters in script
 - Plotting off by one data point
 - String representation of abort flag in raw data file broken
 - Plotting and timestamps of by one data point


## [v1.1] - 2023-02-28

### Functionality
 - Data files are sorted into directories
 - Added Device Interface class
 - Added device and measurement imports for scripts
 - Added more units for scripts
 - Added git tag to logging info

### Other
 - Moved parse_traceback and units to measurements

### Bugs
 - Time Stop in Data file was incorrect
 - Set pulsestreamer package requirement to exact match because newer versions seem to be broken


## [v1.0] - 2023-02-20
initial public release
