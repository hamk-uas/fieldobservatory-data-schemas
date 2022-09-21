import urllib.request
import pandas as pd
import json
import pyjson5

# Read CSV
csv = pd.read_csv('https://raw.githubusercontent.com/PecanProject/fieldactivity/dev/inst/extdata/display_names.csv', comment='#', usecols=[0, 1, 2, 3])
print("csv:")
print(csv)

# Read JSON
with urllib.request.urlopen('https://raw.githubusercontent.com/PecanProject/fieldactivity/dev/inst/extdata/ui_structure.json') as url:
    ui_structure = pyjson5.load(url)

print("ui_structure:")
print(json.dumps(ui_structure, indent=4))

schema = {
    '$schema': 'https://json-schema.org/draft/2020-12/schema',
    'id': '#root',
    'properties': { }
}
categories = csv[csv['category'] == 'mgmt_operations_event_choice']
print("categories:")
print(categories)
for index, row in categories.iterrows():
    schema['properties'][row['code_name']] = {
        'id': f"#{row['code_name']}",
        'properties': {},
        'type': 'object'
    }
    #ui_structure['form']['mgmt_operations_event']['sub_elements'][row['code_name']]

print(json.dumps(schema, indent=4))
