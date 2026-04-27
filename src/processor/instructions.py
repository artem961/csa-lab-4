from src.processor.signals import Signal
from src.isa.isa import Opcode

INSTRUCTION_TICKS = {
    # Память
    Opcode.LD: [
        {Signal.SEL_AR_IR, Signal.LATCH_AR},
        {Signal.DATA_MEM_READ, Signal.SEL_DR_DATA_MEM, Signal.LATCH_DR},
        {Signal.SEL_ALU_L_ZERO, Signal.SEL_ALU_R_DR, Signal.ALU_ADD, Signal.SEL_AC_ALU, Signal.LATCH_AC}
    ],

    Opcode.ST: [
        {Signal.SEL_AR_IR, Signal.LATCH_AR},
        {Signal.SEL_DM_AC, Signal.DATA_MEM_WRITE}
    ],

    Opcode.LDI: [
        {Signal.SEL_DR_IR, Signal.LATCH_DR},
        {Signal.SEL_ALU_L_ZERO, Signal.SEL_ALU_R_DR, Signal.ALU_ADD, Signal.SEL_AC_ALU, Signal.LATCH_AC}
    ],

    # Арифметика
    Opcode.ADD: [
        {Signal.SEL_AR_IR, Signal.LATCH_AR},
        {Signal.DATA_MEM_READ, Signal.SEL_DR_DATA_MEM, Signal.LATCH_DR},
        {Signal.SEL_ALU_L_AC, Signal.SEL_ALU_R_DR, Signal.ALU_ADD, Signal.SEL_AC_ALU, Signal.LATCH_AC}
    ],

    Opcode.SUB: [
        {Signal.SEL_AR_IR, Signal.LATCH_AR},
        {Signal.DATA_MEM_READ, Signal.SEL_DR_DATA_MEM, Signal.LATCH_DR},
        {Signal.SEL_ALU_L_AC, Signal.SEL_ALU_R_DR, Signal.ALU_SUB, Signal.SEL_AC_ALU, Signal.LATCH_AC}
    ],

    Opcode.MUL: [
        {Signal.SEL_AR_IR, Signal.LATCH_AR},
        {Signal.DATA_MEM_READ, Signal.SEL_DR_DATA_MEM, Signal.LATCH_DR},
        {Signal.SEL_ALU_L_AC, Signal.SEL_ALU_R_DR, Signal.ALU_MUL, Signal.SEL_AC_ALU, Signal.LATCH_AC}
    ],

    Opcode.DIV: [
        {Signal.SEL_AR_IR, Signal.LATCH_AR},
        {Signal.DATA_MEM_READ, Signal.SEL_DR_DATA_MEM, Signal.LATCH_DR},
        {Signal.SEL_ALU_L_AC, Signal.SEL_ALU_R_DR, Signal.ALU_DIV, Signal.SEL_AC_ALU, Signal.LATCH_AC}
    ],

    Opcode.MOD: [
        {Signal.SEL_AR_IR, Signal.LATCH_AR},
        {Signal.DATA_MEM_READ, Signal.SEL_DR_DATA_MEM, Signal.LATCH_DR},
        {Signal.SEL_ALU_L_AC, Signal.SEL_ALU_R_DR, Signal.ALU_MOD, Signal.SEL_AC_ALU, Signal.LATCH_AC}
    ],

    # Логика и сравнение
    Opcode.CMP: [
        {Signal.SEL_AR_IR, Signal.LATCH_AR},
        {Signal.DATA_MEM_READ, Signal.SEL_DR_DATA_MEM, Signal.LATCH_DR},
        {Signal.SEL_ALU_L_AC, Signal.SEL_ALU_R_DR, Signal.ALU_CMP}
    ],

    Opcode.NOT: [
        {Signal.SEL_ALU_L_AC, Signal.SEL_ALU_R_ZERO, Signal.ALU_NOT, Signal.SEL_AC_ALU, Signal.LATCH_AC}
    ],

    # Переходы
    Opcode.JMP: [
        {Signal.SEL_IP_IR, Signal.LATCH_IP}
    ],

    # Функции и Стек
    Opcode.CALL: [
        {Signal.SEL_AR_SP, Signal.LATCH_AR},
        {Signal.SEL_DM_IP, Signal.DATA_MEM_WRITE},
        {Signal.SEL_ALU_L_SP, Signal.ALU_DEC, Signal.LATCH_SP},
        {Signal.SEL_IP_IR, Signal.LATCH_IP}
    ],

    Opcode.RET: [
        {Signal.SEL_ALU_L_SP, Signal.ALU_INC, Signal.LATCH_SP},
        {Signal.SEL_AR_SP, Signal.LATCH_AR},
        {Signal.DATA_MEM_READ, Signal.SEL_DR_DATA_MEM, Signal.LATCH_DR},
        {Signal.SEL_ALU_L_ZERO, Signal.SEL_ALU_R_DR, Signal.ALU_ADD, Signal.SEL_IP_ALU, Signal.LATCH_IP}
    ],

    Opcode.PUSH: [
        {Signal.SEL_AR_SP, Signal.LATCH_AR},
        {Signal.SEL_DM_AC, Signal.DATA_MEM_WRITE},
        {Signal.SEL_ALU_L_SP, Signal.ALU_DEC, Signal.LATCH_SP}
    ],

    Opcode.POP: [
        {Signal.SEL_ALU_L_SP, Signal.ALU_INC, Signal.LATCH_SP},
        {Signal.SEL_AR_SP, Signal.LATCH_AR},
        {Signal.DATA_MEM_READ, Signal.SEL_DR_DATA_MEM, Signal.LATCH_DR},
        {Signal.SEL_ALU_L_ZERO, Signal.SEL_ALU_R_DR, Signal.ALU_ADD, Signal.SEL_AC_ALU, Signal.LATCH_AC}
    ],

    Opcode.LDS: [
        {Signal.SEL_DR_IR, Signal.LATCH_DR},
        {Signal.SEL_ALU_L_SP, Signal.SEL_ALU_R_DR, Signal.ALU_ADD, Signal.LATCH_AR, Signal.SEL_AR_ALU},
        {Signal.DATA_MEM_READ, Signal.SEL_DR_DATA_MEM, Signal.LATCH_DR},
        {Signal.SEL_ALU_L_ZERO, Signal.SEL_ALU_R_DR, Signal.ALU_ADD, Signal.SEL_AC_ALU, Signal.LATCH_AC}
    ],

    Opcode.STS: [
        {Signal.SEL_DR_IR, Signal.LATCH_DR},
        {Signal.SEL_ALU_L_SP, Signal.SEL_ALU_R_DR, Signal.ALU_ADD, Signal.LATCH_AR, Signal.SEL_AR_ALU},
        {Signal.SEL_DM_AC, Signal.DATA_MEM_WRITE}
    ],

    # Ввод-вывод
    Opcode.IN: [
        {Signal.LATCH_IO_ADDR},
        {Signal.IO_READ, Signal.SEL_AC_IO, Signal.LATCH_AC}
    ],

    Opcode.OUT: [
        {Signal.LATCH_IO_ADDR},
        {Signal.IO_WRITE}
    ],

    # Системные
    Opcode.IRET: [
        # Restore PS
        {Signal.SEL_ALU_L_SP, Signal.ALU_INC, Signal.LATCH_SP},
        {Signal.SEL_AR_SP, Signal.LATCH_AR},
        {Signal.DATA_MEM_READ, Signal.SEL_DR_DATA_MEM, Signal.LATCH_DR},
        {Signal.LATCH_PS},

        # Restore AC
        {Signal.SEL_ALU_L_SP, Signal.ALU_INC, Signal.LATCH_SP},
        {Signal.SEL_AR_SP, Signal.LATCH_AR},
        {Signal.DATA_MEM_READ, Signal.SEL_DR_DATA_MEM, Signal.LATCH_DR},
        {Signal.SEL_ALU_L_ZERO, Signal.SEL_ALU_R_DR, Signal.ALU_ADD, Signal.SEL_AC_ALU, Signal.LATCH_AC},

        # Restore IP
        {Signal.SEL_ALU_L_SP, Signal.ALU_INC, Signal.LATCH_SP},
        {Signal.SEL_AR_SP, Signal.LATCH_AR},
        {Signal.DATA_MEM_READ, Signal.SEL_DR_DATA_MEM, Signal.LATCH_DR},
        {Signal.SEL_ALU_L_ZERO, Signal.SEL_ALU_R_DR, Signal.ALU_ADD, Signal.SEL_IP_ALU, Signal.LATCH_IP}
    ],

    Opcode.HLT: [
        {Signal.HALT}
    ]
}
