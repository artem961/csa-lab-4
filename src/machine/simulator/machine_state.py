from dataclasses import dataclass


@dataclass
class MachineState:
    tick: int
    instruction: str
    state_name: str
    ip: int
    acc: int
    ar: int
    dr: int
    sp: int
    flags: dict[str, bool]
    signals: list[str]
    stack_view: list[int]