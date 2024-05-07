import tkinter as tk
from tkinter import messagebox, Toplevel, Listbox
import socket
import struct
import threading
import json

class MessageSubscriber:
    def __init__(self, master):
        self.master = master
        self.master.title("Message Board Subscriber")

        self.frame = tk.Frame(self.master)
        self.frame.pack(padx=10, pady=10)

        self.subscription_id = 0

        # Topic selection
        self.topic_label = tk.Label(self.frame, text="Select Topic:")
        self.topic_label.pack(side=tk.TOP)

        self.topic_var = tk.StringVar(self.frame)
        self.topic_option_menu = tk.OptionMenu(self.frame, self.topic_var, "")
        self.topic_option_menu.pack(side=tk.TOP, fill=tk.X)

        self.subscribe_button = tk.Button(self.frame, text="Subscribe", command=self.open_subscription_window)
        self.subscribe_button.pack(side=tk.TOP, pady=5)

        self.refresh_button = tk.Button(self.frame, text="Refresh Topics", command=self.fetch_topics)
        self.refresh_button.pack(side=tk.TOP)

        self.topics = {}
        self.fetch_topics()

    # fetch topics use udp
    def fetch_topics(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.settimeout(2)
                request_message = "Requesting Topics"
                sock.sendto(request_message.encode(), ("localhost", 5003))
                data, addr = sock.recvfrom(1024)
                self.topics = json.loads(data.decode())
                self.update_option_menu()
        except:
            messagebox.showerror("Error", "Failed to connect to the server.")

    # update option menu
    def update_option_menu(self):
        menu = self.topic_option_menu["menu"]
        menu.delete(0, "end")
        for topic in self.topics:
            menu.add_command(label=topic, command=lambda value=topic: self.topic_var.set(value))
        if self.topics:
            self.topic_var.set(list(self.topics.keys())[0])
        else:
            self.topic_var.set('')

    # according selected topics open a new subcription window
    def open_subscription_window(self):
        topic = self.topic_var.get()
        self.subscription_id += 1
        if topic:
            SubscriptionWindow(self.master, self.subscription_id, topic, self.topics[topic])
        else:
            messagebox.showinfo("Error", "No topic selected.")

# a subscription window
class SubscriptionWindow:
    def __init__(self, master, id, topic, multicast_group):
        self.window = Toplevel(master)
        self.window.title(f"Subscription{id}: {topic}({multicast_group[0]}:{multicast_group[1]})")

        self.message_list = Listbox(self.window, width=60, height=10)
        self.message_list.pack(padx=10, pady=10)

        self.topic = topic
        self.multicast_group = multicast_group
        self.messages = []

        # use thread to allow multiple subscription windows.
        thread = threading.Thread(target=self.receive_messages)
        thread.setDaemon(True)
        thread.start()

    def receive_messages(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', self.multicast_group[1]))
            mreq = struct.pack("4sl", socket.inet_aton(self.multicast_group[0]), socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            try:
                while True:
                    data, _ = sock.recvfrom(1024)
                    message = data.decode()
                    self.messages.append(message)
                    if len(self.messages) > 10:
                        self.messages.pop(0)
                    self.update_message_list()
            finally:
                sock.close()
        except:
            messagebox.showinfo("An Error occured while binding multicast group")

    def update_message_list(self):
        self.message_list.delete(0, tk.END)
        for msg in self.messages:
            self.message_list.insert(tk.END, msg)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("350x150")
    app = MessageSubscriber(root)
    root.mainloop()
