import csv
from collections import Counter, defaultdict
from datetime import datetime

def analyze_logs(csv_file):
    logs_per_ip = Counter()
    ips_per_domain = defaultdict(set)
    ips_per_category = defaultdict(set)
    activity_per_time = Counter()

    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                ip = row["Source IP"]
                domain = row["Host Name"]
                category = row["Category"]

                # Conversion du timestamp UNIX en datetime
                timestamp = datetime.utcfromtimestamp(int(row["Timestamp (UTC) Seconds"]))

                # Nombre de logs par IP
                logs_per_ip[ip] += 1

                # IP distinctes par domaine
                ips_per_domain[domain].add(ip)

                # IP distinctes par catégorie
                ips_per_category[category].add(ip)

                # Activité par minute pour le pic d’activité
                minute = timestamp.replace(second=0)
                activity_per_time[minute] += 1

            except Exception:
                continue  # ignore les lignes invalides

    return logs_per_ip, ips_per_domain, activity_per_time, ips_per_category