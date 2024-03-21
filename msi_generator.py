#!/usr/bin/env python3

import os
import uuid
from subprocess import check_output
import argparse
import configparser

def find_file(path: str, seachstring: str):
    """
    Find the first file name matching a seachstring.
    Returns the path.
    """
    for root, directories, files in os.walk(path):
        for file in files:
            if seachstring in file:
                return root + "\\" + file
    return None

def create_folders_dict(folders_dict = None, path_elements: list = [], file_name = None, folder_name = None):
    """
    This method creates and fills a python dict structure as preparation for the xml-Nodes recursivly.
    The dict structure includes for every folder all child folders and the files inside. {"folders": {}, "files": [], "folder_name": "name1"}
    """
    if not type(folders_dict) == dict:
        folders_dict = {"folders": {}, "files": []}
    if folder_name:
        folders_dict["folder_name"] = folder_name
    if len(path_elements) > 0:
        new_path_elements = path_elements[1:]
        folder_name= path_elements[0]
        if folder_name in folders_dict["folders"]:
            result = create_folders_dict(folders_dict= folders_dict["folders"][folder_name], path_elements= new_path_elements, file_name= file_name, folder_name= folder_name)
        else:
            result = create_folders_dict(path_elements= new_path_elements, file_name= file_name, folder_name= folder_name)
        folders_dict["folders"][folder_name] = result
    if len(path_elements) == 0 and file_name:
        folders_dict["files"].append(file_name)
    return folders_dict


# global
directory_ids = []
def xml_dictionary(dirs = "", src = {}, features = ""):
    """
    This method creats xml nodes for the wxs File.
    """
    global directory_ids
    folder_name = src.get("folder_name", "NameNotDefined")

    directory_id = folder_name.replace("-", "_")
    if (src.get("files", []) or src.get("folders")) and folder_name != "root":
        id_index = 1
        while directory_id in directory_ids:
            id_index +=1
            directory_id = folder_name.replace("-", "_") + str(id_index)
        directory_ids.append(directory_id)
        dirs += f"                <Directory Id=\"{directory_id}Folder\" Name=\"{folder_name}\">\n"

    if src.get("files", []):
        ComponentUuid = str(uuid.uuid4())
        dirs += f"                <Component Id=\"{directory_id}FolderComponent\" Guid=\"{ComponentUuid}\">\n"
        features += f"            <ComponentRef Id=\"{directory_id}FolderComponent\"/>\n"
        for file in src.get("files", []):
            dirs += f"                <File Source=\"{arg_app_source_folder}\\{file}\"/>\n"
        dirs += "                </Component>\n"

    if type(src) == dict and src.get("folders"):
        folders = src.get("folders", [])
        for folder_n in src.get("folders", []):
            dirs, features = xml_dictionary(dirs, folders[folder_n], features)

    if (src.get("files", []) or src.get("folders")) and folder_name != "root":
        dirs += f"                </Directory>\n"
    return dirs, features



arguments = {
        "company": { "help": "Put the company name of the manufacturer of the software"},
        "app": { "help": "Put the name of the software/app"},
        "version": { "help": "Put the version of the software/app"},
        "source": { "help": "Put the path to the directory where the needed files are located"},
        "desktop_shortcut": { "help": "Put the path to the desktop shortcut [optional but recommended]"},
        "icon_file": { "help": "Put the path to the icon file (.ico) [optional but recommended]"}
    }

prog_name = "msi_generator"
prog_description = 'Msi generator will create a .msi file for you.'
prog_epilog = 'It creates automaticly a wix configuration file. It runs wix build command and creates .wixpdb, .cab and a .msi file. It creats a config file automaticly from your input. It should be easy to use.'

parser = argparse.ArgumentParser(
                    prog=prog_name,
                    description=prog_description,
                    epilog=prog_epilog)

for arg_id in arguments:
    parser.add_argument('-' + arg_id[0], '--' + arg_id, help=arguments[arg_id]["help"] )

