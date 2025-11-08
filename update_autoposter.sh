#!/bin/bash
set -e

LOG_FILE="/var/log/autoposter_update.log"
INSTALL_DIR="/opt/autoposter_node"
SERVICE_NAME="autoposter.service"
BRANCH="${1:-main}"

echo "" > "$LOG_FILE"

log() {
  echo -e "[`date '+%Y-%m-%d %H:%M:%S'`] $1" | tee -a "$LOG_FILE"
}

check_success() {
  if [ $? -eq 0 ]; then
    log "✅ $1 — успешно"
  else
    log "❌ Ошибка: $1 — см. лог ($LOG_FILE)"
    exit 1
  fi
}

fail_if_error() {
  if grep -q "❌" "$LOG_FILE" || grep -q "⚠️" "$LOG_FILE"; then
    log "❌ Обнаружены ошибки во время проверки. Обновление остановлено."
    exit 1
  fi
}

if [ "$EUID" -ne 0 ]; then
  log "❌ Запустите скрипт через sudo"
  exit 1
fi

log "🚀 Начинаем обновление Autoposter Node Bot..."

if [ ! -d "$INSTALL_DIR/.git" ]; then
  log "❌ Репозиторий не найден в $INSTALL_DIR. Запустите установку."
  exit 1
fi

cd "$INSTALL_DIR"

log "🧼 Проверяем чистоту рабочего дерева..."
if [ -n "$(git status --porcelain)" ]; then
  log "❌ В репозитории есть локальные изменения. Сохраните или откатите их перед обновлением."
  exit 1
fi

log "🛑 Останавливаем сервис..."
systemctl stop "$SERVICE_NAME" >>"$LOG_FILE" 2>&1 || true

log "📡 Подтягиваем обновления из ветки $BRANCH..."
git fetch origin >>"$LOG_FILE" 2>&1
git checkout "$BRANCH" >>"$LOG_FILE" 2>&1
git pull --ff-only origin "$BRANCH" >>"$LOG_FILE" 2>&1
check_success "Обновление репозитория"

if [ -d ".venv" ]; then
  log "🐍 Активируем виртуальное окружение..."
  source .venv/bin/activate
else
  log "⚠️ Виртуальное окружение не найдено — создаём заново"
  python3 -m venv .venv >>"$LOG_FILE" 2>&1
  check_success "Создание .venv"
  source .venv/bin/activate
fi

pip install --upgrade pip >>"$LOG_FILE" 2>&1

if [ -f "requirements.txt" ]; then
  log "📦 Обновляем зависимости..."
  pip install -r requirements.txt >>"$LOG_FILE" 2>&1
  check_success "Установка зависимостей"
else
  log "⚠️ requirements.txt не найден — пропускаем установку"
fi

run_check() {
  FILE="$1"
  DESC="$2"
  TEST_PATH="${INSTALL_DIR}/${FILE}"

  if [ -f "$TEST_PATH" ]; then
    log "▶ Проверка: $DESC"
    (
      cd "${INSTALL_DIR}"
      export $(grep -v '^#' .env | xargs)
      ${INSTALL_DIR}/.venv/bin/python "$FILE"
    ) >>"$LOG_FILE" 2>&1 || {
      log "❌ $DESC — ошибка (см. лог)"
      fail_if_error
    }

    if grep -q "❌" "$LOG_FILE" || grep -q "⚠️" "$LOG_FILE"; then
      log "❌ $DESC — провалено"
      fail_if_error
    else
      log "✅ $DESC — успешно"
    fi
  else
    log "⚠️ Файл $TEST_PATH не найден, пропускаем"
  fi
}

run_check "tests/check_db.py" "Проверка базы данных"
run_check "tests/check_bot.py" "Проверка токена бота"
run_check "tests/check_dublication_ip.py" "Проверка IP дубликатов"

log "🔁 Перезагружаем systemd..."
systemctl daemon-reload >>"$LOG_FILE" 2>&1
check_success "Перезагрузка systemctl"

log "▶ Запускаем сервис..."
systemctl start "$SERVICE_NAME" >>"$LOG_FILE" 2>&1
sleep 3

STATUS=$(systemctl is-active "$SERVICE_NAME")
if [ "$STATUS" = "active" ]; then
  log "🎉 Обновление успешно завершено и сервис запущен!"
  systemctl status "$SERVICE_NAME" --no-pager
else
  log "❌ Ошибка запуска — проверьте лог: journalctl -u $SERVICE_NAME -f"
  exit 1
fi

log "📜 Обновление завершено. Лог: $LOG_FILE"
