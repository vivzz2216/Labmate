# React Project Execution Fix

## Problem
The React project execution was failing with a timeout after 120 seconds. The container would start but the Vite dev server never became ready. Container logs were empty, indicating the npm install and Vite commands weren't running.

## Root Causes

1. **Detached Docker Exec Issue**: The original implementation used `docker exec -d` to run npm install and Vite, which doesn't properly execute commands in detached mode
2. **Complex File Transfer**: Used tar archives and `docker cp` instead of volume mounts
3. **Windows Path Incompatibility**: Windows paths weren't converted to Docker-compatible format for volume mounts
4. **Poor Diagnostics**: No logging to see what was happening inside the container

## Fixes Applied

### 1. Simplified Container Startup
**Before**: 
- Start container with `tail -f /dev/null`
- Create tar archive
- Copy files with `docker cp`
- Extract files in container
- Run `docker exec -d` for npm install

**After**:
- Mount temp directory directly as a volume
- Run npm install and Vite as part of the container start command

```python
# Direct volume mount
'-v', f'{docker_temp_dir}:/app',
'sh', '-c', 
'npm install --silent --no-audit --no-fund && npx vite --host 0.0.0.0 --port 3001'
```

### 2. Windows Path Conversion
Added path conversion for Windows Docker Desktop:

```python
# Convert C:\Users\... to /c/Users/... format
if os.name == 'nt':  # Windows
    docker_temp_dir = temp_dir.replace('\\', '/')
    if len(docker_temp_dir) > 1 and docker_temp_dir[1] == ':':
        docker_temp_dir = '/' + docker_temp_dir[0].lower() + docker_temp_dir[2:]
```

### 3. Enhanced Logging
Added comprehensive logging to diagnose issues:

```python
startup_cmd = (
    'echo "=== Starting React project ===" && '
    'echo "Current directory: $(pwd)" && '
    'echo "Files in /app:" && ls -la /app && '
    'echo "=== Installing dependencies ===" && '
    'npm install --silent --no-audit --no-fund 2>&1 && '
    'echo "=== Starting Vite dev server ===" && '
    'npx vite --host 0.0.0.0 --port 3001'
)
```

### 4. Periodic Log Display
- Show initial logs after 2 seconds
- Show recent logs every 15 seconds during the wait
- Show full logs if container stops unexpectedly
- Show full logs if timeout is reached

## Testing
To test the fix:

1. **Start the application**:
   ```bash
   docker-compose up
   ```

2. **Submit a React SPA task** from the frontend with:
   - Multiple React components
   - React Router routes
   - Project files (App.js, components, etc.)

3. **Monitor the backend logs** to see:
   - Container startup messages
   - Initial file listing
   - npm install progress
   - Vite dev server startup
   - Route screenshot capture

## Expected Behavior

**Successful execution**:
```
[React Project] Created temp directory: /tmp/react_spa_xxxxx
[React Project] Starting container: react_spa_12345678
[React Project] Using port: 45678
[React Project] Docker volume path: /tmp/react_spa_xxxxx (or /c/Users/... on Windows)
[React Project] Container started: abc123...
[React Project] Installing dependencies and starting Vite (this may take 90-120s)...
[React Project] Initial container output:
=== Starting React project ===
Current directory: /app
Files in /app:
-rw-r--r-- 1 root root  281 Oct 21 14:00 package.json
drwxr-xr-x 3 root root 4096 Oct 21 14:00 src
...
=== Installing dependencies ===
[npm install output]
=== Starting Vite dev server ===
[Vite startup output]
[React Project] Vite dev server ready!
[React Project] Capturing 3 routes: ['/', '/about', '/contact'] on port 45678
[React Project] Successfully captured 3 routes
```

**If it fails**, you'll now see detailed logs showing exactly where it failed (volume mount, npm install, or Vite startup).

## File Modified
- `backend/app/services/executor_service.py` - `_start_react_container()` method

## Benefits
1. ✅ Simpler, more reliable container startup
2. ✅ Works with Windows paths
3. ✅ Clear diagnostic logs
4. ✅ Faster to identify issues
5. ✅ No complex tar/copy operations
6. ✅ Direct volume mounting is more efficient

