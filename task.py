from pathlib import Path
import json
from collections import defaultdict
import argparse
import tabulate

def parse_args(argv=None):
    """Парсит аргументы командной строки и возвращает объект с параметрами."""
    allowed_reports = ["average"]
    parser = argparse.ArgumentParser(description="Обработка лог-файлов")
    parser.add_argument("--file", nargs="+", required=True, help="Путь к лог-файлу(ам)")
    parser.add_argument("--report", choices=allowed_reports, required=True, help="Название отчета, например average")
    parser.add_argument("--date", help="Фильтр по дате в формате ГГГГ-ММ-ДД")
    return parser.parse_args(argv)

def read_logs(file_paths):
    """Читает лог-файлы в формате JSON"""
    logs = []
    # Читаем все указанные файлы
    for path_str in file_paths:
        path = Path(path_str)
        if not path.exists():
            print(f"Файл {path} не найден")
            continue
        # Сохраняем все объекты
        with path.open() as file:
            for line in file:
                line = line.strip()
                if line:
                    logs.append(json.loads(line))
    return logs

def process_logs_average(logs, date=None, accuracy=3):
    """Обрабатывает статистику логов"""
    stats = defaultdict(lambda: {"count": 0, "sum_time": 0.0})
    for entry in logs:
        # Фильтр по дате
        if date and entry.get("@timestamp", "")[:10] != date:
            continue

        # Проверка, что url и response_time есть в логе
        url = entry.get("url")
        time = entry.get("response_time")
        if url is None or time is None:
            continue

        stats[url]["count"] += 1
        stats[url]["sum_time"] += time

    # Вычисляем среднее время
    for vals in stats.values():
        vals["avg_time"] = round(vals["sum_time"] / vals["count"], accuracy)
        del vals["sum_time"]

    return stats

def make_table_average(stats):
    """Формирует таблицу для вывода в консоль, для удобства сортирует данные по параметру "count" и добавляет нумерацию к готовым строкам данных"""
    table = []
    for idx, (url, vals) in enumerate(sorted(stats.items(), key=lambda x: x[1]["count"], reverse=True), start=1):
        table.append([idx, url, vals["count"], vals["avg_time"]])
    return table

def main(argv=None):
    args = parse_args(argv)

    logs = read_logs(args.file)
    stats = process_logs_average(logs, date=args.date)
    table = make_table_average(stats)

    headers = ["id", "handler", "total", "avg_response_time"]
    print(tabulate.tabulate(table, headers=headers))

# Точка входа
if __name__ == "__main__":
    main()