# 1. Which Python the venv uses, and the OS
& ".\.venv\Scripts\python.exe" -c "import sys, platform; print(sys.version); print(platform.platform()); print(sys.executable)"

# 2. RAM in GB
[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)

# 3. Free disk space on C: in GB
[math]::Round((Get-PSDrive C).Free / 1GB, 1)

# 4. Graphics adapter(s)
Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion

# 5. NVIDIA details. It's fine if this fails with "not recognized".
nvidia-smi