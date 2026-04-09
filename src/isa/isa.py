from enum import IntEnum, unique
from dataclasses import dataclass


@unique
class Opcode(IntEnum):
    # Память (AC <-> Memory)
    LD = 0x01  # Загрузить из памяти в AC (LD addr)
    ST = 0x02  # Сохранить AC в память (ST addr)
    LDI = 0x03  # Загрузить константу в AC (LDI imm)

    # Арифметика (AC = AC op Mem)
    ADD = 0x10
    SUB = 0x11
    MUL = 0x12
    DIV = 0x13
    MOD = 0x14

    # Логика и сравнение
    CMP = 0x20  # Сравнить AC с операндом (выставляет флаги)
    NOT = 0x21  # Инверсия AC

    # Переходы
    JMP = 0x30  # Безусловный
    JZ = 0x31  # Переход если Zero (результат 0)
    JNZ = 0x32  # Переход если Not Zero

    # Функции и Стек
    CALL = 0x40  # Вызов функции (сохранение IP в стек)
    RET = 0x41  # Возврат из функции
    PUSH = 0x42  # Положить AC в стек
    POP = 0x43  # Достать из стека в AC

    # Ввод-вывод и Системные
    IN = 0x50  # Чтение из порта в AC (IN port)
    OUT = 0x51  # Запись из AC в порт (OUT port)
    TRAP = 0x60  # Программное прерывание
    IRET = 0x61  # Возврат из обработчика прерывания
    HLT = 0xFF  # Остановка


@dataclass
class Instruction:
    opcode: Opcode
    arg: int = 0  # 24-битный операнд (адрес или константа)

    def to_binary(self) -> int:
        """Склеивает 8 бит опкода и 24 бита аргумента в 32-битное число."""
        # Обработка отрицательных чисел (2's complement для 24 бит)
        mask = (1 << 24) - 1
        safe_arg = self.arg & mask
        return (self.opcode << 24) | safe_arg

    @staticmethod
    def from_binary(word: int) -> 'Instruction':
        """Восстанавливает инструкцию из 32-битного числа."""
        opcode = Opcode((word >> 24) & 0xFF)
        arg = word & 0x00FFFFFF
        # Восстановление знака для 24-битного числа
        if arg & (1 << 23):
            arg -= (1 << 24)
        return Instruction(opcode, arg)