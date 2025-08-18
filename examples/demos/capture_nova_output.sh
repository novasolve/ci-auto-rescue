#!/bin/bash
# Nova output capture script
# Captures all terminal output while still displaying it

# Create logs directory
LOGS_DIR="nova_logs"
mkdir -p "$LOGS_DIR"

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOGS_DIR/nova_session_${TIMESTAMP}.log"

echo "🔴 Recording nova session to: $LOG_FILE"
echo "📝 All output will be captured (stdout + stderr)"
echo "💡 Tip: Use 'tail -f $LOG_FILE' in another terminal to monitor"
echo ""

# Start recording with script command (captures everything including colors)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS version
    script -a "$LOG_FILE" nova "$@"
else
    # Linux version
    script -a -c "nova $*" "$LOG_FILE"
fi

echo ""
echo "✅ Session recorded to: $LOG_FILE"
echo "📊 File size: $(ls -lh "$LOG_FILE" | awk '{print $5}')"
echo "📄 Line count: $(wc -l < "$LOG_FILE") lines"
