from tkinter import *
from PIL import Image, ImageTk
from datetime import *
from tkinter import ttk
import os, sys, platform
from steampy import Steam
import customtkinter as ctk
from datetime import datetime as dt


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


colour_dir = resource_path("assets\\images\\colour\\")
grey_dir = resource_path("assets\\images\\grey\\")
latest_img = resource_path("assets\\images\\achievement_icon.jpg")
broken_img = resource_path("assets\\images\\broken.jpg")
config_dir = resource_path("assets\\config\\steam.json")
game_icons_dir = resource_path("assets\\games\\icons\\")

ctk.set_default_color_theme("blue")
ctk.set_appearance_mode("system")
root = ctk.CTk()


def get_data():
    refresh = str(datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))
    print("Data Refreshed: " + refresh)

    steam = Steam()
    achievements = [
        {"name": "Failed to Load", "achieved": 0, "apiname": "None", "unlocktime": 0}
    ]
    data = steam.get_achievements()
    percentages = steam.get_completion_stats()
    details = steam.get_details()["achievement_details"]
    total = data["total"]

    if not data["achievements"][0] == "Failed to Load":
        achievements = list(
            sorted(data["achievements"], key=lambda d: d["unlocktime"], reverse=True)
        )

    latest = steam.get_latest(achievements)
    steam.clear_images(colour_dir)
    steam.clear_images(grey_dir)

    color = []
    gray = []
    if details[0]["name"] != "API Failure":
        for url in details:
            color.append(url["icon"])
            gray.append(url["icongray"])
        steam.download_images(color, colour_dir)
        steam.download_images(gray, grey_dir)
        print("[INFO] Images Loaded")
    else:
        print("[WARN] No Images Loaded")

    return {
        "refresh_on": refresh,
        "data": data,
        "achievements": achievements,
        "details": details,
        "latest": latest,
        "total": total,
        "percentages": percentages,
    }


