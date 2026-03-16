# Game Updater Example (Windows, Python)

Полный пример легального автообновления игры через GitHub Releases.

## Структура проекта

- `app.py` — лаунчер/стартёр игры, проверяет версию и предлагает обновление.
- `updater.py` — отдельный апдейтер с GUI (progress bar, статусы, ошибки).
- `version_checker.py` — логика сравнения версий и запросов к GitHub.
- `config.py` — конфигурация репозитория, имён файлов и URL.
- `version.json` — локальная версия игры.

## Установка зависимостей

```bash
pip install requests
```

`tkinter` обычно уже входит в стандартный Python для Windows.

## Быстрый запуск

```bash
python app.py
```

Для запуска апдейтера отдельно:

```bash
python updater.py
```

## Что изменить под свой проект

Откройте `config.py` и настройте:

- `GITHUB_OWNER` — owner репозитория.
- `GITHUB_REPO` — имя репозитория.
- `GAME_EXE_NAME` — имя основного exe игры.
- `RELEASE_ASSET_NAME` — имя zip-архива в GitHub Release.

## Формат локальной версии (`version.json`)

```json
{
  "version": "1.0.0"
}
```

Поддерживается semver формат `major.minor.patch` (например `1.2.3`).

## Пример запроса к GitHub Releases API

Лаунчер использует endpoint:

```text
https://api.github.com/repos/<owner>/<repo>/releases/latest
```

Ожидаемые поля ответа:

- `tag_name` (например `v1.1.0`)
- `assets[].name`
- `assets[].browser_download_url`
- `html_url`

## Пример raw-источника версии (fallback)

Можно хранить версию в raw-файле:

- Plain text: `1.1.0`
- или JSON: `{"version":"1.1.0"}`

URL настраивается в `RAW_VERSION_URL` в `config.py`.

## Логика обновления

1. `app.py` читает `version.json`.
2. Получает актуальную версию из GitHub (предпочтительно Releases).
3. Сравнивает версии (`1.0.0 < 1.0.1 < 1.1.0`).
4. Если версия устарела, показывает окно с кнопками:
   - `Обновить`
   - `Открыть GitHub`
   - `Выход`
5. При `Обновить` запускается `updater.py`, а launcher завершается.
6. `updater.py`:
   - скачивает zip,
   - показывает прогресс,
   - распаковывает во временную папку,
   - копирует файлы в директорию игры,
   - не трогает папки `saves`, `config`, `userdata`,
   - обновляет `version.json`,
   - запускает игру.

## Обработка ошибок

Есть обработка основных случаев:

- нет интернета / недоступен GitHub,
- ошибка GitHub API,
- повреждённый архив,
- нет прав на запись,
- проблемы с заменой файлов.

Логи:

- `launcher.log`
- `updater.log`

## Примечание по упаковке в exe

Для production на Windows обычно собирают два exe:

- `game_launcher.exe` (из `app.py`)
- `updater.exe` (из `updater.py`)

Например через PyInstaller. Тогда updater сможет запускаться отдельно и обновлять файлы, пока основная игра закрыта.
