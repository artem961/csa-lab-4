from typing import Dict


class MemoryManager:
    def __init__(self, data_mem_size: int = 1024):
        self.data_mem_size = data_mem_size

        self.variables: Dict[str, int] = {} # name -> address

        # Образ статической памяти
        self.data_map: Dict[int, int] = {}

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

        self.data_map[self.current_var_addr] = 0  # null-terminator
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

    def get_data_map(self) -> Dict[int, int]:
        return self.data_map