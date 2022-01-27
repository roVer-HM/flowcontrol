import os

from flowcontrol.crownetcontrol.setup.vadere import VadereServerProvider

if __name__ == "__main__":
	dir_name = os.path.dirname(os.path.abspath(__file__))

	VadereServerProvider().download_vadere_jar_file(jar_file="vadere-server.jar")



