from typing import Dict, List, Tuple
from src.machine.isa import Opcode, Instruction
from src.translator.definition import *
from src.translator.memory_mananger import MemoryManager
from src.translator.linker import Linker


class Translator:
    def __init__(self, data_mem_size: int = 1024):
        self.instr_map: Dict[int, Instruction] = {}
        self.mem_manager = MemoryManager(data_mem_size=data_mem_size)
        self.linker = Linker()

        self.current_scope: Dict[str, int] = {}
        self.stack_offset = 0

        # Обработчик прерываний по умолчанию
        self.default_handler_uid = self.linker.register_lambda(
            parameters=[],
            body_node=BlockNode(expressions=[]),
            is_interrupt=True
        )

        # Заполнение таблицы векторов прерываний
        for vector_addr in range(1, 17):
            self.instr_map[vector_addr] = Instruction(Opcode.JMP, self.linker.UNRESOLVED_VALUE)
            self.linker.add_linking_point(vector_addr, self.default_handler_uid)

        self.instr_ptr = 17

        # Точка входа
        self.instr_map[0] = Instruction(Opcode.JMP, self.instr_ptr)

    def _add_instr(self, opcode: Opcode, arg: int = 0) -> int:
        addr = self.instr_ptr
        self.instr_map[addr] = Instruction(opcode, arg)
        self.instr_ptr += 1

        if opcode == Opcode.PUSH:
            self.stack_offset += 1
        elif opcode == Opcode.POP:
            self.stack_offset -= 1

        return addr

    def translate(self, ast: List[Node]) -> Tuple[Dict[int, Instruction], Dict[int, int]]:
        self.stack_offset = 0
        for node in ast:
            self.generate_code(node)

        self._add_instr(Opcode.HLT)

        # Генерация функций
        while self.linker.has_deferred():
            func = self.linker.pop_deferred()
            self.linker.resolve_lambda(func.uid, self.instr_ptr)

            self.current_scope = {
                param: len(func.parameters) - i + 1
                for i, param in enumerate(func.parameters)
            }
            self.stack_offset = 0

            self.generate_code(func.body_node)

            if func.is_interrupt:
                self._add_instr(Opcode.IRET)
            else:
                self._add_instr(Opcode.RET)

        # Очистка и связывание
        self.current_scope = {}
        self.linker.link(self.instr_map)

        return self.instr_map, self.mem_manager.get_data_map()

    def generate_code(self, node: Node):
        if isinstance(node, NumberNode):
            self._add_instr(Opcode.LDI, node.value)

        elif isinstance(node, BooleanNode):
            self._add_instr(Opcode.LDI, 1 if node.value else 0)

        elif isinstance(node, SymbolNode):
            if node.name in self.current_scope:
                self._add_instr(Opcode.LDS, self.current_scope[node.name] + self.stack_offset)
            else:
                self._add_instr(Opcode.LD, self.mem_manager.get_variable_addr(node.name))

        elif isinstance(node, StringNode):
            addr = self.mem_manager.allocate_string(node.value)
            self._add_instr(Opcode.LDI, addr)

        elif isinstance(node, LambdaNode):
            uid = self.linker.register_lambda(node.parameters, node.body)
            addr = self._add_instr(Opcode.LDI, self.linker.UNRESOLVED_VALUE)
            self.linker.add_linking_point(addr, uid)

        elif isinstance(node, DefNode):
            self.generate_code(node.expression)
            addr = self.mem_manager.define_variable(node.variable)
            self._add_instr(Opcode.ST, addr)

        elif isinstance(node, SetNode):
            self.generate_code(node.expression)
            if node.variable in self.current_scope:
                self._add_instr(Opcode.STS, self.current_scope[node.variable] + self.stack_offset)
            else:
                self._add_instr(Opcode.ST, self.mem_manager.get_variable_addr(node.variable))

        elif isinstance(node, BlockNode):
            for expr in node.expressions:
                self.generate_code(expr)

        elif isinstance(node, IONode):
            if node.operation == "out":
                self.generate_code(node.expression)
                self._add_instr(Opcode.OUT, node.port)
            elif node.operation == "in":
                self._add_instr(Opcode.IN, node.port)

        elif isinstance(node, FunctionCallNode):
            self._translate_function_call(node)

        elif isinstance(node, IfNode):
            self._translate_if(node)

        elif isinstance(node, WhileNode):
            self._translate_while(node)

        elif isinstance(node, InterruptHandlerNode):
            uid = self.linker.register_lambda(
                node.handler.parameters,
                node.handler.body,
                is_interrupt=True
            )
            self.linker.add_linking_point(node.interrupt_code, uid)

    def _translate_function_call(self, node: FunctionCallNode):
        math_map = {"+": Opcode.ADD, "-": Opcode.SUB, "*": Opcode.MUL, "/": Opcode.DIV, "%": Opcode.MOD}
        imm_map = {"+": Opcode.ADDI, "-": Opcode.SUBI, "*": Opcode.MULI, "/": Opcode.DIVI, "%": Opcode.MODI}

        if node.name in math_map:
            self.generate_code(node.args[0])

            for arg in node.args[1:]:
                if isinstance(arg, NumberNode):
                    self._add_instr(imm_map[node.name], arg.value)
                else:
                    self._add_instr(Opcode.PUSH, 0)  # Сохраняем левый аргумент
                    self.generate_code(arg)  # Считаем правый
                    self._add_instr(Opcode.ST, self.mem_manager.SYS_TMP_ADDR)  # AC -> SYS_TMP
                    self._add_instr(Opcode.POP, 0)  # Достаем левый обратно в AC
                    self._add_instr(math_map[node.name], self.mem_manager.SYS_TMP_ADDR)

        elif node.name in ["=", "<", ">"]:
            self._translate_comparison(node)

        else:
            # Положить аргументы на стек
            for arg in node.args:
                self.generate_code(arg)
                self._add_instr(Opcode.PUSH, 0)

            # Загрузить адрес функции в AC
            if node.name in self.current_scope:
                actual_offset = self.current_scope[node.name] + self.stack_offset
                self._add_instr(Opcode.LDS, actual_offset)
            else:
                addr = self.mem_manager.get_variable_addr(node.name)
                self._add_instr(Opcode.LD, addr)

            self._add_instr(Opcode.CALL, 0)

            # Очистка стека от аргументов с сохранением результата
            if node.args:
                self._add_instr(Opcode.ST, self.mem_manager.SYS_TMP_ADDR)
                for _ in node.args:
                    self._add_instr(Opcode.POP, 0)
                self._add_instr(Opcode.LD, self.mem_manager.SYS_TMP_ADDR)

    def _translate_comparison(self, node: FunctionCallNode):
        self.generate_code(node.args[0])
        self._add_instr(Opcode.PUSH, 0)

        self.generate_code(node.args[1])
        self._add_instr(Opcode.ST, self.mem_manager.SYS_TMP_ADDR)

        self._add_instr(Opcode.POP, 0)
        self._add_instr(Opcode.CMP, self.mem_manager.SYS_TMP_ADDR)

        if node.name == "=":
            jz = self._add_instr(Opcode.JZ, 0)
            self._add_instr(Opcode.LDI, 0)
            jmp = self._add_instr(Opcode.JMP, 0)
            self.instr_map[jz].arg = self.instr_ptr
            self._add_instr(Opcode.LDI, 1)
            self.instr_map[jmp].arg = self.instr_ptr

        elif node.name == "<":
            jn = self._add_instr(Opcode.JN, 0)
            self._add_instr(Opcode.LDI, 0)
            jmp = self._add_instr(Opcode.JMP, 0)
            self.instr_map[jn].arg = self.instr_ptr
            self._add_instr(Opcode.LDI, 1)
            self.instr_map[jmp].arg = self.instr_ptr

        elif node.name == ">":
            jn = self._add_instr(Opcode.JN, 0)
            jz = self._add_instr(Opcode.JZ, 0)
            self._add_instr(Opcode.LDI, 1)
            jmp = self._add_instr(Opcode.JMP, 0)

            false_path = self.instr_ptr
            self.instr_map[jn].arg = false_path
            self.instr_map[jz].arg = false_path
            self._add_instr(Opcode.LDI, 0)
            self.instr_map[jmp].arg = self.instr_ptr

    def _translate_if(self, node: IfNode):
        self.generate_code(node.condition)
        jz = self._add_instr(Opcode.JZ, 0)

        self.generate_code(node.then_block)
        jmp = self._add_instr(Opcode.JMP, 0)

        self.instr_map[jz].arg = self.instr_ptr
        self.generate_code(node.else_block)
        self.instr_map[jmp].arg = self.instr_ptr

    def _translate_while(self, node: WhileNode):
        start_addr = self.instr_ptr
        self.generate_code(node.condition)
        jz = self._add_instr(Opcode.JZ, 0)

        self.generate_code(node.body)
        self._add_instr(Opcode.JMP, start_addr)
        self.instr_map[jz].arg = self.instr_ptr