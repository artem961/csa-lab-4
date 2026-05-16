from typing import Dict, Tuple


class MemoryManager:
    def __init__(self, data_mem_size: int = 1024, temp_pool_size: int = 256):
        self.data_mem_size = data_mem_size
        self.temp_pool_size = temp_pool_size

        # Таблица переменных: имя переменной -> адрес в памяти
        self.variables: Dict[str, int] = {}

        # Образ памяти
        self.data_map: Dict[int, int] = {}

        # Пул адресов временных переменных
        self.TEMP_BASE = 0
        self.current_temp_idx = 0

        # Зона статических данных
        self.VAR_BASE = self.temp_pool_size
        self.current_var_addr = self.VAR_BASE

    def define_variable(self, name: str, value: int = 0) -> int:
        if name in self.variables:
            addr = self.variables[name]
        else:
            if self.current_var_addr >= self.data_mem_size:
                raise MemoryError(f"Data memory limit reached while allocating '{name}' variable!")

            addr = self.current_var_addr
            self.variables[name] = addr
            self.current_var_addr += 1

        self.data_map[addr] = value & 0xFFFFFFFF
        return addr

    def get_variable_addr(self, name: str) -> int:
        if name not in self.variables:
            raise NameError(f"Undefined variable: '{name}'!")
        return self.variables[name]

    def has_variable(self, name: str) -> bool:
        return name in self.variables


    def allocate_string(self, value: str) -> int:
        if self.current_var_addr + len(value) + 1 >= self.data_mem_size:
            raise MemoryError(f"Data memory limit reached while allocating '{value}' string!")

        start_addr = self.current_var_addr

        for char in value:
            self.data_map[self.current_var_addr] = ord(char)
            self.current_var_addr += 1

        # Записываем нуль-терминатор
        self.data_map[self.current_var_addr] = 0
        self.current_var_addr += 1

        return start_addr

    def allocate_temp(self) -> int:
        if self.current_temp_idx >= self.temp_pool_size:
            raise MemoryError("Temp memory pool limit reached!")

        addr = self.TEMP_BASE + self.current_temp_idx
        self.current_temp_idx += 1
        return addr

    def free_temp(self):
        if self.current_temp_idx <= 0:
            raise RuntimeError("Temp pool is already empty!")
        self.current_temp_idx -= 1

    def assert_temp_pool_empty(self):
        if self.current_temp_idx != 0:
            raise RuntimeError(f"Temp pool leak detected! {self.current_temp_idx} cells not free.")


    def get_data_map(self) -> Dict[int, int]:
        return self.data_map