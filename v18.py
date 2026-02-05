import sys
import ctypes
import psutil
import platform
import datetime
import subprocess
import winreg
import wmi
import socket
import speedtest
import requests
import time
import struct
import argparse
import os
import json
from rich import box
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Confirm, Prompt

# ==========================================
# 1. SETUP & ARGS
# ==========================================
def parse_arguments():
    parser = argparse.ArgumentParser(description="IT Diagnostic Master Tool v18.0")
    parser.add_argument("--all", action="store_true", help="Run ALL checks")
    parser.add_argument("--auto", action="store_true", help="Skip menu, run all")
    parser.add_argument("--quick", action="store_true", help="Skip Speedtest")
    return parser.parse_args()

def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

if not is_admin():
    args_str = " ".join(sys.argv[1:])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{sys.argv[0]}" {args_str}', None, 1)
    sys.exit()

try: c_wmi = wmi.WMI()
except: c_wmi = None

console = Console()

class IT_Diagnostic_v18:
    def __init__(self, args):
        self.args = args
        self.issues_found = [] 
        self.hostname = platform.node()
        self.specs = {} 
        self.stats = {"PASS": 0, "FAIL": 0, "WARNING": 0, "INFO": 0}
        
        self.modules = {
            "identity": False, "hardware": False, "software": False, 
            "security": False, "network": False, "performance": False
        }

        if args.all or args.auto:
             for k in self.modules: self.modules[k] = True
        else:
            self.show_main_menu()

    def show_main_menu(self):
        console.clear()
        subtitle = "[spring_green1]Ultimate Edition[/]"
        console.print(Panel(Align.center(f"[bold white]IT DIAGNOSTIC MASTER (v18.0)[/]\n{subtitle}"), 
                            border_style="spring_green1", box=box.ROUNDED, padding=(1, 4), expand=True))
        
        console.print("\n[bold cyan]Select Diagnostics:[/bold cyan]")
        console.print("1. [bold white]Run Everything[/] (Full Audit)")
        console.print("2. [bold white]Identity & Context[/] (Serial, OS, Uptime)")
        console.print("3. [bold white]Hardware Deep Dive[/] (Drivers, SMART, Ram Speed)")
        console.print("4. [bold white]Network Stack[/] (Gateway, Ports, Speed)")
        console.print("5. [bold white]Security Audit[/] (AV, TPM, UAC, Admin)")
        console.print("6. [bold white]Software Health[/] (Updates, Startup, Temp)")
        console.print("7. [bold white]Performance[/] (Hogs, BSOD, Power Plan)")
        console.print("0. Exit")
        
        choice = Prompt.ask("\n[bold yellow]Enter Choice[/]", choices=["0", "1", "2", "3", "4", "5", "6", "7"], default="1")
        
        if choice == "0": sys.exit()
        if choice == "1": 
            for k in self.modules: self.modules[k] = True
        elif choice == "2": self.modules["identity"] = True
        elif choice == "3": self.modules["hardware"] = True
        elif choice == "4": self.modules["network"] = True
        elif choice == "5": self.modules["security"] = True
        elif choice == "6": self.modules["software"] = True
        elif choice == "7": self.modules["performance"] = True
        
        console.clear()

    def log(self, category, message, status="INFO", detail=None, action_item=None):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        if status == "PASS": icon="[green]✔[/]"; style="green"; self.stats["PASS"]+=1
        elif status == "FAIL": icon="[red]✖[/]"; style="bold red"; self.stats["FAIL"]+=1
        elif status == "WARNING": icon="[yellow]![/]"; style="yellow"; self.stats["WARNING"]+=1
        else: icon="[blue]i[/]"; style="cyan"; self.stats["INFO"]+=1

        console.print(f"{timestamp} | {icon} | [bold white]{category:18}[/bold white] | [{style}]{message}[/{style}]")
        if detail: console.print(f"             [dim]↳ {detail}[/dim]")

        if status == "INFO":
            if category in self.specs: self.specs[category] += f", {message}"
            else: self.specs[category] = message

        if status in ["FAIL", "WARNING"]:
            if not action_item: action_item = "Investigate manually."
            self.issues_found.append({"category": category, "error": message, "detail": detail if detail else "", "fix": action_item})

    def section(self, title):
        console.print(f"\n[bold magenta italic]--- {title} ---[/bold magenta italic]")

    # ==========================
    # MODULE 1: IDENTITY
    # ==========================
    def check_identity(self):
        self.section("IDENTITY & CONTEXT")
        try:
            os_name = f"{platform.system()} {platform.release()}"
            build = platform.version()
            if c_wmi:
                for os_data in c_wmi.Win32_OperatingSystem():
                    os_name = os_data.Caption
                    build = os_data.BuildNumber
            self.log("OS Version", f"{os_name} (Build {build})", "INFO")
        except: pass

        if c_wmi:
            try:
                for sys in c_wmi.Win32_ComputerSystem():
                    self.log("Model", f"{sys.Manufacturer} {sys.Model}", "INFO")
                for bios in c_wmi.Win32_BIOS():
                    self.log("Serial Number", bios.SerialNumber, "INFO")
            except: pass

        uptime_s = time.time() - psutil.boot_time()
        days = uptime_s // (24 * 3600)
        self.log("Uptime", f"{int(days)} Days", "WARNING" if days > 7 else "PASS", 
                 action_item="Reboot recommended." if days > 7 else None)

    # ==========================
    # MODULE 2: HARDWARE (Restored RAM Speed, SMART, Printers)
    # ==========================
    def check_hardware(self):
        self.section("HARDWARE DIAGNOSTICS")
        
        # CPU
        if c_wmi:
            try:
                for cpu in c_wmi.Win32_Processor(): 
                    self.log("CPU Model", cpu.Name.strip(), "INFO")
                    self.log("CPU Cores", f"{cpu.NumberOfCores}C / {cpu.NumberOfLogicalProcessors}T", "INFO")
            except: pass

        # GPU
        if c_wmi:
            try:
                for gpu in c_wmi.Win32_VideoController():
                    vram = "Unknown"
                    try: vram = f"{int(gpu.AdapterRAM) / (1024**3):.2f} GB"
                    except: pass
                    self.log("GPU Info", f"{gpu.Name} ({vram})", "INFO")
            except: pass

        # RAM (RESTORED DETAILS)
        if c_wmi:
            try:
                total_cap = 0
                for mem in c_wmi.Win32_PhysicalMemory():
                    cap = int(mem.Capacity) / (1024**3)
                    total_cap += cap
                    speed = mem.Speed if hasattr(mem, 'Speed') else "?"
                    maker = mem.Manufacturer if hasattr(mem, 'Manufacturer') else ""
                    self.log("RAM Stick", f"{cap:.0f}GB @ {speed}MHz {maker}", "INFO")
                
                mem_stats = psutil.virtual_memory()
                status = "FAIL" if mem_stats.percent > 90 else "PASS"
                self.log("RAM Usage", f"{mem_stats.percent}% Used (of {total_cap:.0f}GB)", status)
            except: pass

        # Battery
        if c_wmi:
            try:
                for b in c_wmi.Win32_Battery():
                    status = "Plugged In" if b.BatteryStatus == 2 else "On Battery"
                    self.log("Battery", f"{b.EstimatedChargeRemaining}% ({status})", "INFO")
            except: pass

        # Device Drivers (The "Drive Manager" Check)
        if c_wmi:
            try:
                errors = c_wmi.query("SELECT * FROM Win32_PnPEntity WHERE ConfigManagerErrorCode != 0")
                if errors:
                    for dev in errors:
                        self.log("Driver Error", dev.Caption, "FAIL", f"Code: {dev.ConfigManagerErrorCode}", 
                                 action_item=f"Reinstall driver for {dev.Caption}")
                else:
                    self.log("Drivers", "No Yellow Bangs", "PASS")
            except: pass

        # Storage (Type)
        try:
            cmd = "Get-PhysicalDisk | Select-Object MediaType"
            out = subprocess.check_output(["powershell", "-Command", cmd], stderr=subprocess.DEVNULL).decode()
            if "HDD" in out: self.log("Drive Type", "HDD Detected", "WARNING", action_item="Upgrade to SSD.")
            elif "SSD" in out: self.log("Drive Type", "SSD Detected", "PASS")
        except: pass

        # Storage (SMART RESTORED)
        if c_wmi:
            try:
                for d in c_wmi.Win32_DiskDrive():
                    if d.Status != "OK":
                        self.log("SMART Status", d.Caption, "FAIL", d.Status, action_item="REPLACE DRIVE.")
                    else:
                        self.log("SMART Status", "Healthy", "PASS")
            except: pass

        # Storage (Bad Sectors Event 7)
        try:
            ps_cmd = "Get-WinEvent -LogName System -MaxEvents 200 -ErrorAction SilentlyContinue | Where-Object { $_.Id -eq 7 } | Select-Object -First 1"
            out = subprocess.check_output(["powershell", "-Command", ps_cmd], stderr=subprocess.DEVNULL).decode().strip()
            if out: self.log("Bad Sectors", "CONFIRMED", "FAIL", "Event 7 found", action_item="REPLACE DRIVE.")
            else: self.log("Bad Sectors", "Clean", "PASS")
        except: pass

        # Printers (RESTORED)
        if c_wmi:
            try:
                for p in c_wmi.Win32_Printer():
                    if p.Status and p.Status != "OK" and p.Status != "Unknown":
                        self.log("Printer", p.Name, "WARNING", f"Status: {p.Status}")
            except: pass

    # ==========================
    # MODULE 3: NETWORK
    # ==========================
    def check_network(self):
        self.section("NETWORK & CONNECTIVITY")
        
        if c_wmi:
            try:
                for adapter in c_wmi.Win32_NetworkAdapterConfiguration(IPEnabled=True):
                    desc = adapter.Description
                    ip_address = adapter.IPAddress[0] if adapter.IPAddress else "No IP"
                    gateway = adapter.DefaultIPGateway[0] if adapter.DefaultIPGateway else "No Gateway"
                    if "No IP" not in ip_address:
                        self.log("Interface", desc[:30], "INFO")
                        self.log(" > IP", ip_address, "INFO")
                        self.log(" > Gateway", gateway, "INFO")
            except: pass

        try:
            socket.gethostbyname("google.com")
            self.log("DNS", "OK", "PASS")
        except: self.log("DNS", "Failed", "FAIL", action_item="Check DNS.")
        
        try:
            res = requests.get('http://ip-api.com/json', timeout=2).json()
            self.log("Public IP", f"{res.get('query')} ({res.get('isp')})", "INFO")
        except: self.log("Public IP", "Offline", "WARNING")

        try:
            connections = psutil.net_connections(kind='inet')
            listening = [c.laddr.port for c in connections if c.status == 'LISTEN']
            if 3389 in listening: self.log("Open Ports", "RDP (3389) Open", "WARNING", action_item="Secure RDP.")
        except: pass
        
        # if not self.args.quick:
        #     if Confirm.ask("Run Speedtest?", default=False):
        #         try:
        #             self.log("Speedtest", "Testing...", "INFO")
        #             st = speedtest.Speedtest()
        #             st.get_best_server()
        #             down = st.download()/1e6
        #             if down < 10: self.log("Download", f"{down:.1f} Mbps", "WARNING", action_item="Slow Internet.")
        #             else: self.log("Download", f"{down:.1f} Mbps", "PASS")
        #         except: self.log("Speedtest", "Failed", "WARNING")

    # ==========================
    # MODULE 4: SECURITY (Restored AV, TPM, UAC)
    # ==========================
    def check_security(self):
        self.section("SECURITY & COMPLIANCE")
        
        # Antivirus (RESTORED)
        try:
            wmi_sec = wmi.WMI(namespace=r"root\SecurityCenter2")
            av = wmi_sec.AntivirusProduct()
            if av: self.log("Antivirus", "Active", "PASS")
            else: self.log("Antivirus", "Missing", "FAIL", action_item="Install AV.")
        except: pass

        # TPM (RESTORED)
        if c_wmi:
            try:
                tpm = c_wmi.Win32_Tpm()
                if tpm: self.log("TPM Chip", "Present", "PASS")
                else: self.log("TPM Chip", "Not Detected", "WARNING")
            except: pass

        # UAC (RESTORED)
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System")
            val, _ = winreg.QueryValueEx(key, "EnableLUA")
            if val == 1: self.log("UAC", "Enabled", "PASS")
            else: self.log("UAC", "Disabled", "FAIL", action_item="Enable UAC.")
        except: pass

        # BitLocker
        try:
            ps_cmd = "Get-BitLockerVolume -MountPoint C: | Select-Object -ExpandProperty ProtectionStatus"
            out = subprocess.check_output(["powershell", "-Command", ps_cmd], stderr=subprocess.DEVNULL).decode().strip()
            if "1" in out: self.log("BitLocker", "Encrypted", "PASS")
            else: self.log("BitLocker", "Unencrypted", "WARNING", action_item="Enable BitLocker.")
        except: pass
        
        # Firewall
        try:
            out = subprocess.check_output("netsh advfirewall show allprofiles state", shell=True).decode()
            if "OFF" in out: self.log("Firewall", "Disabled", "FAIL", action_item="Enable Firewall.")
            else: self.log("Firewall", "Enabled", "PASS")
        except: pass

        # Local Admin
        try:
            out = subprocess.check_output("net localgroup administrators", shell=True).decode()
            lines = [x.strip() for x in out.splitlines() if x.strip() and "User" not in x and "command" not in x and "-" not in x]
            suspicious = [u for u in lines if u.lower() not in ['administrator', 'domain admins', self.hostname.lower()]]
            if len(suspicious) > 0: self.log("Local Admins", f"Check: {', '.join(suspicious)}", "WARNING")
            else: self.log("Local Admins", "Clean", "PASS")
        except: pass

        # Domain
        if c_wmi:
            try:
                sys_info = c_wmi.Win32_ComputerSystem()[0]
                if sys_info.PartOfDomain:
                    self.log("Domain", f"Joined: {sys_info.Domain}", "PASS")
                    try:
                        cmd = f"nltest /sc_query:{sys_info.Domain}"
                        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode()
                        if "Success" in out: self.log("Trust Status", "OK", "PASS")
                        else: self.log("Trust Status", "Broken", "FAIL", action_item="Rejoin Domain.")
                    except: pass
                else: self.log("Domain", "Workgroup", "INFO")
            except: pass

    # ==========================
    # MODULE 5: SOFTWARE (Restored Update Failures)
    # ==========================
    def check_software(self):
        self.section("SOFTWARE & OS")
        
        try:
            cmd = r"cscript //nologo %windir%\system32\slmgr.vbs /xpr"
            out = subprocess.check_output(cmd, shell=True).decode()
            if "permanently" in out.lower() or "volume" in out.lower(): self.log("Activation", "Licensed", "PASS")
            else: self.log("Activation", "Not Activated", "FAIL", action_item="Activate Windows License.")
        except: pass

        reboot = False
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending"): reboot = True
        except: pass
        if reboot: self.log("Updates", "Reboot Pending", "FAIL", action_item="Restart PC.")
        else: self.log("Updates", "Clean", "PASS")

        # Windows Update History (RESTORED)
        try:
            ps_cmd = "Get-WinEvent -ProviderName 'Microsoft-Windows-WindowsUpdateClient' -MaxEvents 20 -ErrorAction SilentlyContinue | Where-Object {$_.Id -eq 20} | Measure-Object | Select-Object -ExpandProperty Count"
            out = subprocess.check_output(["powershell", "-Command", ps_cmd], stderr=subprocess.DEVNULL).decode().strip()
            if out and int(out) > 0: self.log("Win Updates", f"{out} Recent Failures", "WARNING", action_item="Check Windows Update.")
            else: self.log("Win Updates", "No Recent Failures", "PASS")
        except: pass

        try:
            count = 0
            paths = [r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"]
            for p in paths:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, p)
                for i in range(winreg.QueryInfoKey(key)[0]): count += 1
            status = "WARNING" if count > 10 else "PASS"
            self.log("Startup Apps", f"{count} Apps", status, action_item="Disable unused startup apps.")
        except: pass

        try:
            temp_path = os.environ.get('TEMP')
            total_size = sum(os.path.getsize(os.path.join(dp, f)) for dp, dn, filenames in os.walk(temp_path) for f in filenames) / (1024*1024)
            if total_size > 1024: self.log("Temp Files", f"{total_size:.0f} MB Found", "WARNING", action_item="Run Disk Cleanup.")
            else: self.log("Temp Files", f"{total_size:.0f} MB (Clean)", "PASS")
        except: pass

    # ==========================
    # MODULE 6: PERFORMANCE (Restored Power Plan)
    # ==========================
    def check_performance(self):
        self.section("PERFORMANCE")
        cpu = psutil.cpu_percent(interval=1)
        self.log("CPU Load", f"{cpu}%", "PASS" if cpu < 90 else "FAIL")
        
        # Power Plan (RESTORED)
        try:
            out = subprocess.check_output("powercfg /getactivescheme", shell=True).decode()
            plan = out.split("(")[1].split(")")[0] if "(" in out else "Unknown"
            self.log("Power Plan", plan, "INFO")
        except: pass

        try:
            top = sorted([p.info for p in psutil.process_iter(['name', 'cpu_percent'])], key=lambda p: p['cpu_percent'], reverse=True)[0]
            self.log("Top Hog", f"{top['name']} ({top['cpu_percent']}%)", "INFO")
        except: pass

        try:
            dump_path = os.path.expandvars(r"%SystemRoot%\Minidump")
            if os.path.exists(dump_path) and len(os.listdir(dump_path)) > 0:
                self.log("BSOD History", "Crashes Detected", "WARNING", action_item="Check Minidumps folder.")
            else:
                self.log("BSOD History", "Clean", "PASS")
        except: pass

    # ==========================
    # REPORTING
    # ==========================
    def save_report(self):
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        filename = f"FIX_SHEET_{self.hostname}.txt"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write("IT REPAIR CHECKLIST & DIAGNOSTIC REPORT\n")
            f.write(f"Device: {self.hostname} | {date_str}\n")
            f.write("="*60 + "\n\n")
            
            if self.specs:
                f.write("DEVICE CONTEXT:\n")
                for k,v in self.specs.items(): f.write(f" - {k}: {v}\n")
                f.write("-" * 30 + "\n\n")
            
            if not self.issues_found:
                f.write("STATUS: GREEN (HEALTHY)\n")
                f.write("No actionable issues found. System is ready for use.\n")
            else:
                f.write(f"STATUS: RED ({len(self.issues_found)} ISSUES FOUND)\n")
                f.write("Please perform the following repairs:\n\n")
                
                for idx, issue in enumerate(self.issues_found, 1):
                    f.write(f"{idx}. [ ] ISSUE: {issue['category']} - {issue['error']}\n")
                    if issue['detail']: f.write(f"       DETAIL: {issue['detail']}\n")
                    f.write(f"       FIX:    {issue['fix']}\n")
                    f.write("-" * 60 + "\n")
            
            f.write("\nTechnician Signature: __________________________\n")
        return filename

    def run(self):
        if not any(self.modules.values()): return

        tasks = []
        if self.modules["identity"]: tasks.append(self.check_identity)
        if self.modules["hardware"]: tasks.append(self.check_hardware)
        if self.modules["network"]: tasks.append(self.check_network)
        if self.modules["security"]: tasks.append(self.check_security)
        if self.modules["software"]: tasks.append(self.check_software)
        if self.modules["performance"]: tasks.append(self.check_performance)

        console.print(Panel(Align.center("[bold white]Running Diagnostics...[/]"), border_style="cyan", expand=True))
        
        with Progress(SpinnerColumn(), TextColumn("[bold cyan]{task.description}"), BarColumn(), console=console) as progress:
            t1 = progress.add_task("Scanning...", total=len(tasks))
            for task in tasks:
                task()
                progress.advance(t1)

        console.print("\n")
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="center", ratio=1)
        grid.add_row(
            f"[bold green]PASS: {self.stats['PASS']}[/]",
            f"[bold yellow]WARN: {self.stats['WARNING']}[/]",
            f"[bold red]FAIL: {self.stats['FAIL']}[/]"
        )
        console.print(Panel(grid, border_style="grey50"))

        if self.issues_found:
            table = Table(title="ISSUES DETECTED", show_header=True, header_style="bold red", expand=True)
            table.add_column("Category", style="cyan")
            table.add_column("Error", style="white")
            table.add_column("Recommended Fix", style="yellow")
            for i in self.issues_found:
                table.add_row(i['category'], i['error'], i['fix'])
            console.print(table)
        else:
            console.print(Panel("[bold green]System Healthy - No Issues Found[/]", border_style="green"))

        f = self.save_report()
        console.print(f"\n[bold green]Report Saved:[/bold green] {f}")

if __name__ == "__main__":
    arguments = parse_arguments()
    tool = IT_Diagnostic_v18(arguments)
    tool.run()