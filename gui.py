import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime, timezone, timedelta
import threading
from analyzer import analyze_logs

# =========================
# Variables globales
# =========================
current_file = None
date_min = None
date_max = None
last_results = None

# =========================
# Utilitaires
# =========================
def parse_top_value(value):
    value = value.strip().lower()
    if value == "" or value == "all":
        return None
    if value.isdigit():
        return int(value)
    raise ValueError("Valeur invalide (nombre ou 'all')")

def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Format date invalide (YYYY-MM-DD)")

def parse_time(value):
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        raise ValueError("Format heure invalide (HH:MM)")

# =========================
# Logique applicative
# =========================
def select_file():
    global current_file, date_min, date_max, last_results

    file_path = filedialog.askopenfilename(
        title="Sélectionner un fichier de logs CSV",
        filetypes=[("CSV", "*.csv"), ("Tous les fichiers", "*.*")]
    )
    if not file_path:
        return

    current_file = file_path
    output_text.delete("1.0", tk.END)
    log_count_label.config(text="Lignes trouvées : …")
    output_text.insert(tk.END, "⏳ Analyse du fichier...\n")
    progress.pack(pady=5)
    progress.start(10)

    threading.Thread(target=load_file, daemon=True).start()

def load_file():
    global date_min, date_max, last_results
    try:
        results = analyze_logs(current_file)
        logs_per_ip, ips_per_domain, activity_per_time, ips_per_category, date_min, date_max = results
        last_results = (logs_per_ip, ips_per_domain, activity_per_time, ips_per_category)

        root.after(0, init_date_time_entries)
        root.after(0, apply_options)
    except Exception as e:
        root.after(0, show_error, str(e))

def init_date_time_entries():
    entry_date_start.delete(0, tk.END)
    entry_date_end.delete(0, tk.END)
    entry_time_start.delete(0, tk.END)
    entry_time_end.delete(0, tk.END)

    entry_date_start.insert(0, date_min.strftime("%Y-%m-%d"))
    entry_date_end.insert(0, date_max.strftime("%Y-%m-%d"))
    entry_time_start.insert(0, "00:00")
    entry_time_end.insert(0, "23:59")

def apply_options():
    if not current_file:
        messagebox.showwarning("Aucun fichier", "Veuillez sélectionner un fichier.")
        return

    try:
        top_ip = parse_top_value(entry_top_ip.get())
        top_domain = parse_top_value(entry_top_domain.get())
        top_category = parse_top_value(entry_top_category.get())

        start_date = parse_date(entry_date_start.get())
        end_date = parse_date(entry_date_end.get())
        start_time = parse_time(entry_time_start.get())
        end_time = parse_time(entry_time_end.get())

        # Correction ici pour que tzinfo soit appliqué
        start_datetime = datetime.combine(start_date, start_time).replace(tzinfo=timezone.utc)
        end_datetime = datetime.combine(end_date, end_time).replace(tzinfo=timezone.utc)

        progress.pack(pady=5)
        progress.start(10)

        threading.Thread(
            target=run_filtered_analysis,
            args=(start_datetime, end_datetime, top_ip, top_domain, top_category),
            daemon=True
        ).start()
    except Exception as e:
        show_error(str(e))

def run_filtered_analysis(start_datetime, end_datetime, top_ip, top_domain, top_category):
    try:
        results = analyze_logs(
            current_file,
            start_date=start_datetime,
            end_date=end_datetime
        )
        logs_per_ip, ips_per_domain, activity_per_time, ips_per_category, _, _ = results
        results_to_display = (logs_per_ip, ips_per_domain, activity_per_time, ips_per_category)

        # Mettre à jour le label du nombre de lignes
        total_logs = sum(logs_per_ip.values())
        root.after(0, lambda: log_count_label.config(text=f"Lignes trouvées : {total_logs}"))

        root.after(
            0,
            lambda: display_results(results_to_display, top_ip, top_domain, top_category)
        )
    except Exception as e:
        root.after(0, show_error, str(e))

def display_results(results, top_ip, top_domain, top_category):
    progress.stop()
    progress.pack_forget()

    logs_per_ip, ips_per_domain, activity_per_time, ips_per_category = results

    output_text.delete("1.0", tk.END)

    # Logs par IP
    output_text.insert(tk.END, "📊 Logs par IP source\n" + "-" * 60 + "\n")
    for ip, count in logs_per_ip.most_common(top_ip):
        output_text.insert(tk.END, f"{ip} : {count}\n")

    # IP distinctes par domaine
    output_text.insert(tk.END, "\n🌐 IP distinctes par domaine\n" + "-" * 60 + "\n")
    domains = sorted(ips_per_domain.items(), key=lambda x: len(x[1]), reverse=True)
    if top_domain:
        domains = domains[:top_domain]
    for domain, ips in domains:
        output_text.insert(tk.END, f"{domain} : {len(ips)}\n")

    # IP distinctes par catégorie
    output_text.insert(tk.END, "\n🏷️ IP distinctes par catégorie\n" + "-" * 60 + "\n")
    categories = sorted(ips_per_category.items(), key=lambda x: len(x[1]), reverse=True)
    if top_category:
        categories = categories[:top_category]
    for category, ips in categories:
        output_text.insert(tk.END, f"{category} : {len(ips)}\n")

    # Pic d'activité
    if activity_per_time:
        peak_time, peak_count = activity_per_time.most_common(1)[0]
        output_text.insert(tk.END, f"\n🔥 Pic d’activité : {peak_time} ({peak_count})\n")


    output_text.insert(tk.END, "\n✅ Analyse terminée\n")

