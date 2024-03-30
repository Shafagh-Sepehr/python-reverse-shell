# multiconn-server.py

import socket
import threading
from config import PORT, HEADER, PUBLIC_TERMINAL_FILLS_PERSONAL
import tkinter as tk
from tkinter import simpledialog, scrolledtext
import sys
import re
from typing import List
import os


HOST = socket.gethostbyname(socket.gethostname())
FORMAT = "UTF-8"


def strip_ansi_escape_sequences(text):
    regex = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return regex.sub("", text)


def wrap_data(data: str, mode: str):
    size = len(data) + 3
    new_data = mode + "<SEPARATOR>" + str(size) + "<SEPARATOR>" + data + "end"
    return new_data


class App:
    def __init__(self, root):
        self.root: tk.Tk = root
        self.root.title("Monitor")
        self.root.geometry("295x500")
        self.root.resizable(width=False, height=False)
        self.rows: List[Row] = []
        self.public_terminal_text = ""

        menu = tk.Menu(root)
        root.config(menu=menu)
        menu.add_command(label="to all", command=self.to_all)
        menu.add_command(label="sort", command=self.sort)
        menu.add_command(label="revsort", command=self.revsort)
        menu.add_command(label="refresh", command=self.refresh)

        self.canvas = tk.Canvas(root, bg="white", width=280, height=500)
        self.scrollbar = tk.Scrollbar(root, command=self.canvas.yview)
        self.frame = tk.Frame(self.canvas)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

    def add_row(self, name, conn):
        row = Row(self.frame, name, conn, self)
        row.pack(side=tk.TOP, fill=tk.X)
        self.rows.append(row)
        return row

    def to_all(self):
        Terminal(tk.Frame(), self)

    def sort(self):
        self.rows.sort(key=lambda row: row.name.get())
        for row in self.rows:
            row.pack_forget()
            row.pack(side=tk.TOP, fill=tk.X)

    def revsort(self):
        self.rows.sort(key=lambda row: row.name.get(), reverse=True)
        for row in self.rows:
            row.pack_forget()
            row.pack(side=tk.TOP, fill=tk.X)

    def refresh(self):
        dead_rows = []
        for row in self.rows:
            dead_row = row.check_alive()
            if dead_row != None:
                dead_rows.append(dead_row)
        for dead_row in dead_rows:
            self.rows.remove(dead_row)


class Row(tk.Frame):
    def __init__(self, master, name, conn, app):
        super().__init__(master)
        self.name = tk.StringVar()
        self.name.set(name)
        self.conn: socket.socket = conn
        self.app: App = app
        self.terminal_text = ""

        tk.Label(self, textvariable=self.name).pack(side=tk.LEFT)
        tk.Button(self, text="terminal", command=self.open_terminal).pack(side=tk.RIGHT)
        tk.Button(self, text="rename", command=self.rename_dialog).pack(side=tk.RIGHT)

    def rename_dialog(self):
        new_name = simpledialog.askstring("Rename", "Enter new name")
        if new_name is not None:
            self.rename(new_name)

    def rename(self, new_name):
        self.name.set(new_name)

    def open_terminal(self):
        Terminal(self, self.app, self.conn)

    def check_alive(self):
        send_data = wrap_data("", "norm")
        self.conn.sendall(send_data.encode(FORMAT))
        response = self.conn.recv(HEADER).decode(FORMAT)
        if not response:
            self.destroy()
            return self

    def make_path(self, file_name, dest):
        if os.path.exists(dest):
            if os.path.isdir(dest):
                if dest[:-1] == "/":
                    path = dest + file_name
                else:
                    path = dest + "/" + file_name
            else:
                path = dest
        else:
            if not dest:
                path = file_name
            else:
                path = dest
        return path

    def get_data(self, mode="norm", dest=None, name=None):
        whole_data = ""
        data = self.conn.recv(HEADER)
        if not data:
            return (whole_data, False)

        typ, size, rest = data.split("<SEPARATOR>".encode(FORMAT), 2)

        typ = typ.decode(FORMAT)
        size = int(size.decode(FORMAT))

        if mode == "norm":
            print("in norm")
            whole_data = rest.decode(FORMAT)
            ret_size = len(data)
            while size > ret_size:
                data = self.conn.recv(HEADER).decode(FORMAT)
                if not data:
                    return (whole_data, False)
                ret_size += len(data)
                whole_data += data
            return (whole_data[:-3], True)
        elif mode == "dwnl":
            file_name = typ.split("/")[-1]
            file_size = size

            response, rest = rest.split("<SEPARATOR>".encode(FORMAT), 1)

            if response.decode(FORMAT) == "err":
                return ("file download failed - No such file or directory", True)

            path: str = self.make_path(file_name, dest)
            if name:
                path_parts = path.rsplit("/", 1)
                parts = path_parts[-1].split(".", 1)
                if len(parts) == 1:
                    path += "_" + name
                else:
                    path = parts[0] + "_" + name + "." + parts[1]
                    if len(path_parts) > 1:
                        path = path_parts[0] + "/" + path

            ret_size = len(rest)
            try:
                with open(path, "wb") as f:
                    if rest:
                        f.write(rest)
                    while ret_size < file_size:

                        bytes_read = self.conn.recv(HEADER)
                        if not bytes_read:
                            return ("file download failed", False)
                        ret_size += len(bytes_read)
                        f.write(bytes_read)
                return ("file download was successful", True)
            except FileNotFoundError:
                while ret_size < file_size:
                    bytes_read = self.conn.recv(HEADER)
                    if not bytes_read:
                        return ("file download failed", False)
                    ret_size += len(bytes_read)
                return ("file download failed - No such file or directory", True)


