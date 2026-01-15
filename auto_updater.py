"""
VetRender Auto-Updater
=======================
Checks GitHub for new versions and updates the application automatically.
"""

import os
import sys
import json
import requests
import subprocess
import tempfile
import shutil
from pathlib import Path
from packaging import version as pkg_version

# Current version (update this with each release!)
CURRENT_VERSION = "3.0.1"

# GitHub repository info
GITHUB_USER = "YOUR_USERNAME"  # Update this!
GITHUB_REPO = "VetRender"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}"


class AutoUpdater:
    """Handles automatic updates from GitHub"""
    
    def __init__(self, silent=False):
        """Initialize updater
        
        Args:
            silent: If True, don't show any UI dialogs
        """
        self.silent = silent
        self.update_available = False
        self.latest_version = None
        self.download_url = None
        
    def check_for_updates(self):
        """Check if a new version is available on GitHub
        
        Returns:
            tuple: (update_available, latest_version, download_url)
        """
        try:
            # Get latest release from GitHub
            response = requests.get(f"{GITHUB_API}/releases/latest", timeout=5)
            
            if response.status_code != 200:
                print(f"Update check failed: HTTP {response.status_code}")
                return False, None, None
            
            release_data = response.json()
            
            # Parse version
            latest_version = release_data['tag_name'].lstrip('v')
            
            # Compare versions
            if pkg_version.parse(latest_version) > pkg_version.parse(CURRENT_VERSION):
                self.update_available = True
                self.latest_version = latest_version
                
                # Find the MSI installer asset
                for asset in release_data.get('assets', []):
                    if asset['name'].endswith('.msi'):
                        self.download_url = asset['browser_download_url']
                        break
                
                print(f"Update available: {CURRENT_VERSION} → {latest_version}")
                return True, latest_version, self.download_url
            else:
                print(f"You're up to date! (v{CURRENT_VERSION})")
                return False, None, None
                
        except requests.RequestException as e:
            print(f"Update check failed: {e}")
            return False, None, None
        except Exception as e:
            print(f"Error checking for updates: {e}")
            return False, None, None
    
    def download_update(self, url, dest_path):
        """Download update file
        
        Args:
            url: URL to download from
            dest_path: Where to save the file
            
        Returns:
            bool: True if successful
        """
        try:
            print(f"Downloading update from {url}...")
            
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(dest_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Show progress
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"  Progress: {percent:.1f}%", end='\\r')
            
            print(f"\\nDownload complete: {dest_path}")
            return True
            
        except Exception as e:
            print(f"Download failed: {e}")
            return False
    
    def install_update(self, msi_path):
        """Install the downloaded MSI update
        
        Args:
            msi_path: Path to the downloaded MSI file
            
        Returns:
            bool: True if installation started successfully
        """
        try:
            print(f"Installing update from {msi_path}...")
            
            # Run MSI installer
            # /i = install, /qb = basic UI with progress bar
            subprocess.Popen([
                'msiexec', '/i', msi_path, '/qb'
            ])
            
            print("Installer launched!")
            print("VetRender will close now. The update will complete shortly.")
            
            return True
            
        except Exception as e:
            print(f"Failed to launch installer: {e}")
            return False
    
    def perform_update(self):
        """Check, download, and install update
        
        Returns:
            bool: True if update was installed
        """
        # Check for updates
        update_available, latest_version, download_url = self.check_for_updates()
        
        if not update_available:
            return False
        
        if not download_url:
            print("Update available but no installer found!")
            return False
        
        # Ask user if they want to update (unless silent mode)
        if not self.silent:
            try:
                import tkinter as tk
                from tkinter import messagebox
                
                root = tk.Tk()
                root.withdraw()
                
                response = messagebox.askyesno(
                    "Update Available",
                    f"VetRender {latest_version} is available!\\n\\n"
                    f"Current version: {CURRENT_VERSION}\\n"
                    f"Latest version: {latest_version}\\n\\n"
                    f"Would you like to download and install the update?"
                )
                
                root.destroy()
                
                if not response:
                    print("User declined update")
                    return False
                    
            except:
                # If GUI fails, ask in console
                response = input(f"Update to {latest_version}? (Y/N): ")
                if response.upper() != 'Y':
                    return False
        
        # Download update
        temp_dir = tempfile.gettempdir()
        msi_filename = f"VetRender_{latest_version}.msi"
        msi_path = os.path.join(temp_dir, msi_filename)
        
        if not self.download_update(download_url, msi_path):
            return False
        
        # Install update
        if self.install_update(msi_path):
            # Exit current application
            sys.exit(0)
        
        return False


def check_for_updates_at_startup():
    """Check for updates when the application starts
    
    This is called from vetrender.py on startup.
    """
    try:
        updater = AutoUpdater(silent=False)
        updater.perform_update()
    except Exception as e:
        print(f"Update check failed: {e}")


def get_current_version():
    """Get the current version string"""
    return CURRENT_VERSION


if __name__ == "__main__":
    # Test the updater
    updater = AutoUpdater(silent=False)
    updater.perform_update()
