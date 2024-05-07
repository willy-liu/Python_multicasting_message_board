import socket
import struct
import tkinter as tk
from tkinter import messagebox
import json
import threading

class MessageBoard:
    def __init__(self, master):
        self.master = master
        self.master.title("Message Board Publisher")

        self.window_closed = False

        # 界面佈局
        self.frame = tk.Frame(self.master)
        self.frame.pack(padx=10, pady=10)

        # 新增主題
        tk.Label(self.frame, text="Add New Topic:").grid(row=0, column=0)
        self.topic_entry = tk.Entry(self.frame)
        self.topic_entry.grid(row=0, column=1)
        self.add_topic_button = tk.Button(self.frame, text="Add Topic", command=self.add_topic)
        self.add_topic_button.grid(row=0, column=3)

        # 選擇主題
        tk.Label(self.frame, text="Select Topic:").grid(row=1, column=0)
        self.topic_var = tk.StringVar(self.frame)
        self.topic_option_menu = tk.OptionMenu(self.frame, self.topic_var, "")
        self.topic_option_menu.grid(row=1, column=1, columnspan=2)

        # delete selected topic
        self.delete_topic_button = tk.Button(self.frame, text="Delete Topic", command=self.delete_topic)
        self.delete_topic_button.grid(row=1, column=3)

        # 發送訊息
        tk.Label(self.frame, text="Message:").grid(row=2, column=0)
        self.message_entry = tk.Entry(self.frame)
        self.message_entry.grid(row=2, column=1)
        self.send_button = tk.Button(self.frame, text="Send", command=self.send_message)
        self.send_button.grid(row=2, column=3)

        # 訊息歷史面板
        self.message_history = tk.Listbox(self.frame, height=10, width=50)
        self.message_history.grid(row=3, column=0, columnspan=4, sticky="w", pady=10)
        self.messages = []

        # 主題和地址字典
        self.topics = {
            'sports': ('224.0.0.1', 5004),
            'news': ('224.0.0.2', 5005),
            'technology': ('224.0.0.3', 5006)
        }
        self.update_option_menu()

        # 創建一個服務器 socket 來接收客戶端訊息
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind(("localhost", 5003))  # 使用一個新的端口來接收客戶端訊息
        self.server_socket.settimeout(3)  # Set timeout to catch KeyboardInterrupt
        def handle_client_messages(self):
            """處理來自客戶端的訊息"""
            try:
                while True:
                    try:
                        data, addr = self.server_socket.recvfrom(1024)
                        self.server_socket.sendto(json.dumps(self.topics).encode('utf-8'), addr)
                    except socket.timeout:
                        if self.window_closed:
                            raise KeyboardInterrupt()
            except KeyboardInterrupt:
                pass
            finally:
                self.server_socket.close()
        client_thread = threading.Thread(target=handle_client_messages, args=(self, ))
        client_thread.start()

    def update_option_menu(self):
        menu = self.topic_option_menu["menu"]
        menu.delete(0, "end")
        for topic in self.topics:
            menu.add_command(label=topic, command=lambda value=topic: self.topic_var.set(value))
        if self.topics:
            self.topic_var.set(list(self.topics.keys())[0])
        else:
            self.topic_var.set('')

    def add_topic(self):
        new_topic = self.topic_entry.get()
        if new_topic:
            if new_topic in self.topics:
                messagebox.showerror("Error", "Topic already exists.")
                return
            ip_end = len(self.topics) + 1
            new_address = (f'224.0.0.{ip_end}', 5003 + ip_end)
            self.topics[new_topic] = new_address
            self.update_option_menu()
            self.topic_entry.delete(0, 'end')
            self.topic_var.set(new_topic)

    def delete_topic(self):
        topic = self.topic_var.get()
        if topic and topic in self.topics:
            multicast_group = self.topics[topic]
            del self.topics[topic]
            self.update_option_menu()
            self.multicast_message(topic, multicast_group, f"Topic '{topic}' has been deleted.")
        else:
            messagebox.showerror("Error", "Please select a valid topic to delete.")

    def send_message(self):
        topic = self.topic_var.get()
        message = self.message_entry.get()
        if topic and message:
            multicast_group = self.topics[topic]
            self.multicast_message(topic, multicast_group, message)
            # 添加消息到歷史面板
            msg_record = f"Send to {topic}: {message}"
            self.messages.append(msg_record)
            if len(self.messages) > 10:
                self.messages.pop(0)  # 維持最多10條記錄
            self.update_message_history()
            self.message_entry.delete(0, 'end')
        else:
            messagebox.showerror("Error", "Please select a topic and enter a message.")

    def update_message_history(self):
        self.message_history.delete(0, tk.END)
        for msg in self.messages:
            self.message_history.insert(tk.END, msg)

    def multicast_message(self, topic, multicast_group, message):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ttl = struct.pack('b', 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        try:
            print(f"Sending message to topic {topic}: {message}")
            sock.sendto(message.encode(), multicast_group)
        finally:
            sock.close()

    def on_close(self):
        """Handle the window closing event."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.master.destroy()  # Destroy the main window
            self.window_closed = True

if __name__ == "__main__":
    root = tk.Tk()
    app = MessageBoard(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)  # Attach the close handler
    root.mainloop()
