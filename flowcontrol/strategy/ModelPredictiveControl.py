import pandas as pd
import numpy as np


from abc import ABCMeta, abstractmethod


from flowcontrol.vaderecontrol.VadereModel import SimulationModel


class ModelPredictiveController(metaclass=ABCMeta):
    def __init__(
            self, model: SimulationModel, controller_times: np.array, nr_predition_steps=6
    ):
        self.model = model
        self.nr_prediction_steps = nr_predition_steps
        if controller_times[0] != 0:
            raise ValueError("First time step must be 0.")

        self.controller_times = controller_times
        self.last_position = None
        self.temp_position = None


    def simulate_until_(self, t):
        self.model.get_control().nextStep(t)

    def _get_target_list(self):
        ids = self.model.get_peds().getIDList()
        targets = [self.model.get_peds().getTargetList(id) for id in ids]
        targets = pd.DataFrame(targets, index=list(ids))
        return targets

    def _get_pos_from_model(self):
        positions = self.model.get_peds().getPosition2DList()
        positions = pd.DataFrame(positions).transpose()
        return positions

    def save_last_state(self):
        self.targets = self._get_target_list()
        self.last_position = self._get_pos_from_model()

    def reset_simulation_state(self):
        self._reset_positions()
        self._reset_targets()

    def _reset_targets(self):
        for index, row in self.targets.iterrows():
            targets = [str(t) for t in row]
            self.model.get_peds().setTargetList(personID=index, targets=targets)

    def _reset_positions(self):
        for index, row in self.last_position.iterrows():
            row = row.to_numpy()
            self.model.get_peds().setPosition2D(index, str(row[0]), str(row[1]))

    def get_next_predict_times(self, t):
        if t not in self.controller_times:
            raise ValueError("Time not allowed.")

        ii = np.argwhere(self.controller_times == t)[0][0]
        next_predict_times = self.controller_times[
            ii + 1 : ii + self.nr_prediction_steps + 1
        ]
        return next_predict_times

    def run_MPC(self):

        for i in range(0, len(self.controller_times) - self.nr_prediction_steps):
            t_0 = self.controller_times[i]
            t_next = self.controller_times[i + 1]

            self.save_last_state()
            optimal_control = self.find_optimal_control(t_0)
            print("-------------- Next step -------------------------")
            self.apply_optimal_control_for_next_time(control=optimal_control)
            self.simulate_until_(t_next)

    def apply_optimal_control_for_next_time(self, control):
        self.apply_control(control)

    @abstractmethod
    def find_optimal_control(self, t):
        raise NotImplemented

    @abstractmethod
    def apply_control(self, control):
        raise NotImplemented


class CorridorChoiceController(ModelPredictiveController):
    def __init__(self, model: SimulationModel, controller_times: np.array):
        super().__init__(model, controller_times)

    def find_optimal_control(self, t):

        samples = [
            [1, 1, 1, 1, 1],
            [0.5, 0.2, 0.5, 0.3, 0.7],
            [1, 1, 1, 1, 1],
        ]  # [0.5,0.2,0.5,0.3,0.7]

        samples = np.random.random((10, 5))  #

        samples = np.linspace(0, 1, 2)
        samples = np.repeat(samples.reshape(-1, 1), 20, axis=1)

        norm = list()
        t_ = 0
        for control_vec in samples:

            self._set_indices()

            t_i = self.get_next_predict_times(t) + t_

            print(t_i)

            print(f"Timestep t={t}s. Sample {len(norm)+1}.")
            self.temp_position = self.last_position
            print(f"\t Start position {self.temp_position}")

            density = list()
            for i in range(len(t_i)):
                t_ = t_i[i]
                c = control_vec[i]

                self.apply_control(p=self.temp_position, control=c)
                self.simulate_until_(t_)
                self.temp_position = self._get_pos_from_model()

                # analyze objective
                # print(f"\t NEW position {self.temp_position}")
                d = self.model.get_objective(state=self.temp_position)

                print(f"\t objective = {d}")

                # print(self._get_target_list())

                density.append(d)

            r = np.linalg.norm(density)
            print(f"\t control value = {control_vec}, state objective = {r}")
            norm.append(r)

            self.reset_simulation_state()

        norm = np.array(norm)
        i = np.argwhere(norm == norm.min())[0][0]
        optimal_control_action = samples[i][0]

        plt.scatter(samples.transpose()[0], norm)
        plt.plot(
            optimal_control_action, norm.min(), marker="x", markersize=10, color="green"
        )
        plt.show()

        print(f"Timestep t={t}s. Use control_actiion {optimal_control_action}.")

        return optimal_control_action

    def _get_indices(self):

        return self.indices

    def _set_indices(self):

        self.indices = list()

    def apply_control(self, control, p=None):

        if p is None:
            print("\t Use stored positions.")
            p = self.last_position

        x_ = p.iloc[:, 0].to_numpy()
        y_ = p.iloc[:, 1].to_numpy()

        indices = list(np.argwhere((x_ > 30) & (x_ < 40) & (y_ < 10)).flatten() + 1)

        common_values = set(self.indices) & set(indices)

        for value in common_values:
            indices.remove(value)

        self.indices.extend(indices)
        ii = np.array(indices).astype(str)
        print(ii)
        l = int(len(ii) * control)
        ii = ii[:l]
        print(ii)

        aa = self._get_target_list()

        for index, row in self.targets.iterrows():
            targets = [str(2001), str(1)]

            if index in ii:
                print("Set new target for agent with id=" + index)
                self.model.get_peds().setTargetList(personID=index, targets=targets)

        # if len(indices) > 0:
        #     l = int(len(indices)*control)
        #     if l>0:
        #         print(f"\t Set new targets for {indices[:l]}. {len(indices[:l])}.")
        #         ii = indices #[:l]
        #         for i in ii:
        #             self.model.get_peds().setTargetList(personID=str(i), targets=[str(2001), str(1)])

        bb = self._get_target_list()

        print()