args = parser.parse_args()

# Look in the command-line arguments for missing arguments
for arg_id in arguments:
    arguments[arg_id]["value"] = getattr(args, arg_id)


###### Look in config file for missing arguments
################################################

arg_app_name = arguments.get("app", {}).get("value")
ini_file_name = prog_name
if arg_app_name:
    ini_file_name = arg_app_name
if os.path.isfile(f"{ini_file_name}.ini"):
    config = configparser.ConfigParser()
    config.read(f"{ini_file_name}.ini")

    for (config_key, config_val) in config.items("MAIN"):
        if not config_key in arguments or not arguments[config_key].get("value"):
            if config_key != "version":
                arguments[config_key] = {"value": config["MAIN"][config_key]}


###### Ask the user for missing arguments
#########################################

for arg_id in arguments:
    if not arguments[arg_id].get("value"):
        print(arguments[arg_id]["help"])
        print(">", end="")
        arguments[arg_id]["value"] = input()


###### Search for missing files
###############################

if not arguments.get("upgrade_code", {}).get("value"):
    upgrade_code = str(uuid.uuid4())
    arguments["upgrade_code"] = {"value": upgrade_code}

if not arguments.get("output_file", {}).get("value"):
    arguments["output_file"] = {"value": "components.wxs"}

if not arguments.get("icon_file", {}).get("value"):
    if os.path.isfile("icon.ico"):
        arguments["icon_file"] = {"value": "icon.ico"}
    else:
        icon_file = find_file(path=arguments.get("source",{}).get("value"), seachstring=".ico")
        if icon_file:
            arguments["icon_file"] = {"value": icon_file}

if not arguments.get("desktop_shortcut", {}).get("value"):
    desktop_shortcut = find_file(path=arguments.get("source",{}).get("value"), seachstring=".lnk")
    if desktop_shortcut:
        arguments["desktop_shortcut"] = {"value": desktop_shortcut}

arg_app_manufacturer    = arguments["company"]["value"]
arg_app_name            = arguments["app"]["value"]
arg_app_version         = arguments["version"]["value"]
arg_app_source_folder   = arguments["source"]["value"]
config_output_file      = arguments["output_file"]["value"]
config_app_upgrade_code = arguments["upgrade_code"]["value"]


###### write a config file
##########################

config = configparser.ConfigParser()
config['MAIN'] = {}

for arg_id in arguments:
    if arg_id in arguments and arguments[arg_id].get("value"):
        config['MAIN'][arg_id] = arguments[arg_id].get("value")

with open('msi_generator.ini', 'w') as configfile:
    config.write(configfile)

with open(f'{arg_app_name}.ini', 'w') as configfile:
    config.write(configfile)


###### ICON FILE WIX XML PARTS
##############################

icon_file_xml = ""
config_icon_file = arguments["icon_file"].get("value")
if config_icon_file and os.path.isfile(config_icon_file):
    icon_file_xml = f"""<Icon Id="icon_file" SourceFile="{config_icon_file}"/>
        <Property Id="ARPPRODUCTICON" Value="icon_file" />"""
    print("Icon file: " + config_icon_file)
if not icon_file_xml:
    print(f"Warning: No icon file found. You have multiple options:")
    print("* put a icon.ico file in the folder of this script")
    print("* put one .ico file in the <source>-folder")
    print(f"* put a configuration line like \"icon_file = c:\\path\\to\\fcon_file.ico\" in {prog_name}.ini")
    print()


###### DESKTOP SHORTCUT WIX XML PARTS
#####################################

