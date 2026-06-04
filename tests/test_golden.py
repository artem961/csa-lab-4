import contextlib
import io
import os
import sys

import pytest
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.binary import read_binary, write_binary
from src.machine.processor.control_unit import ControlUnit
from src.machine.processor.data_path import DataPath
from src.machine.simulator.log_presenter import LogPresenter
from src.machine.simulator.simulator import Simulator
from src.translator.definition import print_ast
from src.translator.parser import parse_code
from src.translator.translator import Translator

TESTS_DIR = os.path.dirname(__file__)
GOLD_FIELDS = ("expected_ast", "expected_listing", "expected_output", "expected_journal")


# --- YAML: писать многострочные значения блоком (|-), а не экранированной строкой ---
def _str_representer(dumper, value):
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


yaml.add_representer(str, _str_representer, Dumper=yaml.SafeDumper)


def find_test_files():
    files = [f for f in os.listdir(TESTS_DIR) if f.endswith(".yml")]
    return [os.path.join(TESTS_DIR, f) for f in sorted(files)]


# Построение расписания прерываний из секции `ports-input` (как в config.yml):
# порт -> [[такт, значение], ...]; значение — число или одиночный символ в кавычках.
def build_schedule(io_ports):
    schedule = []
    for port_id, events in (io_ports or {}).items():
        for tick, raw_value in events:
            if isinstance(raw_value, str) and len(raw_value) == 1:
                value = ord(raw_value)
            else:
                value = int(raw_value)
            schedule.append((tick, port_id, value))
    schedule.sort(key=lambda x: x[0])
    return schedule


def _clean(text):
    """Убирает завершающие пробелы в строках — для чистых блоков YAML и стабильного сравнения."""
    return "\n".join(line.rstrip() for line in text.rstrip("\n").split("\n"))


def _capture_ast(ast):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        print_ast(ast)
    return _clean(buf.getvalue())


def _abbrev(items, head=24, tail=12):
    """Список в строку с обрезкой середины для длинных последовательностей (items — строки)."""
    if len(items) <= head + tail + 5:
        return "[" + ", ".join(items) + "]"
    omitted = len(items) - head - tail
    return ("[" + ", ".join(items[:head]) + f", ... ({omitted} ещё) ..., "
            + ", ".join(items[-tail:]) + "]")


def _abbrev_text(s, head=120, tail=60):
    """Текст с обрезкой середины для длинных строк вывода."""
    if len(s) <= head + tail + 20:
        return s
    return s[:head] + f" ...({len(s) - head - tail} символов)... " + s[-tail:]


def _format_output(output_buffer, ticks):
    lines = [f"ticks: {ticks}"]
    if not output_buffer:
        lines.append("output: <none>")
    for port in sorted(output_buffer):
        vals = list(output_buffer[port])
        text = "".join(chr(v) if 32 <= v <= 126 else "." for v in vals)
        lines.append(f"port {port}: {len(vals)} words")
        lines.append(f"  num:  {_abbrev([str(v) for v in vals])}")
        lines.append(f"  hex:  {_abbrev([f'0x{v & 0xFFFFFFFF:x}' for v in vals])}")
        lines.append(f"  text: '{_abbrev_text(text)}'")
    return "\n".join(lines)


def _truncate(text, head, tail):
    """Журнал с сохранением начала и конца; середина сворачивается с указанием числа строк."""
    lines = _clean(text).split("\n")
    if len(lines) <= head + tail + 3:
        return "\n".join(lines)
    omitted = len(lines) - head - tail
    marker = f"... [{omitted} строк журнала пропущено] ..."
    return "\n".join(lines[:head] + ["", marker, ""] + lines[-tail:])


def run_case(data):
    """Компиляция + симуляция теста. Возвращает словарь эталонных полей."""
    source = data["source"]
    limit = int(data.get("limit", 2000))
    mem_size = int(data.get("memory-size", 1024))
    schedule = build_schedule(data.get("ports-input", {}))

    # --- Компиляция ---
    ast = parse_code(source)
    translator = Translator(data_mem_size=mem_size)
    instr, data_map = translator.translate(ast)

    tmp_bin = os.path.join(TESTS_DIR, "_tmp.bin")
    tmp_lst = os.path.join(TESTS_DIR, "_tmp.txt")
    write_binary(tmp_bin, instr, data_map, listing_path=tmp_lst, data_size=mem_size)
    with open(tmp_lst, encoding="utf-8") as f:
        listing = f.read()

    instr_mem, data_mem = read_binary(tmp_bin)
    os.remove(tmp_bin)
    os.remove(tmp_lst)

    # --- Симуляция ---
    dp = DataPath(instr_mem=instr_mem, data_mem=data_mem)
    cu = ControlUnit(dp)
    sim = Simulator(cu, dp, input_schedule=schedule, limit=limit, presenter=LogPresenter())

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        sim.run()

    head = int(data.get("journal-head", 60))
    tail = int(data.get("journal-tail", 30))

    return {
        "expected_ast": _capture_ast(ast),
        "expected_listing": _clean(listing),
        "expected_output": _format_output(dp.output_buffer, sim.tick),
        "expected_journal": _truncate(buf.getvalue(), head, tail),
    }


@pytest.mark.parametrize("test_file", find_test_files())
def test_golden(test_file, request):
    with open(test_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    result = run_case(data)

    if request.config.getoption("--update-gold"):
        # Сохраняем входную часть файла как есть (формат, комментарии),
        # перезаписываем только блок эталонов.
        with open(test_file, encoding="utf-8") as f:
            lines = f.read().splitlines()
        cut = len(lines)
        for i, line in enumerate(lines):
            if any(line == field or line.startswith(field + ":") for field in GOLD_FIELDS):
                cut = i
                break
        prefix = "\n".join(lines[:cut]).rstrip("\n")
        expected = {field: result[field] for field in GOLD_FIELDS}
        dumped = yaml.safe_dump(expected, allow_unicode=True, sort_keys=False, width=1000)
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(prefix + "\n\n" + dumped)
        pytest.skip(f"golden updated: {os.path.basename(test_file)}")

    for field in GOLD_FIELDS:
        assert result[field] == data.get(field), f"{field} mismatch in {os.path.basename(test_file)}"