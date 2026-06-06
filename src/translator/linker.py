from dataclasses import dataclass
from typing import Any, List, Dict, Optional
from src.machine.isa import Instruction

@dataclass
class DeferredFunction:
    uid: str
    parameters: List[str]
    body_node: Any
    is_interrupt: bool = False

class Linker:
    UNRESOLVED_VALUE = 0xCCCCCCCC

    def __init__(self):
        self.deferred_queue: List[DeferredFunction] = []
        self.linking_map: Dict[int, str] = {} # addr -> uid
        self.resolved_addresses: Dict[str, int] = {} # uid -> addr
        self._lambda_counter = 0

    def register_lambda(self, parameters: List[str], body_node: Any, is_interrupt = False) -> str:
        uid = f"lambda_{self._lambda_counter}"
        self._lambda_counter += 1
        self.deferred_queue.append(DeferredFunction(uid, parameters, body_node, is_interrupt))
        return uid

    def add_linking_point(self, instruction_address: int, uid: str):
        self.linking_map[instruction_address] = uid

    def has_deferred(self) -> bool:
        return len(self.deferred_queue) > 0

    def pop_deferred(self) -> Optional[DeferredFunction]:
        return self.deferred_queue.pop(0) if self.deferred_queue else None

    def resolve_lambda(self, uid: str, address: int):
        self.resolved_addresses[uid] = address

    def link(self, instr_map: Dict[int, Instruction]):
        for instr_addr, uid in self.linking_map.items():
            if uid not in self.resolved_addresses:
                raise NameError(f"Linker Error: undefined function '{uid}'")
            instr_map[instr_addr].arg = self.resolved_addresses[uid]