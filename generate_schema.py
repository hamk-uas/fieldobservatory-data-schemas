import urllib.request
import pandas as pd
import json
import pyjson5

# Read CSV
csv = pd.read_csv('https://raw.githubusercontent.com/PecanProject/fieldactivity/dev/inst/extdata/display_names.csv', comment='#', usecols=[0, 1, 2, 3])
#print("csv:")
#print(csv)

# Read JSON
with urllib.request.urlopen('https://raw.githubusercontent.com/PecanProject/fieldactivity/dev/inst/extdata/ui_structure.json') as url:
    ui_structure = pyjson5.load(url)

#print("ui_structure:")
#print(json.dumps(ui_structure, indent=4))

def get_choices(key, value):
    if "choices" in value:
        if type(value['choices']) == list:
            choices = value['choices']
        else:
            choices = csv[csv['category'] == value['choices']]['code_name']
        ret_val = {
            "type": "string",
            "oneOf": []
        }           
        for choice in choices:
            ret_val["oneOf"].append({
                "const": choice
            })
    else:
        ret_val = {
            "type": "string"
        }
    return ret_val


schema = {
    '$schema': 'https://json-schema.org/draft/2020-12/schema',
    'id': '#root',
    "oneOf" : [
    ]
}
categories = csv[csv['category'] == 'mgmt_operations_event_choice']
#print("categories:")
#print(categories)
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
            #if "choices" in sub_element_value:
                #print(sub_element_key)
                #print(sub_element_value)
                #chemical_applic_method
                #{'code_name': 'chemical_applic_method', 'type': 'selectInput', 'label': 'chemical_applic_method_label', 'choices': 'FEACD'}                #print("choices available for:")
            sub_schema["properties"][property] = get_choices(sub_element_key, sub_element_value)
            if "sub_elements" in sub_element_value:
                if "single" in sub_element_value["sub_elements"]:
                    for element_of_single_key, element_of_single_value in sub_element_value["sub_elements"]["single"].items():
                        if "code_name" in element_of_single_value:
                            #print(element_of_single_key)
                            #print(element_of_single_value)
                            # harvest_cut_height
                            # {'code_name': 'harvest_cut_height', 'type': 'numericInput', 'label': 'harvest_cut_height_label', 'min': 0}
                            sub_schema["properties"][element_of_single_key] = get_choices(element_of_single_key, element_of_single_value)
    schema['oneOf'].append(sub_schema)

f = open("management-event.schema.json", mode='w')
print(json.dumps(schema, indent=4), file=f)
