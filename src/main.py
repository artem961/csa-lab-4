from src.binary import read_binary
from src.config_loader import load_simulation_config
from src.machine.processor.control_unit import ControlUnit
from src.machine.processor.data_path import DataPath
from src.machine.simulator.log_presenter import LogPresenter
from src.machine.simulator.simulator import Simulator


def main():

    # Инициализация всей этой технолоджии
    conf = load_simulation_config("config.yml")
    binary = conf["bin"]
    instr_mem, data_mem = read_binary(binary)

    data_mem.extend([0] * (conf["memory_size"] - len(data_mem)))

    dp = DataPath(instr_mem=instr_mem, data_mem=data_mem)

    cu = ControlUnit(dp)

    presenter = LogPresenter(show_signals=conf["show_signals"])
    sim = Simulator(
        cu=cu,
        dp=dp,
        input_schedule=conf["schedule"],
        limit=conf["limit"],
        presenter=presenter
    )
    sim.run()


if __name__ == "__main__":
    main()
