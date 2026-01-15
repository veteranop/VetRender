# Ollama AI Antenna Assistant Installer
# Downloads, installs Ollama, and pulls the required model

Write-Host "Starting Ollama installation for VetRender AI Antenna Assistant..."
Write-Host "This may take a few minutes. Please wait..."

# Download Ollama installer
$installerUrl = "https://github.com/ollama/ollama/releases/latest/download/OllamaSetup.exe"
$installerPath = "$env:TEMP\OllamaSetup.exe"

Write-Host "Downloading Ollama installer (~50MB)..."
try {
    Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -ErrorAction Stop
    Write-Host "Download complete!"
} catch {
    Write-Error "Failed to download Ollama installer: $_"
    exit 1
}

# Install Ollama silently
Write-Host "Installing Ollama..."
try {
    Start-Process -FilePath $installerPath -ArgumentList "/S" -Wait -ErrorAction Stop
    Write-Host "Ollama installed successfully!"
} catch {
    Write-Error "Failed to install Ollama: $_"
    exit 1
}

# Clean up installer
Remove-Item $installerPath -ErrorAction SilentlyContinue

# Wait for installation to settle
Write-Host "Waiting for installation to complete..."
Start-Sleep -Seconds 3

# Find Ollama executable (installer adds it to PATH, but we need the full path for this session)
$ollamaPath = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"

# Check if Ollama was installed
if (-not (Test-Path $ollamaPath)) {
    Write-Error "Ollama executable not found at expected location: $ollamaPath"
    Write-Host "Installation may have failed or Ollama is in a different location."
    exit 1
}

Write-Host "Found Ollama at: $ollamaPath"

# Start Ollama server in background (it will stay running)
Write-Host "Starting Ollama server..."
try {
    Start-Process -FilePath $ollamaPath -ArgumentList "serve" -WindowStyle Hidden -ErrorAction Stop
    Write-Host "Ollama server started in background."
    # Give server time to start
    Start-Sleep -Seconds 5
} catch {
    Write-Warning "Could not start Ollama server automatically: $_"
    Write-Host "Server will start when you use the AI feature."
}

# Pull the model using full path
Write-Host "Downloading AI model (llama3.2:1b) - this is about 1GB..."
Write-Host "This will take several minutes depending on your internet speed."
try {
    $pullProcess = Start-Process -FilePath $ollamaPath -ArgumentList "pull", "llama3.2:1b" -Wait -NoNewWindow -PassThru -ErrorAction Stop
    if ($pullProcess.ExitCode -eq 0) {
        Write-Host "Model downloaded successfully!"
    } else {
        Write-Warning "Model pull may have failed (exit code: $($pullProcess.ExitCode))"
        Write-Host "You can manually run: ollama pull llama3.2:1b"
    }
} catch {
    Write-Warning "Failed to pull model: $_"
    Write-Host "You can manually run 'ollama pull llama3.2:1b' after installation."
}

Write-Host ""
Write-Host "==============================================="
Write-Host "Ollama setup complete!"
Write-Host "==============================================="
Write-Host "The Ollama server is now running in the background."
Write-Host ""
Write-Host "IMPORTANT: Restart your computer to complete the installation."
Write-Host "After restart, the AI Antenna Import feature will be ready to use."
Write-Host "==============================================="

exit 0
