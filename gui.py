import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from analyzer import analyze_logs

# =========================
# Variables globales
# =========================

last_results = None  # Stocke les résultats de la dernière analyse


# =========================
# Utilitaires
# =========================

def parse_top_value(value):
    value = value.strip().lower()

    if value == "" or value == "all":
        return None

    if value.isdigit():
        return int(value)

    raise ValueError("Valeur invalide (utiliser un nombre ou 'all')")


# =========================
# Logique applicative
# =========================

def select_file():
    global last_results

    file_path = filedialog.askopenfilename(
        title="Sélectionner un fichier de logs CSV",
        filetypes=[
            ("Fichiers CSV", "*.csv"),
            ("Tous les fichiers", "*.*")
        ]
    )

    if not file_path:
        return

    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, "⏳ Analyse en cours...\n")

    progress.pack(pady=5)
    progress.start(10)

    threading.Thread(
        target=run_analysis,
        args=(file_path,),
        daemon=True
    ).start()


def run_analysis(file_path):
    global last_results

    try:
        last_results = analyze_logs(file_path)

        root.after(
            0,
            lambda: display_results_from_options()
        )

    except Exception as e:
        root.after(0, show_error, str(e))


def apply_options():
    if last_results is None:
        messagebox.showwarning(
            "Aucun fichier",
            "Veuillez d'abord sélectionner un fichier de logs."
        )
        return

    display_results_from_options()


def display_results_from_options():
    try:
        top_ip = parse_top_value(entry_top_ip.get())
        top_domain = parse_top_value(entry_top_domain.get())
        top_category = parse_top_value(entry_top_category.get())

        display_results(
            last_results,
            top_ip,
            top_domain,
            top_category
        )

    except Exception as e:
        show_error(str(e))


def display_results(results, top_ip, top_domain, top_category):
    progress.stop()
    progress.pack_forget()

    logs_per_ip, ips_per_domain, activity_per_time, ips_per_category = results

    output_text.delete("1.0", tk.END)

    # IP sources
    output_text.insert(tk.END, "📊 Logs par adresse IP source\n")
    output_text.insert(tk.END, "-" * 60 + "\n")

    for ip, count in logs_per_ip.most_common(top_ip):
        output_text.insert(tk.END, f"{ip} : {count}\n")

    # Domaines
    output_text.insert(tk.END, "\n🌐 IP sources distinctes par domaine cible\n")
    output_text.insert(tk.END, "-" * 60 + "\n")

    domain_items = sorted(
        ips_per_domain.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )

    if top_domain is not None:
        domain_items = domain_items[:top_domain]

    for domain, ips in domain_items:
        output_text.insert(tk.END, f"{domain} : {len(ips)}\n")

    # Pic d’activité
    peak_time, peak_count = activity_per_time.most_common(1)[0]
    output_text.insert(
        tk.END,
        f"\n🔥 Pic d’activité : {peak_time} UTC ({peak_count} événements)\n"
    )

    # Catégories
    output_text.insert(tk.END, "\n🏷️ IP sources distinctes par catégorie de site\n")
    output_text.insert(tk.END, "-" * 60 + "\n")

    category_items = sorted(
        ips_per_category.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )

    if top_category is not None:
        category_items = category_items[:top_category]

    for category, ips in category_items:
        output_text.insert(tk.END, f"{category} : {len(ips)}\n")

    output_text.insert(tk.END, "\n✅ Analyse terminée\n")


def show_error(message):
    progress.stop()
    progress.pack_forget()
    messagebox.showerror("Erreur", message)


# =========================
# Interface graphique
# =========================

root = tk.Tk()
root.title("Analyseur automatique de logs CSV")
root.geometry("1150x750")

top_frame = tk.Frame(root)
top_frame.pack(fill="x", padx=10, pady=10)

# ----- Gauche -----
left_frame = tk.Frame(top_frame)
left_frame.pack(side="left", anchor="nw")

tk.Label(
    left_frame,
    text="Analyse automatisée de logs CSV",
    font=("Arial", 16, "bold")
).pack(anchor="w")

tk.Button(
    left_frame,
    text="📂 Sélectionner un fichier de logs",
    font=("Arial", 12),
    command=select_file
).pack(anchor="w", pady=5)

# ----- Droite : options -----
right_frame = tk.Frame(top_frame, relief="groove", bd=2, padx=10, pady=10)
right_frame.pack(side="right", anchor="ne")

tk.Label(
    right_frame,
    text="Options (Top N ou 'all')",
    font=("Arial", 12, "bold")
).pack(anchor="w", pady=(0, 5))

tk.Label(right_frame, text="Top IP sources :").pack(anchor="w")
entry_top_ip = tk.Entry(right_frame, width=10)
entry_top_ip.insert(0, "all")
entry_top_ip.pack(anchor="w", pady=2)

tk.Label(right_frame, text="Top domaines :").pack(anchor="w")
entry_top_domain = tk.Entry(right_frame, width=10)
entry_top_domain.insert(0, "all")
entry_top_domain.pack(anchor="w", pady=2)

tk.Label(right_frame, text="Top catégories :").pack(anchor="w")
entry_top_category = tk.Entry(right_frame, width=10)
entry_top_category.insert(0, "all")
entry_top_category.pack(anchor="w", pady=2)

tk.Button(
    right_frame,
    text="✅ Appliquer les options",
    command=apply_options
).pack(anchor="w", pady=(10, 0))

# ----- Barre de chargement -----
progress = ttk.Progressbar(root, mode="indeterminate", length=400)

# ----- Résultats -----
text_frame = tk.Frame(root)
text_frame.pack(expand=True, fill="both", padx=10, pady=10)

scrollbar = tk.Scrollbar(text_frame)
scrollbar.pack(side="right", fill="y")

output_text = tk.Text(
    text_frame,
    wrap="word",
    font=("Consolas", 10),
    yscrollcommand=scrollbar.set
)
output_text.pack(side="left", expand=True, fill="both")

scrollbar.config(command=output_text.yview)

output_text.bind(
    "<MouseWheel>",
    lambda e: output_text.yview_scroll(-1 * int(e.delta / 120), "units")
)

root.mainloop()
