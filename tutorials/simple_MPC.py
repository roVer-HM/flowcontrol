from flowcontrol.config import add_env_variables

add_env_variables()

from flowcontrol.strategy.ModelPredictiveControl import CorridorChoiceController
from flowcontrol.vaderecontrol.VadereModel import CorridorChoice
import numpy as np

import os

if __name__ == "__main__":

    model = CorridorChoice(
        project_path=os.path.abspath("scenarios/tutorial1"),
        scenario_name="TwoCorridors_unforced",
        start_server=True,
        debug=False,
    )

    times = np.arange(start=0, stop=25, step=2.5)
    mpc = CorridorChoiceController(model=model, controller_times=times)
    mpc.run_MPC()

    print()
