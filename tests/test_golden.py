import contextlib
import io
import os

import pytest
import yaml

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


def _str_representer(dumper, value):
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


yaml.add_representer(str, _str_representer, Dumper=yaml.SafeDumper)


def find_test_files():
    return [os.path.join(TESTS_DIR, f) for f in sorted(os.listdir(TESTS_DIR)) if f.endswith(".yml")]


def build_schedule(io_ports):
    schedule = []
    for port_id, events in (io_ports or {}).items():
        for tick, raw_value in events:
            value = ord(raw_value) if isinstance(raw_value, str) and len(raw_value) == 1 else int(raw_value)
            schedule.append((tick, port_id, value))
    return sorted(schedule, key=lambda x: x[0])


def _clean(text):
    return "\n".join(line.rstrip() for line in text.rstrip("\n").split("\n"))


def _capture_ast(ast):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        print_ast(ast)
    return _clean(buf.getvalue())


def _abbrev(items, head=24, tail=12):
    if len(items) <= head + tail + 5:
        return "[" + ", ".join(items) + "]"
    omitted = len(items) - head - tail
    return "[" + ", ".join(items[:head]) + f", ... ({omitted} ещё) ..., " + ", ".join(items[-tail:]) + "]"


def _abbrev_text(s, head=120, tail=60):
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
    lines = _clean(text).split("\n")
    if len(lines) <= head + tail + 3:
        return "\n".join(lines)
    omitted = len(lines) - head - tail
    return "\n".join(lines[:head] + ["", f"... [{omitted} строк журнала пропущено] ...", ""] + lines[-tail:])


def run_case(data):
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
    cu = ControlUnit(dp)
    sim = Simulator(cu, dp,
                    input_schedule=build_schedule(data.get("ports-input", {})),
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


@pytest.mark.parametrize("test_file", find_test_files())
def test_golden(test_file, request):
    with open(test_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    result = run_case(data)

    if request.config.getoption("--update-gold"):
        with open(test_file, encoding="utf-8") as f:
            lines = f.read().splitlines()
        cut = next(
            (i for i, ln in enumerate(lines)
             if any(ln == fld or ln.startswith(fld + ":") for fld in GOLD_FIELDS)),
            len(lines)
        )
        prefix = "\n".join(lines[:cut]).rstrip("\n")
        dumped = yaml.safe_dump({f: result[f] for f in GOLD_FIELDS}, allow_unicode=True, sort_keys=False, width=1000)
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(prefix + "\n\n" + dumped)
        pytest.skip(f"golden updated: {os.path.basename(test_file)}")

    for field in GOLD_FIELDS:
        assert result[field] == data.get(field), f"{field} mismatch in {os.path.basename(test_file)}"
