import struct
from typing import Any, Dict, List, Tuple, Union
from src.machine.isa import Opcode, Instruction

MAGIC = b'LISP'
HEADER_FMT = '>4sIII'
SECTION_ENTRY_FMT = '>BII'
SECTION_ENTRY_SIZE = struct.calcsize(SECTION_ENTRY_FMT)

SECTION_TYPE_CODE = 0x01
SECTION_TYPE_DATA = 0x02


def _to_int32(value: int) -> int:
    value &= 0xFFFFFFFF
    if value & 0x80000000:
        value -= 0x100000000
    return value


def _group_contiguous(addr_map: Dict[int, Any]) -> List[Tuple[int, List[Any]]]:
    if not addr_map:
        return []

    sorted_items = sorted(addr_map.items())
    groups: List[Tuple[int, List[Any]]] = []
    cur_list: List[Any] = []
    cur_start = prev_addr = sorted_items[0][0]

    for addr, val in sorted_items:
        if addr != prev_addr and addr != prev_addr + 1:
            groups.append((cur_start, cur_list))
            cur_start, cur_list = addr, []
        cur_list.append(val)
        prev_addr = addr

    groups.append((cur_start, cur_list))
    return groups


def _parse_instr(instr: Union[int, Instruction]) -> Tuple[int, int]:
    if isinstance(instr, Instruction):
        return (instr.opcode.value, instr.arg)

    opcode = (instr >> 32) & 0xFF
    operand = instr & 0xFFFFFFFF
    return (opcode, operand - 0x100000000 if operand & 0x80000000 else operand)


def _disasm(op: int, arg: int) -> str:
    """Расшифровывает инструкцию в читаемую мнемонику с описанием операции."""
    try:
        opc = Opcode(op)
    except ValueError:
        return f"op_{op:02X} {arg}"

    mem = f"[{arg}]"
    descr = {
        Opcode.NOP:  ("nop", ""),
        Opcode.LD:   (f"ld {mem}", f"AC <- Mem[{arg}]"),
        Opcode.ST:   (f"st {mem}", f"Mem[{arg}] <- AC"),
        Opcode.LDI:  (f"ldi {arg}", f"AC <- {arg}"),
        Opcode.SWAP: (f"swap {mem}", f"AC <-> Mem[{arg}]"),
        Opcode.LDA:  ("lda", "AC <- Mem[AC]"),
        Opcode.LID:  (f"lid {mem}", f"AC <- Mem[Mem[{arg}]]"),
        Opcode.SID:  (f"sid {mem}", f"Mem[Mem[{arg}]] <- AC"),
        Opcode.ADD:  (f"add {mem}", f"AC <- AC + Mem[{arg}]"),
        Opcode.SUB:  (f"sub {mem}", f"AC <- AC - Mem[{arg}]"),
        Opcode.MUL:  (f"mul {mem}", f"AC <- AC * Mem[{arg}]"),
        Opcode.DIV:  (f"div {mem}", f"AC <- AC / Mem[{arg}]"),
        Opcode.MOD:  (f"mod {mem}", f"AC <- AC % Mem[{arg}]"),
        Opcode.ADDI: (f"addi {arg}", f"AC <- AC + {arg}"),
        Opcode.SUBI: (f"subi {arg}", f"AC <- AC - {arg}"),
        Opcode.MULI: (f"muli {arg}", f"AC <- AC * {arg}"),
        Opcode.DIVI: (f"divi {arg}", f"AC <- AC / {arg}"),
        Opcode.MODI: (f"modi {arg}", f"AC <- AC % {arg}"),
        Opcode.CMP:  (f"cmp {mem}", f"flags(AC - Mem[{arg}])"),
        Opcode.CMPI: (f"cmpi {arg}", f"flags(AC - {arg})"),
        Opcode.NOT:  ("not", "AC <- ~AC"),
        Opcode.JMP:  (f"jmp {arg}", f"IP <- {arg}"),
        Opcode.JZ:   (f"jz {arg}", f"if Z: IP <- {arg}"),
        Opcode.JNZ:  (f"jnz {arg}", f"if !Z: IP <- {arg}"),
        Opcode.JN:   (f"jn {arg}", f"if N: IP <- {arg}"),
        Opcode.CALL: ("call", "push IP; IP <- AC"),
        Opcode.RET:  ("ret", "IP <- pop"),
        Opcode.PUSH: ("push", "Mem[SP] <- AC; SP--"),
        Opcode.POP:  ("pop", "SP++; AC <- Mem[SP]"),
        Opcode.LDS:  (f"lds +{arg}", f"AC <- Mem[SP+{arg}]"),
        Opcode.STS:  (f"sts +{arg}", f"Mem[SP+{arg}] <- AC"),
        Opcode.IN:   (f"in {arg}", f"AC <- Port[{arg}]"),
        Opcode.OUT:  (f"out {arg}", f"Port[{arg}] <- AC"),
        Opcode.IRET: ("iret", "restore PS, AC, IP"),
        Opcode.HLT:  ("hlt", "halt"),
    }

    mnem, comment = descr.get(opc, (f"{opc.name.lower()} {arg}", ""))
    return f"{mnem:<14} ; {comment}" if comment else mnem


