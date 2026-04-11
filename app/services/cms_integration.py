import csv

def load_cms_data(file_path):
    data = []
    with open(file_path, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def match_agency(payload, cms_data):
    agency_name = payload.get("agency_name", "").lower()
    for row in cms_data:
        if agency_name in row.get("Agency Name", "").lower():
            return row
    return None
