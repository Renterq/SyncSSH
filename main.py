import os
import json
import asyncio
import threading
import datetime
from typing import TYPE_CHECKING
import customtkinter as ctk
import paramiko
import tkcalendar

if TYPE_CHECKING:
    pass

# --- GÖRÜNÜM AYARLARI ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

TERMINAL_THEMES = {
    "Beyaz (Arka Plan Beyaz/Yazı Siyah)": {"fg_color": "#ffffff", "text_color": "#000000"},
    "Karanlık (Siyah/Beyaz)": {"fg_color": "#000000", "text_color": "#ffffff"},
    "Hacker (Siyah/Yeşil)": {"fg_color": "#000000", "text_color": "#00ff00"},
    "Okyanus (Mavi/Beyaz)": {"fg_color": "#1e2a3a", "text_color": "#e0f7fa"}
}

# --- YÖNETİCİ SINIFLARI ---
class SettingsManager:
    def __init__(self, filename: str = "settings.json") -> None:
        self.filename = filename
        self.settings = {"notify_days": 3, "app_theme": "System"}
        self.load()

    def load(self) -> None:
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.settings.update(data)
            except (OSError, json.JSONDecodeError) as e:
                print(f"Settings load error: {e}")

    def save(self) -> None:
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4)
        except OSError as e:
            print(f"Settings save error: {e}")


class ServerManager:
    def __init__(self, filename: str = "servers.json") -> None:
        self.filename = filename
        self.servers = []
        self.load()

    def load(self) -> None:
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    self.servers = json.load(f)
                    
                    needs_save = False
                    for i, s in enumerate(self.servers):
                        if "id" not in s:
                            s["id"] = f"legacy_{i}_{datetime.datetime.now().timestamp()}"
                            needs_save = True
                    if needs_save:
                        self.save()
            except (OSError, json.JSONDecodeError) as e:
                print(f"Servers load error: {e}")
                self.servers = []

    def save(self) -> None:
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.servers, f, indent=4)
        except OSError as e:
            print(f"Servers save error: {e}")
            
    def add_server(self, server_data: dict) -> None:
        if "id" not in server_data:
            server_data["id"] = str(datetime.datetime.now().timestamp())
        self.servers.append(server_data)
        self.save()

    def update_server(self, server_id: str, new_data: dict) -> None:
        for i, srv in enumerate(self.servers):
            if str(srv.get("id")) == str(server_id):
                self.servers[i].update(new_data)
                break
        self.save()

    def delete_server(self, server_id: str) -> None:
        self.servers = [s for s in self.servers if str(s.get("id")) != str(server_id)]
        self.save()


def run_ssh_command_sync(server: dict, cmd: str) -> str:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            str(server.get("ip", "")), 
            port=int(server.get("port", 22)), 
            username=str(server.get("username", "root")), 
            password=str(server.get("password", "")), 
            timeout=5
        )
        _, stdout, stderr = client.exec_command(cmd)
        output = stdout.read().decode('utf-8')
        err = stderr.read().decode('utf-8')
        client.close()
        res = output
        if err:
            res += "\nHata:\n" + err
        return res if res.strip() else "Komut çalıştı (çıktı yok)."
    except paramiko.SSHException as e:
        return f"SSH Hatası: {str(e)}"
    except OSError as e:
        return f"Bağlantı Hatası: {str(e)}"


