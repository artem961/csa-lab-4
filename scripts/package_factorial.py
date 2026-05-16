import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.machine.isa import Opcode, Instruction
from src.binary import write_binary

instr_map = {
    0: Instruction(Opcode.JMP, 10),
    1: Instruction(Opcode.JMP, 200),

    # MAIN
    10: Instruction(Opcode.LDI, 5),
    11: Instruction(Opcode.PUSH, 0),
    12: Instruction(Opcode.CALL, 50),
    13: Instruction(Opcode.POP, 0),
    14: Instruction(Opcode.OUT, 1),
    15: Instruction(Opcode.HLT, 0),

    # FACT
    50: Instruction(Opcode.LDS, 2),
    51: Instruction(Opcode.CMP, 100),
    52: Instruction(Opcode.JZ, 80),
    53: Instruction(Opcode.LDS, 2),
    54: Instruction(Opcode.PUSH, 0),
    55: Instruction(Opcode.LDS, 1),
    56: Instruction(Opcode.SUB, 100),
    57: Instruction(Opcode.PUSH, 0),
    58: Instruction(Opcode.CALL, 50),
    59: Instruction(Opcode.POP, 0),
    60: Instruction(Opcode.ST, 101),
    61: Instruction(Opcode.POP, 0),
    62: Instruction(Opcode.MUL, 101),
    63: Instruction(Opcode.STS, 2),
    64: Instruction(Opcode.RET, 0),

    # BASE
    80: Instruction(Opcode.RET, 0),

    # IRQ handler
    200: Instruction(Opcode.IN, 1),
    201: Instruction(Opcode.OUT, 2),
    202: Instruction(Opcode.IRET, 0),
}

data_map = {
    100: 1,  # constant 1 for factorial
}


out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'out'))

write_binary(out_path + ".bin", instr_map, data_map, listing_path=out_path + '.txt')