import pytest
import task

# Тесты передаваемых параметров (task.parse_args)
def test_parse_args_one_file():
    """Позволяет ли ключ "--file" указать один путь"""
    argv = ["--file", "example2.log", "--report", "average"]
    args = task.parse_args(argv)
    assert args.file == ["example2.log"] and args.report == "average"

def test_parse_args_two_files():
    """Позволяет ли ключ "--file" указать два пути"""
    argv = ["--file", "example2.log", "example1.log", "--report", "average"]
    args = task.parse_args(argv)
    assert args.file == ["example2.log", "example1.log"] and args.report == "average"

def test_parse_args_missing_required():
    """Если обязательный аргумент --file не указан, парсер должен завершить работу с ошибкой SystemExit"""
    argv = ["--report", "average"]
    with pytest.raises(SystemExit):
        task.parse_args(argv)

def test_parse_args_invalid_report():
    """Проверяет, что при вводе некорректного --report парсер завершает программу с ошибкой SystemExit"""
    argv = ["--file", "example.log", "--report", "unknown"]
    with pytest.raises(SystemExit):
        task.parse_args(argv)

# Тесты чтения указанных файлов (task.read_logs)
def test_read_logs_single_file(tmp_path):
    """Должен корректно читать один лог-файл с одной JSON-строкой"""
    log_file = tmp_path.joinpath("log.json")
    log_file.write_text('{"url": "/test", "response_time": 1.5}\n')
    logs = task.read_logs([log_file])
    assert logs == [{"url": "/test", "response_time": 1.5}]

def test_read_logs_missing_file(tmp_path):
    """Если файл отсутствует, функция должна вернуть пустой список"""
    missing_file = tmp_path.joinpath("missing_log.json")
    logs = task.read_logs([missing_file])
    assert logs == []

def test_read_logs_empty_file(tmp_path):
    """Если файл пустой, функция должна вернуть пустой список"""
    empty_file = tmp_path.joinpath("empty_log.json")
    empty_file.write_text("")
    logs = task.read_logs([empty_file])
    assert logs == []


def test_read_logs_multiple_files(tmp_path):
    """ Проверяет, что функция read_logs корректно читает несколько файлов одновременно"""
    log_file1 = tmp_path.joinpath("log1.json")
    log_file1.write_text('{"url": "/test1", "response_time": 1.0}\n')

    log_file2 = tmp_path.joinpath("log2.json")
    log_file2.write_text('{"url": "/test2", "response_time": 2.0}\n')

    logs = task.read_logs([log_file1, log_file2])
    assert logs == [
        {"url": "/test1", "response_time": 1.0},
        {"url": "/test2", "response_time": 2.0}
    ]

# Тесты обработки статистики логов (task.process_logs_average)
def test_process_logs_average_single_url_for_logs():
    """Для одного url с несколькими записями нужно посчитать количество этих url и сумму response_time"""
    logs = [
        {"url": "/test", "response_time": 1.0},
        {"url": "/test", "response_time": 1.5},
        {"url": "/test", "response_time": 2.5}
    ]
    stats = task.process_logs_average(logs)
    assert stats == {"/test": {"count": 3, "avg_time": round(5.0 / 3, 3)}}

def test_process_logs_average_multiple_urls():
    """Для нескольких разных url проверяем, что статистика считается по каждому отдельно"""
    logs = [
        {"url": "/test1", "response_time": 1.0},
        {"url": "/test2", "response_time": 1.5},
        {"url": "/test3", "response_time": 2.5}
    ]
    stats = task.process_logs_average(logs)
    assert stats == {
        "/test1": {"count": 1, "avg_time": 1.0},
        "/test2": {"count": 1, "avg_time": 1.5},
        "/test3": {"count": 1, "avg_time": 2.5},
    }

def test_process_logs_average_missing_fields():
    """Проверяет, что записи с отсутствующими полями 'url' или 'response_time' игнорируются при подсчёте статистики"""
    logs = [
        {"url": "/test", "response_time": 1.0},
        {"url": "/test"},  # пропущено response_time
        {"response_time": 2.0}  # пропущено url
    ]
    stats = task.process_logs_average(logs)
    assert stats == {"/test": {"count": 1, "avg_time": 1.0}}

def test_process_logs_average_with_date():
    """Проверяет правильность работы фильтра с датой"""
    logs = [
        {"url": "/a", "response_time": 1.0, "@timestamp": "2025-06-22T12:00:00"},
        {"url": "/b", "response_time": 2.0, "@timestamp": "2025-06-23T12:00:00"}
    ]
    stats = task.process_logs_average(logs, date="2025-06-22")
    assert stats == {"/a": {"count": 1, "avg_time": 1.0}}

# Тест формирования таблицы для вывода её в консоль с обработанных данных (task.make_table_average)
def test_make_table_average_sorting():
    """Проверяет корректность сортировки и нумерацию при создании таблицы для вывода"""
    stats = {
        "/a": {"count": 2, "avg_time": 1.5},
        "/b": {"count": 5, "avg_time": 2.0},
        "/c": {"count": 1, "avg_time": 3.0},
    }
    table = task.make_table_average(stats)
    # Проверяем сортировку по count (по убыванию)
    assert table[0][1] == "/b"
    assert table[1][1] == "/a"
    assert table[2][1] == "/c"
    # Проверяем нумерацию
    assert table[0][0] == 1
    assert table[1][0] == 2
    assert table[2][0] == 3