# Game Updater Example (Windows, Python)

Полный пример легального автообновления игры через GitHub Releases.

## Структура проекта

- `app.py` — лаунчер/стартёр игры, проверяет версию и предлагает обновление.
- `updater.py` — отдельный апдейтер с GUI (progress bar, статусы, ошибки).
- `version_checker.py` — логика сравнения версий и запросов к GitHub.
- `config.py` — конфигурация репозитория, имён файлов и URL.
- `version.json` — локальная версия игры.
- `build_windows.bat` — локальная сборка `.exe` в 1 клик.
- `.github/workflows/build-windows-exe.yml` — автосборка `.exe` на GitHub Actions.

## Установка зависимостей

```bash
pip install -r requirements.txt
```

`tkinter` обычно уже входит в стандартный Python для Windows.

## Быстрый запуск (из исходников)

```bash
python app.py
```

Для запуска апдейтера отдельно:

```bash
python updater.py
```

## Как получить `.exe`, чтобы не компилировать вручную

### Вариант 1 (рекомендуется): GitHub Actions (без локальной компиляции)

1. Запушьте проект в GitHub.
2. Создайте тег версии, например `v1.0.0`, и push тега.
3. Workflow `Build Windows EXE` автоматически соберёт:
   - `game_launcher.exe`
   - `updater.exe`
   - архив `game-updater-windows.zip`
4. Готовый zip появится:
   - в **Actions artifacts**,
   - и автоматически прикрепится к **GitHub Release** для тега.

То есть вам не нужно компилировать на своём ПК — просто скачать готовый архив из релиза.

### Вариант 2: локальная сборка в 1 клик

На Windows просто запустите:

```bat
build_windows.bat
```

Готовые файлы будут в `dist\package\`.

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

Для production на Windows используется 2 exe:

- `game_launcher.exe` (из `app.py`)
- `updater.exe` (из `updater.py`)

Такая схема безопасна и практична: updater работает отдельным процессом и может обновлять файлы, пока игра закрыта.