desktop_shortcut_uuid = str(uuid.uuid4())
menu_folder_shortcut_uuid = str(uuid.uuid4())
menu_folder_shortcut_xml = ""
desktop_shortcut_xml = ""
component_desktop_shortcut_xml = ""
component_menu_folder_shortcut_xml = ""
config_desktop_shortcut = arguments.get("desktop_shortcut",{}).get("value")
if config_desktop_shortcut and os.path.isfile(config_desktop_shortcut):
    print("Desktop Shortcut file: " + config_desktop_shortcut)
    menu_folder_shortcut_xml = f"""<StandardDirectory Id="ProgramMenuFolder">
        <Component Id="ApplicationShortcut" Guid="{menu_folder_shortcut_uuid}">
            <File Source="{config_desktop_shortcut}"/>
        </Component>
    </StandardDirectory>"""
    desktop_shortcut_xml = f"""<StandardDirectory Id="DesktopFolder">
            <Component Id="DesktopShortCut" Guid="{desktop_shortcut_uuid}">
                <File Source="{config_desktop_shortcut}"/>
            </Component>
        </StandardDirectory>"""
    component_menu_folder_shortcut_xml = "<ComponentRef Id=\"ApplicationShortcut\"/>"
    component_desktop_shortcut_xml = "<ComponentRef Id=\"DesktopShortCut\"/>"
if not desktop_shortcut_xml:
    print(f"Warning: No DesktopShortcut found. You have multiple options:")
    print("* put one .lnk file in the <source>-folder")
    print(f"* put a configuration line like \"desktop_shortcut = c:\\path\\to\\desktop_shortcut.lnk\" in {prog_name}.ini")
    print()


###### find APP FILES
#####################

path = arg_app_source_folder
folder_dict = {"folders": {}, "files": [], "folder_name": "root"}
for root, directories, files in os.walk(path):
    for file in files:
        file_path = os.path.join(root, file)
        if not os.path.isdir(file_path):
            relative_file_path = file_path.replace(arg_app_source_folder + "\\", "")
            file_path_splited = relative_file_path.split("\\")
            path_elements = file_path_splited[:-1]

            folder_dict = create_folders_dict(folders_dict= folder_dict, path_elements= path_elements, file_name= relative_file_path, folder_name= "root")


###### APP FILES AS WIX XML PARTS
#################################

xml_dictionaries, xml_features = xml_dictionary(src=folder_dict)


###### Create xml for wxs file
##############################

print("creating wxs ... ", end="", flush=True)
if not os.path.isdir(arg_app_source_folder):
    print("Error. Source folder not found.")
    exit()

file_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
file_content += '<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">\n'
file_content += f"""    <Package Name="{arg_app_name} {arg_app_version}" Manufacturer="{arg_app_manufacturer}" UpgradeCode="{config_app_upgrade_code}" Version="{arg_app_version}" Scope="perMachine" Compressed="yes" >
        {icon_file_xml}
        <MediaTemplate EmbedCab="yes" />
        <MajorUpgrade DowngradeErrorMessage = "A newer version of {arg_app_name} is already installed." />
        <StandardDirectory Id="ProgramFilesFolder">
            <Directory Id="{arg_app_manufacturer}Folder" Name="{arg_app_manufacturer}">
{xml_dictionaries}            </Directory>
        </StandardDirectory>
        {menu_folder_shortcut_xml}
        {desktop_shortcut_xml}
        <Feature Id="Main">
            {component_menu_folder_shortcut_xml}
            {component_desktop_shortcut_xml}
{xml_features}
        </Feature>
    </Package>
</Wix>
"""


###### write wxs file
#####################

f = open(config_output_file, "w", encoding='utf-8')
f.write(file_content)
f.close()
print("Done")


###### run wix build
####################

print("creating msi ... ", end="", flush=True)
try:
    check_output(f"wix build components.wxs -o setup_{arg_app_name}_{arg_app_version}.msi", shell=True)
except Exception as e:
    if e.output:
        print(e.output)
        #print(e.output.decode('utf-8'))
    else:
        print(e)
print("Done")


###### Cleanup
##############

print("Cleanup ... ", end="", flush=True)
for root, directories, files in os.walk("."):
    for file in files:
        if root == "." and (".cab" in file or ".wixpdb" in file):
            os.remove(root + "\\" + file)
print("Done")
