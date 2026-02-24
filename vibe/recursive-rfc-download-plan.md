# План: Рекурсивная загрузка RFC документов

## Задача

Добавить функциональность рекурсивной загрузки RFC документов: при загрузке указанного RFC автоматически загружать все RFC, упомянутые в нём. При этом:
- Если RFC уже скачан, не качать его повторно
- Переконвертировать всегда (даже если файл уже существует)

## Структура плана

План разделён на логические этапы:
1. **Анализ и подготовка** - изучение текущей реализации
2. **Извлечение ссылок** - функция для парсинга RFC ссылок из XML
3. **Рекурсивная загрузка** - основная логика с проверкой дубликатов
4. **Интеграция в CLI** - добавление опции командной строки
5. **Тестирование** - покрытие тестами новой функциональности
6. **Документация** - обновление README

---

## Этап 1: Добавление функции извлечения RFC ссылок

**Что добавить/реализовать:**
- Функция `extract_rfc_references(xml_file: Path) -> set[str]` в модуле [`lib/utils.py`](lib/utils.py:1)
- Функция парсит XML файл и извлекает все RFC номера из элементов `<reference anchor="RFCxxxx">`
- Возвращает set с нормализованными номерами RFC (формат "rfcXXXX")
- Обрабатывает исключения при парсинге XML
- Логика:
  1. Парсить XML файл через `etree.parse()`
  2. Найти все элементы `<reference>` в секции `<back>/<references>`
  3. Для каждого reference извлечь атрибут `anchor`
  4. Если anchor начинается с "RFC" (регистронезависимо), извлечь номер
  5. Нормализовать через `normalize_rfc_number()`
  6. Добавить в set результатов
  7. Обработать исключения XMLSyntaxError и FileNotFoundError
  8. Вернуть set (может быть пустым, если нет ссылок)

**Файлы для редактирования/создания:**
- [`lib/utils.py`](lib/utils.py:1) - добавить функцию `extract_rfc_references()`

**Примеры в существующем коде:**
- [`lib/converter.py`](lib/converter.py:516) - метод `_process_reference()` показывает как обрабатываются reference элементы
- [`lib/utils.py`](lib/utils.py:20) - функция `normalize_rfc_number()` показывает как нормализовать RFC номера

**Команды для проверки:**
```bash
# Запустить тесты после реализации
python3 -m pytest tests/test_utils.py::test_extract_rfc_references -v
```

---

## Этап 2: Добавление функции рекурсивной загрузки

**Что добавить/реализовать:**
- Функция `download_rfc_recursive(rfc_number: str, output_dir: Path, fetch_pdf: bool = False, max_depth: int = 1, processed: set[str] | None = None) -> dict[str, Path]` в модуле [`lib/downloader.py`](lib/downloader.py:1)
- Параметры:
  - `rfc_number` - номер RFC для загрузки (будет нормализован внутри функции)
  - `output_dir` - директория для сохранения
  - `fetch_pdf` - загружать ли PDF (по умолчанию False)
  - `max_depth` - максимальная глубина рекурсии (по умолчанию 1)
  - `processed` - set уже обработанных RFC (для предотвращения дубликатов). Если None, создаётся новый set
- Логика:
  1. Инициализировать `processed` как пустой set, если он None
  2. Нормализовать `rfc_number` через `normalize_rfc_number()`
  3. Проверить, не обработан ли уже этот RFC (проверка в `processed`)
  4. Если уже обработан - вернуть пустой словарь (избежать повторной обработки)
  5. Добавить RFC в `processed`
  6. Инициализировать результирующий словарь `result = {}`
  7. Определить путь к XML файлу: `xml_file = output_dir / f"{rfc_number}.xml"`
  8. Проверить существование XML файла
  9. Если файл не существует:
     - Логировать "Downloading RFC {rfc_number}..."
     - Загрузить через `download_rfc(rfc_number, output_dir, fetch_pdf)`
     - Если загрузка неудачна (вернула None) - логировать ошибку и вернуть текущий result
  10. Если файл существует:
      - Логировать "RFC {rfc_number} already downloaded, skipping download"
  11. Добавить в result: `result[rfc_number] = xml_file`
  12. Извлечь ссылки на другие RFC через `extract_rfc_references(xml_file)`
  13. Если `max_depth > 0`:
      - Для каждого найденного RFC:
        - Логировать "Found reference to RFC {ref_rfc} (depth {max_depth})"
        - Рекурсивно вызвать себя: `download_rfc_recursive(ref_rfc, output_dir, fetch_pdf, max_depth - 1, processed)`
        - Объединить результат с текущим result
  14. Вернуть result

