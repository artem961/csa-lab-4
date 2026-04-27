from typing import List, Tuple, Set

class Simulator:
    def __init__(
            self,
            cu,
            dp,
            input_schedule: List[Tuple[int, int, int, int]],  # (tick, port, value, vector)
            limit: int = 5000
    ):
        self.cu = cu
        self.dp = dp
        self.input_schedule = sorted(input_schedule, key=lambda x: x[0])
        self.tick = 0
        self.limit = limit

    def run(self):
        self._print_header()


        while not self.cu.halted and self.tick < self.limit:
            state = self.fix_state()
            self.tick += 1
            self._handle_external_events()
            active_signals = self.cu.tick()
            self._log_tick(active_signals, state)


        if self.tick >= self.limit:
            print(f"\n[!] Simulation stopped by limit ({self.limit} ticks).")
        else:
            print(f"\nSimulation finished at tick {self.tick}.")

        self._print_final_stats()

    def _handle_external_events(self):
        while self.input_schedule and self.input_schedule[0][0] <= self.tick:
            tick, port, value, vector = self.input_schedule.pop(0)

            if port not in self.dp.input_buffer:
                self.dp.input_buffer[port] = []
            self.dp.input_buffer[port].append(value)

            # Выставляем запрос и номер вектора для CU
            self.cu.irq = True
            self.cu.current_vector = vector # Уходим от "current_irq_vector" к "current_vector"

            print(f"\n>>> [EVENT] Tick {self.tick}: Port[{port}] <- {value} (ASCII: {chr(value) if 32<=value<=126 else '?'}). Triggering Vector {vector}\n")

    def _log_tick(self, signals: Set, state: str):

        sig_names = ", ".join([s.name for s in signals]) if signals else "none"

        print(state)
        if signals:
            print(f"{' ': <26} | SIGNALS: {sig_names}")
        print("-" * 115)

    def fix_state(self) -> str:
        stack = f"{self.dp.data_mem[-1]}  {self.dp.data_mem[-2]}  {self.dp.data_mem[-3]}  {self.dp.data_mem[-4]}  {self.dp.data_mem[-5]}  {self.dp.data_mem[-6]}  {self.dp.data_mem[-7]}  {self.dp.data_mem[-8]}  {self.dp.data_mem[-9]}  {self.dp.data_mem[-10]}"
        flags = f"Z:{int(self.dp.get_z())} N:{int(self.dp.get_n())} IE:{int(self.dp.get_ie())}"
        state_info = f"{self.tick:<6} | {self.cu.state.name:<10} | {self.dp.ip:<4} | {self.dp.acc:<11}"
        regs_info = f"AR:{self.dp.ar:<4} DR:{self.dp.dr:<11} SP:{self.dp.sp:<4} PS:[{flags}] STACK: {stack}"

        return f"{state_info} | {regs_info}"


    def _print_header(self):
        print("-" * 115)
        print(f"{'TICK':<6} | {'STATE':<10} | {'IP':<4} | {'ACC':<11} | {'REGISTERS & FLAGS'}")
        print("-" * 115)

    def _print_final_stats(self):
        print("\n" + "=" * 35)
        print("       FINAL SIMULATION STATE")
        print("=" * 35)
        print(f"Total ticks: {self.tick}")
        print(f"Final AC:    {self.dp.acc} (0x{self.dp.acc & 0xFFFFFFFF:08X})")
        if self.dp.output_buffer:
            print("\nOutput Ports Content:")
            for port, values in self.dp.output_buffer.items():
                decoded = "".join(chr(v) if 32 <= v <= 126 else f"<{v}>" for v in values)
                print(f"  Port {port}: {values} -> '{decoded}'")
        print("=" * 35)