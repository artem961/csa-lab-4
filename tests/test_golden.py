import contextlib
import io
import os
from typing import Any

import pytest
import yaml

from src.binary import PRINTABLE_MAX, PRINTABLE_MIN, read_binary, write_binary
from src.machine.processor.control_unit import ControlUnit
from src.machine.processor.data_path import DataPath
from src.machine.simulator.log_presenter import LogPresenter
from src.machine.simulator.simulator import Simulator
from src.translator.definition import print_ast
from src.translator.parser import parse_code
from src.translator.translator import Translator

TESTS_DIR = os.path.dirname(__file__)
GOLD_FIELDS = ("expected_ast", "expected_listing", "expected_output", "expected_journal")


def _block_str(dumper: Any, value: str) -> Any:
    # Многострочные эталоны печатаем YAML-блоком (|), чтобы они читались как обычный текст.
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


yaml.add_representer(str, _block_str, Dumper=yaml.SafeDumper)


def find_test_files() -> list[str]:
    return [os.path.join(TESTS_DIR, f) for f in sorted(os.listdir(TESTS_DIR)) if f.endswith(".yml")]


def build_schedule(ports_input: dict[Any, Any] | None) -> list[tuple[int, int, int]]:
    schedule = []
    for port, events in (ports_input or {}).items():
        for tick, raw in events:
            value = ord(raw) if isinstance(raw, str) and len(raw) == 1 else int(raw)
            schedule.append((tick, port, value))
    return sorted(schedule)


def _clean(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.rstrip("\n").split("\n"))


def _capture_ast(ast: list[Any]) -> str:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        print_ast(ast)
    return _clean(buf.getvalue())


def _format_output(output_buffer: dict[int, list[int]], ticks: int) -> str:
    lines = [f"ticks: {ticks}"]
    for port in sorted(output_buffer):
        vals = output_buffer[port]
        text = "".join(chr(v) if PRINTABLE_MIN <= v <= PRINTABLE_MAX else "." for v in vals)
        lines.append(f"port {port}: {vals}")
        lines.append(f"  text: '{text}'")
    return "\n".join(lines)


def _truncate(text: str, head: int, tail: int) -> str:
    lines = _clean(text).split("\n")
    if len(lines) <= head + tail:
        return "\n".join(lines)
    omitted = len(lines) - head - tail
    return "\n".join([*lines[:head], "", f"... [{omitted} строк журнала пропущено] ...", "", *lines[-tail:]])


def run_case(data: dict[str, Any]) -> dict[str, str]:
    ast = parse_code(data["source"])
    mem_size = int(data.get("memory-size", 1024))
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

    dp = DataPath(instr_mem=instr_mem, data_mem=data_mem)
    sim = Simulator(ControlUnit(dp), dp,
                    input_schedule=build_schedule(data.get("ports-input")),
                    limit=int(data.get("limit", 2000)),
                    presenter=LogPresenter())

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        sim.run()

    head, tail = int(data.get("journal-head", 60)), int(data.get("journal-tail", 30))
    return {
        "expected_ast":     _capture_ast(ast),
        "expected_listing": _clean(listing),
        "expected_output":  _format_output(dp.output_buffer, sim.tick),
        "expected_journal": _truncate(buf.getvalue(), head, tail),
    }


def _write_gold(test_file: str, result: dict[str, str]) -> None:
    # Оставляем входную часть файла (всё до эталонных полей) и дописываем свежие эталоны.
    with open(test_file, encoding="utf-8") as f:
        lines = f.read().splitlines()
    cut = next((i for i, ln in enumerate(lines) if ln.startswith(GOLD_FIELDS)), len(lines))
    prefix = "\n".join(lines[:cut]).rstrip("\n")
    dumped = yaml.safe_dump({f: result[f] for f in GOLD_FIELDS}, allow_unicode=True, sort_keys=False, width=1000)
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(prefix + "\n\n" + dumped)


@pytest.mark.parametrize("test_file", find_test_files())
def test_golden(test_file: str, request: pytest.FixtureRequest) -> None:
    with open(test_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    result = run_case(data)

    if request.config.getoption("--update-gold"):
        _write_gold(test_file, result)
        pytest.skip(f"golden updated: {os.path.basename(test_file)}")

    for field in GOLD_FIELDS:
        assert result[field] == data.get(field), f"{field} mismatch in {os.path.basename(test_file)}"
