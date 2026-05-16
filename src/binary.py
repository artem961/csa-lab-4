import struct
from typing import Dict, List, Tuple, Union
from src.machine.isa import Opcode, Instruction

MAGIC = b'CSA\0'
HEADER_FMT = '>4sIII'
SECTION_ENTRY_FMT = '>BII'
SECTION_ENTRY_SIZE = struct.calcsize(SECTION_ENTRY_FMT)

SECTION_TYPE_CODE = 0x01
SECTION_TYPE_DATA = 0x02


def _group_contiguous(addr_map: Dict[int, any]) -> List[Tuple[int, List[any]]]:
    if not addr_map: return []

    sorted_items = sorted(addr_map.items())
    groups, cur_list = [], []
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


def _write_listing(lf, stype: int, start: int, vals: list):
    for i, val in enumerate(vals):
        addr = start + i
        if stype == SECTION_TYPE_CODE:
            opcode, operand = _parse_instr(val)
            hexcode = ((opcode & 0xFF) << 32) | (operand & 0xFFFFFFFF)

            try:
                mnem = Opcode(opcode).name
            except ValueError:
                mnem = f"OP_{opcode:02X}"

            prefix = "#" if opcode in (Opcode.LDI.value, Opcode.LDS.value, Opcode.STS.value) else ""
            lf.write(f"{addr:04X} - {hexcode:010X} - {mnem.lower()} {prefix}{operand}\n")
        else:
            hex_val = int(val) & 0xFFFFFFFF
            lf.write(f"{addr:04X} - {hex_val:08X}   - DATA {val}\n")


def write_binary(file_path: str, instr_map: Union[Dict, List], data_map: Dict[int, int],
                 listing_path: str = None, instr_size: int = 1024, data_size: int = 1024) -> None:
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
                    f.write(struct.pack('>Bi', op, arg))
            else:
                for val in vals:
                    f.write(struct.pack('>i', int(val)))

    # Листинг
    if listing_path:
        with open(listing_path, 'w', encoding='utf-8') as lf:
            for stype, start, vals in sections:
                if stype == SECTION_TYPE_DATA: lf.write("--- DATA SECTION ---\n")
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