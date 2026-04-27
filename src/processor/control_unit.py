from enum import Enum, auto
from src.isa.isa import Opcode
from src.processor.data_path import DataPath
from src.processor.instructions import INSTRUCTION_TICKS
from src.processor.signals import Signal


class State(Enum):
    FETCH = auto()
    INC_IP = auto()
    EXECUTE = auto()
    INTERRUPT = auto()


class ControlUnit:
    def __init__(self, data_path: DataPath):
        self.dp = data_path
        self.state = State.FETCH
        self.step_index = 0
        self.halted = False

        self.irq = False
        self.current_vector = 0

        self._interrupt_sequence = [
            {Signal.SEL_AR_SP, Signal.LATCH_AR, Signal.SEL_DM_IP, Signal.DATA_MEM_WRITE},
            {Signal.SEL_ALU_L_SP, Signal.ALU_DEC, Signal.LATCH_SP},
            {Signal.SEL_AR_SP, Signal.LATCH_AR, Signal.SEL_DM_AC, Signal.DATA_MEM_WRITE},
            {Signal.SEL_ALU_L_SP, Signal.ALU_DEC, Signal.LATCH_SP},
            {Signal.SEL_AR_SP, Signal.LATCH_AR, Signal.SEL_DM_PS, Signal.DATA_MEM_WRITE},
            {Signal.SEL_ALU_L_SP, Signal.ALU_DEC, Signal.LATCH_SP},
            {Signal.SEL_IP_IV, Signal.LATCH_IP, Signal.DISABLE_INTERRUPTS}
        ]

    def decode_opcode(self) -> Opcode:
        return Opcode((self.dp.ir >> 24) & 0xFF)

    def tick(self) -> set:
        if self.halted:
            return set()

        signals = set()

        if self.state == State.FETCH:
            signals = {Signal.INSTR_MEM_READ, Signal.LATCH_IR}
            self.state = State.INC_IP

        elif self.state == State.INC_IP:
            signals = {Signal.SEL_ALU_R_IP, Signal.SEL_ALU_L_ZERO, Signal.ALU_INC, Signal.SEL_IP_ALU, Signal.LATCH_IP}
            self.state = State.EXECUTE
            self.step_index = 0

        elif self.state == State.EXECUTE:
            opcode = self.decode_opcode()
            print(f"==={opcode.name}===")

            if opcode == Opcode.HLT:
                self.halted = True
                return set()


            if opcode in [Opcode.JZ, Opcode.JNZ, Opcode.JN]:
                signals = self._handle_branching(opcode)
                self._check_and_finalize_instruction()
            else:
                seq = INSTRUCTION_TICKS.get(opcode, [])
                if self.step_index < len(seq):
                    signals = seq[self.step_index]
                    self.step_index += 1

                # all instruction tacts finished
                if self.step_index >= len(seq):
                    self._check_and_finalize_instruction()

        elif self.state == State.INTERRUPT:
            if self.step_index < len(self._interrupt_sequence):
                signals = self._interrupt_sequence[self.step_index]

                if Signal.SEL_IP_IV in signals:
                    self.dp.interrupt_vector = self.current_vector

                self.step_index += 1

            if self.step_index >= len(self._interrupt_sequence):
                self.state = State.FETCH
                self.step_index = 0
                self.current_vector = 0

        if signals:
            self.dp.execute_tick(signals)

        return signals

    def _handle_branching(self, opcode: Opcode) -> set:
        condition_met = False
        if opcode == Opcode.JZ and self.dp.get_z():
            condition_met = True
        elif opcode == Opcode.JNZ and not self.dp.get_z():
            condition_met = True
        elif opcode == Opcode.JN and self.dp.get_n():
            condition_met = True
        return {Signal.SEL_IP_IR, Signal.LATCH_IP} if condition_met else set()

    def _check_and_finalize_instruction(self):
        if self.irq and self.dp.get_ie():
            self.state = State.INTERRUPT
            self.irq = False
        else:
            self.state = State.FETCH
        self.step_index = 0