class Terminal(tk.Toplevel):
    def __init__(self, master, app, conn=None):
        super().__init__(master)
        self.title("Terminal")
        self.conn: socket.socket = conn
        self.row: Row = master
        self.app: App = app

        self.text_area = scrolledtext.ScrolledText(self)
        self.text_area.config(width=75, height=25)
        self.text_area.pack(side="left", fill="both", expand=True)
        self.text_area.bind("<Return>", self.on_enter)

        self.read_area = scrolledtext.ScrolledText(self)
        self.read_area.config(width=75, height=25)
        self.read_area.pack(side="left", fill="both", expand=True)
        if self.conn:
            self.read_area.insert("end", self.row.terminal_text)
        else:
            self.read_area.insert("end", self.app.public_terminal_text)

        self.read_area.config(state="disabled")

        tk.Button(self, text="Send", command=self.on_send).pack()
        tk.Button(self, text="Clear", command=self.on_clear).pack()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.minsize(1300, 500)

    def upload(self, path, conn=None):
        if conn:
            connection = conn
        else:
            connection = self.conn

        file_size = os.path.getsize(path)
        send_data = path.split("/")[-1] + "<SEPARATOR>" + str(file_size) + "<SEPARATOR>"
        connection.sendall(send_data.encode(FORMAT))

        with open(path, "rb") as f:
            while True:
                bytes_read = f.read(HEADER)
                if not bytes_read:
                    break
                connection.sendall(bytes_read)

    def on_send(self):
        inp = self.text_area.get("0.0", "end")

        splits = inp.strip().split(" ", 2)
        if len(splits) < 3:
            dest = ""
        else:
            dest = splits[2]

        if splits[0] == "DOWNLOAD":
            data_to_send = wrap_data(splits[1], "dwnl")
        elif splits[0] == "UPLOAD":
            try:
                os.path.getsize(splits[1])
            except FileNotFoundError:
                if self.conn:
                    self.append_to_read_area("file download failed - No such file\n")
                else:
                    if PUBLIC_TERMINAL_FILLS_PERSONAL:
                        for row in self.app.rows:
                            row.terminal_text += "file download failed - No such file\n"
                    self.append_to_read_area("file download failed - No such file\n")

            data_to_send = wrap_data(dest, "upld")
        else:
            data_to_send = wrap_data(inp, "norm")

        if self.conn:
            self.conn.sendall(data_to_send.encode(FORMAT))

            if splits[0] == "DOWNLOAD":
                data, online = self.listen_for_answer("dwnl", dest)
            elif splits[0] == "UPLOAD":
                self.upload(splits[1])
                data, online = self.listen_for_answer("norm")
            else:
                data, online = self.listen_for_answer("norm")

            self.show_data(data)
            if not online:
                self.client_died()

        else:
            for row in self.app.rows:
                row.conn.sendall(data_to_send.encode(FORMAT))

                if splits[0] == "DOWNLOAD":
                    data, online = row.get_data("dwnl", dest, row.name.get())
                elif splits[0] == "UPLOAD":
                    self.upload(splits[1], row.conn)
                    data, online = row.get_data("norm")
                else:
                    data, online = row.get_data("norm")

                data = strip_ansi_escape_sequences(data)
                if PUBLIC_TERMINAL_FILLS_PERSONAL:
                    row.terminal_text += data + "\n"
                self.append_to_read_area("from " + row.name.get() + ":\n" + data)
                if not online:
                    self.destroy()
                    self.app.rows.remove(row)

    def on_clear(self):
        self.read_area.config(state="normal")
        self.read_area.delete("0.0", "end")
        self.read_area.config(state="disabled")

    def on_close(self):
        if self.conn:
            self.row.terminal_text = self.read_area.get("0.0", "end")
        else:
            self.app.public_terminal_text = self.read_area.get("0.0", "end")
        self.destroy()
        pass

    def on_enter(self, key):
        self.text_area.delete("end-1c")
        self.on_send()

    def append_to_read_area(self, str, *args):
        self.read_area.config(state="normal")
        self.read_area.insert("end", str)
        self.read_area.insert("end", "\n")
        self.read_area.insert("end", "----------------------------------------\n")
        self.read_area.config(state="disabled")

    def listen_for_answer(self, mode, dest=None):
        data, online = self.row.get_data(mode, dest)
        data = strip_ansi_escape_sequences(data)
        return data, online

    def show_data(self, data):
        self.append_to_read_area(data)

    def client_died(self):
        if self.conn:
            self.row.destroy()
            self.app.rows.remove(self.row)
            self.destroy()


class Server:
    def __init__(self, app):
        self.server: socket.socket = None
        self.app: App = app

    def start(self):
        print("[STARTING] server is starting...")
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with self.server:
            i = 0
            while True:
                try:
                    self.server.bind((HOST, PORT + i))
                    break
                except OSError:
                    i += 1
                    print("port occupied")

            self.server.listen()
            print(f"[LISTENING] Server is listening on {HOST}")
            conn_count = 1
            while True:

                conn, addr = self.server.accept()

                self.app.add_row(str(conn_count), conn)

                print(f"[ACTIVE CONNECTIONS] {conn_count}")
                conn_count += 1

    def begin_server(self):
        th = threading.Thread(target=self.start)
        th.daemon = True
        th.start()

    def close_server(self):
        self.server.close()


# server = None
def begin():
    root = tk.Tk()
    app = App(root)

    server = Server(app)

    server_th = threading.Thread(target=server.begin_server)
    server_th.daemon = True
    server_th.start()

    root.mainloop()
    print("closed")
    server.close_server()
    sys.exit()


begin()