def show_error(message):
    progress.stop()
    progress.pack_forget()
    messagebox.showerror("Erreur", message)

# ----- Réinitialiser options -----
def reset_options():
    entry_top_ip.delete(0, tk.END)
    entry_top_ip.insert(0, "all")

    entry_top_domain.delete(0, tk.END)
    entry_top_domain.insert(0, "all")

    entry_top_category.delete(0, tk.END)
    entry_top_category.insert(0, "all")

    if date_min and date_max:
        entry_date_start.delete(0, tk.END)
        entry_date_start.insert(0, date_min.strftime("%Y-%m-%d"))

        entry_date_end.delete(0, tk.END)
        entry_date_end.insert(0, date_max.strftime("%Y-%m-%d"))

        entry_time_start.delete(0, tk.END)
        entry_time_start.insert(0, "00:00")
        entry_time_end.delete(0, tk.END)
        entry_time_end.insert(0, "23:59")

# =========================
# Interface graphique
# =========================
root = tk.Tk()
root.title("Analyseur automatique de logs CSV")
root.geometry("1200x800")

# ----- Frame haut pour sélection + options -----
top_frame = tk.Frame(root)
top_frame.pack(fill="x", padx=10, pady=10)

# Zone compteur de logs
log_count_label = tk.Label(top_frame, text="Lignes trouvées : 0", font=("Arial", 12, "bold"))
log_count_label.pack(anchor="e", pady=2)

# Sélection fichier + barre de chargement
left_frame = tk.Frame(top_frame)
left_frame.pack(side="top", anchor="nw", fill="x")

tk.Label(left_frame, text="Analyse automatisée de logs CSV",
         font=("Arial", 16, "bold")).pack(anchor="w")
tk.Button(left_frame, text="📂 Sélectionner un fichier",
          font=("Arial", 12), command=select_file).pack(anchor="w", pady=5)

# Barre de chargement
progress = ttk.Progressbar(left_frame, mode="indeterminate", length=400)

# Options horizontales
options_frame = tk.Frame(left_frame)
options_frame.pack(anchor="w", pady=10, fill="x")

tk.Label(options_frame, text="Top IP:").grid(row=0, column=0, padx=5)
entry_top_ip = tk.Entry(options_frame, width=6)
entry_top_ip.insert(0, "all")
entry_top_ip.grid(row=0, column=1, padx=5)

tk.Label(options_frame, text="Top Domaines:").grid(row=0, column=2, padx=5)
entry_top_domain = tk.Entry(options_frame, width=6)
entry_top_domain.insert(0, "all")
entry_top_domain.grid(row=0, column=3, padx=5)

tk.Label(options_frame, text="Top Catégories:").grid(row=0, column=4, padx=5)
entry_top_category = tk.Entry(options_frame, width=6)
entry_top_category.insert(0, "all")
entry_top_category.grid(row=0, column=5, padx=5)

tk.Label(options_frame, text="Date début:").grid(row=0, column=6, padx=5)
entry_date_start = tk.Entry(options_frame, width=10)
entry_date_start.grid(row=0, column=7, padx=5)

tk.Label(options_frame, text="Heure début:").grid(row=0, column=8, padx=5)
entry_time_start = tk.Entry(options_frame, width=6)
entry_time_start.grid(row=0, column=9, padx=5)

tk.Label(options_frame, text="Date fin:").grid(row=0, column=10, padx=5)
entry_date_end = tk.Entry(options_frame, width=10)
entry_date_end.grid(row=0, column=11, padx=5)

tk.Label(options_frame, text="Heure fin:").grid(row=0, column=12, padx=5)
entry_time_end = tk.Entry(options_frame, width=6)
entry_time_end.grid(row=0, column=13, padx=5)

tk.Button(options_frame, text="✅ Appliquer",
          command=apply_options).grid(row=0, column=14, padx=5)
tk.Button(options_frame, text="♻️ Réinitialiser",
          command=reset_options).grid(row=0, column=15, padx=5)

# ----- Zone texte résultats -----
text_frame = tk.Frame(root)
text_frame.pack(expand=True, fill="both", padx=10, pady=10)

scrollbar = tk.Scrollbar(text_frame)
scrollbar.pack(side="right", fill="y")

output_text = tk.Text(text_frame, wrap="word",
                      font=("Consolas", 10),
                      yscrollcommand=scrollbar.set)
output_text.pack(side="left", expand=True, fill="both")

scrollbar.config(command=output_text.yview)

root.mainloop()

