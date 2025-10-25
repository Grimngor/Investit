# Logging Infrastructure

## Backend Logging

The backend uses Python's built-in logging with rotating file handlers.

### Configuration
- Location: `backend/app/logger.py`
- Log directory: `backend/logs/`
- Files:
  - `app.log` - All application logs (INFO and above)
  - `error.log` - Error logs only (ERROR and above)
- Rotation: 10MB max file size, keeps 5 backup files
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

### Log Levels
- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical errors

### Usage
```python
from app.logger import logger

logger.info("User logged in", extra={"user": username})
logger.error("Failed to process order", extra={"error": str(e)})
```

### Console Output
- Console (stdout): INFO and above
- File (app.log): All levels based on configuration
- File (error.log): ERROR and above only

## Frontend Logging

The frontend uses a custom logger with localStorage persistence.

### Configuration
- Location: `frontend/src/utils/logger.ts`
- Storage: Browser localStorage (key: `investit_logs`)
- Max logs: 1000 most recent entries
- Levels: DEBUG, INFO, WARN, ERROR

### Why localStorage?
Browser-based web applications cannot directly write to the file system for security reasons. The logs are stored in localStorage and can be:
1. Viewed in browser DevTools (Application > Local Storage)
2. Exported manually if needed
3. Automatically rotated (keeps last 1000 entries)

### Usage
```typescript
import { logger } from '@/utils/logger'

logger.info('Portfolio loaded', { count: portfolio.holdings.length })
logger.error('API request failed', { error: err.message })
```

### Viewing Logs
- **Browser Console**: All logs are also output to console in development mode
- **localStorage**: Open DevTools > Application > Local Storage > `investit_logs`
- **Export**: Use `logger.getLogs()` and `logger.exportLogs()` methods

## Best Practices

1. **Be Specific**: Include relevant context in log messages
2. **Log Errors**: Always log errors with stack traces
3. **Avoid Sensitive Data**: Never log passwords, tokens, or PII
4. **Use Appropriate Levels**: 
   - DEBUG for detailed tracing
   - INFO for normal operations
   - WARN for recoverable issues
   - ERROR for failures
5. **Include Context**: Use the context parameter for structured data

## Log Rotation

### Backend
- Automatic rotation at 10MB
- Keeps 5 backup files
- Old logs are automatically compressed and deleted

### Frontend
- Automatic rotation at 1000 entries
- Older entries are automatically removed
- Can be manually cleared via `logger.clear()`
