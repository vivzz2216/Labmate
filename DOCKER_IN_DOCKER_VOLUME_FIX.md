# Docker-in-Docker Volume Mount Fix for React Projects

## Problem

React project execution was failing with an empty `/app` directory in the React container. The logs showed:

```
Files in /app:
total 4
drwxr-xr-x 2 root root   40 Oct 21 13:59 .
drwxr-xr-x 1 root root 4096 Oct 21 13:59 ..
```

### Root Cause

The backend service runs inside a Docker container and uses Docker-in-Docker (DinD) to spawn additional containers for React projects. When the backend created temp files in `/tmp/react_spa_xxx` and tried to mount that path to the React container, the mount failed because:

1. **Path Context Issue**: `/tmp/react_spa_xxx` exists inside the backend container, not on the host
2. **Docker Volume Mounts**: Docker volume mounts require host filesystem paths, not container filesystem paths
3. **DinD Limitation**: When a container controls Docker via `/var/run/docker.sock`, volume mounts must reference the host filesystem

## Solution

Use a shared volume that's mounted from the host to both the backend container and the React containers.

### Changes Made

#### 1. Docker Compose Configuration (`docker-compose.yml`)

Added a new volume mount for React temporary files and an environment variable for the host project root:

```yaml
backend:
  environment:
    - REACT_TEMP_DIR=/app/react_temp
    - HOST_PROJECT_ROOT=${PWD}  # Host path to the project directory
  volumes:
    - ./backend/react_temp:/app/react_temp  # NEW: Temp directory for React projects
    - /var/run/docker.sock:/var/run/docker.sock  # Docker-in-Docker
```

#### 2. Configuration Updates (`backend/app/config.py`)

Added new settings:

```python
REACT_TEMP_DIR: str = "/app/react_temp"  # Inside container
HOST_PROJECT_ROOT: str = os.getenv("HOST_PROJECT_ROOT", os.getcwd())  # Host path
```

#### 3. Executor Service Updates (`backend/app/services/executor_service.py`)

**Changed temp directory location:**

```python
# OLD: Used system temp directory (inside container)
temp_dir = tempfile.mkdtemp(prefix="react_spa_")  # Creates /tmp/react_spa_xxx

# NEW: Use mounted volume
base_temp_dir = settings.REACT_TEMP_DIR  # /app/react_temp
temp_dir = os.path.join(base_temp_dir, f"react_spa_{project_id}")
```

**Calculate host path for Docker mounts:**

```python
# Inside backend container: /app/react_temp/react_spa_xxx
# On host: <PROJECT_ROOT>/backend/react_temp/react_spa_xxx
host_path = os.path.join(
    settings.HOST_PROJECT_ROOT,
    "backend",
    "react_temp",
    f"react_spa_{project_id}"
)

# Convert Windows paths to Docker format
docker_host_path = host_path.replace('\\', '/')
if os.name == 'nt' and docker_host_path[1] == ':':
    # C:/Users/... → /c/Users/...
    docker_host_path = '/' + docker_host_path[0].lower() + docker_host_path[2:]

# Mount to React container
docker run -v {docker_host_path}:/app ...
```

#### 4. Directory Structure

Created the host directory:
```bash
mkdir backend/react_temp
```

This directory is now:
- Mounted to `/app/react_temp` in the backend container
- Used as the source for volume mounts to React containers

## How It Works

### Data Flow

1. **Backend creates project files**:
   - Location inside backend container: `/app/react_temp/react_spa_12345678/`
   - Location on host: `<PROJECT_ROOT>/backend/react_temp/react_spa_12345678/`

2. **Backend starts React container**:
   ```bash
   docker run -v <PROJECT_ROOT>/backend/react_temp/react_spa_12345678:/app node:20-slim
   ```

3. **React container sees files**:
   - The host directory is mounted to `/app` in the React container
   - Files are immediately available

### Path Mapping

```
Host Filesystem:
  /path/to/Labmate/
    └── backend/
        └── react_temp/           # Created on host
            └── react_spa_xxx/    # Project files
                ├── package.json
                ├── src/
                └── ...

Backend Container:
  /app/
    └── react_temp/              # Mounted from host
        └── react_spa_xxx/       # Same files
            ├── package.json
            ├── src/
            └── ...

React Container:
  /app/                          # Mounted from host
    ├── package.json
    ├── src/
    └── ...
```

## Testing

1. **Start services**:
   ```bash
   cd /path/to/Labmate
   docker-compose up -d
   ```

2. **Submit React project** from the frontend

3. **Check logs**:
   ```bash
   docker logs labmate-backend-1 -f
   ```

4. **Expected output**:
   ```
   [React Project] Container temp dir: /app/react_temp/react_spa_12345678
   [React Project] Host path for mount: /path/to/Labmate/backend/react_temp/react_spa_12345678
   [React Project] Docker volume path: /path/to/labmate/backend/react_temp/react_spa_12345678
   [React Project] Initial container output:
   === Starting React project ===
   Files in /app:
   total 20
   -rw-r--r-- 1 root root  281 Oct 21 14:00 package.json
   -rw-r--r-- 1 root root  185 Oct 21 14:00 vite.config.js
   -rw-r--r-- 1 root root  300 Oct 21 14:00 index.html
   drwxr-xr-x 3 root root 4096 Oct 21 14:00 src
   === Installing dependencies ===
   [npm install output...]
   === Starting Vite dev server ===
   [Vite output...]
   [React Project] Vite dev server ready!
   ```

## Benefits

✅ **Reliable volume mounts**: Files are accessible to both containers  
✅ **Cross-platform compatible**: Works on Windows, macOS, and Linux  
✅ **Proper cleanup**: Temp files can be cleaned up after use  
✅ **Debuggable**: Can inspect files on host during execution  
✅ **No tar/copy overhead**: Direct volume mounting is faster  

## Files Modified

1. `docker-compose.yml` - Added volume mount and environment variable
2. `backend/app/config.py` - Added REACT_TEMP_DIR and HOST_PROJECT_ROOT
3. `backend/app/services/executor_service.py` - Updated to use mounted volume
4. Created: `backend/react_temp/` directory

## Environment Variables

- `REACT_TEMP_DIR`: Path inside backend container for React temp files (default: `/app/react_temp`)
- `HOST_PROJECT_ROOT`: Absolute path to the project root on the host (set by Docker Compose to `${PWD}`)

## Cleanup

Temp React projects are automatically cleaned up after execution. To manually clean:

```bash
# Inside backend container
rm -rf /app/react_temp/react_spa_*

# On host
rm -rf backend/react_temp/react_spa_*
```

## Troubleshooting

**Files still empty?**
- Check that `backend/react_temp` exists on host
- Verify Docker Compose mounted the volume: `docker inspect labmate-backend-1 | grep react_temp`
- Check HOST_PROJECT_ROOT is set correctly: `docker exec labmate-backend-1 env | grep HOST_PROJECT_ROOT`

**Windows path issues?**
- Ensure Docker Desktop has access to the drive
- Check path conversion in logs for proper `/c/Users/...` format

**Permission errors?**
- React container runs as root by default, should have access
- Check folder permissions: `ls -la backend/react_temp`

