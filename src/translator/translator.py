from typing import Dict, Tuple

from src.machine.isa import Opcode, Instruction
from src.translator.definition import *
from src.translator.memory_mananger import MemoryManager


class Translator:
    def __init__(self, data_mem_size: int = 1024):
        self.instr_map: Dict[int, Instruction] = {}
        self.mem_manager = MemoryManager(data_mem_size=data_mem_size)
        # 0-16 зарезервировано под вектора прерываний
        self.instr_ptr = 17
        # Точка входа
        self.instr_map[0] = Instruction(Opcode.JMP, self.instr_ptr)

    def add_instr(self, opcode: Opcode, arg: int = 0) -> int:
        addr = self.instr_ptr
        self.instr_map[addr] = Instruction(opcode, arg)
        self.instr_ptr += 1
        return addr

    def translate(self, ast: List[Node]) -> Tuple[Dict[int, Instruction], Dict[int, int]]:
        """Превращает AST в готовые образы памяти команд и данных."""
        for node in ast:
            self.generate_code(node)
        self.add_instr(Opcode.HLT)
        return self.instr_map, self.mem_manager.get_data_map()

    def generate_code(self, node: Node):
        """Рекурсивный генератор кода для узлов AST."""
        if isinstance(node, NumberNode):
            self.add_instr(Opcode.LDI, node.value)

        elif isinstance(node, BooleanNode):
            self.add_instr(Opcode.LDI, 1 if node.value else 0)

        elif isinstance(node, SymbolNode):
            addr = self.mem_manager.get_variable_addr(node.name)
            self.add_instr(Opcode.LD, addr)

        elif isinstance(node, StringNode):
            # Литерал строки возвращает адрес её начала в памяти
            addr = self.mem_manager.allocate_string(node.value)
            self.add_instr(Opcode.LDI, addr)

        elif isinstance(node, DefNode):
            self.generate_code(node.expression)
            addr = self.mem_manager.define_variable(node.variable)
            self.add_instr(Opcode.ST, addr)

        elif isinstance(node, SetNode):
            self.generate_code(node.expression)
            addr = self.mem_manager.get_variable_addr(node.variable)
            self.add_instr(Opcode.ST, addr)

        elif isinstance(node, BlockNode):
            for expr in node.expressions:
                self.generate_code(expr)

        elif isinstance(node, IONode):
            if node.operation == "out":
                self.generate_code(node.expression)
                self.add_instr(Opcode.OUT, node.port)
            elif node.operation == "in":
                self.add_instr(Opcode.IN, node.port)

        elif isinstance(node, FunctionCallNode):
            self._translate_function_call(node)

        elif isinstance(node, IfNode):
            self._translate_if(node)

        elif isinstance(node, WhileNode):
            self._translate_while(node)


    def _translate_function_call(self, node: FunctionCallNode):
        math_map = {
            "+": Opcode.ADD, "-": Opcode.SUB, "*": Opcode.MUL,
            "/": Opcode.DIV, "%": Opcode.MOD
        }
        imm_map = {
            "+": Opcode.ADDI, "-": Opcode.SUBI, "*": Opcode.MULI,
            "/": Opcode.DIVI, "%": Opcode.MODI
        }

        if node.name in math_map:
            self.generate_code(node.args[0])

            for arg in node.args[1:]:
                if isinstance(arg, NumberNode):
                    self.add_instr(imm_map[node.name], arg.value)
                else:
                    tmp = self.mem_manager.allocate_temp()
                    self.add_instr(Opcode.ST, tmp)
                    self.generate_code(arg)
                    self.add_instr(Opcode.SWAP, tmp)
                    self.add_instr(math_map[node.name], tmp)
                    self.mem_manager.free_temp()

        elif node.name in ["=", "<", ">"]:
            self._translate_comparison(node)

    def _translate_comparison(self, node: FunctionCallNode):
        self.generate_code(node.args[0])
        tmp = self.mem_manager.allocate_temp()
        self.add_instr(Opcode.ST, tmp)
        self.generate_code(node.args[1])

        self.add_instr(Opcode.SWAP, tmp)
        self.add_instr(Opcode.CMP, tmp)
        self.mem_manager.free_temp()

        true_label_addr = 0  # Заглушка

        if node.name == "=":
            jz = self.add_instr(Opcode.JZ, 0)
            self.add_instr(Opcode.LDI, 0)
            jmp_end = self.add_instr(Opcode.JMP, 0)
            self.instr_map[jz].arg = self.instr_ptr  # true path
            self.add_instr(Opcode.LDI, 1)
            self.instr_map[jmp_end].arg = self.instr_ptr  # end

        elif node.name == "<":
            jn = self.add_instr(Opcode.JN, 0)
            self.add_instr(Opcode.LDI, 0)
            jmp_end = self.add_instr(Opcode.JMP, 0)
            self.instr_map[jn].arg = self.instr_ptr
            self.add_instr(Opcode.LDI, 1)
            self.instr_map[jmp_end].arg = self.instr_ptr

        elif node.name == ">":
            jn = self.add_instr(Opcode.JN, 0)
            jz = self.add_instr(Opcode.JZ, 0)
            self.add_instr(Opcode.LDI, 1)
            jmp_end = self.add_instr(Opcode.JMP, 0)

            false_path = self.instr_ptr
            self.instr_map[jn].arg = false_path
            self.instr_map[jz].arg = false_path
            self.add_instr(Opcode.LDI, 0)
            self.instr_map[jmp_end].arg = self.instr_ptr

    def _translate_if(self, node: IfNode):
        self.generate_code(node.condition)
        jz_else = self.add_instr(Opcode.JZ, 0)

        self.generate_code(node.then_block)
        jmp_end = self.add_instr(Opcode.JMP, 0)

        self.instr_map[jz_else].arg = self.instr_ptr
        self.generate_code(node.else_block)
        self.instr_map[jmp_end].arg = self.instr_ptr

    def _translate_while(self, node: WhileNode):
        start_addr = self.instr_ptr
        self.generate_code(node.condition)
        jz_exit = self.add_instr(Opcode.JZ, 0)

        self.generate_code(node.body)
        self.add_instr(Opcode.JMP, start_addr)
        self.instr_map[jz_exit].arg = self.instr_ptr