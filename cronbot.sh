if ! pgrep -F /home/alarm/tradingbot/bot.pid; then
  chronyd -q
  /bin/bash -e /home/alarm/tradingbot/runbot.sh
fi


