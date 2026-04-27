# from translator.parser import *
# from translator.translator import *
#
# code = """
# (def x (+ 1 2 3))
# """
#
# # 1. На токены
# tokens = tokenize(code)
#
# # 2. В сырое дерево
# raw_ast = Parser(tokens).parse()
#
# # 3. В логические структуры
# analyzer = SemanticAnalyzer()
# final_ast = analyzer.analyze(raw_ast)
#
#
# def pretty_print(node, indent=0):
#     prefix = "  " * indent
#
#     if isinstance(node, DefNode):
#         print(f"{prefix}DefNode: variable='{node.variable}'")
#         pretty_print(node.expression, indent + 1)
#
#     elif isinstance(node, SetNode):
#         print(f"{prefix}SetNode: variable='{node.variable}'")
#         pretty_print(node.expression, indent + 1)
#
#     elif isinstance(node, IfNode):
#         print(f"{prefix}IfNode:")
#         print(f"{prefix}  CONDITION:")
#         pretty_print(node.condition, indent + 2)
#         print(f"{prefix}  THEN:")
#         pretty_print(node.then_block, indent + 2)
#         print(f"{prefix}  ELSE:")
#         pretty_print(node.else_block, indent + 2)
#
#     elif isinstance(node, WhileNode):
#         print(f"{prefix}WhileNode:")
#         print(f"{prefix}  CONDITION:")
#         pretty_print(node.condition, indent + 2)
#         print(f"{prefix}  BODY:")
#         pretty_print(node.body, indent + 2)
#
#     elif isinstance(node, BlockNode):
#         print(f"{prefix}BlockNode:")
#         for expr in node.expressions:
#             pretty_print(expr, indent + 1)
#
#     elif isinstance(node, IONode):
#         print(f"{prefix}IONode: op='{node.operation}', port={node.port}")
#         if node.expression:
#             pretty_print(node.expression, indent + 1)
#
#     elif isinstance(node, FunctionCallNode):
#         print(f"{prefix}FunctionCallNode: name='{node.name}'")
#         for arg in node.args:
#             pretty_print(arg, indent + 1)
#
#     elif isinstance(node, LambdaNode):
#         print(f"{prefix}LambdaNode: params={node.parameters}")
#         pretty_print(node.body, indent + 1)
#
#     # Атомы
#     elif isinstance(node, SymbolNode):
#         print(f"{prefix}SymbolNode: '{node.name}'")
#     elif isinstance(node, NumberNode):
#         print(f"{prefix}NumberNode: {node.value}")
#     elif isinstance(node, StringNode):
#         print(f"{prefix}StringNode: \"{node.value}\"")
#     elif isinstance(node, BooleanNode):
#         print(f"{prefix}BooleanNode: {node.value}")
#     else:
#         print(f"{prefix}Unknown Node: {node}")
#
#
#
# print("--- Итоговое дерево---")
# for node in final_ast:
#     pretty_print(node)
#     print("-" * 30)
#
#
# # 4. Транслятор (машинный код)
# translator = Translator()
# instructions = translator.translate(final_ast)
#
# # --- Вывод результатов ---
#
# print("\n--- Сгенерированные машинные команды ---")
# print(f"{'Адрес':<7} | {'Команда':<10} | {'Аргумент':<10}")
# print("-" * 35)
# for addr, inst in enumerate(instructions):
#     # inst.opcode.name вернет строку типа 'LDI', 'ST'
#     print(f"{addr:<7} | {inst.opcode.name:<10} | {inst.arg:<10}")
#
# print("\n--- Таблица символов (Data Memory) ---")
# for var, addr in translator.symbol_table.items():
#     print(f"Переменная '{var}' -> Адрес {addr}")


from src.isa.isa import Opcode
from src.processor.data_path import DataPath
from src.processor.control_unit import ControlUnit
from src.simulator import Simulator
from src.processor.signals import Signal
# Важно: убедись, что в INSTRUCTION_TICKS прописан RET
from src.processor.instructions import INSTRUCTION_TICKS


def make_instr(op, arg):
    return (op.value << 24) | (arg & 0xFFFFFF)


from src.isa.isa import Opcode
from src.processor.data_path import DataPath
from src.processor.control_unit import ControlUnit
from src.simulator import Simulator

def make_instr(op, arg):
    return (op.value << 24) | (arg & 0xFFFFFF)


def test_factorial_recursive():
    instr_mem = [0] * 200

    # 0: JMP 10 (Main)
    instr_mem[0] = make_instr(Opcode.JMP, 10)

    # --- MAIN ---
    instr_mem[10] = make_instr(Opcode.LDI, 5)  # N = 5
    instr_mem[11] = make_instr(Opcode.PUSH, 0)  # Push N
    instr_mem[12] = make_instr(Opcode.CALL, 50)  # CALL fact
    instr_mem[13] = make_instr(Opcode.POP, 0)  # Очистить стек
    instr_mem[14] = make_instr(Opcode.OUT, 1)  # Вывод результата (120)
    instr_mem[15] = make_instr(Opcode.HLT, 0)

    # --- FACTORIAL ---
    instr_mem[50] = make_instr(Opcode.LDS, 2)  # AC = N
    instr_mem[51] = make_instr(Opcode.CMP, 100)  # CMP 1
    instr_mem[52] = make_instr(Opcode.JZ, 80)  # Если N==1, переход на базовый случай

    # Рекурсивный шаг: N * fact(N-1)
    instr_mem[53] = make_instr(Opcode.LDS, 2)  # AC = N
    instr_mem[54] = make_instr(Opcode.PUSH, 0)  # Push N для сохранения

    instr_mem[55] = make_instr(Opcode.LDS, 1)  # AC = N
    instr_mem[56] = make_instr(Opcode.SUB, 100)  # AC = N - 1
    instr_mem[57] = make_instr(Opcode.PUSH, 0)  # Push (N-1)
    instr_mem[58] = make_instr(Opcode.CALL, 50)  # CALL fact(N-1)
    instr_mem[59] = make_instr(Opcode.POP, 0)  # снять результат
    instr_mem[60] = make_instr(Opcode.ST, 101)  # сохранить в tmp
    instr_mem[61] = make_instr(Opcode.POP, 0)  # снять N с сохранения

    instr_mem[62] = make_instr(Opcode.MUL, 101)  # AC = fact(N-1) * N
    instr_mem[63] = make_instr(Opcode.STS, 2)  # сохранить результат на стек
    instr_mem[64] = make_instr(Opcode.RET, 0)

    # --- БАЗОВЫЙ СЛУЧАЙ ---
    instr_mem[80] = make_instr(Opcode.RET, 0)


    dp = DataPath(instr_mem=instr_mem, data_mem_size=512)
    dp.data_mem[100] = 1  # Константа 1

    cu = ControlUnit(dp)
    sim = Simulator(cu, dp, input_schedule=[], limit=1000)
    sim.run()


if __name__ == "__main__":
    test_factorial_recursive()
