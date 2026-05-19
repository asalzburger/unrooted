# UNROOTED

This is a python based helper library for displaying data, overlay and compare histograms and other plots.

It follows the following design principle, characterized by the components
- I/O: and I/O layer for loading the data:
    - different formats: ROOT/uproot, Parquet/Arrow, Boost/CSV, etc.
- A data representation known to the library
    - data stored in internal objects based on `numpy`, or `numpy` wrapper classes
- A drawing, displaying module with different backends (default: matplotlib)
    - customization, e.g. by adding detector logos, style, color schemes