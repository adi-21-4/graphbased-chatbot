import csv

with open("schemes.csv", encoding="utf-8") as fh:
    reader = csv.DictReader(fh)
    print("CSV Headers:", reader.fieldnames)
