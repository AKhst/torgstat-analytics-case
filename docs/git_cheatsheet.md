# Git: повседневная шпаргалка

## 1. Настройка Git на новом компьютере

Выполняется один раз:

```bash
git config --global user.name "Ваше имя"
git config --global user.email "email@example.com"
git config --global init.defaultBranch main
```

Проверить настройки:

```bash
git config --global --list
```

## 2. Скачать проект впервые

```bash
git clone https://github.com/AKhst/torgstat-analytics-case.git
cd torgstat-analytics-case
```

Проверить подключённый GitHub-репозиторий:

```bash
git remote -v
```

## 3. Начало каждого рабочего дня

Перейти в проект:

```bash
cd /путь/к/torgstat-analytics-case
```

На Windows:

```powershell
cd C:\Projects\torgstat-analytics-case
```

Получить актуальную информацию с GitHub:

```bash
git fetch origin
git status --short --branch
```

Подтянуть изменения:

```bash
git pull --ff-only origin main
```

`--ff-only` запрещает Git создавать неожиданный merge-коммит.

## 4. Проверить синхронизацию

```bash
git fetch origin
git rev-list --left-right --count HEAD...origin/main
```

Расшифровка:

```text
0  0  — локальная ветка полностью синхронизирована
0  2  — локальная ветка отстаёт на два коммита
2  0  — локально есть два неотправленных коммита
2  3  — ветки разошлись; не выполнять push вслепую
```

Сравнить последние коммиты:

```bash
git log -1 --oneline HEAD
git log -1 --oneline origin/main
```

## 5. Посмотреть текущие изменения

Краткий список:

```bash
git status --short
```

Полный статус:

```bash
git status
```

Изменения внутри файлов:

```bash
git diff
```

Изменения конкретного файла:

```bash
git diff path/to/file
```

Список изменённых файлов:

```bash
git diff --name-only
```

## 6. Подготовить commit

Добавлять лучше конкретные файлы:

```bash
git add path/to/file
git add path/to/another-file
```

Добавить целую папку:

```bash
git add report/power_bi
```

Добавить все изменения:

```bash
git add .
```

`git add .` использовать только после проверки `git status`.

Проверить то, что войдёт в commit:

```bash
git diff --staged
git status
```

## 7. Создать commit

```bash
git commit -m "feat: add revenue dashboard"
```

Полезные префиксы:

```text
feat:     новая функциональность
fix:      исправление ошибки
docs:     документация
test:     тесты
refactor: изменение кода без изменения поведения
chore:    техническое обслуживание
```

Примеры:

```bash
git commit -m "feat: add Power BI data quality page"
git commit -m "fix: correct invoice date relationship"
git commit -m "docs: add Git workflow guide"
```

## 8. Отправить commit в GitHub

```bash
git push origin main
```

Проверить результат:

```bash
git status --short --branch
```

Чистое синхронизированное состояние:

```text
## main...origin/main
```

## 9. Полный ежедневный цикл

```bash
git fetch origin
git pull --ff-only origin main

# Работа с файлами

git status
git diff
git add path/to/changed-file
git diff --staged
git commit -m "feat: describe the change"
git push origin main
git status --short --branch
```

## 10. Работа через отдельную ветку

Создать ветку:

```bash
git switch -c feature/revenue-dashboard
```

Проверить текущую ветку:

```bash
git branch --show-current
```

Первый push новой ветки:

```bash
git push -u origin feature/revenue-dashboard
```

Вернуться на `main`:

```bash
git switch main
git pull --ff-only origin main
```

Удалить локальную ветку после merge:

```bash
git branch -d feature/revenue-dashboard
```

Для командной production-разработки изменения обычно вливаются в `main` через Pull Request.

## 11. Безопасно отменить изменения

Отменить незакоммиченные изменения файла:

```bash
git restore path/to/file
```

Вернуть файл из staged обратно в unstaged:

```bash
git restore --staged path/to/file
```

Восстановить случайно удалённый файл:

```bash
git restore path/to/deleted-file
```

Отменить уже опубликованный commit новым обратным commit:

```bash
git revert COMMIT_HASH
git push origin main
```

Для опубликованных коммитов `git revert` безопаснее переписывания истории.

## 12. Исправить последний commit

Добавить забытый файл в последний commit, если commit ещё не отправлен:

```bash
git add path/to/file
git commit --amend --no-edit
```

Изменить сообщение последнего неопубликованного commit:

```bash
git commit --amend -m "fix: correct commit message"
```

Не использовать `--amend` для уже опубликованного commit без понимания последствий.

## 13. Временно отложить изменения

Сохранить незакоммиченные изменения:

```bash
git stash push -m "WIP: Power BI dashboard"
```

Посмотреть список:

```bash
git stash list
```

Вернуть последние изменения:

```bash
git stash pop
```

Перед `stash pop` желательно иметь чистую рабочую директорию.

## 14. Посмотреть историю

Краткая история:

```bash
git log --oneline --decorate --graph -10
```

Посмотреть конкретный commit:

```bash
git show COMMIT_HASH
```

Посмотреть изменённые в commit файлы:

```bash
git show --stat COMMIT_HASH
```

Сравнить два commit:

```bash
git diff OLD_COMMIT NEW_COMMIT
```

## 15. Если push отклонён

Типичная причина: в GitHub появились новые коммиты.

```bash
git fetch origin
git status --short --branch
git pull --ff-only origin main
```

Если `pull --ff-only` сообщает о diverged branches, не выполнять `force push`. Сначала посмотреть:

```bash
git log --oneline --graph --decorate --all -15
```

После этого решить, нужно ли делать rebase, merge или переносить локальные изменения.

## 16. Конфликты

Посмотреть конфликтующие файлы:

```bash
git status
```

Внутри файла Git показывает:

```text
<<<<<<< HEAD
локальная версия
=======
версия из другой ветки
>>>>>>> branch
```

Нужно вручную оставить правильный вариант, удалить маркеры и выполнить:

```bash
git add path/to/resolved-file
git commit
```

Прервать незавершённый merge:

```bash
git merge --abort
```

## 17. Mac ↔ Windows VM

Перед переходом с одного компьютера на другой:

```bash
git status
git add <нужные файлы>
git commit -m "feat: describe changes"
git push origin main
```

На другом компьютере:

```bash
git fetch origin
git pull --ff-only origin main
```

Правила для Power BI:

- закрывать Power BI Desktop перед `git pull`;
- сохранять PBIP перед `git status`;
- проверять PBIR/TMDL изменения перед commit;
- не редактировать один отчёт одновременно на Mac и Windows;
- не коммитить локальный IP, пароли и Power BI cache.

## 18. Что нельзя коммитить

```text
.env
пароли и токены
*.pbix
**/.pbi/cache.abf
**/.pbi/localSettings.json
**/.pbi/unappliedChanges.json
```

Проверить игнорирование файла:

```bash
git check-ignore -v path/to/file
```

## 19. Опасные команды

Не выполнять без понимания:

```bash
git reset --hard
git clean -fd
git push --force
git rebase
```

Они могут удалить локальную работу или переписать опубликованную историю.

## 20. Минимальный набор на каждый день

```bash
git fetch origin
git pull --ff-only origin main
git status
git diff
git add <файлы>
git diff --staged
git commit -m "type: meaningful description"
git push origin main
```
