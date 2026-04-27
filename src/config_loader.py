import yaml


def load_simulation_config(config_path: str) -> dict:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    limit = config.get('limit', 5000)
    memory_size = config.get('memory-size', 1024)
    show_signals = config.get('show-signals', False)

    schedule = []
    io_ports = config.get('ports-input', {})

    for port_id, events in io_ports.items():
        for event in events:
            tick, raw_value = event

            if isinstance(raw_value, str) and len(raw_value) == 1:
                value = ord(raw_value)
            else:
                value = int(raw_value)

            schedule.append((tick, port_id, value))

    schedule.sort(key=lambda x: x[0])

    return {
        "limit": limit,
        "show_signals": show_signals,
        "schedule": schedule,
        "memory_size": memory_size,
    }