import glob
for f in glob.glob('news/monthly/*.json'):
    with open(f, 'r') as file:
        content = file.read()
    content = content.replace('"timezone": "Asia/Kolkata"', '"timezone": "UTC"')
    with open(f, 'w') as file:
        file.write(content)

for f in glob.glob('news/last_run/*.json'):
    with open(f, 'r') as file:
        content = file.read()
    content = content.replace('"timezone": "Asia/Kolkata"', '"timezone": "UTC"')
    with open(f, 'w') as file:
        file.write(content)
