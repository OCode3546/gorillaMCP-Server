"""__APP_TITLE__ — desktop app (Tkinter).

__APP_DESCRIPTION__
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from store import Store

APP_TITLE = "__APP_TITLE__"
APP_VERSION = "0.1.0"


class App(ttk.Frame):
    def __init__(self, root: tk.Tk, store: Store | None = None) -> None:
        super().__init__(root, padding=8)
        self.root = root
        self.store = store or Store()
        self.current_id: str | None = None
        self.search_var = tk.StringVar()
        self.title_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")

        root.title(APP_TITLE)
        root.geometry("900x560")
        root.minsize(600, 380)
        self.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        self._build_menu()
        self._build_ui()
        self._bind_keys()
        self.refresh_list()

    # ------------------------------------------------------------ layout

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="New", accelerator="Ctrl+N", command=self.on_new)
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.on_save)
        file_menu.add_command(label="Export…", command=self.on_export)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", accelerator="Ctrl+Q", command=self.root.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label=f"About {APP_TITLE}", command=self.on_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menubar)

    def _build_ui(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Sidebar: search + list
        sidebar = ttk.Frame(self)
        sidebar.grid(row=0, column=0, sticky="nsw", padx=(0, 8))
        sidebar.rowconfigure(1, weight=1)

        search = ttk.Entry(sidebar, textvariable=self.search_var)
        search.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        self.search_var.trace_add("write", lambda *_: self.refresh_list())

        self.listbox = tk.Listbox(sidebar, width=28, activestyle="none", exportselection=False)
        self.listbox.grid(row=1, column=0, sticky="ns")
        scroll = ttk.Scrollbar(sidebar, orient="vertical", command=self.listbox.yview)
        scroll.grid(row=1, column=1, sticky="ns")
        self.listbox.config(yscrollcommand=scroll.set)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        buttons = ttk.Frame(sidebar)
        buttons.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        ttk.Button(buttons, text="New", command=self.on_new).pack(side="left", expand=True, fill="x")
        ttk.Button(buttons, text="Delete", command=self.on_delete).pack(side="left", expand=True, fill="x", padx=(6, 0))

        # Editor: title + body
        editor = ttk.Frame(self)
        editor.grid(row=0, column=1, sticky="nsew")
        editor.columnconfigure(0, weight=1)
        editor.rowconfigure(1, weight=1)

        ttk.Entry(editor, textvariable=self.title_var, font=("TkDefaultFont", 14)).grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self.body = tk.Text(editor, wrap="word", undo=True, padx=8, pady=8)
        self.body.grid(row=1, column=0, sticky="nsew")
        ttk.Button(editor, text="Save", command=self.on_save).grid(row=2, column=0, sticky="e", pady=(6, 0))

        ttk.Label(self, textvariable=self.status_var, anchor="w").grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))

    def _bind_keys(self) -> None:
        mod = "Command" if self.root.tk.call("tk", "windowingsystem") == "aqua" else "Control"
        self.root.bind_all(f"<{mod}-n>", lambda e: self.on_new())
        self.root.bind_all(f"<{mod}-s>", lambda e: self.on_save())
        self.root.bind_all(f"<{mod}-q>", lambda e: self.root.destroy())

    # ------------------------------------------------------------ helpers

    def refresh_list(self) -> None:
        self.visible = self.store.search(self.search_var.get())
        self.listbox.delete(0, "end")
        for item in self.visible:
            self.listbox.insert("end", item.title)
        if self.current_id:
            for index, item in enumerate(self.visible):
                if item.id == self.current_id:
                    self.listbox.selection_set(index)
        self.status_var.set(f"{len(self.store.items)} items · data: {self.store.path}")

    def load_editor(self, title: str, body: str) -> None:
        self.title_var.set(title)
        self.body.delete("1.0", "end")
        self.body.insert("1.0", body)

    # ------------------------------------------------------------ handlers

    def on_select(self, _event=None) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        item = self.visible[selection[0]]
        self.current_id = item.id
        self.load_editor(item.title, item.body)

    def on_new(self) -> None:
        item = self.store.add("Untitled")
        self.current_id = item.id
        self.search_var.set("")
        self.refresh_list()
        self.load_editor(item.title, item.body)
        self.status_var.set("Created a new item")

    def on_save(self) -> None:
        title, body = self.title_var.get(), self.body.get("1.0", "end-1c")
        if self.current_id is None:
            self.current_id = self.store.add(title, body).id
        else:
            self.store.update(self.current_id, title, body)
        self.refresh_list()
        self.status_var.set("Saved")

    def on_delete(self) -> None:
        if self.current_id is None:
            return
        if not messagebox.askyesno(APP_TITLE, "Delete this item?"):
            return
        self.store.delete(self.current_id)
        self.current_id = None
        self.load_editor("", "")
        self.refresh_list()
        self.status_var.set("Deleted")

    def on_export(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as fh:
            for item in self.store.items:
                fh.write(f"# {item.title}\n\n{item.body}\n\n")
        self.status_var.set(f"Exported to {path}")

    def on_about(self) -> None:
        messagebox.showinfo(f"About {APP_TITLE}", f"{APP_TITLE} {APP_VERSION}\n\n__APP_DESCRIPTION__")


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
