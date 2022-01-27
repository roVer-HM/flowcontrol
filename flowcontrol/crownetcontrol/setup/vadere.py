import logging
import os
import platform
import signal
import subprocess
import threading
import time
from tempfile import NamedTemporaryFile
from urllib.request import urlopen
from xml.etree import ElementTree as xml
import shutil

import glob
from zipfile import ZipFile

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
        self,
        is_start_server=False,
        is_gui_mode=False,
        output_dir="vadere-server-output",
        vadere_server_provider=None,
    ):
        self.server_thread = None
        self.is_start_server = is_start_server
        self.output_dir = output_dir

        self.vadere_server_provider = vadere_server_provider

        self._start_server(is_start_server, is_gui_mode)
        self.domains = VadereControlCommandApi()

    def _server_args(self):
        cmd = ["--single-client"]
        if self._is_gui_mode:
            cmd.extend(["--gui-mode"])
        cmd.extend(["--output-dir", self.output_dir])
        return cmd

    def _start_server(self, is_start_server, is_gui_mode):

        if is_start_server:

            self._is_gui_mode = is_gui_mode

            if is_start_server:
                logging.info(
                    f"Start vadere server automatically. Gui-mode: {is_gui_mode}."
                )

            vadere_path = self.vadere_server_provider.get_jar_file()

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

    def get_server_thread(self):
        return self.server_thread


class VadereServerProvider:
    def __init__(
        self,
        jar_file_path=None,
        path_to_vadere_repo=None,
        is_package_local=True,
        ask_user=True,
        download_dir=None,
    ):
        self.jar_file_path = jar_file_path
        self.repo_path = path_to_vadere_repo
        self.is_package_local = is_package_local
        self.ask_user = ask_user
        self.download_dir = download_dir

    def get_jar_file(self):

        if self.is_package_local:
            self.package_vadere_local()
        else:
            self.download_vadere_jar_file()

        return self.jar_file_path

    def package_vadere_local(self,):

        if not self.is_jar_provided_in_vadere_repo():

            is_package_vadere = True

            if self.ask_user:
                is_package_vadere = query_yes_no(f"Package vadere in {self.repo_path}?")

            if is_package_vadere:

                self._package_vadere()
            else:
                exit("No vadere-server.jar available")

    def _check_pom_file(self):

        pom_file = self.get_pom_file_path()

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
                f"Pom file {pom_file} does not exist. Please check whether path/to/vadere-repo is correct."
            )

        return True

    def _package_vadere(self):

        pom_file = self.get_pom_file_path()
        print(
            "Start to package vadere. This can take several minutes depending on your system."
        )
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

    def download_vadere_jar_file(self, zipurl=None, jar_file = "vadere-server.jar"):

        if self.download_dir is None:
            self.download_dir = os.getcwd()

        working_dir = self.download_dir

        if zipurl is None:
            if platform.system() == "Linux":
                zipurl = "http://www.vadere.org/builds/master/vadere.master.linux.zip"
            elif platform.system() == "Windows":
                zipurl = "http://www.vadere.org/builds/master/vadere.master.windows.zip"
            else:
                raise SystemError("Linux or Windows system required.")

        jar_file_path = os.path.join(working_dir, jar_file)

        if os.path.isfile(jar_file_path):
            print(f"{jar_file} file found: {working_dir}/{jar_file}.")
        else:
            is_download = True

            if self.ask_user:
                is_download = query_yes_no("Download vadere?")

            print(f"Download {jar_file}. Download link: {zipurl}")
            print("Download started .. (this can take a couple of minutes)")
            with urlopen(zipurl) as zipresp, NamedTemporaryFile() as tfile:
                tfile.write(zipresp.read())
                tfile.seek(0)

                # Create a ZipFile Object and load sample.zip in it
                with ZipFile(tfile.name, "r") as zipObj:
                    # Get a list of all archived file names from the zip
                    listOfFileNames = zipObj.namelist()
                    # Iterate over the file names
                    for fileName in listOfFileNames:
                        # Check filename endswith csv
                        if os.path.split(fileName)[-1] == jar_file:

                            # Why not use: zipObj.extract(fileName, path=working_dir) ?
                            # Because the directory structure remains -> we only want to extract the jar-file (not the subdirs)

                            source = zipObj.open(fileName)
                            target = open(
                                os.path.join(working_dir, os.path.split(fileName)[-1]),
                                "wb",
                            )
                            with source, target:
                                shutil.copyfileobj(source, target)

                            print(f"Saved {jar_file} to {os.path.dirname(jar_file_path)}.")

        self.jar_file_path = jar_file_path

    def is_jar_provided_in_vadere_repo(self):

        if self.jar_file_path is not None:
            return os.path.isfile(self.jar_file_path)

        if self.jar_file_path is None and self.repo_path is None:

            print(
                "Neither a vadere-server.jar file nor a path to a local vadere repo is provided."
            )
            print(
                "Check whether a path is defined in enviromental variable VADERE_PATH."
            )
            try:
                self.repo_path = os.environ["VADERE_PATH"]
                print(
                    f"VADERE_PATH is provided. Use {self.repo_path} in the following."
                )
            except:
                raise ValueError(
                    "Add VADERE_PATH to your enviroment variables: VADERE_PATH = /path/to/vadere-repo/"
                )

        print("Check local vadere repo for vadere-server-jar.")
        if self._check_pom_file():
            self.jar_file_path = os.path.join(
                self.repo_path, "VadereManager/target/vadere-server.jar"
            )
            return os.path.isfile(self.jar_file_path)

        return False

    def get_pom_file_path(self):
        if self.repo_path is not None:
            return os.path.join(self.repo_path, "pom.xml")
        else:
            raise ValueError(
                "Please provide a path to vadere repo. Add VADERE_PATH to your your environmental variables"
            )


if __name__ == "__main__":
    pass
