from enum import Enum, auto


class Signal(Enum):
    # Защёлки
    LATCH_AC = auto()
    LATCH_IP = auto()
    LATCH_SP = auto()
    LATCH_AR = auto()
    LATCH_DR = auto()
    LATCH_IR = auto()
    LATCH_IO = auto()
    LATCH_PS = auto()
    LATCH_IO_ADDR = auto()

    # MUX перед AR
    SEL_AR_IR = auto()
    SEL_AR_ALU = auto()
    SEL_AR_SP = auto()

    # MUX перед DATA MEM
    SEL_DM_AC = auto()
    SEL_DM_IP = auto()
    SEL_DM_PS = auto()

    # MUX перед AC
    SEL_AC_ALU = auto()
    SEL_AC_IO = auto()

    # MUX перед IP
    SEL_IP_IR = auto()
    SEL_IP_ALU = auto()

    # MUX перед DR
    SEL_DR_IR = auto()
    SEL_DR_DATA_MEM = auto()

    # MUX левого входа АЛУ
    SEL_ALU_L_AC = auto()
    SEL_ALU_L_SP = auto()
    SEL_ALU_L_ZERO = auto()

    # MUX правого входа АЛУ
    SEL_ALU_R_DR = auto()
    SEL_ALU_R_IP = auto()
    SEL_ALU_R_ZERO = auto()

    # Операции АЛУ
    ALU_ADD = auto()
    ALU_INC = auto()
    ALU_DEC = auto()
    ALU_SUB = auto()
    ALU_MUL = auto()
    ALU_DIV = auto()
    ALU_MOD = auto()
    ALU_CMP = auto()
    ALU_NOT = auto()

    # Управление памятью и портами
    DATA_MEM_READ = auto()
    DATA_MEM_WRITE = auto()
    INSTR_MEM_READ = auto()
    IO_READ = auto()
    IO_WRITE = auto()

    # Служебные сигналы CU
    HALT = auto()

    # Прерывания
    ENABLE_INTERRUPTS = auto()
    DISABLE_INTERRUPTS = auto()