class FrameWindow(ctk.CTkFrame):
    def __init__(self, colour="#252525", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(fg_color=colour)
        self.pack(fill=BOTH, expand=True)


class DisplayWindow(ctk.CTkToplevel):
    def __init__(self, title, geometry, colour, *args, **kwargs):
        super().__init__(*args, **kwargs)
        v = ctk.IntVar()
        v.set(1)

        self.title(title)
        self.geometry(geometry)

        self.steam = Steam()
        self.configure(fg_color=colour)

        self.data = self.steam.get_achievements()
        self.total = self.data["total"]
        achievements = self.data["achievements"]

        self.latest = self.steam.get_latest(achievements)
        self.num_earned = self.latest["num_earned"]
        self.a_name = self.steam.get_latest_details(self.latest["latest"]["apiname"])

        self.title(title)
        self.geometry(geometry)

        self.steam = Steam()
        self.configure(fg_color=colour)

        self.data = self.steam.get_achievements()
        self.total = self.data["total"]
        achievements = self.data["achievements"]

        self.latest = self.steam.get_latest(achievements)
        self.num_earned = self.latest["num_earned"]
        self.a_name = self.steam.get_latest_details(self.latest["latest"]["apiname"])

        self.game_name = ctk.CTkLabel(
            self,
            text="Game: {}".format(self.data["gamename"]),
            font=("", 36, "bold"),
            justify="left",
            anchor="w",
        )
        self.game_name.grid(
            row=0, column=0, columnspan=2, sticky="w", padx=(15, 0), pady=(5, 0)
        )

        self.title = ctk.CTkLabel(
            self,
            text="Achievements Earned:",
            font=("", 36, "bold"),
            justify="left",
            anchor="w",
        )
        self.title.grid(
            row=1, column=0, columnspan=1, sticky="w", padx=(15, 0), pady=(5, 0)
        )

        self.earned_count = ctk.CTkLabel(
            self,
            text="{}/{}".format(self.num_earned, self.total),
            font=("", 36, "bold"),
            justify="left",
            anchor="w",
        )
        self.earned_count.grid(
            row=2, column=0, columnspan=1, sticky="w", padx=(15, 0), pady=(5, 0)
        )

        self.achievement_latest_title = ctk.CTkLabel(
            self,
            text="Last Achievement:",
            font=("", 36, "bold"),
            justify="left",
            anchor="w",
        )
        self.achievement_latest_title.grid(
            row=3, column=0, columnspan=1, sticky="w", padx=(15, 0), pady=(5, 0)
        )

        self.achievement_latest = ctk.CTkLabel(
            self,
            text="{}".format(self.a_name),
            font=("", 28, "bold"),
            justify="left",
            anchor="w",
        )
        self.achievement_latest.grid(
            row=4, column=0, sticky="sw", padx=(145, 0), pady=(10, 5)
        )

        self.image = ctk.CTkImage(
            Image.open(latest_img).resize((112, 112), Image.LANCZOS),
            size=(112, 112),
        )
        self.img_display = ctk.CTkLabel(self, text="", image=self.image, anchor="w")
        self.img_display.grid(
            row=4, column=0, columnspan=1, rowspan=2, sticky="w", padx=(18, 0)
        )

        self.radiobutton_1 = ctk.CTkRadioButton(
            self,
            text="Blue",
            command=lambda: self.configure(fg_color="Blue"),
            variable=v,
            value=2,
        )
        self.radiobutton_2 = ctk.CTkRadioButton(
            self,
            text="Green",
            command=lambda: self.configure(fg_color="Green"),
            variable=v,
            value=1,
        )
        self.radiobutton_3 = ctk.CTkRadioButton(
            self,
            text="Desktop",
            command=lambda: self.configure(fg_color="#252525"),
            variable=v,
            value=3,
        )

        self.radiobutton_1.place(relx=0.15, rely=0.96, anchor="e")
        self.radiobutton_2.place(relx=0.25, rely=0.96, anchor="e")
        self.radiobutton_3.place(relx=0.35, rely=0.96, anchor="e")

        self.submit_button = ctk.CTkButton(self, text="Done", command=self.done)
        self.submit_button.place(relx=0.89, rely=0.96, anchor="center")

        self.after(30000, self.refresh)
        self.mainloop()

    def refresh(self):
        print("[INFO] (Display Window) refresh method called!")
        self.steam = Steam()
        # get_images(self.steam)

        data = self.steam.get_achievements()
        latest = self.steam.get_latest(data["achievements"])
        a_name = self.steam.get_latest_details(latest["latest"]["apiname"])

        self.game_name.configure(text=f"Game: {data['gamename']}")
        self.earned_count.configure(text=f"{latest['num_earned']}/{data['total']}")
        self.achievement_latest.configure(text=f"{a_name}")

        update = ctk.CTkImage(
            Image.open(latest_img).resize((112, 112), Image.LANCZOS),
            size=(112, 112),
        )
        self.img_display.configure(image=update)
        self.img_display.image = update

        self.update()
        self.after(30000, self.refresh)

    def done(self):
        print("[INFO] (Display Window) done method called!")
        self.update()
        self.destroy()


class Settings(ctk.CTkToplevel):
    def __init__(self, title, res, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title(title)
        self.geometry(res)
        self.steam = Steam()

        self.title_label = ctk.CTkLabel(
            self, text="ACHEEVO! - Settings", font=("", 20, "bold")
        )
        self.title_label.grid(row=0, column=0, columnspan=2, pady=(8, 6), sticky="nswe")

        self.steam_api_key_lbl = ctk.CTkLabel(self, text="Steam API Key:", anchor="w")
        self.steam_api_key_lbl.grid(
            row=1, column=0, padx=(10, 10), pady=(10, 0), sticky="w"
        )
        self.steam_api_key = ctk.CTkEntry(self, width=360)
        self.steam_api_key.grid(row=1, column=1, pady=(10, 0))

        self.steam_user_id_lbl = ctk.CTkLabel(self, text="Steam User ID:", anchor="w")
        self.steam_user_id_lbl.grid(
            row=2, column=0, padx=(10, 10), pady=(10, 0), sticky="w"
        )
        self.steam_user_id = ctk.CTkEntry(self, width=360)
        self.steam_user_id.grid(row=2, column=1, pady=(10, 0))

        self.steam_game_id_lbl = ctk.CTkLabel(self, text="Steam Game ID:", anchor="w")

        self.steam_game_id_lbl.grid(
            row=3, column=0, padx=(10, 10), pady=(10, 0), sticky="w"
        )
        self.steam_game_id = ctk.CTkEntry(self, width=360)
        self.steam_game_id.grid(row=3, column=1, pady=(10, 0))

        self.steam_game_id.insert(ctk.END, self.steam.config["appid"])
        self.steam_user_id.insert(ctk.END, self.steam.config["steamid"])
        self.steam_api_key.insert(ctk.END, self.steam.config["key"])

        self.submit_button = ctk.CTkButton(
            self, text="Update", command=self.write_user_info
        )
        self.submit_button.place(relx=0.54, rely=0.9, anchor="center")

        self.submit_button = ctk.CTkButton(self, text="Done", command=self.done)
        self.submit_button.place(relx=0.84, rely=0.9, anchor="center")

    def done(self):
        print("[Info] (Settings Window) done method called!")
        data = {
            "appid": str(self.steam_game_id.get()),
            "steamid": self.steam_user_id.get(),
            "key": self.steam_api_key.get(),
        }
        self.steam.configure_creds(data)

        get_data()

        self.destroy()
        self.update()

    def write_user_info(self):
        print("[Info] (Settings Window) write_user_info method called!")
        data = {
            "appid": str(self.steam_game_id.get()),
            "steamid": self.steam_user_id.get(),
            "key": self.steam_api_key.get(),
        }
        self.steam.configure_creds(data)

        get_data()

        self.destroy()
        self.update()


class App:
    def __init__(self, master):
        self.window = master
        self.window.title("Acheevo! - Steam Achievement Dashboard")
        self.window.geometry("1280x720")
        self.window.resizable(0, 0)

        self.photo_image_list = []
        self.photo_images = []
        self.display = None
        self.settings = None

        # == BANNER ==#
        self.configure_top_bar()

        self.data = get_data()

        # == LOG FRAME ==#
        self.configure_log_frame()

        # == GAME FRAME ==#
        self.configure_game_frame()

        self.window.after(30000, self.refresh)

    def configure_top_bar(self):
        print("CONFIGURE TOP BAR CALLED")
        self.banner = ctk.CTkFrame(self.window, width=1280, height=120, corner_radius=0)
        self.banner.pack(side="top", fill=X)

        self.title = ctk.CTkLabel(self.banner, text="ACHEEVO!", font=("", 34, "bold"))
        self.title.pack(fill="both", side=LEFT, padx=30)

        # Log
        self.log_button = ctk.CTkButton(
            self.banner,
            text="Log Window",
            image=ctk.CTkImage(Image.open(resource_path("assets\\images\\log.png"))),
            cursor="hand2",
            font=("", 12, "bold"),
            corner_radius=0,
            command=lambda: self.show_frame(array_pos=0),
        )
        self.log_button.pack(side=LEFT, fill=BOTH, expand=True)

        # Games
        self.games_button = ctk.CTkButton(
            self.banner,
            text="Game Window",
            image=ctk.CTkImage(
                Image.open(resource_path("assets\\images\\library.png"))
            ),
            cursor="hand2",
            font=("", 12, "bold"),
            corner_radius=0,
            command=lambda: self.show_frame(array_pos=1),
        )
        self.games_button.pack(side=LEFT, fill=BOTH, expand=True)

        # tracker
        self.tracker_button = ctk.CTkButton(
            self.banner,
            text="Tracker Window",
            image=ctk.CTkImage(
                Image.open(resource_path("assets\\images\\library.png"))
            ),
            cursor="hand2",
            font=("", 12, "bold"),
            corner_radius=0,
            command=self.open_tracker,
        )
        self.tracker_button.pack(side=LEFT, fill=BOTH, expand=True)

        # steam manage
        self.manage_button = ctk.CTkButton(
            self.banner,
            text="Settings",
            image=ctk.CTkImage(Image.open(resource_path("assets\\images\\steam.png"))),
            cursor="hand2",
            font=("", 12, "bold"),
            corner_radius=0,
            command=self.open_settings,
        )
        self.manage_button.pack(side=LEFT, fill=BOTH, expand=True)

        # steam manage
        self.restart_button = ctk.CTkButton(
            self.banner,
            text="Refresh App",
            image=ctk.CTkImage(
                Image.open(resource_path("assets\\images\\restart.png"))
            ),
            cursor="hand2",
            font=("", 12, "bold"),
            corner_radius=0,
            command=self.refresh,
        )
        self.restart_button.pack(side=RIGHT, fill=BOTH, expand=True)

        self.frames = [
            FrameWindow(master=self.window, corner_radius=0),
            FrameWindow(master=self.window, corner_radius=0),
        ]
        self.frames[0].forget()

    def configure_log_frame(self):
        log_frame = self.frames[0]

        self.log_title_label = ctk.CTkLabel(
            log_frame,
            text="Acheevo! - Achievement Log",
            font=("", 36, "bold"),
            justify="left",
            anchor="w",
        )
        self.log_title_label.pack(padx=10, pady=(10, 0))

        self.log_game_label = ctk.CTkLabel(
            log_frame,
            text="Game: LOADING",
            font=("", 16, "bold"),
            justify="left",
            anchor="w",
        )
        self.log_game_label.pack(padx=10, pady=(5, 0))

        self.log_sgame_label = ctk.CTkLabel(
            log_frame,
            text="0 of 0 Achieved",
            font=("", 16, "bold"),
            justify="left",
            anchor="w",
        )
        self.log_sgame_label.pack(padx=10, pady=(5, 0))

        style = ttk.Style(log_frame)
        ops = platform.system()
        theme = "aqua" if ops == "Darwin" else "clam"

        style.theme_use(theme)
        style.configure(
            "Treeview", foreground="white", fieldbackground="#252525", rowheight=64
        )
        self.tree = ttk.Treeview(master=log_frame)
        self.tree.tag_configure("oddrow", background="#252535")
        self.tree.tag_configure("evenrow", background="#252525")

        self.scrollbar = ttk.Scrollbar(
            self.tree, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.tree["columns"] = ("one", "two", "three", "four")
        self.tree.column("#0", width=100, minwidth=100, stretch=NO)
        self.tree.column("one", width=100, minwidth=100, stretch=YES)
        self.tree.column("two", width=100, minwidth=100, stretch=YES)
        self.tree.column("three", width=400, minwidth=100, stretch=YES)
        self.tree.column("four", width=100, minwidth=100, stretch=YES)

        self.tree.heading("#0", text="Icon", anchor=W)
        self.tree.heading("one", text="Name", anchor=W)
        self.tree.heading("two", text="Date Achieved", anchor=W)
        self.tree.heading("three", text="Description", anchor=W)
        self.tree.heading("four", text="Global %", anchor=W)

        self.tree.pack(side=TOP, fill=BOTH, expand=True, padx=5, pady=5)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        position = 0
        self.tree.delete(*self.tree.get_children())

        self.tree.insert(
            "", index=0, iid="Achieved", text="Achieved", tags="evenrow", open=True
        )
        self.tree.insert(
            "", index=1, iid="Unachieved", text="Not Achieved", tags="oddrow", open=True
        )

        position = 2

        self.log_game_label.configure(text=f"Game: {self.data['data']['gamename']}")
        if self.data["total"] != 0:
            extra = f"- {round(self.data['latest']['num_earned'] *100 / self.data['total'])}% Completion"
        else:
            extra = "0%"
        self.log_sgame_label.configure(
            text=f"{self.data['latest']['num_earned']} of {self.data['total']} Achieved {extra}"
        )
        name = "blank"
        description = "blank"
        percentage = "blank"
        for i in self.data["achievements"]:
            for detail in self.data["details"]:
                if detail["name"] == i["apiname"]:
                    name = detail["displayName"]
                    description = (
                        "Hidden by Steam"
                        if detail["hidden"] == 1
                        else detail["description"]
                    )
                    icon_url = detail["icon"]
                    icon_hash = icon_url[icon_url.rfind("/") :].replace("/", "")
                    icongurl = detail["icongray"]
                    icong_hash = icongurl[icongurl.rfind("/") :].replace("/", "")
                    for n, p in self.data["percentages"].items():
                        if i["apiname"] == n:
                            percentage = round(p, 2)

            tag = self.get_tag(pos=position)

            time = (
                dt.fromtimestamp(i["unlocktime"]).strftime("%c")
                if i["unlocktime"] != 0
                else "Not Achieved!"
            )

            parent = ""

            if time != "Not Achieved!":
                file = "{}{}".format(colour_dir, icon_hash)
                parent = "Achieved"
            elif i["apiname"] == "None":
                file = "{}".format(broken_img)
            else:
                file = "{}{}".format(grey_dir, icong_hash)
                parent = "Unachieved"

            img = ImageTk.PhotoImage(file=file)
            self.photo_image_list.append(img)

            self.tree.insert(
                parent=parent,
                index=position + 1,
                text="",
                image=img,
                open=True,
                values=[name, str(time), str(description), (str(percentage) + "%")],
                tags=tag,
            )
            position += 1

        self.update_label = ctk.CTkLabel(
            log_frame,
            text=f"Last Update: {self.data['refresh_on']}",
            font=("", 16, "bold"),
            justify="left",
            anchor="w",
        )
        self.update_label.pack(padx=10, pady=(5, 0))

    def configure_game_frame(self):
        game_frame = self.frames[1]
        steam = Steam()

        self.game_title_label = ctk.CTkLabel(
            game_frame, text="Steam Game List", font=("", 30, "bold")
        )
        self.game_title_label.pack(padx=10, pady=(15, 0))

        self.stitle_label = ctk.CTkLabel(
            game_frame,
            text="Only games with achievements are shown.\nClicking an item below will copy the Game ID to paste in the Settings Window.",
            font=("", 12, "bold"),
        )
        self.stitle_label.pack(padx=10, pady=(5, 0))

        style = ttk.Style(game_frame)
        ops = platform.system()
        theme = "aqua" if ops == "Darwin" else "clam"

        style.theme_use(theme)
        style.configure(
            "Treeview", foreground="white", fieldbackground="#252525", rowheight=64
        )

        self.game_tree = ttk.Treeview(master=game_frame)
        self.game_tree.tag_configure("oddrow", background="#252535")
        self.game_tree.tag_configure("evenrow", background="#252525")

        self.scrollbar = ttk.Scrollbar(
            self.game_tree, orient="vertical", command=self.game_tree.yview
        )
        self.game_tree.configure(yscrollcommand=self.scrollbar.set)
        self.game_tree["columns"] = ("one", "two", "three")
        self.game_tree.column("#0", width=100, minwidth=100, stretch=NO)
        self.game_tree.column("one", width=100, minwidth=100, stretch=YES)
        self.game_tree.column("two", width=100, minwidth=100, stretch=YES)
        self.game_tree.column("three", width=100, minwidth=100, stretch=YES)

        self.game_tree.heading("#0", text="Icon", anchor=W)
        self.game_tree.heading("one", text="Name", anchor=W)
        self.game_tree.heading("two", text="Appplication ID", anchor=W)
        self.game_tree.heading("three", text="Total Play-Time (Since 2009)", anchor=W)

        self.game_tree.pack(side=TOP, fill=BOTH, expand=True, padx=5, pady=5)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        self.game_tree.bind("<ButtonRelease-1>", self.tree_click_handler)

        position = 0

        steam.clear_images(game_icons_dir)

        data = steam.get_games_list()
        for i in data:
            img = ImageTk.PhotoImage(
                file="{}\\{}.jpg".format(game_icons_dir, i["img_logo_url"])
            )
            self.photo_images.append(img)

            tag = self.get_tag(pos=position)
            self.game_tree.insert(
                parent="",
                index=position + 1,
                text="",
                image=img,
                open=True,
                values=[i["name"], i["appid"], i["playtime_forever"]],
                tags=tag,
            )
            position += 1

    def tree_click_handler(self, event):
        cur_item = self.game_tree.item(self.game_tree.focus())
        col = self.game_tree.identify_column(event.x)
        if col == "#2":
            self.window.clipboard_clear()
            self.window.clipboard_append(cur_item["values"][1])

    def open_tracker(self):
        print("[INFO] open_display method called!")
        if self.display is None or not self.display.winfo_exists():
            self.display = DisplayWindow(
                "Acheevo! - Display",
                "720x480",
                colour="Green",
            )
            self.display.resizable(width=0, height=0)
        else:
            self.display.focus()

    def open_settings(self):
        print("[INFO] (MainWindow) open_settings method called!")
        if self.settings is None or not self.settings.winfo_exists():
            self.settings = Settings("Acheevo! - Settings", "480x240")
            self.settings.resizable(width=False, height=False)
        else:
            self.settings.focus()

    def refresh(self):
        root.iconbitmap(resource_path("assets\\images\\award.ico"))
        self.data = get_data()
        name = ""
        position = 0
        icon_hash = ""
        icong_hash = ""
        description = ""
        latest = self.data["latest"]
        total = self.data["total"]
        print(self.tree.get_children())

        # TREEVIEW REFRESH
        self.tree.delete(*self.tree.get_children())
        self.tree.insert(
            "", index=0, iid="Achieved", text="Achieved", tags="evenrow", open=True
        )
        self.tree.insert(
            "", index=1, iid="Unachieved", text="Not Achieved", tags="oddrow", open=True
        )

        position = 2

        self.log_game_label.configure(text=f"Game: {self.data['data']['gamename']}")
        extra = f"- {round(latest['num_earned'] *100 / total)}% Completion"
        self.log_sgame_label.configure(
            text=f"{latest['num_earned']} of {total} Achieved {extra}"
        )
        for i in self.data["achievements"]:
            for detail in self.data["details"]:
                if detail["name"] == i["apiname"]:
                    name = detail["displayName"]
                    description = (
                        "Hidden by Steam"
                        if detail["hidden"] == 1
                        else detail["description"]
                    )
                    icon_url = detail["icon"]
                    icon_hash = icon_url[icon_url.rfind("/") :].replace("/", "")
                    icongurl = detail["icongray"]
                    icong_hash = icongurl[icongurl.rfind("/") :].replace("/", "")
                    for n, p in self.data["percentages"].items():
                        if i["apiname"] == n:
                            percentage = round(p, 2)

            tag = self.get_tag(pos=position)
            time = (
                dt.fromtimestamp(i["unlocktime"]).strftime("%c")
                if i["unlocktime"] != 0
                else "Not Achieved!"
            )

            if time != "Not Achieved!":
                file = "{}{}".format(colour_dir, icon_hash)
                parent = "Achieved"
            else:
                file = "{}{}".format(grey_dir, icong_hash)
                parent = "Unachieved"

            img = ImageTk.PhotoImage(file=file)
            self.photo_image_list.append(img)

            self.tree.insert(
                parent=parent,
                index=position + 1,
                text="",
                image=img,
                open=True,
                values=[name, str(time), str(description), (str(percentage) + "%")],
                tags=tag,
            )

            position += 1
        self.update_label.configure(text=f"Last Update: {self.data['refresh_on']}")

        self.window.after(30000, self.refresh)

    def show_frame(self, array_pos):
        for i in self.frames:
            i.forget()
        self.frames[array_pos].pack(fill=BOTH, expand=True)

    @staticmethod
    def get_tag(pos):
        if pos % 2:
            return "evenrow"
        else:
            return "oddrow"


if __name__ == "__main__":
    root.iconbitmap(resource_path("assets\\images\\award.ico"))
    App(root)
    root.mainloop()
