from typing import Dict
from src.translator.definition import *
from src.machine.isa import Opcode, Instruction


class Translator:
    def __init__(self):
        self.instructions: List[Instruction] = []
        self.symbol_table: Dict[str, int] = {}

        self.data_ptr = 0
        self.MATH_TEMP = self.allocate_memory()

        self.label_count = 0
        self.function_addresses: Dict[str, int] = {}
        self.strings: Dict[int, str] = {}

    def allocate_memory(self, size: int = 1) -> int:
        addr = self.data_ptr
        self.data_ptr += size
        return addr

    def add_instruction(self, opcode: Opcode, arg: int = 0) -> int:
        self.instructions.append(Instruction(opcode, arg))
        return len(self.instructions) - 1

    def translate(self, typed_ast: List[Node]) -> List[Instruction]:
        for node in typed_ast:
            self.generate_code(node)
        self.add_instruction(Opcode.HLT)
        self._patch_function_calls()
        return self.instructions

    def _patch_function_calls(self):
        for instr in self.instructions:
            if instr.opcode == Opcode.CALL and isinstance(instr.arg, str):
                if instr.arg in self.function_addresses:
                    instr.arg = self.function_addresses[instr.arg]
                else:
                    raise NameError(f"Undefined function: {instr.arg}")

    def generate_code(self, node: Node):
        # атомы
        if isinstance(node, NumberNode):
            self.add_instruction(Opcode.LDI, node.value)
        elif isinstance(node, BooleanNode):
            self.add_instruction(Opcode.LDI, 1 if node.value else 0)
        elif isinstance(node, SymbolNode):
            if node.name not in self.symbol_table:
                raise NameError(f"Symbol '{node.name}' not defined")
            self.add_instruction(Opcode.LD, self.symbol_table[node.name])
        elif isinstance(node, StringNode):
            addr = self.allocate_memory(len(node.value) + 1)
            self.strings[addr] = node.value
            self.add_instruction(Opcode.LDI, addr)

        # переменные и def
        elif isinstance(node, DefNode):
            if isinstance(node.expression, LambdaNode):
                self.function_addresses[node.variable] = self._generate_lambda(node.expression)
                if node.variable not in self.symbol_table:
                    self.symbol_table[node.variable] = self.allocate_memory()
                self.add_instruction(Opcode.LDI, self.function_addresses[node.variable])
                self.add_instruction(Opcode.ST, self.symbol_table[node.variable])
            else:
                self.generate_code(node.expression)
                if node.variable not in self.symbol_table:
                    self.symbol_table[node.variable] = self.allocate_memory()
                self.add_instruction(Opcode.ST, self.symbol_table[node.variable])

        elif isinstance(node, SetNode):
            self.generate_code(node.expression)
            self.add_instruction(Opcode.ST, self.symbol_table[node.variable])

        elif isinstance(node, BlockNode):
            for expr in node.expressions:
                self.generate_code(expr)
        elif isinstance(node, IfNode):
            self._generate_if(node)
        elif isinstance(node, WhileNode):
            self._generate_while(node)

        elif isinstance(node, FunctionCallNode):
            self._generate_call(node)
        elif isinstance(node, TrapNode):
            self.add_instruction(Opcode.TRAP, node.interrupt_code)
        elif isinstance(node, IONode):
            if node.operation == "out":
                self.generate_code(node.expression)
                self.add_instruction(Opcode.OUT, node.port)
            else:
                self.add_instruction(Opcode.IN, node.port)

    def _generate_math(self, name: str, args: List[Node]):
        ops = {"+": Opcode.ADD, "-": Opcode.SUB, "*": Opcode.MUL,
               "/": Opcode.DIV, "%": Opcode.MOD, "=": Opcode.CMP,
               "<": Opcode.CMP, ">": Opcode.CMP}


        self.generate_code(args[0])

        for next_arg in args[1:]:
            self.add_instruction(Opcode.PUSH)
            self.generate_code(next_arg)
            self.add_instruction(Opcode.ST, self.MATH_TEMP)
            self.add_instruction(Opcode.POP)
            self.add_instruction(ops[name], self.MATH_TEMP)

    def _generate_call(self, node: FunctionCallNode):
        if node.name in ["+", "-", "*", "/", "%", "=", "<", ">"]:
            self._generate_math(node.name, node.args)
        else:
            for arg in node.args:
                self.generate_code(arg)
                self.add_instruction(Opcode.PUSH)

            addr = self.function_addresses.get(node.name, node.name)
            self.add_instruction(Opcode.CALL, addr)

    def _generate_lambda(self, node: LambdaNode) -> int:
        jmp_over = self.add_instruction(Opcode.JMP, 0)
        entry_addr = len(self.instructions)

        for param in reversed(node.parameters):
            if param not in self.symbol_table:
                self.symbol_table[param] = self.allocate_memory()
            self.add_instruction(Opcode.POP)
            self.add_instruction(Opcode.ST, self.symbol_table[param])

        self.generate_code(node.body)
        self.add_instruction(Opcode.RET)

        self.instructions[jmp_over].arg = len(self.instructions)
        return entry_addr

    def _generate_if(self, node: IfNode):
        self.generate_code(node.condition)
        jz_else = self.add_instruction(Opcode.JZ, 0)
        self.generate_code(node.then_block)
        jmp_end = self.add_instruction(Opcode.JMP, 0)
        self.instructions[jz_else].arg = len(self.instructions)
        self.generate_code(node.else_block)
        self.instructions[jmp_end].arg = len(self.instructions)

    def _generate_while(self, node: WhileNode):
        start = len(self.instructions)
        self.generate_code(node.condition)
        jz_exit = self.add_instruction(Opcode.JZ, 0)
        self.generate_code(node.body)
        self.add_instruction(Opcode.JMP, start)
        self.instructions[jz_exit].arg = len(self.instructions)