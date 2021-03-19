import platform, os, subprocess


def create_vadere_jar_files():

    if platform.system() != "Linux":
        raise NotImplemented

    jarfiles = [
        os.path.join(
            os.environ["VADERE_PATH"],
            "VadereManager/target/vadere-traci-entrypoint.jar",
        ),
        os.path.join(
            os.environ["VADERE_PATH"], "VadereManager/target/vadere-server.jar"
        ),
    ]

    if os.path.exists(jarfiles[0]) is False or os.path.exists(jarfiles[1]) is False:

        try:
            command = [
                "mvn",
                "clean",
                "-f",
                os.path.join(os.environ["VADERE_PATH"], "pom.xml"),
            ]
            return_code = subprocess.check_call(command)
            command = [
                "mvn",
                "package",
                "-f",
                os.path.join(os.environ["VADERE_PATH"], "pom.xml"),
                "-Dmaven.test.skip=true",
            ]
            return_code = subprocess.check_call(command)
        except:
            pass
