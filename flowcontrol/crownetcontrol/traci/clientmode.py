import logging
import os
import subprocess
import warnings
from time import sleep
from xml.etree import ElementTree as xml

from flowcontrol.crownetcontrol.setup.vadere import Runner
from flowcontrol.crownetcontrol.traci import constants_vadere as tc
from flowcontrol.crownetcontrol.traci.connection import BaseTraCIConnection, _create_client_socket
from flowcontrol.crownetcontrol.traci.connection_manager import TraCiManager


class ClientModeConnection(TraCiManager):
    def __init__(
        self,
        control_handler,
        host="127.0.0.1",
        port=9999,
        is_start_server=False,
        is_gui_mode=False,
        scenario = None
    ):

        super().__init__(host, port, control_handler)
        self._set_connection(BaseTraCIConnection(_create_client_socket()))
        self._con._socket.connect((host, port))


    def _simulation_step(self, step=0.0):
        """
        Make a simulation step and simulate up to the given second in sim time.
        If the given value is 0 or absent, exactly one step is performed.
        Values smaller than or equal to the current sim time result in no action.
        """
        if type(step) is int and step >= 1000:
            warnings.warn(
                "API change now handles step as floating point seconds", stacklevel=2
            )
        result = self._con.send_cmd(tc.CMD_SIMSTEP, None, None, "D", step)
        return self._parse_subscription_result(result)


    def _initialize(self, *arg, **kwargs):

        # default subscriptions
        print("register default subscriptions")
        for listener in self._con.subscriptionListener:
            listener.subscribe(self.domains)
        self._con.notify_subscription_listener()
        if len(self._default_sub.new_pedestrian_ids) > 0:
            print(
                f"new pedestrians found {self._default_sub.new_pedestrian_ids}. Subscribe pedestrians variables"
            )
            self._default_sub.update_pedestrian_subscription(self.domains.v_person)
        self._con.notify_subscription_listener()

        # call controller callback
        self._control_hdl.handle_init(
            self._default_sub.time, self.sub_listener, self._base_client
        )

    def _run(self):
        while self._running:
            self._simulation_step(self._sim_until)
            # no response required for ClientModeConnection
            self._handle_sim_step()
            # clear connection state (for ClientModeConnection _con == _base_client)
            self._con.clear()

            # TODO stop process:  + -> self.server_thread.stop()


    def _handle_sim_step(self):
        # subscription listener already notified. Use default listener to update
        # subscription of new/removed pedestrians because we are the only client
        # and must mange the subscription here.
        self._default_sub.update_pedestrian_subscription(self.domains.v_person)
        self._con.notify_subscription_listener()

        # set current time
        self.current_time = self._default_sub.time

        # self.sub_listener contains state for controller
        self._control_hdl.handle_sim_step(
            self._default_sub.time, self.sub_listener, self._base_client
        )

        # no result expected. Controller should use base_client to trigger control action
        return None



class VadereClientModeConnection(ClientModeConnection):

    def __init__(
            self,
            control_handler,
            host="127.0.0.1",
            port=9999,
            is_start_server=False,
            is_gui_mode=False,
            scenario=None
    ):
        self.is_start_server = is_start_server
        self.scenario = scenario
        self._start_server(is_start_server, is_gui_mode, scenario)

        super().__init__(host, port, control_handler)

    def _initialize(self, *arg, **kwargs):
        print(f"Send scenario file: {self.scenario}")
        self._start_simulation()
        super()._initialize(arg, kwargs)


    def _check_vadere_server_jar_available(self, vadere_man):

        vadere_path = os.environ["VADERE_PATH"]

        if os.path.isfile(vadere_man):
            logging.info(f"Found vadere-server.jar in {os.path.dirname(vadere_man)}.")
        else:
            logging.info(f"Could not find {vadere_man}.")
            pom_file = os.path.join(vadere_path, "pom.xml")

            self._package_vadere(pom_file)
            if os.path.isfile(vadere_man) is False:
                raise FileExistsError(f"Failed to generate {vadere_man}.")


    def _check_pom_file(self, pom_file):

        if os.path.isfile(pom_file):
            pom_file_content = xml.parse(pom_file)
            root = pom_file_content.getroot()
            namesp = root.tag.replace("project", "")
            repo_name = root.find(namesp + "artifactId").text

            if repo_name != "vadere":
                raise ValueError(f"Extract project {repo_name} from pom.xml. Pom file does not belong to vadere project.")
        else:
            raise ValueError(f"Pom file {pom_file} does not exist. Please check whether env var VADERE_PATH is set correctly.")

        return True

    def _package_vadere(self, pom_file):

        if self._check_pom_file(pom_file):
            print(f"Start packaging vadere ... ")
            try:
                command = ["mvn", "clean", "-f", pom_file]
                subprocess.check_call(command, stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                command = [
                    "mvn",
                    "package",
                    "-f",
                    pom_file,
                    "-Dmaven.test.skip=true",
                ]
                subprocess.check_call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print("Finished packaging vadere.")
            except:
                print("Failed to package vadere.")

    def _start_simulation(self):
        if self.scenario.endswith(".scenario"):
            with open(self.scenario, 'r') as f:
                scenario_content = f.read()
        else:
            raise ValueError(f"Scenario file (*.scenario) expexted. Got: {self.scenario}")

        self._con.send_file(self.scenario, scenario_content)

    def _server_args(self):
        cmd = ["--single-client"]
        if self._is_gui_mode:
            cmd.extend(["--gui-mode"])
        return cmd

    def _start_server(self, is_start_server, is_gui_mode, scenario):

        if is_start_server:
            try:
                vadere_path = os.environ["VADERE_PATH"]
            except:
                raise ValueError("Add VADERE_PATH to your enviroment variables.")

            self._is_gui_mode = is_gui_mode
            self.scenario = scenario

            if is_start_server:
                logging.info(f"Start vadere server automatically. Gui-mode: {is_gui_mode}.")

            vadere_man = os.path.join(
                vadere_path,
                "VadereManager/target/vadere-server.jar",
            )

            self._check_vadere_server_jar_available(vadere_man)

            vadere_server_cmd = [
                "java",
                "-jar",
                vadere_man,
            ]
            vadere_server_cmd.extend(self._server_args())
            self.server_thread = Runner(command=vadere_server_cmd, thread_name="Server", )
            print("Start Server Thread...")
            self.server_thread.start()
            sleep(0.8)

            # TODO end?