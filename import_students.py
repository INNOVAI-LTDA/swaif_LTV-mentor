import csv
import json
import os

def generate_initials(name):
    # Take the first letter of each part of the name, uppercase, then truncate to 2 chars
    initials = ''.join([part[0].upper() for part in name.split() if part])
    return initials[:2]

def map_status(tsv_status):
    status = tsv_status.strip().upper()
    if status == "ATIVO":
        return "active"
    elif status == "A RENOVAR":
        return "renewing"
    elif status == "":
        return "caution"
    else:
        return "caution"

def is_active(status):
    return status in ("active", "renewing")

input_tsv = os.path.join("backend", "data_ops", "master_accmed_students.tsv")
output_json = os.path.join("backend", "data_ops", "students_imported.json")

students = []
id_counter = 11  # Start after your last std_10

with open(input_tsv, encoding="utf-8") as tsvfile:
    reader = csv.DictReader(tsvfile, delimiter="\t")
    for row in reader:
        name = row.get("Nome", "").strip()
        email = row.get("E-MAIL", "").strip()
        phone = row.get("TELEFONE", "").strip()
        status = map_status(row.get("STATUS", ""))
        if not name or not email:
            continue  # Skip incomplete records

        student = {
            "id": f"std_{id_counter}",
            "full_name": name,
            "initials": generate_initials(name),
            "email": email,
            "phone": phone if phone else None,
            "status": status,
            "is_active": is_active(status)
        }
        students.append(student)
        id_counter += 1

# Remove None values for cleaner JSON
for s in students:
    for k in list(s.keys()):
        if s[k] is None:
            del s[k]

with open(output_json, "w", encoding="utf-8") as jsonfile:
    json.dump({"version": 1, "items": students}, jsonfile, ensure_ascii=False, indent=2)

print(f"Imported {len(students)} students to {output_json}")