# --- ANA UYGULAMA ---
class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title("SSH VDS Manager")
        self.geometry("1100x700")
        self.minsize(900, 600)

        self.server_manager = ServerManager()
        self.settings_manager = SettingsManager()
        
        ctk.set_appearance_mode(str(self.settings_manager.settings.get("app_theme", "System")))

        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.start_asyncio_loop, args=(self.loop,), daemon=True)
        self.thread.start()

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="VDS Manager", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text="Dashboard", command=self.show_dashboard)
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10)

        self.btn_bulk = ctk.CTkButton(self.sidebar_frame, text="Toplu Komut", command=self.show_bulk_ssh)
        self.btn_bulk.grid(row=2, column=0, padx=20, pady=10)

        self.btn_single = ctk.CTkButton(self.sidebar_frame, text="Tekli Kontrol", command=self.show_single_ssh)
        self.btn_single.grid(row=3, column=0, padx=20, pady=10)

        self.btn_manage = ctk.CTkButton(self.sidebar_frame, text="Sunucu Yönetimi", command=self.show_management)
        self.btn_manage.grid(row=4, column=0, padx=20, pady=10)

        self.btn_settings = ctk.CTkButton(self.sidebar_frame, text="Ayarlar", command=self.show_settings)
        self.btn_settings.grid(row=5, column=0, padx=20, pady=10)

        self.top_bar = ctk.CTkFrame(self, height=40, corner_radius=0, fg_color="transparent")
        self.top_bar.grid(row=0, column=1, sticky="ew", padx=20, pady=(10, 0))
        
        self.notification_btn = ctk.CTkButton(self.top_bar, text="🔔 Bildirimler (0)", fg_color="transparent", text_color=("black", "white"), border_width=1, command=self.show_notifications_dialog)
        self.notification_btn.pack(side="right")
        self.current_alerts = []

        self.frames = {
            "dashboard": DashboardFrame(self),
            "bulk": BulkSSHFrame(self),
            "single": SingleSSHFrame(self),
            "manage": ManagementFrame(self),
            "settings": SettingsFrame(self)
        }

        for frame in self.frames.values():
            frame.grid(row=1, column=1, sticky="nsew", padx=20, pady=10)

        self.show_dashboard()
        self.check_notifications()

    def check_notifications(self) -> None:
        today = datetime.date.today()
        notify_days = int(self.settings_manager.settings.get("notify_days", 3))
        alerts = []
        
        for srv in self.server_manager.servers:
            exp_date_str = str(srv.get("expiration_date", ""))
            if exp_date_str:
                try:
                    exp_date = datetime.datetime.strptime(exp_date_str, "%Y-%m-%d").date()
                    diff = (exp_date - today).days
                    if 0 <= diff <= notify_days:
                        alerts.append(f"⚠️ {srv.get('name', 'Bilinmeyen')}: Süresi dolmasına {diff} gün kaldı! ({exp_date_str})")
                    elif diff < 0:
                        alerts.append(f"❌ {srv.get('name', 'Bilinmeyen')}: Süresi DOLDU! ({-diff} gün geçti)")
                except ValueError:
                    pass
        
        self.current_alerts = alerts
        if alerts:
            self.notification_btn.configure(text=f"🔔 Bildirimler ({len(alerts)})", fg_color="#8B0000", text_color="white", border_width=0)
        else:
            self.notification_btn.configure(text="🔔 Bildirim Yok", fg_color="transparent", text_color=("black", "white"), border_width=1)

    def show_notifications_dialog(self) -> None:
        if not self.current_alerts:
            return
            
        dialog = ctk.CTkToplevel(self)
        dialog.title("Süresi Yaklaşan Sunucular")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Bildirimler", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        
        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        for alert in self.current_alerts:
            ctk.CTkLabel(scroll, text=alert, text_color="red", font=ctk.CTkFont(weight="bold"), wraplength=350).pack(pady=5, anchor="w")

    @staticmethod
    def start_asyncio_loop(loop: asyncio.AbstractEventLoop) -> None:
        asyncio.set_event_loop(loop)
        loop.run_forever()

    def run_async_task(self, coro) -> None:
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    def show_frame(self, name: str) -> None:
        for frame_name, frame in self.frames.items():
            if frame_name == name:
                frame.tkraise()
                if hasattr(frame, 'on_show'):
                    frame.on_show()

    def show_dashboard(self) -> None: self.show_frame("dashboard")
    def show_bulk_ssh(self) -> None: self.show_frame("bulk")
    def show_single_ssh(self) -> None: self.show_frame("single")
    def show_management(self) -> None: self.show_frame("manage")
    def show_settings(self) -> None: self.show_frame("settings")


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master: 'App') -> None:
        super().__init__(master, corner_radius=10)
        self.app = master
        self.label = ctk.CTkLabel(self, text="Dashboard (Gözlem)", font=ctk.CTkFont(size=24, weight="bold"))
        self.label.pack(pady=20, padx=20, anchor="w")
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.refresh()

    def on_show(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        servers = self.app.server_manager.servers
        if not servers:
            ctk.CTkLabel(self.content_frame, text="Henüz sunucu eklenmedi. Lütfen 'Sunucu Yönetimi' sekmesinden ekleyin.").pack(pady=20)
            return

        for i, srv in enumerate(servers):
            self.content_frame.columnconfigure(i, weight=1)
            srv_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
            srv_frame.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            
            lbl = ctk.CTkLabel(srv_frame, text=f"{srv.get('name', 'Bilinmeyen')}", font=ctk.CTkFont(size=18, weight="bold"))
            lbl.pack(pady=10)
            ctk.CTkLabel(srv_frame, text="CPU Kullanımı:").pack(anchor="w", padx=20)
            cpu_pb = ctk.CTkProgressBar(srv_frame)
            cpu_pb.pack(fill="x", padx=20, pady=5)
            cpu_pb.set(0.0) 
            ctk.CTkLabel(srv_frame, text="RAM Kullanımı:").pack(anchor="w", padx=20, pady=(10,0))
            ram_pb = ctk.CTkProgressBar(srv_frame)
            ram_pb.pack(fill="x", padx=20, pady=5)
            ram_pb.set(0.0) 


class BulkSSHFrame(ctk.CTkFrame):
    def __init__(self, master: 'App') -> None:
        super().__init__(master, corner_radius=10)
        self.app = master
        self.label = ctk.CTkLabel(self, text="Toplu Komut (Bulk SSH)", font=ctk.CTkFont(size=24, weight="bold"))
        self.label.pack(pady=20, padx=20, anchor="w")

        self.cmd_entry = ctk.CTkEntry(self, placeholder_text="Komut yazın ve Enter tuşuna basın (örn: uptime)")
        self.cmd_entry.pack(fill="x", padx=20, pady=10)
        self.cmd_entry.bind("<Return>", self.send_command)

        self.grid_frame = ctk.CTkScrollableFrame(self)
        self.grid_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.textboxes = []

    def on_show(self) -> None:
        self.rebuild_grid()

    def rebuild_grid(self) -> None:
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        
        self.textboxes.clear()
        servers = self.app.server_manager.servers
        n = len(servers)
        if n == 0:
            ctk.CTkLabel(self.grid_frame, text="Hiç sunucu bulunamadı. Önce sunucu ekleyin.").pack(pady=20)
            return

        cols = 2 if n > 1 else 1
        for i in range(cols):
            self.grid_frame.columnconfigure(i, weight=1)

        for i, srv in enumerate(servers):
            row = i // cols
            col = i % cols
            
            box_frame = ctk.CTkFrame(self.grid_frame)
            box_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.grid_frame.rowconfigure(row, weight=1)
            
            lbl = ctk.CTkLabel(box_frame, text=f"{srv.get('name', 'İsimsiz')} ({srv.get('ip', 'IP Yok')})", font=ctk.CTkFont(weight="bold"))
            lbl.pack(pady=(5,0))

            theme_name = str(srv.get("theme", "Karanlık (Siyah/Beyaz)"))
            colors = TERMINAL_THEMES.get(theme_name, TERMINAL_THEMES["Karanlık (Siyah/Beyaz)"])

            txt = ctk.CTkTextbox(
                box_frame, 
                font=ctk.CTkFont(family="Consolas", size=13), 
                height=200, 
                fg_color=colors["fg_color"], 
                text_color=colors["text_color"]
            )
            txt.pack(fill="both", expand=True, padx=10, pady=10)
            self.textboxes.append({"server": srv, "textbox": txt})

    def send_command(self, event=None) -> None:
        _ = event
        cmd = self.cmd_entry.get().strip()
        if not cmd: return
        self.cmd_entry.delete(0, 'end')

        for item in self.textboxes:
            srv = item["server"]
            txt = item["textbox"]
            ip_str = str(srv.get('ip', 'IP Yok'))
            txt.insert("end", f"\nroot@{ip_str}:~$ {cmd}\n")
            txt.see("end")
            self.app.run_async_task(self.async_ssh_command(srv, cmd, txt))

    async def async_ssh_command(self, server: dict, cmd: str, textbox: ctk.CTkTextbox) -> None:
        output = await asyncio.to_thread(run_ssh_command_sync, server, cmd)
        self.app.after(0, self._update_textbox, textbox, output)

    @staticmethod
    def _update_textbox(textbox: ctk.CTkTextbox, output: str) -> None:
        textbox.insert("end", f"{output}\n")
        textbox.see("end")


class SingleSSHFrame(ctk.CTkFrame):
    def __init__(self, master: 'App') -> None:
        super().__init__(master, corner_radius=10)
        self.app = master
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(fill="x", pady=20, padx=20)
        
        self.label = ctk.CTkLabel(self.top_frame, text="Tekli Kontrol", font=ctk.CTkFont(size=24, weight="bold"))
        self.label.pack(side="left")

        self.server_var = ctk.StringVar(value="")
        self.server_dropdown = ctk.CTkOptionMenu(
            self.top_frame, 
            variable=self.server_var,
            command=self.on_server_select
        )
        self.server_dropdown.pack(side="right", padx=10)

        self.cmd_entry = ctk.CTkEntry(self, placeholder_text="Seçili sunucuya komut yazın ve Enter'a basın")
        self.cmd_entry.pack(fill="x", padx=20, pady=(0, 10))
        self.cmd_entry.bind("<Return>", self.send_command)

        self.terminal_text = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=14))
        self.terminal_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.terminal_text.insert("end", "Sunucu seçin...\n")
        
        self.selected_server = None

    def on_show(self) -> None:
        servers = self.app.server_manager.servers
        if not servers:
            self.server_dropdown.configure(values=["Sunucu Bulunamadı"])
            self.server_dropdown.set("Sunucu Bulunamadı")
            self.selected_server = None
            return

        names = [f"{s.get('name', 'İsimsiz')} ({s.get('ip', 'IP Yok')})" for s in servers]
        self.server_dropdown.configure(values=names)
        
        current_val = self.server_var.get()
        if current_val not in names:
            self.server_dropdown.set(names[0])
            self.on_server_select(names[0])
        else:
            self.on_server_select(current_val)

    def on_server_select(self, choice: str) -> None:
        if choice == "Sunucu Bulunamadı": return
        servers = self.app.server_manager.servers
        for srv in servers:
            if f"{srv.get('name', 'İsimsiz')} ({srv.get('ip', 'IP Yok')})" == choice:
                self.selected_server = srv
                self.apply_theme(srv)
                self.terminal_text.delete("1.0", "end")
                ip_str = str(srv.get('ip', 'IP Yok'))
                self.terminal_text.insert("end", f"{srv.get('name', 'İsimsiz')} bağlantısı hazır.\nroot@{ip_str}:~$ ")
                break

    def apply_theme(self, srv: dict) -> None:
        theme_name = str(srv.get("theme", "Karanlık (Siyah/Beyaz)"))
        colors = TERMINAL_THEMES.get(theme_name, TERMINAL_THEMES["Karanlık (Siyah/Beyaz)"])
        self.terminal_text.configure(fg_color=colors["fg_color"], text_color=colors["text_color"])

    def send_command(self, event=None) -> None:
        _ = event
        cmd = self.cmd_entry.get().strip()
        if not cmd or not self.selected_server: return
        self.cmd_entry.delete(0, 'end')

        srv = self.selected_server
        self.terminal_text.insert("end", f"{cmd}\n")
        self.terminal_text.see("end")
        self.app.run_async_task(self.async_ssh_command(srv, cmd))

    async def async_ssh_command(self, server: dict, cmd: str) -> None:
        output = await asyncio.to_thread(run_ssh_command_sync, server, cmd)
        ip_str = str(server.get('ip', 'IP Yok'))
        self.app.after(0, self._update_textbox, output, ip_str)

    def _update_textbox(self, output: str, ip: str) -> None:
        self.terminal_text.insert("end", f"{output}\nroot@{ip}:~$ ")
        self.terminal_text.see("end")


