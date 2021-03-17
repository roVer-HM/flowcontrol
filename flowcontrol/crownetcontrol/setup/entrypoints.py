import argparse

from flowcontrol.crownetcontrol.setup.vadere import VadereServer
from flowcontrol.crownetcontrol.traci.connection_manager import (
    ServerModeConnection,
    ClientModeConnection)


def get_controller_from_args(working_dir, args=None, controller=None):
    ns = parse_args_as_dict(args)

    if ns["port"] == 9999 and ns["is_in_client_mode"]:
        # TODO: start server if necessary

        VadereServer(is_start_server=ns["start_server"], is_gui_mode=ns["gui_mode"])

        return ClientModeConnection(
            control_handler=controller,
            port=ns["port"],
            host=ns["host_name"],
        )
    elif (
        ns["port"] == 9997  # TODO check port number
        and not ns["is_in_client_mode"]
    ):
        return ServerModeConnection(control_handler=controller, port=ns["port"], host=ns["host_name"])
    else:
        raise NotImplementedError("Port and host configuration not found.")


def parse_args_as_dict(args=None):
    # parse arguments
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-n",
        "--host-name",
        dest="host_name",
        default="localhost",  # TODO: discuss -> defaults
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
    # parser.add_argument(
    #     "-s",
    #     "--scenario",
    #     dest="scenario_file",
    #     default="",  # TODO: discuss -> defaults
    #     required=False,
    #     help="Only available in client-mode.",
    # )

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

    return ns
