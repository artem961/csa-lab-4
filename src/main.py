import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.binary import read_binary, write_binary  # noqa: E402
from src.config_loader import load_simulation_config  # noqa: E402
from src.machine.processor.control_unit import ControlUnit  # noqa: E402
from src.machine.processor.data_path import DataPath  # noqa: E402
from src.machine.simulator.log_presenter import LogPresenter  # noqa: E402
from src.machine.simulator.simulator import Simulator  # noqa: E402
from src.translator.parser import parse_code  # noqa: E402
from src.translator.definition import print_ast  # noqa: E402
from src.translator.translator import Translator  # noqa: E402

def print_usage():
    print("Usage:")
    print("  python main.py compile <source.lisp> <output.bin> [listing.txt]")
    print("  python main.py run <config.yml>")
    sys.exit(1)

def handle_compile(source_path: str, bin_path: str, listing_path: str | None = None):
    if not os.path.exists(source_path):
        print(f"Error: Source file '{source_path}' not found.")
        sys.exit(1)

    with open(source_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    final_ast = parse_code(source_code)
    print("--- AST Structure ---")
    print_ast(final_ast)
    print("-" * 50)

    # Трансляция в машинный код
    translator = Translator(data_mem_size=1024)
    instr, data = translator.translate(final_ast)

    # Запись бинарного файла и листинга
    write_binary(bin_path, instr, data, listing_path=listing_path)
    print("Compilation successful.")
    print(f"  Binary written to: {bin_path}")
    if listing_path:
        print(f"  Listing written to: {listing_path}")

def handle_run(config_path: str):
    if not os.path.exists(config_path):
        print(f"Error: Config file '{config_path}' not found.")
        sys.exit(1)

    # Чтение конфига
    conf = load_simulation_config(config_path)
    binary = conf["bin"]

    if not os.path.exists(binary):
        print(f"Error: Binary file '{binary}' specified in config not found.")
        sys.exit(1)

    # Загрузка программы из бинарного файла
    instr_mem, data_mem = read_binary(binary)


    # Инициализация компонентов
    data_mem.extend([0] * (conf["memory_size"] - len(data_mem)))
    dp = DataPath(instr_mem=instr_mem, data_mem=data_mem)
    cu = ControlUnit(dp)
    presenter = LogPresenter(show_signals=conf["show_signals"])

    # Запуск симулятора
    sim = Simulator(
        cu=cu,
        dp=dp,
        input_schedule=conf["schedule"],
        limit=conf["limit"],
        presenter=presenter
    )
    sim.run()

def main():
    if len(sys.argv) < 2:
        print_usage()

    mode = sys.argv[1]

    if mode == "compile":
        if len(sys.argv) < 4:
            print_usage()
        source = sys.argv[2]
        target = sys.argv[3]
        listing = sys.argv[4] if len(sys.argv) > 4 else None
        handle_compile(source, target, listing)

    elif mode == "run":
        if len(sys.argv) < 3:
            print_usage()
        config_file = sys.argv[2]
        handle_run(config_file)

    else:
        print(f"Error: Unknown mode '{mode}'")
        print_usage()

if __name__ == "__main__":
    main()