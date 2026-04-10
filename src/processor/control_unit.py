from src.isa.isa import Opcode
from src.processor.data_path import DataPath
from src.processor.instructions import INSTRUCTION_TICKS
from src.processor.signals import Signal


class ControlUnit:
    def __init__(self, data_path: DataPath):
        self.dp = data_path
        self._tick = 0
        self.halted = False

    def decode_opcode(self) -> Opcode:
        raw_op = (self.dp.ir >> 24) & 0xFF
        try:
            return Opcode(raw_op)
        except ValueError:
            raise RuntimeError(f"Unknown opcode: {raw_op}")

    def _execute_and_log(self, signals: set):
        self._tick += 1
        self.dp.execute_tick(signals)

        sig_names = [s.name for s in signals]
        print(f"TICK: {self._tick:4} | Signals: {sig_names}")
        print(f"  AC: {self.dp.acc:8} | DR: {self.dp.dr:8} | AR: {self.dp.ar:4} | IP: {self.dp.ip:4}")
        print(
            f"  PS: [Z={int(self.dp._get_z())} N={int(self.dp._get_n())} IE={int(self.dp._get_ie())}] | IR: 0x{self.dp.ir:08X}")
        print("-" * 60)

    def main_step(self):
        if self.halted:
            return

        # 1- COMMAND FETCH
        self._execute_and_log({Signal.INSTR_MEM_READ, Signal.LATCH_IR})

        # 2- INCREMENT IP
        self._execute_and_log({
            Signal.SEL_ALU_R_IP,
            Signal.SEL_ALU_L_ZERO,
            Signal.ALU_INC,
            Signal.SEL_IP_ALU,
            Signal.LATCH_IP
        })

        # 3- DECODE OPCODE
        opcode = self.decode_opcode()

        if opcode == Opcode.JZ:
            if self.dp._get_z():
                self._execute_and_log({Signal.SEL_IP_CU, Signal.LATCH_IP})
            else:
                self._execute_and_log(set())
            return

        if opcode == Opcode.JNZ:
            if not self.dp._get_z():
                self._execute_and_log({Signal.SEL_IP_CU, Signal.LATCH_IP})
            else:
                self._execute_and_log(set())
            return

        if opcode == Opcode.JN:
            if self.dp._get_n():
                self._execute_and_log({Signal.SEL_IP_CU, Signal.LATCH_IP})
            else:
                self._execute_and_log(set())
            return

        if opcode == Opcode.HLT:
            self.halted = True
            print(f"--- HALT AT TICK {self._tick} ---")
            return

        # 4- EXECUTE
        ticks_sequence = INSTRUCTION_TICKS.get(opcode, [])
        for signals in ticks_sequence:
            self._execute_and_log(signals)

        # 5- INTERRUPT CHECK
        self.check_interrupts()

    def check_interrupts(self):
        # TODO
        pass