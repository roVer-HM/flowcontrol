import logging
import os
import signal
import subprocess
import threading
import time
from time import sleep
from xml.etree import ElementTree as xml

import glob

from flowcontrol.crownetcontrol.traci.domains.VadereControlDomain import (
    VadereControlCommandApi,
)
from flowcontrol.utils.misc import query_yes_no


def get_scenario_content(scenario):
    if scenario.endswith(".scenario"):
        with open(scenario, "r") as f:
            scenario_content = f.read()
    else:
        raise ValueError(f"Scenario file (*.scenario) expexted. Got: {scenario}")
    return scenario_content


class Runner(threading.Thread):
    def __init__(self, command, thread_name, log_location=None, use_stdout=False):
        threading.Thread.__init__(self)
        self.command = command
        self.log_location = log_location
        self.use_stdout = use_stdout
        self.thread_name = thread_name
        self.log = logging.getLogger()

    def stop(self):
        self._cleanup()

    def run(self):
        try:
            if self.log_location is None:
                self.log_location = os.devnull

            log_file = open(self.log_location, "w")
            self.process = subprocess.Popen(
                self.command,
                cwd=os.path.curdir,
                shell=False,
                stdin=None,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            for line in self.process.stdout:
                if self.use_stdout:
                    print(f"{self.thread_name}> {line.decode('utf-8')}", end="")
                log_file.write(line.decode("utf-8"))

            if self.process.returncode is not None:

                self._cleanup()

        finally:
            log_file.close()
            if self.process is not None:
                print(
                    f"{self.thread_name}> subprocess returncode={self.process.returncode}"
                )
                ##TODO: fix


    def _cleanup(self):
        try:
            os.kill(self.process.pid, signal.SIGTERM)
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.log.error("subprocess not stopping. Send SIGKILL")

        if self.process.returncode is None:
            os.kill(self.process.pid, signal.SIGKILL)
            time.sleep(0.5)
            if self.process.returncode is None:
                self.log.error("subprocess still not dead")
                raise


class VadereServer:
    def __init__(
        self, is_start_server=False, is_gui_mode=False, output_dir = "vadere-server-output"
    ):
        self.server_thread = None
        self.is_start_server = is_start_server
        self.output_dir = output_dir
        self._start_server(is_start_server, is_gui_mode)
        self.domains = VadereControlCommandApi()

    def _check_vadere_server_jar_available(self):

        try:
            vadere_path = os.environ["VADERE_PATH"]
            vadere_man = os.path.join(vadere_path, "VadereManager/target/vadere-server.jar")
        except:
            raise ValueError("Add VADERE_PATH to your enviroment variables: VADERE_PATH = /path/to/vadere-repo/")

        if os.path.isfile(vadere_man):
            print(f"Found vadere-server.jar in {os.path.dirname(vadere_man)}.")
        else:
            print(f"Could not find {vadere_man}.")
            pom_file = os.path.join(vadere_path, "pom.xml")

            self._package_vadere(pom_file)
            if os.path.isfile(vadere_man) is False:
                raise FileExistsError(f"Failed to generate {vadere_man}.")
        return vadere_man

    def _check_pom_file(self, pom_file):

        if os.path.isfile(pom_file):
            pom_file_content = xml.parse(pom_file)
            root = pom_file_content.getroot()
            namesp = root.tag.replace("project", "")
            repo_name = root.find(namesp + "artifactId").text

            if repo_name != "vadere":
                raise ValueError(
                    f"Extract project {repo_name} from pom.xml. Pom file does not belong to vadere project."
                )
        else:
            raise ValueError(
                f"Pom file {pom_file} does not exist. Please check whether env var VADERE_PATH is set correctly."
            )

        return True

    def _package_vadere(self, pom_file):

        if self._check_pom_file(pom_file):
            if query_yes_no("Create vadere-server.jar?"):
                print(f"Start packaging vadere ... ")
                try:
                    command = ["mvn", "clean", "-f", pom_file]
                    subprocess.check_call(
                        command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    command = [
                        "mvn",
                        "package",
                        "-f",
                        pom_file,
                        "-Dmaven.test.skip=true",
                    ]
                    subprocess.check_call(
                        command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    print("Finished packaging vadere.")
                except:
                    print("Failed to package vadere.")
            else:
                exit("Please provide vadere-server.jar in vadere repo.")

    def _server_args(self):
        cmd = ["--single-client"]
        if self._is_gui_mode:
            cmd.extend(["--gui-mode"])
        cmd.extend(["--output-dir", self.output_dir])
        return cmd

    def _start_server(self, is_start_server, is_gui_mode, vadere_path = None):

        if is_start_server:

            self._is_gui_mode = is_gui_mode

            if is_start_server:
                logging.info(
                    f"Start vadere server automatically. Gui-mode: {is_gui_mode}."
                )
            #TODO refactor
            if vadere_path is None:
                jar_files = [x for x in glob.glob(os.getcwd() + "/**/vadere-server.jar", recursive = True) if os.path.isfile(x)]
                if len(jar_files) == 1:
                    vadere_path = jar_files[0]
                    print(f"Found vadere-server.jar in {vadere_path}.")
                elif len(jar_files) == 0:
                    print(f"Could not locate vadere-server jar.")
                    if query_yes_no("Package vadere in local vadere-repository [Y] or download [n]?"):
                        vadere_path = self._check_vadere_server_jar_available()
                    else:
                        print("Please run the download script 'download_vadere.py'")
                        print("Then restart the script.")
                        exit(0)

            vadere_server_cmd = [
                "java",
                "-jar",
                vadere_path,
            ]
            vadere_server_cmd.extend(self._server_args())
            self.server_thread = Runner(
                command=vadere_server_cmd, thread_name="Server",
            )
            print("Start Server Thread...")
            self.server_thread.start()
            sleep(2.0)

    def get_server_thread(self):
        return self.server_thread


if __name__ == "__main__":
    pass
