sleep 10
python -u /home/alarm/tradingbot/bot.py >> /home/alarm/tradingbot/bot.log 2>&1 &
PID=$!
echo $PID > /home/alarm/tradingbot/bot.pid
