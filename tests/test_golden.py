import os
import sys
import io
import contextlib
import pytest
import yaml

# Добавляем корневую папку в пути импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.translator.parser import parse_code
from src.translator.translator import Translator
from src.binary import write_binary, read_binary
from src.machine.processor.data_path import DataPath
from src.machine.processor.control_unit import ControlUnit
from src.machine.simulator.log_presenter import LogPresenter
from src.machine.simulator.simulator import Simulator


# Находим все файлы .yml в папке tests
def find_test_files():
    test_dir = os.path.dirname(__file__)
    files = [f for f in os.listdir(test_dir) if f.endswith('.yml')]
    return [os.path.join(test_dir, f) for f in files]


@pytest.mark.parametrize("test_file", find_test_files())
def test_golden(test_file, request):
    # Читаем конфигурацию теста
    with open(test_file, "r", encoding="utf-8") as f:
        test_data = yaml.safe_load(f)

    source_code = test_data["source"]
    input_schedule = [tuple(x) for x in test_data.get("input", [])]
    limit = test_data.get("limit", 2000)

    # Временные файлы для компиляции
    temp_bin = "temp_test.bin"
    temp_txt = "temp_test_listing.txt"

    # --- 1. КОМПИЛЯЦИЯ ---
    ast = parse_code(source_code)
    translator = Translator(data_mem_size=128)
    instr, data = translator.translate(ast)
    write_binary(temp_bin, instr, data, listing_path=temp_txt)

    # --- 2. СИМУЛЯЦИЯ С ПЕРЕХВАТОМ ВЫВОДА ---
    instr_mem, data_mem = read_binary(temp_bin)

    # Расширяем память до нужного размера
    data_mem.extend([0] * (128 - len(data_mem)))

    dp = DataPath(instr_mem=instr_mem, data_mem=data_mem)
    cu = ControlUnit(dp)

    # Скрываем сигналы АЛУ в логах тестов, чтобы файлы не были по 10 МБ
    presenter = LogPresenter(show_signals=False)
    sim = Simulator(cu, dp, input_schedule=input_schedule, limit=limit, presenter=presenter)

    # Перехватываем stdout (вывод симулятора) в буфер
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        sim.run()

    output_log = f.getvalue()

    # Очищаем временные файлы
    if os.path.exists(temp_bin): os.remove(temp_bin)
    if os.path.exists(temp_txt): os.remove(temp_txt)

    # --- 3. ОБРАБОТКА РЕЗУЛЬТАТОВ ---

    # Сокращаем лог процессора (берем первые 50 тактов и конец),
    # чтобы файлы не весили слишком много (требование реализма)
    log_lines = output_log.split("\n")
    if len(log_lines) > 200:
        truncated_log = "\n".join(log_lines[:150]) + "\n\n... [TRUNCATED FOR READABILITY] ...\n\n" + "\n".join(
            log_lines[-50:])
    else:
        truncated_log = output_log

    # Считываем итоговый вывод портов
    output_ports = {}
    for port, values in dp.output_buffer.items():
        output_ports[port] = values

    # Если запущен pytest с флагом обновления золотых файлов
    if request.config.getoption("--update-gold"):
        test_data["expected_output"] = output_ports
        test_data["expected_log"] = truncated_log
        with open(test_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(test_data, f, allow_unicode=True, default_flow_style=False)
        print(f"\n[GOLD] Updated expectations for {test_file}")
    else:
        # Иначе — сравниваем результаты с эталоном
        assert output_ports == test_data.get("expected_output"), "Output ports mismatch!"
        # Сравниваем логи (игнорируя пробелы на концах строк)
        actual_lines = [line.strip() for line in truncated_log.split("\n") if line.strip()]
        expected_lines = [line.strip() for line in test_data.get("expected_log", "").split("\n") if line.strip()]
        assert actual_lines == expected_lines, "Simulation trace log mismatch!"


# Опция pytest для обновления файлов
def pytest_addoption(parser):
    parser.addoption("--update-gold", action="store_true", help="update golden test expectation files")