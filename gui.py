import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from analyzer import analyze_logs

# =========================
# Logique applicative
# =========================

def select_file():
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

    # Afficher la barre de chargement et démarrer l'animation
    progress.pack(pady=5)
    progress.start(10)

    # Lancer l'analyse dans un thread pour ne pas bloquer l'UI
    threading.Thread(
        target=run_analysis,
        args=(file_path,),
        daemon=True
    ).start()


def run_analysis(file_path):
    try:
        logs_per_ip, ips_per_domain, activity_per_time, ips_per_category = analyze_logs(file_path)
        root.after(
            0,
            display_results,
            logs_per_ip,
            ips_per_domain,
            activity_per_time,
            ips_per_category
        )
    except Exception as e:
        root.after(0, show_error, str(e))


def display_results(logs_per_ip, ips_per_domain, activity_per_time, ips_per_category):
    # Arrêter et cacher la barre de chargement
    progress.stop()
    progress.pack_forget()

    output_text.delete("1.0", tk.END)

    output_text.insert(tk.END, "📊 Nombre de lignes de log par IP source (ordre décroissant)\n")
    output_text.insert(tk.END, "-" * 60 + "\n")
    for ip, count in logs_per_ip.most_common():
        output_text.insert(tk.END, f"{ip} : {count}\n")

    output_text.insert(tk.END, "\n🌐 Nombre d’IP sources distinctes par domaine cible\n")
    output_text.insert(tk.END, "-" * 60 + "\n")
    for domain, ips in sorted(ips_per_domain.items(), key=lambda x: len(x[1]), reverse=True):
        output_text.insert(tk.END, f"{domain} : {len(ips)}\n")

    peak_time, peak_count = activity_per_time.most_common(1)[0]
    output_text.insert(
        tk.END,
        f"\n🔥 Pic d’activité : {peak_time} UTC ({peak_count} événements)\n"
    )

    output_text.insert(tk.END, "\n🏷️ Nombre d’IP sources distinctes par catégorie de site\n")
    output_text.insert(tk.END, "-" * 60 + "\n")
    for category, ips in sorted(ips_per_category.items(), key=lambda x: len(x[1]), reverse=True):
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
root.geometry("1100x700")

# ----- Frame du haut -----
top_frame = tk.Frame(root)
top_frame.pack(fill="x", padx=10, pady=10)

# Partie gauche : titre + bouton
left_frame = tk.Frame(top_frame)
left_frame.pack(side="left", anchor="nw")

title_label = tk.Label(
    left_frame,
    text="Analyse automatisée de logs CSV",
    font=("Arial", 16, "bold")
)
title_label.pack(anchor="w")

select_button = tk.Button(
    left_frame,
    text="📂 Sélectionner un fichier de logs",
    font=("Arial", 12),
    command=select_file
)
select_button.pack(anchor="w", pady=5)

# Partie droite : options (placeholder)
right_frame = tk.Frame(top_frame)
right_frame.pack(side="right", anchor="ne")

options_label = tk.Label(
    right_frame,
    text="Options",
    font=("Arial", 12, "bold")
)
options_label.pack(anchor="e")

tk.Label(right_frame, text="(à venir)").pack(anchor="e")

# ----- Barre de chargement (invisible au départ) -----
progress = ttk.Progressbar(
    root,
    mode="indeterminate",
    length=400
)

# ----- Zone résultats avec scrollbar -----
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

# Scroll molette
output_text.bind(
    "<MouseWheel>",
    lambda e: output_text.yview_scroll(-1 * int(e.delta / 120), "units")
)

root.mainloop()
