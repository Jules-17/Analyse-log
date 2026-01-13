import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
import tldextract

def analyze_logs(csv_file, start_date=None, end_date=None):
    logs_per_ip = Counter()
    ips_per_domain = defaultdict(set)
    ips_per_category = defaultdict(set)
    activity_per_time = Counter()

    min_date = None
    max_date = None

    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                ip = row["Source IP"]
                url = row["URL"]
                category = row["Category"]

                # Extraire le domaine principal
                domain_info = tldextract.extract(url)
                main_domain = f"{domain_info.domain}.{domain_info.suffix}"

                timestamp = datetime.fromtimestamp(
                    int(row["Timestamp (UTC) Seconds"]),
                    tz=timezone.utc
                )

                # Détection date min / max
                if min_date is None or timestamp < min_date:
                    min_date = timestamp
                if max_date is None or timestamp > max_date:
                    max_date = timestamp

                # Filtrage par date
                if start_date and timestamp < start_date:
                    continue
                if end_date and timestamp > end_date:
                    continue

                # Comptage des logs et IP
                logs_per_ip[ip] += 1
                ips_per_domain[main_domain].add(ip)
                ips_per_category[category].add(ip)

                # Activité par minute (timestamp arrondi à la minute)
                minute = timestamp.replace(second=0, microsecond=0)
                activity_per_time[minute] += 1

            except Exception:
                # Ignore les lignes mal formées
                continue

    return logs_per_ip, ips_per_domain, activity_per_time, ips_per_category, min_date, max_date
