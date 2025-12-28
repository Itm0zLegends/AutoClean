#!/usr/bin/env python3
import sys
import gi
import os
import shutil
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GLib

class AutoCleanApplication(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="org.gnome.AutoClean",
            flags=Gio.ApplicationFlags.NON_UNIQUE
        )

    def do_activate(self):
        window = self.get_active_window()
        if window:
            window.present()
            return

        window = Adw.ApplicationWindow(application=self)
        window.set_title("AutoClean")
        window.set_default_size(420, 500)

        # HeaderBar Adwaita
        header = Adw.HeaderBar()

        # Contenu principal dans une ToolbarView
        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(header)

        content = Adw.Clamp(
            margin_top=20,
            margin_bottom=20,
            margin_start=20,
            margin_end=20
        )

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        title = Gtk.Label(label="🧹 AutoClean")
        title.add_css_class("title-1")
        title.set_halign(Gtk.Align.START)

        subtitle = Gtk.Label(
            label="Analyse et nettoyage sécurisé de votre système"
        )
        subtitle.add_css_class("dim-label")
        subtitle.set_halign(Gtk.Align.START)

        # Liste des catégories
        categories = [
            {"name": "Cache utilisateur", "path": "~/.cache", "checked": True},
            {"name": "Fichiers temporaires", "path": "/tmp", "checked": True},
            {"name": "Logs utilisateur", "path": "~/.local/share/logs", "checked": False},
            {"name": "Miniatures GNOME", "path": "~/.cache/thumbnails", "checked": True},
            {"name": "Cache Flatpak", "path": "~/.var/app", "checked": False}
        ]

        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        listbox.add_css_class("boxed-list")

        # Stocker les rows avec leurs données
        rows_data = []

        for cat in categories:
            row = Adw.ActionRow()
            row.set_title(cat["name"])
            row.set_subtitle("Prêt pour l'analyse")
            checkbox = Gtk.CheckButton()
            checkbox.set_active(cat["checked"])
            row.add_suffix(checkbox)
            listbox.append(row)

            # Stocker la row, checkbox et catégorie ensemble
            rows_data.append({
                "row": row,
                "checkbox": checkbox,
                "category": cat
            })

        analyze_button = Gtk.Button(label="Analyser")
        analyze_button.add_css_class("suggested-action")

        clean_button = Gtk.Button(label="Nettoyer")
        clean_button.add_css_class("destructive-action")
        clean_button.set_sensitive(False)

        # Fonction d'analyse au clic
        def on_analyze_clicked(button):
            button.set_sensitive(False)
            clean_button.set_sensitive(False)
            button.set_label("Analyse en cours...")

            # Parcourir les données stockées
            for data in rows_data:
                row = data["row"]
                checkbox = data["checkbox"]
                cat = data["category"]

                if checkbox.get_active():
                    count, size = analyze_path(cat["path"])
                    row.set_subtitle(f"{count} fichiers – {format_size(size)}")
                else:
                    row.set_subtitle("Non sélectionné")

            button.set_label("Analyser")
            button.set_sensitive(True)
            clean_button.set_sensitive(True)

        # Fonction de nettoyage
        def on_clean_clicked(button):
            button.set_sensitive(False)
            analyze_button.set_sensitive(False)
            button.set_label("Nettoyage en cours...")

            total_deleted = 0
            for data in rows_data:
                row = data["row"]
                checkbox = data["checkbox"]
                cat = data["category"]

                if checkbox.get_active():
                    deleted = clean_path(cat["path"])
                    row.set_subtitle(f"✓ Nettoyé : {deleted} fichiers supprimés")
                    total_deleted += deleted
                else:
                    row.set_subtitle("Non sélectionné")

            button.set_label("Nettoyer")
            button.set_sensitive(True)
            analyze_button.set_sensitive(True)

            # Afficher un message de succès
            subtitle.set_label(f"✓ Nettoyage terminé : {total_deleted} fichiers supprimés")

        analyze_button.connect("clicked", on_analyze_clicked)
        clean_button.connect("clicked", on_clean_clicked)

        button_box = Gtk.Box(spacing=6)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.append(analyze_button)
        button_box.append(clean_button)

        box.append(title)
        box.append(subtitle)
        box.append(Gtk.Separator())
        box.append(listbox)
        box.append(button_box)

        content.set_child(box)
        toolbar_view.set_content(content)
        window.set_content(toolbar_view)
        window.present()

def analyze_path(path):
    """Retourne le nombre de fichiers et la taille totale en octets"""
    total_size = 0
    file_count = 0
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return file_count, total_size

    for root, dirs, files in os.walk(path):
        for f in files:
            try:
                fp = os.path.join(root, f)
                total_size += os.path.getsize(fp)
                file_count += 1
            except Exception:
                pass
    return file_count, total_size

def clean_path(path):
    """Supprime tous les fichiers et dossiers d'un chemin"""
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return 0  # rien à supprimer

    deleted_files = 0
    for root, dirs, files in os.walk(path, topdown=False):
        for f in files:
            try:
                os.remove(os.path.join(root, f))
                deleted_files += 1
            except Exception:
                pass
        for d in dirs:
            try:
                shutil.rmtree(os.path.join(root, d))
            except Exception:
                pass
    return deleted_files

def format_size(size_bytes):
    if size_bytes >= 1_000_000_000:
        return f"{size_bytes / 1_000_000_000:.2f} Go"
    elif size_bytes >= 1_000_000:
        return f"{size_bytes / 1_000_000:.2f} Mo"
    elif size_bytes >= 1000:
        return f"{size_bytes / 1000:.2f} Ko"
    else:
        return f"{size_bytes} o"

def main(version=None):
    app = AutoCleanApplication()
    return app.run(sys.argv)

if __name__ == "__main__":
    sys.exit(main())