def _write_listing(lf, stype: int, start: int, vals: list):
    for i, val in enumerate(vals):
        addr = start + i
        if stype == SECTION_TYPE_CODE:
            opcode, operand = _parse_instr(val)
            hexcode = ((opcode & 0xFF) << 32) | (operand & 0xFFFFFFFF)
            lf.write(f"{addr:04X} - {hexcode:010X} - {_disasm(opcode, operand)}\n")
        else:
            ival = int(val)
            hex_val = ival & 0xFFFFFFFF
            if 32 <= ival <= 126:
                body = f"data {ival:<3}   ('{chr(ival)}')"
            else:
                body = f"data {ival}"
            lf.write(f"{addr:04X} - {hex_val:08X}   - {body}\n")


def write_binary(file_path: str, instr_map: Union[Dict, List], data_map: Dict[int, int],
                 listing_path: str | None = None, instr_size: int = 1024, data_size: int = 1024) -> None:
    """Записывает бинарный файл с заголовком и секциями."""

    if isinstance(instr_map, list):
        instr_map = {i: v for i, v in enumerate(instr_map) if v is not None}

    sections = [
                   (SECTION_TYPE_CODE, start, vals) for start, vals in _group_contiguous(instr_map)
               ] + [
                   (SECTION_TYPE_DATA, start, vals) for start, vals in _group_contiguous(data_map or {})
               ]

    with open(file_path, 'wb') as f:
        # Заголовок
        f.write(struct.pack(HEADER_FMT, MAGIC, len(sections), instr_size, data_size))

        # Таблица секций
        for stype, start, vals in sections:
            f.write(struct.pack(SECTION_ENTRY_FMT, stype, start, len(vals)))

        # Данные секций
        for stype, _, vals in sections:
            if stype == SECTION_TYPE_CODE:
                for instr in vals:
                    op, arg = _parse_instr(instr)
                    f.write(struct.pack('>Bi', op, _to_int32(arg)))
            else:
                for val in vals:
                    f.write(struct.pack('>i', _to_int32(int(val))))

    # Листинг
    if listing_path:
        with open(listing_path, 'w', encoding='utf-8') as lf:
            for idx, (stype, start, vals) in enumerate(sections):
                if idx > 0:
                    lf.write("\n")
                seg = "CODE" if stype == SECTION_TYPE_CODE else "DATA"
                lf.write(f"--- {seg} @ 0x{start:04X} ---\n")
                _write_listing(lf, stype, start, vals)


def read_binary(file_path: str) -> Tuple[List[int], List[int]]:
    """Читает бинарный файл, возвращая массивы памяти нужного размера."""
    with open(file_path, 'rb') as f:
        header = f.read(struct.calcsize(HEADER_FMT))
        magic, s_count, i_size, d_size = struct.unpack(HEADER_FMT, header)

        if magic != MAGIC:
            raise ValueError(f"Invalid magic number: {magic}")

        sections = [struct.unpack(SECTION_ENTRY_FMT, f.read(SECTION_ENTRY_SIZE))
                    for _ in range(s_count)]

        instr_mem, data_mem = [0] * i_size, [0] * d_size

        # Заполняем память
        for stype, start, count in sections:
            if stype == SECTION_TYPE_CODE:
                for i in range(count):
                    op, arg = struct.unpack('>Bi', f.read(5))
                    instr_mem[start + i] = ((op & 0xFF) << 32) | (arg & 0xFFFFFFFF)
            elif stype == SECTION_TYPE_DATA:
                for i in range(count):
                    data_mem[start + i] = struct.unpack('>i', f.read(4))[0]

    return instr_mem, data_mem