from tkinter import *
from PIL import Image, ImageTk
from tkinter import ttk
import os, sys, platform
from steampy import Steam
import customtkinter as ctk
import logging
from datetime import datetime as dt
from operator import itemgetter


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


images_dir = resource_path("assets\\images\\")
grey_dir = resource_path("assets\\images\\grey\\")
colour_dir = resource_path("assets\\images\\colour\\")
game_icons_dir = resource_path("assets\\games\\icons\\")

app_img = resource_path("assets\\images\\award.ico")
latest_img = resource_path("assets\\images\\achievement_icon.jpg")
broken_img = resource_path("assets\\images\\broken.jpg")
config_file = resource_path("assets\\config\\steam.json")
display_open = None
datag = None

log = logging.getLogger("main.py")


ctk.set_default_color_theme("blue")
ctk.set_appearance_mode("system")
root = ctk.CTk()


class FrameWindow(ctk.CTkFrame):
    def __init__(self, colour="#252525", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(fg_color=colour)
        self.pack(fill=BOTH, expand=True)


class Settings(ctk.CTkToplevel):
    def __init__(self, title, res, steam, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title(title)
        self.geometry(res)
        self.steam = steam

        self.title_label = ctk.CTkLabel(
            self, text="A-cheevo! - Settings", font=("", 20, "bold")
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
        log.info("(Settings Window) done method called!")
        data = {
            "appid": str(self.steam_game_id.get()),
            "steamid": self.steam_user_id.get(),
            "key": self.steam_api_key.get(),
        }

        self.steam.configure_creds(data)

        self.steam.clear_images(colour_dir)
        self.steam.clear_images(grey_dir)

        self.destroy()
        self.update()

    def write_user_info(self):
        log.info("(Settings Window) write_user_info method called!")
        data = {
            "appid": str(self.steam_game_id.get()),
            "steamid": self.steam_user_id.get(),
            "key": self.steam_api_key.get(),
        }

        self.steam.configure_creds(data)

        self.steam.clear_images(colour_dir)
        self.steam.clear_images(grey_dir)

        self.destroy()
        self.update()


class DisplayWindow(ctk.CTkToplevel):
    def __init__(self, title, geometry, colour, master, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title(title)
        self.geometry(geometry)
        self.configure(fg_color=colour)
        self.main_win = master
        self.protocol("WM_DELETE_WINDOW", self.done)

        self.resizable(width=0, height=0)
        self.focus()

        v = ctk.IntVar()
        v.set(1)

        self.game_name = ctk.CTkLabel(
            self,
            text="Game: loading",
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
            text="0/0",
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
            text="Loading",
            font=("", 28, "bold"),
            justify="left",
            anchor="w",
        )
        self.achievement_latest.grid(
            row=4, column=0, sticky="sw", padx=(150, 0), pady=(10, 5)
        )

        self.image = ctk.CTkImage(
            Image.open(latest_img).resize((118, 118), Image.LANCZOS),
            size=(118, 118),
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
        self.refresh()

        self.after(30000, self.refresh)
        self.mainloop()

    def refresh(self):
        log.info("(Display Window) refresh method called!")
        data = datag

        self.game_name.configure(text=f"Game: {data['gamename']}")
        self.earned_count.configure(
            text=f"{data['latest']['num_earned']}/{data['total']}"
        )
        self.achievement_latest.configure(text=f"{data['latest']['latest']['name']}")

        update = ctk.CTkImage(
            Image.open(latest_img).resize((112, 112), Image.LANCZOS),
            size=(112, 112),
        )
        self.img_display.configure(image=update)
        self.img_display.image = update

        self.update()
        self.after(30000, self.refresh)

    def done(self):
        log.info("(Display Window) done method called!")
        self.main_win.tracker_button.configure(state=NORMAL)
        self.update()
        self.destroy()


class PopUp(ctk.CTkToplevel):
    def __init__(self, old, new, game_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Update")
        self.geometry("325x150")

        self.title_label = ctk.CTkLabel(
            self,
            text=f"Your Game ID has changed\nfrom {old} to {new}\n\n\nNew Game Name: {game_name}",
        )
        self.title_label.pack()
        self.submit_button = ctk.CTkButton(self, text="OK", command=self.destroy).pack(
            pady=15
        )

        self.after(3000, self.destroy)


class Main:
    def __init__(self, master):
        self.master = master
        self.master.title("A-cheevo! - Steam Achievement Dashboard")
        self.master.geometry("1200x720")
        self.master.resizable(0, 0)
        self.photo_images_cache = []
        self.photo_images_games_cache = []
        self.settings = None

        self.generate_elements()
        self.data = self.refresh_data()
        self.fill_games_list()
        self.master.after(30000, self.refresh_data)

    def generate_elements(self):
        # DEFAULTS
        ops = platform.system()
        theme = "aqua" if ops == "Darwin" else "clam"

        # TOPBAR
        self.topbar = ctk.CTkFrame(self.master, width=1200, height=120, corner_radius=0)
        self.topbar.pack(side="top", fill=X)
        self.topbar_title = ctk.CTkLabel(
            self.topbar, text="A-cheevo!", font=("", 34, "bold")
        )
        self.topbar_title.pack(fill="both", side=LEFT, padx=30, pady=5)
        # TOPBAR BUTTONS
        # LOG BUTTON
        self.log_button = ctk.CTkButton(
            self.topbar,
            text="Log Window",
            image=ctk.CTkImage(Image.open(f"{images_dir}log.png")),
            cursor="hand2",
            font=("", 12, "bold"),
            corner_radius=0,
            command=lambda: self.show_frame("LOG"),
        )
        self.log_button.pack(side=LEFT, fill=BOTH, expand=True)
        # GAME BUTTON
        self.games_button = ctk.CTkButton(
            self.topbar,
            text="Game Window",
            image=ctk.CTkImage(Image.open(f"{images_dir}library.png")),
            cursor="hand2",
            font=("", 12, "bold"),
            corner_radius=0,
            command=lambda: self.show_frame("GAME"),
        )
        self.games_button.pack(side=LEFT, fill=BOTH, expand=True)
        # TRACKER BUTTON
        self.tracker_button = ctk.CTkButton(
            self.topbar,
            text="Tracker Window",
            image=ctk.CTkImage(Image.open(f"{images_dir}library.png")),
            cursor="hand2",
            font=("", 12, "bold"),
            corner_radius=0,
            command=self.open_tracker,
        )
        self.tracker_button.pack(side=LEFT, fill=BOTH, expand=True)
        # MANAGE BUTTON
        self.manage_button = ctk.CTkButton(
            self.topbar,
            text="Settings",
            image=ctk.CTkImage(Image.open(f"{images_dir}steam.png")),
            cursor="hand2",
            font=("", 12, "bold"),
            corner_radius=0,
            command=self.open_settings,
        )
        self.manage_button.pack(side=LEFT, fill=BOTH, expand=True)
        # REFRESH BUTTON
        self.restart_button = ctk.CTkButton(
            self.topbar,
            text="Refresh App",
            image=ctk.CTkImage(
                Image.open(resource_path("assets\\images\\restart.png"))
            ),
            cursor="hand2",
            font=("", 12, "bold"),
            corner_radius=0,
            command=self.refresh_data,
        )
        self.restart_button.pack(side=RIGHT, fill=BOTH, expand=True)

        # FRAMES SETUP
        # LOG FRAME
        self.log_frame = FrameWindow(master=self.master, corner_radius=0)
        style = ttk.Style(self.log_frame)
        style.theme_use(theme)
        style.configure(
            "Treeview", foreground="white", fieldbackground="#252525", rowheight=64
        )
        self.log_title = ctk.CTkLabel(
            self.log_frame,
            text="Achievement Log",
            font=("", 30, "bold"),
            justify="left",
            anchor="w",
        ).pack(padx=10, pady=(15, 5))
        self.log_game_label = ctk.CTkLabel(
            self.log_frame,
            text="Game: LOADING",
            font=("", 12, "bold"),
            justify="left",
            anchor="w",
        )
        self.log_game_label.pack(padx=10)
        self.log_ach_label = ctk.CTkLabel(
            self.log_frame,
            text="0 of 0 Achieved",
            font=("", 12, "bold"),
            justify="left",
            anchor="w",
        )
        self.log_ach_label.pack(padx=10)

        # LOG TREEVIEW
        self.check_var = ctk.StringVar(value="off")
        self.checkbox = ctk.CTkCheckBox(
            master=self.log_frame,
            text="Show only Unachieved?",
            command=self.checkbox_event,
            variable=self.check_var,
            onvalue="on",
            offvalue="off",
            checkbox_width=16,
            checkbox_height=16,
        )
        self.checkbox.pack(padx=10)

        self.log_tree = ttk.Treeview(master=self.log_frame)
        self.log_tree.tag_configure("oddrow", background="#252535")
        self.log_tree.tag_configure("evenrow", background="#252525")
        self.scrollbar = ttk.Scrollbar(
            self.log_tree, orient="vertical", command=self.log_tree.yview
        )
        self.log_tree.configure(yscrollcommand=self.scrollbar.set)

        self.log_tree["columns"] = ("one", "two", "epoch", "three", "four")
        self.log_tree.column("#0", width=110, minwidth=110, stretch=NO)
        self.log_tree.column("one", width=100, minwidth=100, stretch=YES)
        self.log_tree.column("two", width=100, minwidth=100, stretch=YES)
        self.log_tree.column("epoch", width=50, minwidth=50, stretch=YES)
        self.log_tree.column("three", width=400, minwidth=100, stretch=YES)
        self.log_tree.column("four", width=100, minwidth=100, stretch=YES)

        self.log_tree.heading("#0", text="Icon", anchor=W)
        self.log_tree.heading(
            "one",
            text="Name",
            anchor=W,
            command=lambda: self.col_sort("LOG", "one", False),
        )
        self.log_tree.heading(
            "two",
            text="Date Achieved",
            anchor=W,
            command=lambda: self.col_sort("LOG", "epoch", False),
        )
        self.log_tree.heading(
            "epoch",
            text="Unlock Time",
            anchor=W,
            command=lambda: self.col_sort("LOG", "epoch", False),
        )
        self.log_tree.heading(
            "three",
            text="Description",
            anchor=W,
        )
        self.log_tree.heading(
            "four",
            text="Global %",
            anchor=W,
        )

        self.log_tree.pack(side=TOP, fill=BOTH, expand=True, padx=5, pady=5)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.update_label = ctk.CTkLabel(
            self.log_frame,
            text=f"Last Update: Pending",
            font=("", 14, "bold"),
            justify="left",
            anchor="w",
        )
        self.update_label.pack(pady=(5, 5))

        # We want the default screen to be the GAME FRAME
        self.log_frame.forget()

        # GAME FRAME
        self.game_frame = FrameWindow(master=self.master, corner_radius=0)
        style = ttk.Style(self.game_frame)
        self.game_title = ctk.CTkLabel(
            self.game_frame, text="Steam Game List", font=("", 30, "bold")
        ).pack(padx=10, pady=(15, 5))
        self.stitle_label = ctk.CTkLabel(
            self.game_frame,
            text="Only games with achievements are shown.",
            font=("", 12, "bold"),
        ).pack(padx=10)
        self.stitle2_label = ctk.CTkLabel(
            self.game_frame,
            text="Clicking an item below will copy the Game ID to paste in the Settings Window.",
            font=("", 12, "bold"),
        ).pack(padx=10)

        style.theme_use(theme)
        style.configure(
            "Treeview", foreground="white", fieldbackground="#252525", rowheight=64
        )

        # GAME TREEVIEW
        self.game_tree = ttk.Treeview(master=self.game_frame)
        self.game_tree.tag_configure("oddrow", background="#252535")
        self.game_tree.tag_configure("evenrow", background="#252525")
        self.scrollbar = ttk.Scrollbar(
            self.game_tree, orient="vertical", command=self.game_tree.yview
        )
        self.game_tree.configure(yscrollcommand=self.scrollbar.set)
        self.game_tree["columns"] = ("one", "two", "three", "four")
        self.game_tree.column("#0", width=100, minwidth=100, stretch=NO)
        self.game_tree.column("one", width=100, minwidth=100, stretch=YES)
        self.game_tree.column("two", width=100, minwidth=100, stretch=YES)
        self.game_tree.column("three", width=100, minwidth=100, stretch=YES)
        self.game_tree.column("four", width=100, minwidth=100, stretch=YES)

        self.game_tree.heading(
            "#0",
            text="Icon",
            anchor=W,
        )
        self.game_tree.heading(
            "one",
            text="Name",
            anchor=W,
            command=lambda: self.col_sort("GAME", "one", False),
        )
        self.game_tree.heading(
            "two",
            text="Appplication ID",
            anchor=W,
            command=lambda: self.col_sort("GAME", "two", False),
        )
        self.game_tree.heading(
            "three",
            text="Total Playtime in mins (Since 2009)",
            anchor=W,
            command=lambda: self.col_sort("GAME", "three", False),
        )
        self.game_tree.heading(
            "four",
            text="Total Playtime Human",
            anchor=W,
        )

        self.game_tree.pack(side=TOP, fill=BOTH, expand=True, padx=5, pady=5)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.game_tree.bind("<ButtonRelease-1>", self.tree_click_handler)

    def tree_click_handler(self, event):
        cur_item = self.game_tree.item(self.game_tree.focus())
        col = self.game_tree.identify_column(event.x)
        if col == "#2":
            self.master.clipboard_clear()
            self.master.clipboard_append(cur_item["values"][1])
            print(cur_item["values"][1], "is being written to the config")
            creds = self.data.get_creds()
            old = creds["appid"]
            creds["appid"] = str(cur_item["values"][1])
            new = creds["appid"]
            self.data.configure_creds(creds)
            PopUp(old=old, new=new, game_name=cur_item["values"][0])
        self.game_tree.selection_remove(*self.game_tree.selection())

    def open_settings(self):
        log.info("(MainWindow) open_settings method called!")
        if self.settings is None or not self.settings.winfo_exists():
            self.settings = Settings("A-cheevo! - Settings", "480x240", steam=self.data)
            self.settings.resizable(width=False, height=False)
        else:
            self.settings.focus()

    def show_frame(self, frame):
        temp_frame = None
        if frame == "LOG":
            self.game_frame.forget()
            temp_frame = self.log_frame
        else:
            self.log_frame.forget()
            temp_frame = self.game_frame
        temp_frame.pack(fill=BOTH, expand=True)

    def checkbox_event(self):
        log.info("Checkbox toggled, current value: {}".format(self.check_var.get()))

    def col_sort(self, treeview_name, column, reverse: bool):
        # epoch
        try:
            if treeview_name == "LOG":
                print(f"column sort called for log, column={column}")

                data_list = [
                    (self.log_tree.set(k, column), k)
                    for k in self.log_tree.get_children("")
                ]

                if column == "epoch":
                    data_list = sorted(
                        data_list, key=lambda e: int(e[0]), reverse=reverse
                    )
                else:
                    data_list.sort(reverse=reverse)
                new_pos = 0
                for index, (val, k) in enumerate(data_list):
                    self.log_tree.item(
                        k,
                        tags=(self.get_tag(new_pos)),
                    )
                    self.log_tree.move(k, "", index)
                    new_pos += 1

                if column == "epoch":
                    self.log_tree.heading(
                        "two",
                        text=self.log_tree.heading("two")["text"],
                        command=lambda: self.col_sort("LOG", "two", not reverse),
                    )
                    self.log_tree.heading(
                        column,
                        text=self.log_tree.heading(column)["text"],
                        command=lambda: self.col_sort("LOG", column, not reverse),
                    )
                else:
                    self.log_tree.heading(
                        column,
                        text=self.log_tree.heading(column)["text"],
                        command=lambda: self.col_sort("LOG", column, not reverse),
                    )

            if treeview_name == "GAME":
                print(f"column sort called for game, column={column}")

                data_list = [
                    (self.game_tree.set(k, column), k)
                    for k in self.game_tree.get_children("")
                ]

                if column != "one":
                    data_list = sorted(
                        data_list, key=lambda e: int(e[0]), reverse=reverse
                    )
                else:
                    data_list.sort(reverse=reverse)

                new_pos = 0
                for index, (val, k) in enumerate(data_list):
                    self.game_tree.item(
                        k,
                        tags=(self.get_tag(new_pos)),
                    )
                    self.game_tree.move(k, "", index)
                    new_pos += 1

                self.game_tree.heading(
                    column,
                    text=self.game_tree.heading(column)["text"],
                    command=lambda: self.col_sort("GAME", column, not reverse),
                )
        except Exception as ex:
            log.error(f"Sort Broken: {ex}")

    @staticmethod
    def get_tag(pos):
        if pos % 2:
            return "evenrow"
        else:
            return "oddrow"

    def refresh_data(self):
        self.photo_images_cache.clear()
        self.restart_button.configure(state=DISABLED)
        self.master.config(cursor="clock")
        self.master.update()

        global datag
        position = 0
        log.info("Data Refreshing!")

        # CALL STEAM MODULE
        steam = Steam()
        data = steam.combine()
        datag = data

        # LOG WINDOW REFRESH
        self.log_game_label.configure(text=f"Game: {data['gamename']}")
        extra = (
            f"- {round(data['latest']['num_earned'] *100 / data['total'])}% Completion"
        )
        self.log_ach_label.configure(
            text=f"{data['latest']['num_earned']} of {data['total']} Achieved {extra}"
        )
        self.log_tree.delete(*self.log_tree.get_children())

        sorted_achs = data["achievements"]
        sorted_achs.sort(key=itemgetter("name"), reverse=True)
        sorted_achs.sort(key=itemgetter("unlocktime"), reverse=True)

        for achievement in sorted_achs:
            description = (
                "Hidden by Steam"
                if achievement["hidden"] == 1
                else achievement["description"]
            )
            icon_url = achievement["icon"]
            icon_hash = icon_url[icon_url.rfind("/") :].replace("/", "")
            icongurl = achievement["icongray"]
            icong_hash = icongurl[icongurl.rfind("/") :].replace("/", "")

            time = (
                dt.fromtimestamp(achievement["unlocktime"]).strftime("%c")
                if achievement["unlocktime"] != 0
                else "Not Achieved!"
            )

            if self.check_var.get() == "on":
                if time == "Not Achieved!":
                    file = "{}{}".format(grey_dir, icong_hash)
                    if os.path.exists(file):
                        image = Image.open(file)
                    else:
                        image = Image.open(broken_img)
                    imgg = image.resize((48, 48))
                    img = ImageTk.PhotoImage(imgg)
                    self.photo_images_cache.append(img)
                    image.close()

                    self.log_tree.insert(
                        parent="",
                        index=END,
                        text="",
                        image=img,
                        open=True,
                        values=[
                            achievement["displayName"],
                            str(time),
                            achievement["unlocktime"],
                            str(description),
                            f"{round(achievement['percentage'], 2)}%",
                        ],
                        tags=self.get_tag(position),
                    )
            else:
                if time != "Not Achieved!":
                    file = "{}{}".format(colour_dir, icon_hash)
                else:
                    file = "{}{}".format(grey_dir, icong_hash)

                if os.path.exists(file):
                    image = Image.open(file)
                else:
                    image = Image.open(broken_img)
                imgg = image.resize((48, 48))
                img = ImageTk.PhotoImage(imgg)
                self.photo_images_cache.append(img)
                image.close()

                self.log_tree.insert(
                    parent="",
                    index=END,
                    text="",
                    image=img,
                    open=True,
                    values=[
                        achievement["displayName"],
                        str(time),
                        achievement["unlocktime"],
                        str(description),
                        f"{round(achievement['percentage'], 2)}%",
                    ],
                    tags=self.get_tag(position),
                )
            position += 1
        self.update_label.configure(text=f"Last Update: {data['refresh_time']}")
        self.restart_button.configure(state=NORMAL)
        self.master.update()
        self.master.config(cursor="")
        self.master.after(30000, self.refresh_data)
        return steam

    def fill_games_list(self):
        self.photo_images_games_cache.clear()
        print("CLEARED")
        self.game_tree.delete(*self.game_tree.get_children())
        data = Steam().get_games_list()
        position = 0
        for i in data:
            image = Image.open("{}\{}.jpg".format(game_icons_dir, i["img_logo_url"]))
            imgg = image.resize((48, 48))
            img = ImageTk.PhotoImage(imgg)
            self.photo_images_games_cache.append(img)
            self.game_tree.insert(
                parent="",
                index=END,
                text="",
                image=img,
                open=True,
                values=[i["name"], i["appid"], i["playtime_forever"], i["time_played"]],
                tags=self.get_tag(pos=position),
            )
            position += 1

    def open_tracker(self):
        global display_open
        print("[INFO] open_display method called!")
        if display_open is None:
            self.tracker_button.configure(state=DISABLED)

            display_open = DisplayWindow(
                "A-cheevo! - Display",
                "720x480",
                colour="Green",
                master=self,
            )


if __name__ == "__main__":
    Main(root)
    root.mainloop()
