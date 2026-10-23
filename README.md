# GridGuard

GridGuard is an AI-powered smart grid cybersecurity and monitoring platform designed for real-time anomaly detection, edge device telemetry, and automated threat mitigation.

---

## Project Structure

```
gridguard/
├── backend/          # Backend API services
├── ai-service/       # AI / ML anomaly detection engine
├── web-dashboard/    # Operations web dashboard
├── mobile-app/       # Mobile application for alerts & field monitoring
├── iot-simulator/    # Smart grid IoT telemetry simulator
├── iot-firmware/     # Firmware for smart grid edge devices & RTUs
├── security-tools/   # Security auditing, IDS, and penetration testing tools
├── deployments/      # Docker, Kubernetes, and deployment configs
├── tests/            # End-to-end and integration test suites
└── docs/             # Architecture, design specs, and documentation
```

---

## Python Virtual Environment

### 1. Create Virtual Environment
To create a virtual environment named `gridguard` (same name as the project folder):

```bash
# Windows / Linux / macOS
python -m venv gridguard
```

### 2. Activate Virtual Environment

Choose the command matching your shell/OS:

- **Windows (PowerShell):**
  ```powershell
  .\gridguard\Scripts\Activate.ps1
  ```
  *(If execution policies block the script in PowerShell, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`)*

- **Windows (Command Prompt - CMD):**
  ```cmd
  .\gridguard\Scripts\activate.bat
  ```

- **Linux / macOS (Bash / Zsh):**
  ```bash
  source gridguard/bin/activate
  ```

- **Git Bash (Windows):**
  ```bash
  source gridguard/Scripts/activate
  ```

### 3. Deactivate Environment
When finished working:

```bash
deactivate
```
