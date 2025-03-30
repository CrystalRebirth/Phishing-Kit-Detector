import asyncio
import yaml
import sys
import threading
import os
import winreg
from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog
from PyQt5.QtCore import Qt
from phish_annihilator.annihilator import PhishingAnnihilator
from phish_annihilator.ui.main_window import MainWindow
from phish_annihilator.ui.config_window import ConfigWindow
import pystray
from PIL import Image

class App:
    def __init__(self, config):
        self.config = config
        self.app = QApplication(sys.argv)
        self.main_window = MainWindow()
        self.annihilator = PhishingAnnihilator(config)
        
        # Connect signals
        self.annihilator.alert_callback = lambda domain, score, reasons: (
            self.main_window.alert_received.emit(
                f"Phishing detected!\nDomain: {domain}\nScore: {score:.1f}\nReason: {reasons[0]}"
            )
        )
        self.main_window.config_requested.connect(self.show_config)
        self.main_window.auto_start.stateChanged.connect(self.toggle_autostart)
        self.main_window.hide_console.clicked.connect(self.toggle_console)
        
        # Track console state
        self.console_visible = True
        
        # Check current autostart state
        self.check_autostart_state()
        
    def verify_startup_entry(self):
        """Verify the startup entry exists and is correct"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_READ
            )
            value, _ = winreg.QueryValueEx(key, "Phishing Annihilator")
            exe_path = os.path.abspath(sys.executable)
            script_path = os.path.abspath(__file__)
            expected = f'"{exe_path}" "{script_path}"'
            return value == expected
        except Exception:
            return False

    def check_autostart_state(self):
        """Check if app is set to auto-start"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_READ
            )
            try:
                winreg.QueryValueEx(key, "Phishing Annihilator")
                self.main_window.auto_start.setChecked(True)
            except FileNotFoundError:
                self.main_window.auto_start.setChecked(False)
            finally:
                key.Close()
        except Exception:
            self.main_window.auto_start.setChecked(False)
        
    def toggle_autostart(self, state):
        """Enable/disable auto-start on boot"""
        try:
            # Request admin permissions if needed
            if state == Qt.Checked:
                import ctypes
                if not ctypes.windll.shell32.IsUserAnAdmin():
                    # Request admin elevation
                    ctypes.windll.shell32.ShellExecuteW(
                        None, "runas", sys.executable, __file__, None, 1
                    )
                    self.main_window.auto_start.setChecked(False)
                    return

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            if state == Qt.Checked:
                exe_path = os.path.abspath(sys.executable)
                script_path = os.path.abspath(__file__)
                # Create proper startup entry that appears in Task Manager
                winreg.SetValueEx(
                    key, "Phishing Annihilator", 0, winreg.REG_SZ,
                    f'"{exe_path}" "{script_path}"'
                )
                # Also set the friendly name in Local Machine if admin
                try:
                    lm_key = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r"Software\Microsoft\Windows\CurrentVersion\Run",
                        0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY
                    )
                    winreg.SetValueEx(
                        lm_key, "Phishing Annihilator", 0, winreg.REG_SZ,
                        f'"{exe_path}" "{script_path}"'
                    )
                    lm_key.Close()
                except PermissionError:
                    pass  # Not running as admin, skip HKLM
            else:
                # Clean up all possible registry entries
                entries = ["PhishingAnnihilator", "Phishing Annihilator"]
                for entry in entries:
                    try:
                        winreg.DeleteValue(key, entry)
                    except FileNotFoundError:
                        pass
                
                # Clean up HKLM if admin
                try:
                    lm_key = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r"Software\Microsoft\Windows\CurrentVersion\Run",
                        0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY
                    )
                    for entry in entries:
                        try:
                            winreg.DeleteValue(lm_key, entry)
                        except FileNotFoundError:
                            pass
                    lm_key.Close()
                except PermissionError:
                    pass
            key.Close()
        except Exception as e:
            QMessageBox.warning(
                self.main_window,
                "Auto-Start Error",
                f"Failed to set auto-start: {str(e)}"
            )
            self.main_window.auto_start.setChecked(False)
    
    def show_config(self):
        """Show configuration window"""
        config_window = ConfigWindow(self.config, self.main_window)
        if config_window.exec_() == QDialog.Accepted:
            # Update config with new values
            self.config['phishtank_api_key'] = config_window.phishtank_key.text()
            self.config['virustotal_api_key'] = config_window.virustotal_key.text()
            self.config['network']['enable_network_monitoring'] = config_window.network_monitoring.isChecked()
            self.config['thresholds']['homoglyph'] = float(config_window.homoglyph_threshold.text())
            
            # Save to file
            with open('config.yaml', 'w') as f:
                yaml.dump(self.config, f)
            
            # Restart annihilator with new config
            self.annihilator = PhishingAnnihilator(self.config)
            self.annihilator.alert_callback = self.handle_alert
            
    def handle_alert(self, domain, score, reasons):
        """Forward alerts to UI and notifications"""
        message = f"Phishing detected!\nDomain: {domain}\nScore: {score:.1f}\nReason: {reasons[0]}"
        self.main_window.alert_received.emit(message)
        # Also show system notification
        try:
            import win10toast
            toast = win10toast.ToastNotifier()
            toast.show_toast("Phishing Alert", message, duration=10)
        except ImportError:
            pass
        
    def create_tray_icon(self):
        """Create system tray icon with menu"""
        image = Image.new('RGB', (64, 64), 'black')
        menu = pystray.Menu(
            pystray.MenuItem('Show Window', self.main_window.show),
            pystray.MenuItem('Configuration', self.show_config),
            pystray.MenuItem('Exit', self.exit_app)
        )
        return pystray.Icon("phish_annihilator", image, "Phishing Annihilator", menu)

    def toggle_console(self):
        """Toggle console window visibility"""
        import ctypes
        console_window = ctypes.windll.kernel32.GetConsoleWindow()
        if console_window:
            if self.console_visible:
                ctypes.windll.user32.ShowWindow(console_window, 0)  # SW_HIDE
                self.main_window.hide_console.setText("🖥️ Show Console")
            else:
                ctypes.windll.user32.ShowWindow(console_window, 5)  # SW_SHOW
                self.main_window.hide_console.setText("🖥️ Hide Console")
            self.console_visible = not self.console_visible

    def exit_app(self):
        """Cleanup and exit"""
        if self.annihilator.traffic_analyzer:
            self.annihilator.traffic_analyzer.stop_capture()
        self.app.quit()

    async def run(self):
        """Start the application"""
        # Start annihilator in background thread
        thread = threading.Thread(
            target=lambda: asyncio.run(self.annihilator.run()),
            daemon=True
        )
        thread.start()
        
        # Setup tray icon
        tray_icon = self.create_tray_icon()
        threading.Thread(
            target=tray_icon.run,
            daemon=True
        ).start()
        
        # Show main window and start Qt event loop
        self.main_window.show()
        sys.exit(self.app.exec_())

if __name__ == '__main__':
    with open('config.yaml') as f:
        config = yaml.safe_load(f)
    
    app = App(config)
    asyncio.run(app.run())
