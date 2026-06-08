from typing import Any

from src.machine.isa import Instruction, Opcode
from src.translator.definition import *
from src.translator.tools import Linker, MemoryManager


class Translator:
    def __init__(self, data_mem_size: int = 1024):
        self.instr_map: dict[int, Instruction] = {}
        self.mem_manager = MemoryManager(data_mem_size=data_mem_size)
        self.linker = Linker()

        self.current_scope: dict[str, int] = {}
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

    def translate(self, ast: list[Node]) -> tuple[dict[int, Instruction], dict[int, int]]:
        self.stack_offset = 0
        for node in ast:
            self.generate_code(node)

        self._add_instr(Opcode.HLT)

        # Генерация функций
        while self.linker.has_deferred():
            func = self.linker.pop_deferred()
            if func is None:
                continue
            self.linker.resolve_lambda(func.uid, self.instr_ptr)

            self.current_scope = {
                param: len(func.parameters) - i + 1
                for i, param in enumerate(func.parameters)
            }
            self.stack_offset = 0

            if func.is_interrupt:
                self._add_instr(Opcode.LD, self.mem_manager.SYS_TMP_ADDR)
                self._add_instr(Opcode.PUSH)
                self.generate_code(func.body_node)
                self._add_instr(Opcode.POP)
                self._add_instr(Opcode.ST, self.mem_manager.SYS_TMP_ADDR)
                self._add_instr(Opcode.IRET)
            else:
                self.generate_code(func.body_node)
                self._add_instr(Opcode.RET)

        # Очистка и связывание
        self.current_scope = {}
        self.linker.link(self.instr_map)

        return self.instr_map, self.mem_manager.get_data_map()

    def generate_code(self, node: Any) -> None:
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
            elif node.operation == "out-str":
                self.generate_code(node.expression)
                ptr_tmp = self.mem_manager.SYS_TMP_ADDR
                self._add_instr(Opcode.ST, ptr_tmp)

                start_loop = self.instr_ptr

                self._add_instr(Opcode.LD, ptr_tmp)
                self._add_instr(Opcode.LDA, 0)

                jz_exit = self._add_instr(Opcode.JZ, 0)
                self._add_instr(Opcode.OUT, node.port)

                self._add_instr(Opcode.LD, ptr_tmp)
                self._add_instr(Opcode.ADDI, 1)
                self._add_instr(Opcode.ST, ptr_tmp)

                self._add_instr(Opcode.JMP, start_loop)

                self.instr_map[jz_exit].arg = self.instr_ptr

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
                is_interrupt=True,
            )
            self.linker.add_linking_point(node.interrupt_code, uid)


        elif isinstance(node, DefArrayNode):
            if node.name == "alloc":
                size = node.size.value if isinstance(node.size, NumberNode) else 0
                addr = self.mem_manager.allocate_space(size)
                self._add_instr(Opcode.LDI, addr)

            elif node.name == "array":
                args = node.args or []
                size = len(args)
                start_addr = self.mem_manager.allocate_space(size)

                for i, arg in enumerate(args):
                    target_cell = start_addr + i
                    if isinstance(arg, NumberNode):
                        self.mem_manager.set_value(target_cell, arg.value)
                    elif isinstance(arg, BooleanNode):
                        self.mem_manager.set_value(target_cell, 1 if arg.value else 0)
                    else:
                        self.generate_code(arg)
                        self._add_instr(Opcode.ST, target_cell)
                self._add_instr(Opcode.LDI, start_addr)

        elif isinstance(node, ArrayOpsNode):
            if node.name == "aref":
                self._translate_aref(node)
            elif node.name == "aset":
                self._translate_aset(node)

    def _translate_function_call(self, node: FunctionCallNode) -> None:
        math_map = {"+": Opcode.ADD, "-": Opcode.SUB, "*": Opcode.MUL, "/": Opcode.DIV, "%": Opcode.MOD}
        imm_map = {"+": Opcode.ADDI, "-": Opcode.SUBI, "*": Opcode.MULI, "/": Opcode.DIVI, "%": Opcode.MODI}

        if node.name in math_map:
            self.generate_code(node.args[0])

            for arg in node.args[1:]:
                if isinstance(arg, NumberNode):
                    self._add_instr(imm_map[node.name], arg.value)
                else:
                    self._add_instr(Opcode.PUSH, 0)
                    self.generate_code(arg)
                    self._add_instr(Opcode.ST, self.mem_manager.SYS_TMP_ADDR)
                    self._add_instr(Opcode.POP, 0)
                    self._add_instr(math_map[node.name], self.mem_manager.SYS_TMP_ADDR)

        elif node.name in ["=", "<", ">"]:
            self._translate_comparison(node)

        else:
            for arg in node.args:
                self.generate_code(arg)
                self._add_instr(Opcode.PUSH, 0)

            if node.name in self.current_scope:
                self._add_instr(Opcode.LDS, self.current_scope[node.name] + self.stack_offset)
            else:
                self._add_instr(Opcode.LD, self.mem_manager.get_variable_addr(node.name))

            self._add_instr(Opcode.CALL, 0)

            if node.args:
                self._add_instr(Opcode.ST, self.mem_manager.SYS_TMP_ADDR)
                for _ in node.args:
                    self._add_instr(Opcode.POP, 0)
                self._add_instr(Opcode.LD, self.mem_manager.SYS_TMP_ADDR)

    def _translate_comparison(self, node: FunctionCallNode) -> None:
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

    def _translate_if(self, node: IfNode) -> None:
        self.generate_code(node.condition)
        jz = self._add_instr(Opcode.JZ, 0)

        self.generate_code(node.then_block)
        jmp = self._add_instr(Opcode.JMP, 0)

        self.instr_map[jz].arg = self.instr_ptr
        self.generate_code(node.else_block)
        self.instr_map[jmp].arg = self.instr_ptr

    def _translate_while(self, node: WhileNode) -> None:
        start_addr = self.instr_ptr
        self.generate_code(node.condition)
        jz = self._add_instr(Opcode.JZ, 0)

        self.generate_code(node.body)
        self._add_instr(Opcode.JMP, start_addr)
        self.instr_map[jz].arg = self.instr_ptr

    def _translate_aref(self, node: ArrayOpsNode) -> None:
        self.generate_code(node.offset)
        tmp = self.mem_manager.SYS_TMP_ADDR
        self._add_instr(Opcode.ST, tmp)
        self.generate_code(node.array_ref)
        self._add_instr(Opcode.ADD, tmp)

        self._add_instr(Opcode.ST, tmp)
        self._add_instr(Opcode.LID, tmp)  # AC = Mem[Mem[tmp]]

    def _translate_aset(self, node: ArrayOpsNode) -> None:
        self.generate_code(node.value)
        self._add_instr(Opcode.PUSH, 0)

        self.generate_code(node.offset)
        tmp = self.mem_manager.SYS_TMP_ADDR
        self._add_instr(Opcode.ST, tmp)
        self.generate_code(node.array_ref)
        self._add_instr(Opcode.ADD, tmp)
        self._add_instr(Opcode.ST, tmp)
        self._add_instr(Opcode.POP, 0)

        self._add_instr(Opcode.SID, tmp)  # Mem[Mem[0]] = AC
