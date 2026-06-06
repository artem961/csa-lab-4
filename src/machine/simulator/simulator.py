from src.machine.processor.control_unit import ControlUnit
from src.machine.processor.data_path import DataPath
from src.machine.simulator.log_presenter import LogPresenter, MachineState


class Simulator:
    def __init__(self, cu: ControlUnit, dp: DataPath, input_schedule: list[tuple[int, int, int]],
                 presenter: LogPresenter = LogPresenter(), limit: int = 5000) -> None:
        self.cu = cu
        self.dp = dp
        self.presenter = presenter
        self.input_schedule = sorted(input_schedule, key=lambda x: x[0])
        self.tick = 0
        self.limit = limit

    def run(self) -> None:
        self.presenter.print_header()

        while not self.cu.halted and self.tick < self.limit:
            self.tick += 1
            state_snapshot = self._capture_state()

            self._handle_external_events()
            active_signals = self.cu.tick()

            state_snapshot.signals = [s.name for s in active_signals]
            state_snapshot.instruction = self.cu.decode_opcode().name
            self.presenter.print_tick(state_snapshot)

        self.presenter.print_final_stats(self.tick, self.dp.acc, self.dp.output_buffer)

    def _capture_state(self) -> MachineState:
        return MachineState(
            tick=self.tick,
            instruction="",
            state_name=self.cu.state.name,
            ip=self.dp.ip,
            acc=self.dp.acc,
            ar=self.dp.ar,
            dr=self.dp.dr,
            sp=self.dp.sp,
            flags={
                'Z': self.dp.get_z(),
                'N': self.dp.get_n(),
                'IE': self.dp.get_ie()
            },
            signals=[],
            stack_view=list(reversed(self.dp.data_mem[-10:]))
        )

    def _handle_external_events(self) -> None:
        if not self.input_schedule:
            return

        tick, port, value = self.input_schedule[0]

        if tick <= self.tick:
            self.input_schedule.pop(0)
            self.dp.port_input[port] = value
            self.dp.irq = True
            self.dp.iv = port
            print(f"\n>>> [EVENT] Tick {self.tick}: Port[{port}] <- {value} (IRQ raised)\n")