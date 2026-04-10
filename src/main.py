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


def make_instr(op, arg):
    return (op.value << 24) | (arg & 0xFFFFFF)


def test_loop_program():
    program = [
        make_instr(Opcode.LDI, 3),
        make_instr(Opcode.ST, 14),
        make_instr(Opcode.LDI, 2),
        make_instr(Opcode.SUB, 14),
        make_instr(Opcode.OUT, 1),
        make_instr(Opcode.HLT, 0)
    ]

    dp = DataPath(instr_mem=program, data_mem_size=64)
    cu = ControlUnit(dp)

    print(f"{'TICK':<10} | {'IP':<4} | {'OPCODE':<10} | {'ACC':<10} | {'FLAGS'}")
    print("-" * 60)

    while not cu.halted and cu._tick < 200:
        current_ip = dp.ip
        cu.main_step()

        try:
            op_name = Opcode((dp.instr_mem[current_ip] >> 24) & 0xFF).name
        except:
            op_name = "???"

        z = "Z" if dp._get_z() else "_"
        n = "N" if dp._get_n() else "_"

        print(f"{cu._tick:<10} | {current_ip:<4} | {op_name:<10} | {dp.acc:<10} | [{z} {n}]")

    print("-" * 60)
    print("FINISH. Output buffer (Port 1):", dp.output_buffer.get(1, []))


if __name__ == "__main__":
    test_loop_program()