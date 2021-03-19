import os, glob
from .config_parser import OppConfigFileBase

# author: Christina Maria Mayr


def get_abs_path(scenario_name):

    if os.path.isfile(scenario_name):
        return os.path.abspath(scenario_name)
    else:
        print(f"File {os.path.abspath(scenario_name)} not found. Search in directory.")
        scenario_files = glob.glob(os.getcwd() + f"/**/{scenario_name}", recursive=True)
        if len(scenario_files) == 0:
            raise ValueError(f"Scenario file {scenario_name} not found.")
        elif len(scenario_files) > 1:
            raise ValueError(f"Multiple scenario files found: {scenario_files}")
        return scenario_files[0]


def get_scenario_file(file_path, config="final"):

    if file_path.endswith(".ini"):
        print(f"File {os.path.abspath(file_path)} not found. Search in directory.")
        ini_files = glob.glob(os.getcwd() + f"/**/{file_path}", recursive=True)
        if len(ini_files) != 1:
            raise ValueError(f"Ini file {file_path} not found in {os.getcwd()}.")

        opp_file = OppConfigFileBase.from_path(ini_files[0], config=config)
        file_path = opp_file["*.traci.launcher.vadereScenarioPath"].strip('"')
        return get_abs_path(file_path)

    elif file_path.endswith(".scenario"):
        return get_abs_path(file_path)
    else:
        raise ValueError(
            f"Vadere scenario file *.scenario or omnetpp inifile *.ini required. Got {file_path}."
        )
