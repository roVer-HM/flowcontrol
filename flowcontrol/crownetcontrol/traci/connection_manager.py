import argparse
import logging
import signal
import threading
import warnings
from typing import Union
import os
import subprocess
import time
from time import sleep
import xml.etree.ElementTree as xml

from flowcontrol.crownetcontrol.traci import constants_vadere as tc
from flowcontrol.crownetcontrol.traci.connection import (
    _create_accept_server_socket,
    WrappedTraCIConnection,
    DomainHandler,
    BaseTraCIConnection,
    _create_client_socket,
)
from flowcontrol.crownetcontrol.traci.exceptions import (
    FatalTraCIError,
    TraCISimulationEnd,
)
from flowcontrol.crownetcontrol.traci.subsciption_listners import (
    SubscriptionListener,
    VaderePersonListener,
)


def parse_args_as_dict(args=None):
    # parse arguments
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-n",
        "--host-name",
        dest="host_name",
        default="vadere",  # TODO: discuss -> defaults
        required=True,
        help="If vadere is set, the controller is started in client-mode",
    )

    parser.add_argument(
        "-p",
        "--port",
        dest="port",
        default=9999,
        required=True,
        help="Client: 9999, server: 9997?",
        type=int,
    )

    parser.add_argument(
        "--client-mode",
        dest="is_in_client_mode",
        action="store_true",
        default=False,
        required=False,
        help="Additional information.",  # TODO: redundant?
    )

    parser.add_argument(
        "--gui-mode",
        dest="gui_mode",
        action="store_true",
        default=False,
        required=False,
        help="Only available when server is started automatically.",
    )

    parser.add_argument(
        "--start-server",
        dest="start_server",
        action="store_true",
        default=False,
        required=False,
        help="Only available when server is started automatically.",
    )
    parser.add_argument(
        "-s",
        "--scenario",
        dest="scenario_file",
        default="",  # TODO: discuss -> defaults
        required=False,
        help="Only available in client-mode.",
    )


    if args is None:
        ns = vars(parser.parse_args())
    else:
        ns = vars(parser.parse_args(args))

    if ns["start_server"] is True and ns["is_in_client_mode"] is False:
        raise ValueError(
            "Start server option is only available in client-mode. Set --client-mode option."
        )

    if ns["start_server"] is False and ns["gui_mode"] is True:
        raise ValueError(
            "Gui mode is only available if the server is started automatically. Set --start-server option."
        )

    if ns["start_server"] is True and ns["scenario_file"] is None:
        raise ValueError("Please provide scenario file.")

    if ns["is_in_client_mode"] is True and ns["scenario_file"] is None:
        raise ValueError("Please provide scenario file.")

    return ns


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
            print(
                f"{self.thread_name}> subprocess returncode={self.process.returncode}"
            )

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


