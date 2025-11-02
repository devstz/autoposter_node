#!/bin/bash
set -e

LOG_FILE="/var/log/autoposter_install.log"
REPO_URL="https://github.com/devstz/autoposter_node"
INSTALL_DIR="/opt/autoposter_node"
SERVICE_NAME="autoposter.service"

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
    log "❌ Обнаружены ошибки во время проверки. Установка остановлена."
    exit 1
  fi
}

if [ "$EUID" -ne 0 ]; then
  log "❌ Запустите скрипт через sudo"
  exit 1
fi

TOKEN="$1"
DATABASE_URL="$2"

if [ -z "$TOKEN" ] || [ -z "$DATABASE_URL" ]; then
  log "Использование: sudo ./install_autoposter.sh TOKEN DATABASE_URL"
  exit 1
fi

log "🚀 Начинаем установку Autoposter Node Bot..."
sleep 1

log "🔧 Обновляем пакеты..."
apt update -y >>"$LOG_FILE" 2>&1
check_success "Обновление apt"

log "🧩 Проверяем наличие Python3..."
if ! command -v python3 &>/dev/null; then
  log "Python3 не найден, устанавливаем..."
  apt install -y python3 >>"$LOG_FILE" 2>&1
  check_success "Установка Python3"
fi

log "🧩 Проверяем наличие git..."
if ! command -v git &>/dev/null; then
  apt install -y git >>"$LOG_FILE" 2>&1
  check_success "Установка Git"
fi

PYTHON_VERSION=$(python3 -V 2>&1 | awk '{print $2}' | cut -d. -f1,2)
log "🧩 Проверяем pip для Python ${PYTHON_VERSION}..."
apt install -y python${PYTHON_VERSION}-pip >>"$LOG_FILE" 2>&1 || apt install -y python3-pip >>"$LOG_FILE" 2>&1
check_success "Установка pip"

log "📦 Клонируем репозиторий..."
rm -rf "$INSTALL_DIR"
git clone "$REPO_URL" "$INSTALL_DIR" >>"$LOG_FILE" 2>&1
check_success "Клонирование репозитория"

cd "$INSTALL_DIR"

log "🧾 Создаём .env файл..."
cat > .env <<EOF
TOKEN=${TOKEN}
DATABASE_URL=${DATABASE_URL}
LOG_FILE=output.log
LOG_LEVEL=INFO
EOF
check_success "Создание .env"

log "🐍 Создаём виртуальное окружение..."
python3 -m venv .venv >>"$LOG_FILE" 2>&1
check_success "Создание .venv"

source .venv/bin/activate
pip install --upgrade pip >>"$LOG_FILE" 2>&1

if [ -f "requirements.txt" ]; then
  log "📥 Устанавливаем зависимости..."
  pip install -r requirements.txt >>"$LOG_FILE" 2>&1
  check_success "Установка зависимостей"
else
  log "⚠️ requirements.txt не найден — пропускаем установку"
fi

# --- проверки ---
run_check() {
  FILE="$1"
  DESC="$2"
  if [ -f "$FILE" ]; then
    log "▶ Проверка: $DESC"
    python3 "$FILE" >>"$LOG_FILE" 2>&1 || {
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
    log "⚠️ Файл $FILE не найден, пропускаем"
  fi
}

run_check "tests/check_db.py" "Проверка базы данных"
run_check "tests/check_bot.py" "Проверка токена бота"
run_check "tests/check_dublication_ip.py" "Проверка IP дубликатов"

log "⚙️ Создаём systemd сервис..."
cat > /etc/systemd/system/$SERVICE_NAME <<EOF
[Unit]
Description=Autoposter Node Bot
After=network.target

[Service]
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/.venv/bin/python ${INSTALL_DIR}/main.py
Restart=always
User=root
EnvironmentFile=${INSTALL_DIR}/.env
StandardOutput=append:${INSTALL_DIR}/output.log
StandardError=append:${INSTALL_DIR}/output.log

[Install]
WantedBy=multi-user.target
EOF
check_success "Создание systemd сервиса"

log "🔁 Перезагружаем systemd..."
systemctl daemon-reload >>"$LOG_FILE" 2>&1
check_success "Перезагрузка systemctl"

log "📌 Активируем и запускаем сервис..."
systemctl enable "$SERVICE_NAME" >>"$LOG_FILE" 2>&1
systemctl restart "$SERVICE_NAME" >>"$LOG_FILE" 2>&1
sleep 3

STATUS=$(systemctl is-active "$SERVICE_NAME")
if [ "$STATUS" = "active" ]; then
  log "🎉 Всё успешно установлено и запущено!"
  systemctl status "$SERVICE_NAME" --no-pager
else
  log "❌ Ошибка запуска — проверьте лог: journalctl -u $SERVICE_NAME -f"
  exit 1
fi

log "📜 Установка завершена. Подробный лог: $LOG_FILE"
