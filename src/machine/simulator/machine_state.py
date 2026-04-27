from dataclasses import dataclass
from typing import List, Set

@dataclass
class MachineState:
    tick: int
    state_name: str
    ip: int
    acc: int
    ar: int
    dr: int
    sp: int
    flags: dict
    signals: List[str]
    stack_view: List[int]
    current_opcode: str = ""