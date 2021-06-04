import sys
import os, glob
from omnetinireader.config_parser import OppConfigFileBase

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")



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