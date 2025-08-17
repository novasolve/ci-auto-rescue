#!/bin/bash
# Script to run nova and capture ALL output to a file

# Create logs directory if it doesn't exist
mkdir -p nova_logs

# Generate timestamp for unique log file
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="nova_logs/nova_run_${TIMESTAMP}.log"

echo "🔴 Recording nova session to: $LOG_FILE"
echo "📝 All output will be captured (stdout + stderr)"
echo "💡 Tip: Use 'tail -f $LOG_FILE' in another terminal to monitor"
echo ""

# Run nova with all arguments passed to this script, capturing everything
nova "$@" 2>&1 | tee "$LOG_FILE"

echo ""
echo "✅ Session recorded to: $LOG_FILE"
echo "📊 File size: $(ls -lh "$LOG_FILE" | awk '{print $5}')"
echo "📄 Line count: $(wc -l < "$LOG_FILE") lines"
echo ""
echo "📖 To view the log:"
echo "   cat $LOG_FILE          # View entire log"
echo "   less $LOG_FILE         # View with paging"
echo "   tail -100 $LOG_FILE    # View last 100 lines"
