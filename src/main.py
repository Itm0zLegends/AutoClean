#!/usr/bin/env python3
import sys
import gi
import os
import gettext
import locale
import shutil

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GLib, Gdk

# =========================
# GETTEXT INITIALISATION
# =========================
APP_ID = "autoclean"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCALE_DIR = os.path.join(BASE_DIR, "..", "locale")

try:
    locale.setlocale(locale.LC_ALL, "")
except:
    pass
gettext.bindtextdomain(APP_ID, LOCALE_DIR)
gettext.textdomain(APP_ID)

# Utiliser un nom différent pour éviter les conflits
def _(message):
    return gettext.gettext(message)
# =========================


class AutoCleanApplication(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="fr.crowdev.AutoClean",
            flags=Gio.ApplicationFlags.NON_UNIQUE
        )
        self.current_theme = "system"
        self.auto_analyze = False

    def apply_theme(self, theme_choice):
        """Applique le thème sélectionné"""
        style_manager = Adw.StyleManager.get_default()
        window = self.get_active_window()

        if window:
            window.remove_css_class("oled")

        if theme_choice == "oled":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
            if window:
                window.add_css_class("oled")
        elif theme_choice == "dark":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        elif theme_choice == "light":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        else:
            style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)

        self.current_theme = theme_choice

    def load_css(self):
        """Charge le CSS personnalisé pour le mode OLED"""
        css_provider = Gtk.CssProvider()
        css = """
        .oled {
          background-color: #000000;
        }

        .oled window,
        .oled headerbar,
        .oled box,
        .oled preferenceswindow,
        .oled toolbar,
        .oled .toolbar-view {
          background-color: #000000;
        }

        .oled .boxed-list {
          background-color: #0a0a0a;
        }

        .oled label {
          color: #ffffff;
        }

        .oled button {
          background-color: #1a1a1a;
          border-color: #2a2a2a;
        }

        .oled button:hover {
          background-color: #2a2a2a;
        }

        .oled separator {
          background-color: #1a1a1a;
        }

        .oled .card,
        .oled row {
          background-color: #0a0a0a;
        }

        .oled .dim-label {
          color: #cccccc;
        }
        """
        css_provider.load_from_data(css.encode())

        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def open_settings(self, action=None, param=None):
        settings = Adw.PreferencesWindow(transient_for=self.get_active_window())
        settings.set_title(_("Paramètres"))
        settings.set_default_size(450, 500)

        # Page principale
        page = Adw.PreferencesPage()
        settings.add(page)

        # Groupe Apparence
        appearance_group = Adw.PreferencesGroup(
            title=_("Apparence"),
            description=_("Personnalisez l'apparence de l'application")
        )
        page.add(appearance_group)

        theme_row = Adw.ComboRow(
            title=_("Thème"),
            subtitle=_("Choisissez le thème de l'interface"),
            model=Gtk.StringList.new([
                _("Système"),
                _("Clair"),
                _("Sombre"),
                _("OLED")
            ]),
            selected=0 if self.current_theme == "system" else
                     1 if self.current_theme == "light" else
                     2 if self.current_theme == "dark" else 3
        )

        def on_theme_changed(row, param):
            choice = row.get_selected()
            themes = ["system", "light", "dark", "oled"]
            self.apply_theme(themes[choice])

        theme_row.connect("notify::selected", on_theme_changed)
        appearance_group.add(theme_row)

        # Groupe Comportement
        behavior_group = Adw.PreferencesGroup(
            title=_("Comportement"),
            description=_("Options de fonctionnement de l'application")
        )
        page.add(behavior_group)

        auto_analyze_row = Adw.ActionRow(
            title=_("Analyse automatique au démarrage"),
            subtitle=_("Lance l'analyse dès l'ouverture de l'application")
        )
        auto_analyze_switch = Gtk.Switch()
        auto_analyze_switch.set_active(self.auto_analyze)
        auto_analyze_switch.set_valign(Gtk.Align.CENTER)

        def on_auto_analyze_changed(switch, param):
            self.auto_analyze = switch.get_active()

        auto_analyze_switch.connect("notify::active", on_auto_analyze_changed)
        auto_analyze_row.add_suffix(auto_analyze_switch)
        auto_analyze_row.set_activatable_widget(auto_analyze_switch)
        behavior_group.add(auto_analyze_row)

        confirm_delete_row = Adw.ActionRow(
            title=_("Confirmation avant nettoyage"),
            subtitle=_("Demander confirmation pour toutes les catégories")
        )
        confirm_switch = Gtk.Switch()
        confirm_switch.set_active(True)
        confirm_switch.set_valign(Gtk.Align.CENTER)
        confirm_delete_row.add_suffix(confirm_switch)
        confirm_delete_row.set_activatable_widget(confirm_switch)
        behavior_group.add(confirm_delete_row)

        # Groupe Langue
        language_group = Adw.PreferencesGroup(
            title=_("Langue"),
            description=_("Sélectionnez la langue de l'interface")
        )
        page.add(language_group)

        language_row = Adw.ComboRow(
            title=_("Langue de l'interface"),
            model=Gtk.StringList.new([
                _("Automatique"),
                _("Français"),
                _("English")
            ]),
            selected=0
        )
        language_group.add(language_row)

        # Groupe Statistiques
        stats_group = Adw.PreferencesGroup(
            title=_("Statistiques")
        )
        page.add(stats_group)

        stats_row = Adw.ActionRow(
            title=_("Espace libéré au total"),
            subtitle=_("0 Go libérés depuis l'installation")
        )
        stats_group.add(stats_row)

        # Groupe À propos
        about_group = Adw.PreferencesGroup(
            title=_("À propos")
        )
        page.add(about_group)

        about_row = Adw.ActionRow(
            title=_("AutoClean"),
            subtitle=_("Version 1.0.0 – CrowDEV")
        )
        about_row.add_suffix(
            Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
        )
        about_group.add(about_row)

        github_row = Adw.ActionRow(
            title=_("Code source"),
            subtitle=_("Consulter le projet sur GitHub")
        )
        github_icon = Gtk.Image.new_from_icon_name("web-browser-symbolic")
        github_row.add_suffix(github_icon)
        about_group.add(github_row)

        settings.present()

    def do_activate(self):
        window = self.get_active_window()
        if window:
            window.present()
            return

        window = Adw.ApplicationWindow(application=self)
        window.set_title(_("AutoClean"))
        window.set_default_size(420, 550)

        # HeaderBar avec boutons
        header = Adw.HeaderBar()

        # Menu hamburger
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.set_tooltip_text(_("Menu principal"))
        header.pack_start(menu_button)

        # Menu actions
        menu = Gio.Menu()
        menu.append(_("Rafraîchir"), "app.refresh")
        menu.append(_("Paramètres"), "app.settings")
        menu.append(_("À propos"), "app.about")
        menu_button.set_menu_model(menu)

        # Actions
        refresh_action = Gio.SimpleAction.new("refresh", None)
        self.add_action(refresh_action)

        settings_action = Gio.SimpleAction.new("settings", None)
        settings_action.connect("activate", self.open_settings)
        self.add_action(settings_action)

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.show_about_dialog)
        self.add_action(about_action)

        # Contenu principal
        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(header)

        content = Adw.Clamp(
            margin_top=20,
            margin_bottom=20,
            margin_start=20,
            margin_end=20
        )

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        title = Gtk.Label(label=_("🧹 AutoClean"))
        title.add_css_class("title-1")
        title.set_halign(Gtk.Align.START)

        subtitle = Gtk.Label(
            label=_("Analyse et nettoyage sécurisé de votre système")
        )
        subtitle.add_css_class("dim-label")
        subtitle.set_halign(Gtk.Align.START)

        # Barre de progression
        progress_bar = Gtk.ProgressBar()
        progress_bar.set_visible(False)
        progress_bar.set_show_text(True)

        # Liste des catégories
        categories = [
            {"name": _("Cache utilisateur"), "path": "~/.cache", "checked": True},
            {"name": _("Fichiers temporaires"), "path": "/tmp", "checked": True},
            {"name": _("Logs utilisateur"), "path": "~/.local/share/logs", "checked": False},
            {"name": _("Miniatures GNOME"), "path": "~/.cache/thumbnails", "checked": True},
            {"name": _("Cache Flatpak"), "path": "~/.var/app", "checked": False},
            {"name": _("Téléchargements"), "path": "~/Téléchargements", "checked": False}
        ]

        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        listbox.add_css_class("boxed-list")

        rows_data = []

        for cat in categories:
            row = Adw.ActionRow()
            row.set_title(cat["name"])
            row.set_subtitle(_("Prêt pour l'analyse"))
            checkbox = Gtk.CheckButton()
            checkbox.set_active(cat["checked"])
            row.add_suffix(checkbox)
            listbox.append(row)

            rows_data.append({
                "row": row,
                "checkbox": checkbox,
                "category": cat
            })

        analyze_button = Gtk.Button(label=_("Analyser"))
        analyze_button.add_css_class("suggested-action")

        clean_button = Gtk.Button(label=_("Nettoyer"))
        clean_button.add_css_class("destructive-action")
        clean_button.set_sensitive(False)

        # Fonction d'analyse
        def on_analyze_clicked(button):
            button.set_sensitive(False)
            clean_button.set_sensitive(False)
            button.set_label(_("Analyse en cours..."))
            progress_bar.set_visible(True)
            progress_bar.set_fraction(0)

            total_categories = sum(1 for data in rows_data if data["checkbox"].get_active())
            current = 0

            for data in rows_data:
                row = data["row"]
                checkbox = data["checkbox"]
                cat = data["category"]

                if checkbox.get_active():
                    count, size = analyze_path(cat["path"])
                    row.set_subtitle(_("%d fichiers – %s") % (count, format_size(size)))
                    current += 1
                    if total_categories > 0:
                        progress_bar.set_fraction(current / total_categories)
                else:
                    row.set_subtitle(_("Non sélectionné"))

            button.set_label(_("Analyser"))
            button.set_sensitive(True)
            clean_button.set_sensitive(True)
            progress_bar.set_visible(False)

        # Fonction de nettoyage
        def on_clean_clicked(button):
            button.set_sensitive(False)
            analyze_button.set_sensitive(False)
            button.set_label(_("Nettoyage en cours..."))

            total_deleted = 0

            for data in rows_data:
                row = data["row"]
                checkbox = data["checkbox"]
                cat = data["category"]

                if checkbox.get_active():
                    if cat["name"] == _("Téléchargements"):
                        dialog = Adw.MessageDialog.new(window)
                        dialog.set_heading(_("Confirmer la suppression"))
                        dialog.set_body(_("Voulez-vous vraiment supprimer tous les fichiers du dossier Téléchargements ? Cette action est irréversible !"))
                        dialog.add_response("cancel", _("Annuler"))
                        dialog.add_response("delete", _("Supprimer"))
                        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
                        dialog.set_default_response("cancel")
                        dialog.set_close_response("cancel")

                        def on_dialog_response(dlg, response, data=data):
                            if response == "delete":
                                deleted = clean_path(data["category"]["path"])
                                data["row"].set_subtitle(_("✓ Nettoyé : %d fichiers supprimés") % deleted)
                                nonlocal total_deleted
                                total_deleted += deleted
                            else:
                                data["row"].set_subtitle(_("Annulé"))

                        dialog.connect("response", on_dialog_response)
                        dialog.present()
                    else:
                        deleted = clean_path(cat["path"])
                        row.set_subtitle(_("✓ Nettoyé : %d fichiers supprimés") % deleted)
                        total_deleted += deleted
                else:
                    row.set_subtitle(_("Non sélectionné"))

            button.set_label(_("Nettoyer"))
            button.set_sensitive(True)
            analyze_button.set_sensitive(True)

            subtitle.set_label(_("✓ Nettoyage terminé : %d fichiers supprimés") % total_deleted)

        analyze_button.connect("clicked", on_analyze_clicked)
        clean_button.connect("clicked", on_clean_clicked)

        button_box = Gtk.Box(spacing=6)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.append(analyze_button)
        button_box.append(clean_button)

        box.append(title)
        box.append(subtitle)
        box.append(Gtk.Separator())
        box.append(progress_bar)
        box.append(listbox)
        box.append(button_box)

        content.set_child(box)
        toolbar_view.set_content(content)
        window.set_content(toolbar_view)
        window.present()

        # Analyse automatique si activée
        if self.auto_analyze:
            GLib.timeout_add(500, lambda: analyze_button.emit("clicked") or False)

    def show_about_dialog(self, action=None, param=None):
        """Affiche la boîte de dialogue À propos"""
        about = Adw.AboutWindow(
            transient_for=self.get_active_window(),
            application_name=_("AutoClean"),
            application_icon="fr.crowdev.AutoClean",
            developer_name="CrowDEV",
            version="1.0.0",
            website="https://github.com/crowdev/autoclean",
            issue_url="https://github.com/crowdev/autoclean/issues",
            copyright="© 2025 CrowDEV",
            license_type=Gtk.License.GPL_3_0,
            developers=["CrowDEV"]
        )
        about.present()

    def do_startup(self):
        Adw.Application.do_startup(self)
        self.load_css()


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
        return 0

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
        return "%.2f Go" % (size_bytes / 1_000_000_000)
    elif size_bytes >= 1_000_000:
        return "%.2f Mo" % (size_bytes / 1_000_000)
    elif size_bytes >= 1000:
        return "%.2f Ko" % (size_bytes / 1000)
    else:
        return "%d o" % size_bytes


def main(version=None):
    app = AutoCleanApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