class TraCiManager:
    def __init__(self, host, port, control_handler):
        self.host = host
        self.port = port
        self._running = False
        self._control_hdl = control_handler
        self.domains: DomainHandler = DomainHandler()
        self.sub_listener = {}
        self.current_time = -1
        self._sim_until = -1
        self._default_sub: Union[None, VaderePersonListener] = None

    def _set_connection(self, connection):
        self._con = connection
        self._base_client: BaseTraCIConnection = self._con
        self.domains.register(self._base_client)

    def next_call_in(self, step=-1):
        if step <= 0:
            self._sim_until = -1
        else:
            self._sim_until = self.current_time + step

    def next_call_at(self, step=-1):
        if step <= 0:
            self._sim_until = -1
        else:
            self._sim_until = step

    def register_subscription_listener(
        self, name, listener: SubscriptionListener, set_default=False
    ):
        self.sub_listener[name] = listener
        if set_default:
            self._default_sub = listener

    def unregister_subscription_listener(self, name):
        if name in self.sub_listener:
            del self.sub_listener[name]

    def _init_sub_listener(self):
        for name, listener in self.sub_listener.items():
            print(f"register listener {name}")
            self._con.add_sub_listener(listener)

    def _initialize(self, *arg, **kwargs):
        pass

    def _parse_subscription_result(self, result):
        for subscriptionResults in self._con.subscriptionMapping.values():
            subscriptionResults.reset()
        num_subs = result.readInt()
        responses = []
        while num_subs > 0:
            responses.append(self._con.read_subscription(result))
            num_subs -= 1
        self._con.notify_subscription_listener()
        return responses

    def _handle_sim_step(self):
        pass

    def _run(self):
        pass

    def _cleanup(self):
        pass

    def start(self):
        try:
            self._init_sub_listener()
            self._initialize()
            self._running = True
            self._run()
        except NotImplementedError as e:
            print(e)
        except TraCISimulationEnd as sim_end:
            print("Simulation end reached.")
        finally:
            self._cleanup()


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
        self.is_start_server = is_start_server
        self.scenario = scenario
        self._start_server(is_start_server, is_gui_mode, scenario)

        # TODO remove
        print("sleep ... 20 sec")
        time.sleep(20)


        super().__init__(host, port, control_handler)
        self._set_connection(BaseTraCIConnection(_create_client_socket()))

        print((host, port))
        self._con._socket.connect((host, port))

        #self._start_simulation()



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
            self.server_thread = Runner(command=vadere_server_cmd, thread_name="Server",)
            print("Start Server Thread...")
            self.server_thread.start()
            sleep(0.8)

    def _initialize(self, *arg, **kwargs):

        print(f"Send scenario file: {self.scenario}")
        self._start_simulation()

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

    def _server_args(self):
        cmd = ["--single-client"]
        if self._is_gui_mode:
            cmd.extend(["--gui-mode"])
        return cmd

    def _start_simulation(self):
        if self.scenario.endswith(".scenario"):
            with open(self.scenario, 'r') as f:
                scenario_content = f.read()
        else:
            raise ValueError(f"Scenario file (*.scenario) expexted. Got: {self.scenario}")

        self._con.send_file(self.scenario, scenario_content)



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







class ServerModeConnection(TraCiManager):
    def __init__(self, control_handler, host="127.0.0.1", port=9997):
        super().__init__(host, port, control_handler)
        self.server_port = -1

    def _initialize(self, *arg, **kwargs):
        data = kwargs["data"]
        self._control_hdl.handle_init(
            self._default_sub.time, self.sub_listener, self._base_client
        )
        return b"ACK/NACK"

    def _run(self):
        while self._running:
            # wait for command
            action, data = self._con.recv_control()

            if action == "init":
                # response: simple act
                # data contains scenario files and omnetpp init.
                response = self._initialize(data=data)
            elif action == "sim_step":
                # data contains subscription result
                subscription_result = self._base_client.parse_subscription_result(data)
                # response: None
                self._handle_sim_step(subscription_result)
                response = b"ACK/NACK"
            else:
                raise FatalTraCIError("unknown command")

            if response is not None:
                # todo
                self._con.send_control_response(response, "bar")

            # clear state
            self._base_client._string = bytes()
            self._base_client._queue = []

        self._con.close()
        logging.info("connection closed.")

    def start(self):
        try:
            # Connection is controlled by OMNeT++ move _initialize() into _run()
            _, _socket, _, _server_port = _create_accept_server_socket(
                self.host, self.port
            )
            self._set_connection(WrappedTraCIConnection(_socket))
            self.server_port = _server_port

            self._running = True
            self._run()
        except NotImplementedError as e:
            print(e)
        finally:
            self._cleanup()


class ControlTraciWrapper:
    @classmethod
    def get_controller_from_args(cls, working_dir, args=None, controller=None):
        ns = parse_args_as_dict(args)
        logging.info(ns)
        print(ns)

        if (
            ns["host_name"] == "vadere"
            and ns["port"] == 9999
            and ns["is_in_client_mode"]
        ):
            return ClientModeConnection(
                control_handler=controller,
                port=ns["port"],
                is_start_server=ns["start_server"],
                is_gui_mode=ns["gui_mode"],
                scenario=ns["scenario_file"],
                host="172.18.0.2"
            )
        elif (
            ns["host_name"] == "omnet"
            and ns["port"] == 9997 #TODO check port number
            and not ns["is_in_client_mode"]
        ):
            return ServerModeConnection(control_handler=controller, port=ns["port"])
        else:
            raise NotImplementedError("Port and host configuration not found.")
