from enum import IntEnum, unique
from dataclasses import dataclass


@unique
class Opcode(IntEnum):
    # Память
    LD = 0x01
    ST = 0x02
    LDI = 0x03

    # Арифметика
    ADD = 0x10
    SUB = 0x11
    MUL = 0x12
    DIV = 0x13
    MOD = 0x14

    # Логика и сравнение
    CMP = 0x20
    NOT = 0x21

    # Переходы
    JMP = 0x30
    JZ = 0x31
    JNZ = 0x32
    JN = 0x33

    # Функции и Стек
    CALL = 0x40
    RET = 0x41
    PUSH = 0x42
    POP = 0x43
    LDS = 0x44
    STS = 0x45

    # Ввод-вывод
    IN = 0x50
    OUT = 0x51

    # Системные
    IRET = 0x61
    HLT = 0xFF


@dataclass
class Instruction:
    opcode: Opcode
    arg: int = 0

    def to_binary(self) -> int:
        mask = 0xFFFFFFFF
        return (self.opcode << 32) | (self.arg & mask)

    @staticmethod
    def from_binary(word: int) -> 'Instruction':
        opcode_val = (word >> 32) & 0xFF
        opcode = Opcode(opcode_val)

        arg = word & 0xFFFFFFFF

        if arg & 0x80000000:
            arg -= 0x100000000

        return Instruction(opcode, arg)