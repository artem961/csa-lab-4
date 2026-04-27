from enum import Enum, auto
from typing import Set

from src.machine.isa import Opcode
from src.machine.processor.data_path import DataPath
from src.machine.processor.instruction_exec_logic import INSTRUCTION_TICKS
from src.machine.processor.signals import Signal


class State(Enum):
    FETCH = auto()
    INC_IP = auto()
    EXECUTE = auto()
    INTERRUPT = auto()


class ControlUnit:

    # Аппаратные последовательности сигналов

    FETCH_SEQUENCE = {
        Signal.INSTR_MEM_READ, Signal.LATCH_IR
    }

    INC_IP_SEQUENCE = {
        Signal.SEL_ALU_R_IP, Signal.SEL_ALU_L_ZERO,
        Signal.ALU_INC, Signal.SEL_IP_ALU, Signal.LATCH_IP
    }

    INTERRUPT_TRAP_SEQUENCE = [
        {Signal.SEL_AR_SP, Signal.LATCH_AR, Signal.SEL_DM_IP, Signal.DATA_MEM_WRITE},  # Save IP
        {Signal.SEL_ALU_L_SP, Signal.ALU_DEC, Signal.LATCH_SP},  # SP--
        {Signal.SEL_AR_SP, Signal.LATCH_AR, Signal.SEL_DM_AC, Signal.DATA_MEM_WRITE},  # Save AC
        {Signal.SEL_ALU_L_SP, Signal.ALU_DEC, Signal.LATCH_SP},  # SP--
        {Signal.SEL_AR_SP, Signal.LATCH_AR, Signal.SEL_DM_PS, Signal.DATA_MEM_WRITE},  # Save PS
        {Signal.SEL_ALU_L_SP, Signal.ALU_DEC, Signal.LATCH_SP},  # SP--
        {Signal.SEL_IP_IV, Signal.LATCH_IP, Signal.DISABLE_INTERRUPTS}  # IP <- IV
    ]

    def __init__(self, data_path: DataPath):
        self.dp = data_path
        self.state = State.FETCH
        self.step_index = 0
        self.halted = False

    def decode_opcode(self) -> Opcode:
        return Opcode((self.dp.ir >> 32) & 0xFF)

    def tick(self) -> Set[Signal]:
        if self.halted:
            return set()

        signals = set()

        if self.state == State.FETCH:
            signals = self._handle_fetch()
        elif self.state == State.INC_IP:
            signals = self._handle_inc_ip()
        elif self.state == State.EXECUTE:
            signals = self._handle_execute()
        elif self.state == State.INTERRUPT:
            signals = self._handle_interrupt()

        if signals:
            self.dp.execute_tick(signals)
        return signals


    def _handle_fetch(self) -> Set[Signal]:
        self.state = State.INC_IP
        return {Signal.INSTR_MEM_READ, Signal.LATCH_IR}

    def _handle_inc_ip(self) -> Set[Signal]:
        self.state = State.EXECUTE
        self.step_index = 0
        return self.INC_IP_SEQUENCE

    def _handle_execute(self) -> Set[Signal]:
        opcode = self.decode_opcode()

        if opcode == Opcode.HLT:
            self.halted = True
            return set()

        if opcode in [Opcode.JZ, Opcode.JNZ, Opcode.JN]:
            signals = self._handle_branching(opcode)
            self._finalize_instruction()
            return signals

        seq = INSTRUCTION_TICKS.get(opcode)
        signals = seq[self.step_index] if self.step_index < len(seq) else set()

        self.step_index += 1
        # Все такты цикла EXECUTION команды завершились
        if self.step_index >= len(seq):
            self._finalize_instruction()

        return signals

    def _handle_interrupt(self) -> Set[Signal]:
        seq = self.INTERRUPT_TRAP_SEQUENCE
        signals = seq[self.step_index] if self.step_index < len(seq) else set()

        self.step_index += 1
        if self.step_index >= len(seq):
            self.state = State.FETCH
            self.step_index = 0

        return signals

    def _handle_branching(self, opcode: Opcode) -> Set[Signal]:
        jump_conditions = {
            Opcode.JZ: self.dp.get_z(),
            Opcode.JNZ: not self.dp.get_z(),
            Opcode.JN: self.dp.get_n()
        }

        if jump_conditions.get(opcode, False):
            return {Signal.SEL_IP_IR, Signal.LATCH_IP}
        return set()

    def _finalize_instruction(self):
        if self.dp.irq and self.dp.get_ie():
            self.state = State.INTERRUPT
            self.dp.irq = False
        else:
            self.state = State.FETCH
        self.step_index = 0