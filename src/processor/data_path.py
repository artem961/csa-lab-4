from typing import Dict, List, Set, Optional
from src.processor.signals import Signal


class DataPath:
    def __init__(self, instr_mem: List[int], data_mem_size: int):
        # Память
        self.instr_mem = instr_mem
        self.data_mem = [0] * data_mem_size

        # Регистры
        self.acc = 0
        self.ip = 0
        self.sp = data_mem_size - 1
        self.ar = 0
        self.dr = 0
        self.ir = 0
        self.ps = 0b100
        self.io_addr = 0

        self.MASK_32 = 0xFFFFFFFF
        self.BIT_31 = 0x80000000

        # Порты ввода-вывода
        self.output_buffer: Dict[int, List[int]] = {}
        self.input_buffer: Dict[int, List[int]] = {}

    def _get_z(self) -> bool:
        return bool(self.ps & 0b001)

    def _get_n(self) -> bool:
        return bool(self.ps & 0b010)

    def _get_ie(self) -> bool:
        return bool(self.ps & 0b100)

    def _apply_mask(self, val: int) -> int:
        return val & self.MASK_32

    def execute_tick(self, signals: Set[Signal]):
        # decode operand
        imm = self.ir & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x1000000

        # ALU compute
        alu_res = self._run_alu(signals)

        # MUX out values
        addr_for_mem = self.ar
        if Signal.SEL_AR_CU in signals:
            addr_for_mem = imm
        elif Signal.SEL_AR_ALU in signals:
            addr_for_mem = alu_res
        elif Signal.SEL_AR_SP in signals:
            addr_for_mem = self.sp

        data_to_mem = self.acc
        if Signal.SEL_DM_IP in signals:
            data_to_mem = self.ip
        elif Signal.SEL_DM_PS in signals:
            data_to_mem = self.ps

        val_for_acc = alu_res
        if Signal.SEL_AC_IO in signals:
            val_for_acc = self._read_io()

        next_ip = self.ip
        if Signal.SEL_IP_CU in signals:
            next_ip = imm
        elif Signal.SEL_IP_ALU in signals:
            next_ip = alu_res

        val_for_dr = self.dr
        if Signal.SEL_DR_CU in signals:
            val_for_dr = imm
        elif Signal.SEL_DR_DATA_MEM in signals:
            val_for_dr = self.data_mem[self._apply_mask(addr_for_mem)]

        # MEM + IO write
        if Signal.DATA_MEM_WRITE in signals:
            self.data_mem[self._apply_mask(addr_for_mem)] = self._apply_mask(data_to_mem)

        if Signal.IO_WRITE in signals:
            self._write_io()

        # LATCHES
        if Signal.LATCH_AR in signals:
            self.ar = self._apply_mask(addr_for_mem)

        if Signal.LATCH_DR in signals:
            self.dr = self._apply_mask(val_for_dr)

        if Signal.LATCH_AC in signals:
            self.acc = self._apply_mask(val_for_acc)
            self._update_zn_flags(self.acc)

        if Signal.LATCH_SP in signals:
            self.sp = self._apply_mask(alu_res)

        if Signal.LATCH_IP in signals:
            self.ip = self._apply_mask(next_ip)

        if Signal.LATCH_IR in signals:
            self.ir = self.instr_mem[self.ip]

        if Signal.LATCH_IO_ADDR in signals:
            self.io_addr = imm

        # PS + CMP
        if Signal.ENABLE_INTERRUPTS in signals:
            self.ps |= 0b100
        if Signal.DISABLE_INTERRUPTS in signals:
            self.ps &= ~0b100

        if Signal.LATCH_PS in signals:
            self.ps = self.dr & 0b111

        if Signal.ALU_CMP in signals:
            self._update_zn_flags(alu_res)

    def _update_zn_flags(self, val: int):
        self.ps &= ~0b011
        if val == 0:
            self.ps |= 0b001
        if val & self.BIT_31:
            self.ps |= 0b010

    def _run_alu(self, signals: Set[Signal]) -> int:
        left = 0
        if Signal.SEL_ALU_L_AC in signals:
            left = self.acc
        elif Signal.SEL_ALU_L_SP in signals:
            left = self.sp
        elif Signal.SEL_ALU_L_ZERO in signals:
            left = 0

        right = 0
        if Signal.SEL_ALU_R_DR in signals:
            right = self.dr
        elif Signal.SEL_ALU_R_IP in signals:
            right = self.ip
        elif Signal.SEL_ALU_R_ZERO in signals:
            right = 0

        res = 0
        if Signal.ALU_ADD in signals:
            res = left + right
        elif Signal.ALU_SUB in signals:
            res = left - right
        elif Signal.ALU_MUL in signals:
            res = left * right
        elif Signal.ALU_DIV in signals:
            res = left // right if right != 0 else 0
        elif Signal.ALU_MOD in signals:
            res = left % right if right != 0 else 0
        elif Signal.ALU_CMP in signals:
            res = left - right
        else:
            res = left + right

        if Signal.ALU_INC in signals:
            res += 1
        if Signal.ALU_DEC in signals:
            res -= 1
        if Signal.ALU_NOT in signals:
            res = ~res

        return self._apply_mask(res)

    def _read_io(self) -> int:
        port = self.io_addr
        if port in self.input_buffer and self.input_buffer[port]:
            return self.input_buffer[port].pop(0)
        return 0

    def _write_io(self):
        port = self.io_addr
        if port not in self.output_buffer:
            self.output_buffer[port] = []
        self.output_buffer[port].append(self.acc)