from dataclasses import dataclass
from typing import Any

from src.machine.isa import Instruction


class MemoryManager:
    def __init__(self, data_mem_size: int = 1024):
        self.data_mem_size = data_mem_size
        self.variables: dict[str, int] = {}
        self.data_map: dict[int, int] = {}
        self.SYS_TMP_ADDR = 0
        self.data_map[self.SYS_TMP_ADDR] = 0
        self.current_var_addr = 1

    def define_variable(self, name: str, value: int = 0) -> int:
        if name in self.variables:
            return self.variables[name]
        if self.current_var_addr >= self.data_mem_size:
            raise MemoryError(f"Data memory limit reached allocating '{name}'!")
        addr = self.current_var_addr
        self.variables[name] = addr
        self.data_map[addr] = value & 0xFFFFFFFF
        self.current_var_addr += 1
        return addr

    def get_variable_addr(self, name: str) -> int:
        if name not in self.variables:
            raise NameError(f"Undefined variable: '{name}'")
        return self.variables[name]

    def allocate_string(self, value: str) -> int:
        if self.current_var_addr + len(value) + 1 >= self.data_mem_size:
            raise MemoryError(f"Data memory limit reached allocating string '{value}'!")
        start_addr = self.current_var_addr
        for char in value:
            self.data_map[self.current_var_addr] = ord(char)
            self.current_var_addr += 1
        self.data_map[self.current_var_addr] = 0
        self.current_var_addr += 1
        return start_addr

    def allocate_space(self, size: int) -> int:
        if self.current_var_addr + size >= self.data_mem_size:
            raise MemoryError(f"Data memory limit reached while allocating buffer of size {size}!")
        start_addr = self.current_var_addr
        for i in range(size):
            self.data_map[self.current_var_addr + i] = 0
        self.current_var_addr += size
        return start_addr

    def set_value(self, addr: int, value: int) -> None:
        self.data_map[addr] = value

    def get_data_map(self) -> dict[int, int]:
        return self.data_map


@dataclass
class DeferredFunction:
    uid: str
    parameters: list[str]
    body_node: Any
    is_interrupt: bool = False


class Linker:
    UNRESOLVED_VALUE = 0xCCCCCCCC

    def __init__(self) -> None:
        self.deferred_queue: list[DeferredFunction] = []
        self.linking_map: dict[int, str] = {}
        self.resolved_addresses: dict[str, int] = {}
        self._lambda_counter = 0

    def register_lambda(self, parameters: list[str], body_node: Any, is_interrupt: bool = False) -> str:
        uid = f"lambda_{self._lambda_counter}"
        self._lambda_counter += 1
        self.deferred_queue.append(DeferredFunction(uid, parameters, body_node, is_interrupt))
        return uid

    def add_linking_point(self, instruction_address: int, uid: str) -> None:
        self.linking_map[instruction_address] = uid

    def has_deferred(self) -> bool:
        return len(self.deferred_queue) > 0

    def pop_deferred(self) -> DeferredFunction | None:
        return self.deferred_queue.pop(0) if self.deferred_queue else None

    def resolve_lambda(self, uid: str, address: int) -> None:
        self.resolved_addresses[uid] = address

    def link(self, instr_map: dict[int, Instruction]) -> None:
        for instr_addr, uid in self.linking_map.items():
            if uid not in self.resolved_addresses:
                raise NameError(f"Linker Error: undefined function '{uid}'")
            instr_map[instr_addr].arg = self.resolved_addresses[uid]
