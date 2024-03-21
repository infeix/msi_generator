This python script uses wix to create a .msi file from a folder with programm files.

## Requirements

* .NET 6.0 sdk (not runtime)
* wix toolset v4
* python3

* Only tested on a windows machine.

## Steps
1. Download and install .NET:

    https://dotnet.microsoft.com/en-us/download/visual-studio-sdks


2. Install wix:

    - open windows command prompt cmd.exe
    - type the following command:

        `dotnet tool install --global wix`

3. Download and install python:

    https://www.python.org/downloads/

4. Clone Repository:

    `git clone git@bitbucket.org:hvle-sda/msi_generator.git`


# Usage

- open windows command prompt cmd.exe
- navigate to the msi_generator script with cd

    `cd path\to\the\script`

- run the script by typing the following command:

    `python .\msi_generator.py`

- if something went not as you expected then you con check the generated `msi_generator.ini` file 
and change the values for your needs

If you want to use commandline arguments check the help:

`python .\msi_generator.py -h`

The script generates a config file to be able to run it again with the same configuration.

Also check the example configuration. `msi_generator.ini.example`