class ManagementFrame(ctk.CTkFrame):
    def __init__(self, master: 'App') -> None:
        super().__init__(master, corner_radius=10)
        self.app = master
        self.label = ctk.CTkLabel(self, text="Sunucu Yönetimi", font=ctk.CTkFont(size=24, weight="bold"))
        self.label.pack(pady=20, padx=20, anchor="w")

        self.btn_add = ctk.CTkButton(self, text="+ Yeni Sunucu Ekle", command=lambda: self.open_server_dialog())
        self.btn_add.pack(padx=20, pady=(0, 10), anchor="e")

        self.list_frame = ctk.CTkScrollableFrame(self)
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.refresh_list()

    def on_show(self) -> None:
        self.refresh_list()

    def refresh_list(self) -> None:
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        for srv in self.app.server_manager.servers:
            item = ctk.CTkFrame(self.list_frame)
            item.pack(fill="x", pady=5)
            
            lbl_tag = ctk.CTkLabel(item, text="■", text_color=str(srv.get("color", "gray")), font=ctk.CTkFont(size=20))
            lbl_tag.pack(side="left", padx=10, pady=10)

            exp = str(srv.get("expiration_date", "Belirtilmedi"))
            lbl = ctk.CTkLabel(item, text=f"{srv.get('name', 'İsimsiz')} | IP: {srv.get('ip', 'IP Yok')} | Bitiş: {exp}")
            lbl.pack(side="left", padx=10, pady=10)

            btn_frame = ctk.CTkFrame(item, fg_color="transparent")
            btn_frame.pack(side="right", padx=10, pady=5)

            btn_delete = ctk.CTkButton(btn_frame, text="Kaldır", width=60, fg_color="#b30000", hover_color="#800000", command=lambda s=srv: self.delete_server(s))
            btn_delete.pack(side="right", padx=5)

            btn_edit = ctk.CTkButton(btn_frame, text="Düzenle", width=60, command=lambda s=srv: self.open_server_dialog(s))
            btn_edit.pack(side="right", padx=5)

            btn_date = ctk.CTkButton(btn_frame, text="Tarih", width=60, fg_color="#e68a00", hover_color="#cc7a00", command=lambda s=srv: self.open_date_dialog(s))
            btn_date.pack(side="right", padx=5)

    def delete_server(self, srv: dict) -> None:
        self.app.server_manager.delete_server(str(srv.get("id")))
        self.refresh_list()
        self.app.check_notifications()

    def open_date_dialog(self, srv: dict) -> None:
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Tarih Ayarla")
        dialog.geometry("350x450")
        dialog.transient(self.app)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=f"{srv.get('name', 'İsimsiz')} için Bitiş Tarihi Seçin:", font=ctk.CTkFont(weight="bold")).pack(pady=(15,5))
        
        current_date_str = str(srv.get("expiration_date", ""))
        now = datetime.datetime.now()
        year, month, day = now.year, now.month, now.day
        if current_date_str:
            try:
                parts = current_date_str.split('-')
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            except ValueError:
                pass

        cal = tkcalendar.Calendar(dialog, selectmode='day', year=year, month=month, day=day, date_pattern='y-mm-dd')
        cal.pack(pady=10, padx=20, fill="both", expand=True)

        ctk.CTkLabel(dialog, text="Veya elle yazın (YYYY-AA-GG):").pack(pady=(10,0))
        entry_date = ctk.CTkEntry(dialog)
        entry_date.insert(0, current_date_str)
        entry_date.pack(fill="x", padx=40, pady=5)

        def on_cal_select(event=None) -> None:
            _ = event
            entry_date.delete(0, 'end')
            entry_date.insert(0, cal.get_date())

        cal.bind("<<CalendarSelected>>", on_cal_select)

        def save_date() -> None:
            date_val = entry_date.get().strip()
            self.app.server_manager.update_server(str(srv.get("id")), {"expiration_date": date_val})
            self.refresh_list()
            self.app.check_notifications()
            dialog.destroy()

        ctk.CTkButton(dialog, text="Kaydet", command=save_date).pack(pady=15)

    def open_server_dialog(self, server_to_edit: dict = None) -> None:
        dialog = ctk.CTkToplevel(self.app)
        title = "Sunucu Düzenle" if server_to_edit else "Sunucu Ekle"
        dialog.title(title)
        dialog.geometry("400x550")
        dialog.transient(self.app)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Sunucu Adı:").pack(pady=(15, 0), padx=20, anchor="w")
        entry_name = ctk.CTkEntry(dialog)
        entry_name.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(dialog, text="IP Adresi:").pack(pady=(5, 0), padx=20, anchor="w")
        entry_ip = ctk.CTkEntry(dialog)
        entry_ip.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(dialog, text="Port:").pack(pady=(5, 0), padx=20, anchor="w")
        entry_port = ctk.CTkEntry(dialog)
        entry_port.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(dialog, text="Kullanıcı Adı:").pack(pady=(5, 0), padx=20, anchor="w")
        entry_user = ctk.CTkEntry(dialog)
        entry_user.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(dialog, text="Şifre:").pack(pady=(5, 0), padx=20, anchor="w")
        entry_pass = ctk.CTkEntry(dialog, show="*")
        entry_pass.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(dialog, text="Terminal Teması:").pack(pady=(5, 0), padx=20, anchor="w")
        theme_var = ctk.StringVar(value="Karanlık (Siyah/Beyaz)")
        theme_menu = ctk.CTkOptionMenu(dialog, variable=theme_var, values=list(TERMINAL_THEMES.keys()))
        theme_menu.pack(fill="x", padx=20, pady=5)

        if server_to_edit:
            entry_name.insert(0, str(server_to_edit.get("name", "")))
            entry_ip.insert(0, str(server_to_edit.get("ip", "")))
            entry_port.insert(0, str(server_to_edit.get("port", "22")))
            entry_user.insert(0, str(server_to_edit.get("username", "root")))
            entry_pass.insert(0, str(server_to_edit.get("password", "")))
            theme_var.set(str(server_to_edit.get("theme", "Karanlık (Siyah/Beyaz)")))
        else:
            entry_port.insert(0, "22")
            entry_user.insert(0, "root")

        def save() -> None:
            srv_data = {
                "name": str(entry_name.get()),
                "ip": str(entry_ip.get()),
                "port": str(entry_port.get()),
                "username": str(entry_user.get()),
                "password": str(entry_pass.get()),
                "color": "#1f538d",
                "theme": str(theme_var.get())
            }
            if server_to_edit:
                srv_data["id"] = str(server_to_edit.get("id"))
                if "expiration_date" in server_to_edit:
                    srv_data["expiration_date"] = str(server_to_edit["expiration_date"])

            if srv_data["name"] and srv_data["ip"]:
                if server_to_edit:
                    self.app.server_manager.update_server(str(server_to_edit.get("id")), srv_data)
                else:
                    self.app.server_manager.add_server(srv_data)
                
                self.refresh_list()
                self.app.check_notifications()
                dialog.destroy()

        btn_save = ctk.CTkButton(dialog, text="Kaydet", command=save)
        btn_save.pack(pady=15)


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master: 'App') -> None:
        super().__init__(master, corner_radius=10)
        self.app = master
        self.label = ctk.CTkLabel(self, text="Ayarlar", font=ctk.CTkFont(size=24, weight="bold"))
        self.label.pack(pady=20, padx=20, anchor="w")

        self.theme_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.theme_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(self.theme_frame, text="Uygulama Görünümü (Genel Tema):", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        
        self.app_theme_var = ctk.StringVar(value=str(self.app.settings_manager.settings.get("app_theme", "System")))
        self.app_theme_menu = ctk.CTkOptionMenu(
            self.theme_frame, 
            variable=self.app_theme_var, 
            values=["Light", "Dark", "System"],
            command=self.change_app_theme
        )
        self.app_theme_menu.pack(anchor="w", pady=5)

        ctk.CTkLabel(self.theme_frame, text="Son Gün Bildirimi (Kaç gün kala uyarsın?):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(20,0))
        
        self.notify_days_var = ctk.StringVar(value=str(self.app.settings_manager.settings.get("notify_days", 3)))
        self.notify_days_menu = ctk.CTkOptionMenu(
            self.theme_frame,
            variable=self.notify_days_var,
            values=["1", "2", "3", "4", "5", "10"],
            command=self.change_notify_days
        )
        self.notify_days_menu.pack(anchor="w", pady=5)

        ctk.CTkLabel(self, text="Veri Yönetimi:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(20,5))
        self.btn_export = ctk.CTkButton(self, text="JSON Dışa Aktar (Export)")
        self.btn_export.pack(padx=20, pady=5, anchor="w")
        self.btn_import = ctk.CTkButton(self, text="JSON İçe Aktar (Import)")
        self.btn_import.pack(padx=20, pady=5, anchor="w")

    def change_app_theme(self, choice: str) -> None:
        ctk.set_appearance_mode(choice)
        self.app.settings_manager.settings["app_theme"] = choice
        self.app.settings_manager.save()

    def change_notify_days(self, choice: str) -> None:
        self.app.settings_manager.settings["notify_days"] = int(choice)
        self.app.settings_manager.save()
        self.app.check_notifications()

if __name__ == "__main__":
    app = App()
    app.mainloop()
