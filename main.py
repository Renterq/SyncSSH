import os
import json
import asyncio
import threading
import math
import customtkinter as ctk
import paramiko

# Genel CustomTkinter Görünüm Ayarları
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class ServerManager:
    def __init__(self, filename="servers.json"):
        self.filename = filename
        self.servers = []
        self.load()

    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    self.servers = json.load(f)
            except:
                self.servers = []

    def save(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(self.servers, f, indent=4)
            
    def add_server(self, server_data):
        self.servers.append(server_data)
        self.save()

def run_ssh_command_sync(server, cmd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            server["ip"], 
            port=int(server["port"]), 
            username=server["username"], 
            password=server["password"], 
            timeout=5
        )
        stdin, stdout, stderr = client.exec_command(cmd)
        output = stdout.read().decode('utf-8')
        err = stderr.read().decode('utf-8')
        client.close()
        res = output
        if err:
            res += "\nHata:\n" + err
        return res if res.strip() else "Komut çalıştı (çıktı yok)."
    except Exception as e:
        return f"Bağlantı Hatası: {str(e)}"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SSH VDS Manager")
        self.geometry("1100x700")
        self.minsize(900, 600)

        self.server_manager = ServerManager()

        # Asenkron Loop
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.start_asyncio_loop, args=(self.loop,), daemon=True)
        self.thread.start()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
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

        # Frames
        self.frames = {}
        self.frames["dashboard"] = DashboardFrame(self)
        self.frames["bulk"] = BulkSSHFrame(self)
        self.frames["single"] = SingleSSHFrame(self)
        self.frames["manage"] = ManagementFrame(self)
        self.frames["settings"] = SettingsFrame(self)

        for frame in self.frames.values():
            frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.show_dashboard()

    def start_asyncio_loop(self, loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    def run_async_task(self, coro):
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    def show_frame(self, name):
        for frame_name, frame in self.frames.items():
            if frame_name == name:
                frame.tkraise()
                if hasattr(frame, 'on_show'):
                    frame.on_show()

    def show_dashboard(self): self.show_frame("dashboard")
    def show_bulk_ssh(self): self.show_frame("bulk")
    def show_single_ssh(self): self.show_frame("single")
    def show_management(self): self.show_frame("manage")
    def show_settings(self): self.show_frame("settings")

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=10)
        self.label = ctk.CTkLabel(self, text="Dashboard (Gözlem)", font=ctk.CTkFont(size=24, weight="bold"))
        self.label.pack(pady=20, padx=20, anchor="w")
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.refresh()

    def on_show(self):
        self.refresh()

    def refresh(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        servers = self.master.server_manager.servers
        if not servers:
            ctk.CTkLabel(self.content_frame, text="Henüz sunucu eklenmedi. Lütfen 'Sunucu Yönetimi' sekmesinden ekleyin.").pack(pady=20)
            return

        for i, srv in enumerate(servers):
            self.content_frame.columnconfigure(i, weight=1)
            srv_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
            srv_frame.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            
            lbl = ctk.CTkLabel(srv_frame, text=f"{srv['name']}", font=ctk.CTkFont(size=18, weight="bold"))
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
    def __init__(self, master):
        super().__init__(master, corner_radius=10)
        self.label = ctk.CTkLabel(self, text="Toplu Komut (Bulk SSH)", font=ctk.CTkFont(size=24, weight="bold"))
        self.label.pack(pady=20, padx=20, anchor="w")

        self.cmd_entry = ctk.CTkEntry(self, placeholder_text="Komut yazın ve Enter tuşuna basın (örn: uptime)")
        self.cmd_entry.pack(fill="x", padx=20, pady=10)
        self.cmd_entry.bind("<Return>", self.send_command)

        self.grid_frame = ctk.CTkScrollableFrame(self)
        self.grid_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.textboxes = []

    def on_show(self):
        self.rebuild_grid()

    def rebuild_grid(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        
        self.textboxes.clear()
        servers = self.master.server_manager.servers
        n = len(servers)
        if n == 0:
            ctk.CTkLabel(self.grid_frame, text="Hiç sunucu bulunamadı. Önce sunucu ekleyin.").pack(pady=20)
            return

        # Çok sunucu varsa 2 kolon yap
        cols = 2 if n > 1 else 1
        for i in range(cols):
            self.grid_frame.columnconfigure(i, weight=1)

        for i, srv in enumerate(servers):
            row = i // cols
            col = i % cols
            
            box_frame = ctk.CTkFrame(self.grid_frame)
            box_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.grid_frame.rowconfigure(row, weight=1)
            
            lbl = ctk.CTkLabel(box_frame, text=f"{srv['name']} ({srv['ip']})", font=ctk.CTkFont(weight="bold"))
            lbl.pack(pady=(5,0))

            txt = ctk.CTkTextbox(box_frame, font=ctk.CTkFont(family="Consolas", size=13), height=200, fg_color="#1e1e1e", text_color="#00ff00")
            txt.pack(fill="both", expand=True, padx=10, pady=10)
            self.textboxes.append({"server": srv, "textbox": txt})

    def send_command(self, event=None):
        cmd = self.cmd_entry.get().strip()
        if not cmd: return
        self.cmd_entry.delete(0, 'end')

        for item in self.textboxes:
            srv = item["server"]
            txt = item["textbox"]
            txt.insert("end", f"\nroot@{srv['ip']}:~$ {cmd}\n")
            txt.see("end")
            self.master.run_async_task(self.async_ssh_command(srv, cmd, txt))

    async def async_ssh_command(self, server, cmd, textbox):
        output = await asyncio.to_thread(run_ssh_command_sync, server, cmd)
        self.master.after(0, lambda: self._update_textbox(textbox, output))

    def _update_textbox(self, textbox, output):
        textbox.insert("end", f"{output}\n")
        textbox.see("end")

class SingleSSHFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=10)
        self.label = ctk.CTkLabel(self, text="Tekli Kontrol", font=ctk.CTkFont(size=24, weight="bold"))
        self.label.pack(pady=20, padx=20, anchor="w")
        self.terminal_text = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=14), fg_color="#1e1e1e", text_color="#00ff00")
        self.terminal_text.pack(fill="both", expand=True, padx=20, pady=20)
        self.terminal_text.insert("end", "root@server:~$ (Tekli SSH yakında eklenecek)\n")

class ManagementFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=10)
        self.label = ctk.CTkLabel(self, text="Sunucu Yönetimi", font=ctk.CTkFont(size=24, weight="bold"))
        self.label.pack(pady=20, padx=20, anchor="w")

        self.btn_add = ctk.CTkButton(self, text="+ Yeni Sunucu Ekle", command=self.open_add_dialog)
        self.btn_add.pack(padx=20, pady=(0, 10), anchor="e")

        self.list_frame = ctk.CTkScrollableFrame(self)
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.refresh_list()

    def on_show(self):
        self.refresh_list()

    def refresh_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        for srv in self.master.server_manager.servers:
            item = ctk.CTkFrame(self.list_frame)
            item.pack(fill="x", pady=5)
            
            lbl_tag = ctk.CTkLabel(item, text="■", text_color=srv.get("color", "red"), font=ctk.CTkFont(size=20))
            lbl_tag.pack(side="left", padx=10, pady=10)

            lbl = ctk.CTkLabel(item, text=f"{srv['name']} | IP: {srv['ip']} | User: {srv['username']}")
            lbl.pack(side="left", padx=10, pady=10)

    def open_add_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Sunucu Ekle")
        dialog.geometry("400x500")
        dialog.transient(self.master)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Sunucu Adı (örn: Web Server):").pack(pady=(20, 0), padx=20, anchor="w")
        entry_name = ctk.CTkEntry(dialog)
        entry_name.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(dialog, text="IP Adresi:").pack(pady=(10, 0), padx=20, anchor="w")
        entry_ip = ctk.CTkEntry(dialog)
        entry_ip.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(dialog, text="Port:").pack(pady=(10, 0), padx=20, anchor="w")
        entry_port = ctk.CTkEntry(dialog)
        entry_port.insert(0, "22")
        entry_port.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(dialog, text="Kullanıcı Adı:").pack(pady=(10, 0), padx=20, anchor="w")
        entry_user = ctk.CTkEntry(dialog)
        entry_user.insert(0, "root")
        entry_user.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(dialog, text="Şifre:").pack(pady=(10, 0), padx=20, anchor="w")
        entry_pass = ctk.CTkEntry(dialog, show="*")
        entry_pass.pack(fill="x", padx=20, pady=5)

        def save():
            srv = {
                "name": entry_name.get(),
                "ip": entry_ip.get(),
                "port": entry_port.get(),
                "username": entry_user.get(),
                "password": entry_pass.get(),
                "color": "#00ff00" # Örnek yeşil
            }
            if srv["name"] and srv["ip"]:
                self.master.server_manager.add_server(srv)
                self.refresh_list()
                dialog.destroy()

        btn_save = ctk.CTkButton(dialog, text="Kaydet", command=save)
        btn_save.pack(pady=20)

class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=10)
        self.label = ctk.CTkLabel(self, text="Ayarlar", font=ctk.CTkFont(size=24, weight="bold"))
        self.label.pack(pady=20, padx=20, anchor="w")
        self.btn_export = ctk.CTkButton(self, text="JSON Dışa Aktar (Export)")
        self.btn_export.pack(padx=20, pady=10, anchor="w")
        self.btn_import = ctk.CTkButton(self, text="JSON İçe Aktar (Import)")
        self.btn_import.pack(padx=20, pady=10, anchor="w")

if __name__ == "__main__":
    app = App()
    app.mainloop()
