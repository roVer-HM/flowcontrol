import os

config_file = ".flowcontrolconfig"
crownet_env = "CROWNET_HOME"
vadere_env = "VADERE_PATH"

def read_config_file():
	config_file_path = os.path.join(os.path.expanduser('~'), config_file)

	with open(config_file_path, "r") as f:
		data = f.read().splitlines()

	if len(data) != 1:
		raise ValueError(f"The number of source paths in {config_file_path} must be 1.")

	source_path = data[0]

	if not os.path.isdir(source_path):
		raise ValueError(f"File {config_file_path} does not exist. Use 'echo $CROWNET_HOME > ~/.flowcontrolconfig' to generate the file automatically, see https://sam-dev.cs.hm.edu/rover/flowcontrol")

	return source_path


def add_env_variables():

	crownet_path = read_config_file()
	os.environ[crownet_env] = crownet_path
	vadere_path = os.path.join(crownet_path , "vadere")
	os.environ[vadere_env] = vadere_path


if __name__ == "__main__":

	add_env_variables()
	print(f"Add {crownet_env}={os.environ[crownet_env]} and {vadere_env}={os.environ[vadere_env]} to enviroment variables.")