**Файлы для редактирования/создания:**
- [`lib/downloader.py`](lib/downloader.py:1) - добавить функцию `download_rfc_recursive()`

**Важные детали реализации:**
- Функция должна импортировать `extract_rfc_references` из `lib.utils`
- Обработка ошибок: если `download_rfc()` вернула None, не прерывать весь процесс, а продолжить с другими RFC
- Логирование должно показывать текущую глубину рекурсии для отладки
- Функция должна быть устойчива к отсутствующим или недоступным RFC

**Примеры в существующем коде:**
- [`lib/downloader.py`](lib/downloader.py:13) - функция `download_rfc()` показывает как загружать RFC
- [`lib/utils.py`](lib/utils.py:20) - функция `normalize_rfc_number()` для нормализации номеров

**Команды для проверки:**
```bash
# Запустить тесты после реализации
python3 -m pytest tests/test_downloader.py::test_download_rfc_recursive -v
```

---

## Этап 3: Добавление CLI опции для рекурсивной загрузки

**Что добавить/реализовать:**
- Добавить аргумент `--recursive` в функцию `parse_arguments()` в [`rfc2md.py`](rfc2md.py:24)
- Параметры:
  - `action="store_true"` - флаг без значения
  - `help="Recursively download all RFCs referenced in the specified RFC"`
- Добавить аргумент `--max-depth` (опциональный)
  - `type=int`
  - `default=1`
  - `help="Maximum recursion depth for --recursive (default: 1)"`
- Валидация: `--recursive` можно использовать только с `--rfc`, не с `--file`

**Файлы для редактирования/создания:**
- [`rfc2md.py`](rfc2md.py:24) - модифицировать функцию `parse_arguments()`

**Примеры в существующем коде:**
- [`rfc2md.py`](rfc2md.py:51) - существующие аргументы `--pdf`, `--output-dir` показывают паттерн

**Команды для проверки:**
```bash
# Проверить help
python3 rfc2md.py --help

# Проверить валидацию
python3 rfc2md.py --file test.xml --recursive  # Должна быть ошибка
```

---

## Этап 4: Интеграция рекурсивной загрузки в main()

**Что добавить/реализовать:**
- Модифицировать функцию `main()` в [`rfc2md.py`](rfc2md.py:76)
- Добавить импорт: `from lib import download_rfc_recursive` (в дополнение к существующим)
- Логика изменений:
  1. После создания `output_dir`, если `args.recursive` и `args.rfc`:
     - Нормализовать rfc_number через `normalize_rfc_number(args.rfc)`
     - Логировать "Starting recursive download for RFC {rfc_number} with max depth {args.max_depth}"
     - Вызвать `rfc_files = download_rfc_recursive(rfc_number, output_dir, args.pdf, args.max_depth)`
     - Если словарь пустой - логировать ошибку и выйти с кодом 1
     - Логировать "Downloaded {len(rfc_files)} RFC(s), starting conversion..."
     - Для каждого RFC в словаре (отсортировать по ключу для предсказуемости):
       - Определить output filename: `output_file = output_dir / f"{rfc_num}.md"`
       - Обернуть конвертацию в try-except для обработки ошибок отдельных файлов
       - Создать `XmlToMdConverter(xml_file)` и конвертировать
       - Записать markdown файл
       - Логировать "Successfully converted {rfc_num} to Markdown"
       - При ошибке - логировать "Error converting {rfc_num}: {error}" и продолжить
     - Логировать финальную статистику: "Conversion complete: {success}/{total} RFCs converted successfully"
  2. Если не `args.recursive` - использовать существующую логику (строки 92-134)

**Файлы для редактирования/создания:**
- [`rfc2md.py`](rfc2md.py:76) - модифицировать функцию `main()`

