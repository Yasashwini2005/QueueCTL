@echo off
echo ========================================
echo Testing Bonus Features
echo ========================================

echo.
echo [1] Priority Queue Test
call queuectl enqueue -c "echo Low Priority" -p 1
call queuectl enqueue -c "echo HIGH PRIORITY" -p 10
call queuectl enqueue -c "echo Medium Priority" -p 5
echo Jobs will process in order: 10, 5, 1

echo.
echo [2] Scheduled Job Test
call queuectl enqueue -c "echo Scheduled Job" --run-at "2025-11-05T15:30:00"
echo Job scheduled for future execution

echo.
echo [3] Timeout Test
call queuectl enqueue -c "timeout /t 5" -t 3
echo Job will timeout after 3 seconds

echo.
echo [4] View Metrics
call queuectl metrics

echo.
echo [5] Start Dashboard
echo Starting web dashboard on http://localhost:5000
call queuectl dashboard

pause