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

#print("ui_structure:")
#print(json.dumps(ui_structure, indent=4))

schema = {
    '$schema': 'https://json-schema.org/draft/2020-12/schema',
    'id': '#root',
    "oneOf" : [
    ]
}
categories = csv[csv['category'] == 'mgmt_operations_event_choice']
print("categories:")
print(categories)
for index, row in categories.iterrows():
    sub_schema = {
        'id': f"#{row['code_name']}",
        'properties': {
            "mgmt_operations_event": {
                "type": "string",
                "const": row['code_name']
            },
            "date": {
                "type": "string",
                "format": "date"
            },
            "mgmt_event_notes": {
                "type": "string"
            }
        },
        'type': 'object',
        "required": ['mgmt_operations_event', 'date']
    }
    sub_element = ui_structure['form']['mgmt_operations_event']['sub_elements'][row['code_name']]
    for sub_element_key, sub_element_value in sub_element.items():
        if "code_name" in sub_element_value:
            property = sub_element_value["code_name"]
            sub_schema["properties"][property] = {
                "type": "string"
            }
    schema['oneOf'].append(sub_schema)

f = open("management-event.schema.json", mode='w')
print(json.dumps(schema, indent=4), file=f)