**Примеры в существующем коде:**
- [`rfc2md.py`](rfc2md.py:92) - существующая логика загрузки и конвертации одного RFC
- [`rfc2md.py`](rfc2md.py:122) - логика конвертации XML в Markdown

**Команды для проверки:**
```bash
# Тестовая рекурсивная загрузка
python3 rfc2md.py --rfc 9514 --recursive --output-dir test_output --debug

# Проверить, что файлы созданы
ls -la test_output/

# Проверить, что повторная загрузка не скачивает заново
python3 rfc2md.py --rfc 9514 --recursive --output-dir test_output --debug
```

---

## Этап 5: Добавление тестов для extract_rfc_references

**Что добавить/реализовать:**
- Тест `test_extract_rfc_references()` в файле [`tests/test_utils.py`](tests/test_utils.py:1)
- Тестовые случаи:
  1. Извлечение RFC из реального XML файла (использовать [`examples/rfc9514.xml`](examples/rfc9514.xml:1))
  2. Проверка, что возвращается set
  3. Проверка, что номера нормализованы (формат "rfcXXXX")
  4. Проверка обработки пустого XML (без references)
  5. Проверка обработки невалидного XML

**Файлы для редактирования/создания:**
- [`tests/test_utils.py`](tests/test_utils.py:1) - добавить тест `test_extract_rfc_references()`

**Примеры в существующем коде:**
- [`tests/test_utils.py`](tests/test_utils.py:8) - существующие тесты показывают структуру

**Команды для проверки:**
```bash
# Запустить новый тест
python3 -m pytest tests/test_utils.py::test_extract_rfc_references -v

# Запустить все тесты utils
python3 -m pytest tests/test_utils.py -v

# Проверить покрытие
python3 -m pytest tests/test_utils.py --cov=lib.utils --cov-report=term-missing
```

---

## Этап 6: Добавление тестов для рекурсивной загрузки

**Что добавить/реализовать:**
- Создать новый файл `tests/test_downloader.py`
- Тесты:
  1. `test_download_rfc_recursive_single()` - загрузка одного RFC без рекурсии
  2. `test_download_rfc_recursive_with_depth()` - загрузка с глубиной 1
  3. `test_download_rfc_recursive_skip_existing()` - проверка пропуска существующих файлов
  4. `test_download_rfc_recursive_max_depth()` - проверка ограничения глубины
  5. `test_download_rfc_recursive_circular_refs()` - проверка обработки циклических ссылок
- Использовать `pytest.fixture` для создания временной директории
- Использовать `unittest.mock` для мокирования HTTP запросов

**Файлы для редактирования/создания:**
- `tests/test_downloader.py` - создать новый файл с тестами

**Примеры в существующем коде:**
- [`tests/test_utils.py`](tests/test_utils.py:1) - структура тестов и использование pytest

**Команды для проверки:**
```bash
# Запустить новые тесты
python3 -m pytest tests/test_downloader.py -v

# Запустить все тесты
python3 -m pytest tests/ -v

# Проверить покрытие
python3 -m pytest tests/test_downloader.py --cov=lib.downloader --cov-report=term-missing
```

---

## Этап 7: Обновление документации

**Что добавить/реализовать:**
- Обновить [`README.md`](README.md:1) с описанием новой функциональности
- Добавить в раздел "Features":
  - "Recursive RFC download - automatically download all referenced RFCs"
- Добавить в раздел "Usage" новые примеры:
  ```bash
  # Recursive download with default depth (1 level)
  python3 rfc2md.py --rfc 9514 --recursive
  
  # Recursive download with custom depth
  python3 rfc2md.py --rfc 9514 --recursive --max-depth 2
  
  # Recursive download with PDF
  python3 rfc2md.py --rfc 9514 --recursive --pdf --output-dir downloads
  ```
- Добавить в раздел "Complete Examples":
  ```bash
  # Download RFC 9514 and all its references recursively
  python3 rfc2md.py --rfc 9514 --recursive --output-dir output
  
  # Download with depth 2 and debug logging
  python3 rfc2md.py --rfc 9514 --recursive --max-depth 2 --debug
  ```
- Обновить раздел "Known Limitations":
  - "Recursive download respects already downloaded files (skips re-download but always reconverts)"

**Файлы для редактирования/создания:**
- [`README.md`](README.md:1) - обновить документацию

