from src.machine.simulator.machine_state import MachineState


class LogPresenter:
    def __init__(self, show_signals: bool = False):
        self.show_signals = show_signals

    @staticmethod
    def print_header() -> None:
        header = f"{'TICK':<6} | {'INSTRUCTION':<12} | {'STATE':<10} | {'IP':<3} | REGISTERS & FLAGS"
        print("\n" + "=" * 135)
        print(header)
        print("-" * 135)

    def print_tick(self, s: MachineState) -> None:
        f = s.flags
        flags_str = f"Z:{int(f['Z'])} N:{int(f['N'])} IE:{int(f['IE'])}"

        regs_line = (f"AC: {s.acc:<10} "
                     f"SP: {s.sp:<5} "
                     f"AR: {s.ar:<5} "
                     f"DR: {s.dr:<10} "
                     f"{flags_str}")

        stack_str = " ".join(f"{val}" for val in s.stack_view[:8])

        main_line = f"{s.tick:<6} | {s.instruction:<12} | {s.state_name:<10} | {s.ip:<3} | {regs_line}"

        print(main_line + f"     STACK: [{stack_str}]")

        if self.show_signals and s.signals:
            sig_names = ", ".join(s.signals)
            print(f"{' ': <23} SIGNALS: {sig_names}")

        print("-" * 135)

    @staticmethod
    def print_final_stats(tick: int, acc: int, output_buffer: dict[int, list[int]]) -> None:
        print("\n" + "=" * 50)
        print("       FINAL SIMULATION STATE")
        print("=" * 50)
        print(f" Total ticks: {tick}")
        print(f" Final AC:    {acc} (0x{acc & 0xFFFFFFFF:08X})")

        if output_buffer:
            print("\n OUTPUT PORTS:")
            for port, values in output_buffer.items():
                decoded = "".join(chr(v) if 32 <= v <= 136 else f"<{v}>" for v in values)
                print(f"  Port {port}: {values}")
                print(f"  String : '{decoded}'")
        print("\n" + "=" * 50)