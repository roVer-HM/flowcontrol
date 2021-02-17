import os

from flowcontrol.strategy.strategies import CorridorChoice

if __name__ == "__main__":

    VADERE_PATH = os.environ["VADERE_PATH"]  # absolute path to the vadere repo

    model = CorridorChoice(
        VADERE_PATH=VADERE_PATH,
        project_path=f"{VADERE_PATH}/Scenarios/Demos/Density_controller/scenarios",
        scenario_name="TwoCorridors_unforced",
        start_server=True,
        debug=True
    )

    times = np.arange(start=0, stop=25, step=2.5)
    mpc = CorridorChoiceController(model=model,controller_times=times )
    mpc.run_MPC()

    print()