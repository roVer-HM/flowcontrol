import struct

from flowcontrol.crownetcontrol.traci.domains.domain import Domain, BaseDomain
from flowcontrol.crownetcontrol.traci import constants_vadere as tc


class VadereControlCommandApi(BaseDomain):

    def __init__(self):
        super().__init__("vCtrl")

    def send_file(self, file_name, file_content):
        _cmd = bytes()
        _cmd += struct.pack("!B", tc.CMD_FILE_SEND)
        _cmd += struct.pack("!i", len(file_name)) + file_name.encode("latin1")
        _cmd += struct.pack("!i", len(file_content)) + file_content.encode("latin1")

        # assume big packet
        _cmd = struct.pack("!Bi", 0, len(_cmd) + 5) + _cmd

        self._connection.send_raw(_cmd, append_message_len=True)
        # todo: check result
        return self._connection.recv_exact()

    def sim_step(self, simstep=0.0):
        """simulate to simstep and return subscription data """
        return self._connection.send_cmd(tc.CMD_SIMSTEP, None, None, "D", simstep)

    def sim_state(self, simstep=0.0):
        """access subscription data (i.e. current state) """
        return self._connection.send_cmd(tc.CMD_SIMSTATE, None, None, "D", simstep)