**Примеры в существующем коде:**
- [`README.md`](README.md:39) - существующие примеры использования
- [`README.md`](README.md:94) - раздел "Complete Examples"

**Команды для проверки:**
```bash
# Проверить markdown синтаксис
# (можно использовать любой markdown linter или просто открыть в VS Code)

# Проверить, что примеры работают
python3 rfc2md.py --rfc 9514 --recursive --output-dir test_output
```

---

## Этап 8: Финальная проверка и интеграция

**Что добавить/реализовать:**
- Запустить все тесты
- Проверить линтеры (ruff, mypy)
- Проверить работу на реальных примерах
- Убедиться, что существующая функциональность не сломана

**Файлы для редактирования/создания:**
- Нет новых файлов, только проверка

**Команды для проверки:**
```bash
# Запустить все тесты
make test

# Запустить линтеры
make lint

# Запустить type checker
make type-check

# Запустить все проверки
make all

# Тестовые сценарии
# 1. Обычная загрузка (не должна сломаться)
python3 rfc2md.py --rfc 9514 --output-dir test1

# 2. Рекурсивная загрузка
python3 rfc2md.py --rfc 9514 --recursive --output-dir test2

# 3. Повторная рекурсивная загрузка (должна пропустить скачивание)
python3 rfc2md.py --rfc 9514 --recursive --output-dir test2

# 4. Рекурсивная загрузка с глубиной 2
python3 rfc2md.py --rfc 9514 --recursive --max-depth 2 --output-dir test3

# 5. Рекурсивная загрузка с PDF
python3 rfc2md.py --rfc 9514 --recursive --pdf --output-dir test4

# Очистка тестовых директорий
rm -rf test1 test2 test3 test4
```

---

## Порядок выполнения

1. **Этап 1** - Добавить функцию извлечения RFC ссылок
2. **Этап 2** - Добавить функцию рекурсивной загрузки
3. **Этап 3** - Добавить CLI опции
4. **Этап 4** - Интегрировать в main()
5. **Этап 5** - Добавить тесты для extract_rfc_references
6. **Этап 6** - Добавить тесты для рекурсивной загрузки
7. **Этап 7** - Обновить документацию
8. **Этап 8** - Финальная проверка

## Ключевые технические решения

### Предотвращение дубликатов
- Используется `set` для отслеживания обработанных RFC
- Проверка существования XML файла перед загрузкой
- Всегда выполняется конвертация (даже для существующих файлов)

### Ограничение глубины рекурсии
- Параметр `max_depth` контролирует глубину
- По умолчанию `max_depth=1` (загружать только прямые ссылки)
- При каждом рекурсивном вызове `max_depth` уменьшается на 1

### Обработка циклических ссылок
- Set `processed` предотвращает повторную обработку
- RFC добавляется в `processed` до начала обработки его ссылок

### Логирование
- Информативные сообщения о каждом шаге
- Отдельные сообщения для "downloading" и "already exists"
- Debug-логи для отслеживания рекурсии

## Примеры использования после реализации

```bash
# Базовая рекурсивная загрузка
python3 rfc2md.py --rfc 9514 --recursive

# С указанием глубины
python3 rfc2md.py --rfc 9514 --recursive --max-depth 2

# С PDF и кастомной директорией
python3 rfc2md.py --rfc 9514 --recursive --pdf --output-dir downloads

# С debug логами
python3 rfc2md.py --rfc 9514 --recursive --debug
```

## Дополнительные соображения

### Обработка ошибок
- Если один из RFC не удалось загрузить, процесс должен продолжиться с остальными
- Все ошибки должны логироваться, но не прерывать выполнение
- В конце должна выводиться статистика успешных/неудачных операций

### Производительность
- Загрузка RFC выполняется последовательно (не параллельно) для простоты
- При большой глубине рекурсии может потребоваться значительное время
- Пользователь должен видеть прогресс через логирование

### Безопасность
- Ограничение max_depth предотвращает бесконечную рекурсию
- Set processed предотвращает циклические зависимости
- Валидация входных данных (только с --rfc, не с --file)

### Совместимость
- Существующая функциональность (без --recursive) не должна измениться
- Все существующие тесты должны продолжать работать
- Новая функциональность добавляется опционально