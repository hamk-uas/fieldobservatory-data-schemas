import urllib.request
import pandas as pd
import json
import pyjson5

banned_properties = {
    "fertilizer_element_table_title": True,
    "fertilizer_element_table": True
}

choice_list_name = {
    "CRID": "crop_ident_ICASA",
    "FEACD": "fertilizer_applic_method",
    "MLTP": "mulch_type"
}

# Read CSV
csv = pd.read_csv('https://raw.githubusercontent.com/PecanProject/fieldactivity/dev/inst/extdata/display_names.csv', comment='#', usecols=[0, 1, 2, 3])
#print("csv:")
#print(csv)

# Read JSON
with urllib.request.urlopen('https://raw.githubusercontent.com/PecanProject/fieldactivity/dev/inst/extdata/ui_structure.json') as url:
    ui_structure = pyjson5.load(url)

#print("ui_structure:")
#print(json.dumps(ui_structure, indent=4))

def set_choices(element, property, key, value):
    # TODO: Handle "required".
    # Ignore for now: value["type"] == "fileInput", because we don't yet store the image links in the data
    if property in banned_properties:
        return
    if "type" in value:
        ret_val = {
            "title": code_name_to_disp_name_eng[key] if key in code_name_to_disp_name_eng else 'unknown',
            "title_en": code_name_to_disp_name_eng[key] if key in code_name_to_disp_name_eng else 'unknown',
            "title_fi": code_name_to_disp_name_fin[key] if key in code_name_to_disp_name_fin else 'unknown'
        }
        if value["type"] == "selectInput":
            if type(value['choices']) == list:
                choices = value['choices']
            else:
                choices = csv[csv['category'] == value['choices']]['code_name']
            if type(value['choices']) != list and value['choices'] in choices_appeared_in:
                other = choices_appeared_in[value['choices']]
                if "type" in other:
                    schema["$defs"][choice_list_name[value['choices']]] = {
                        "type": other["type"],
                        "oneOf": other["oneOf"]
                    }
                    other.pop("type")
                    other.pop("oneOf")
                    other["$ref"] = f"#/$defs/{choice_list_name[value['choices']]}"
                ret_val["$ref"] = f"#/$defs/{choice_list_name[value['choices']]}"
            else:
                ret_val["type"] = "string"
                ret_val["oneOf"] = []
                for choice in choices:
                    ret_val["oneOf"].append({
                        "const": choice,
                        "title": code_name_to_disp_name_eng[choice] if choice in code_name_to_disp_name_eng else 'unknown',
                        "title_en": code_name_to_disp_name_eng[choice] if choice in code_name_to_disp_name_eng else 'unknown',
                        "title_fi": code_name_to_disp_name_fin[choice] if choice in code_name_to_disp_name_fin else 'unknown'
                    })
                if type(value['choices']) != list:
                    choices_appeared_in[value['choices']] = ret_val
        elif value["type"] == "textInput" or value["type"] == "textAreaInput":
            ret_val["type"] = "string"
            ret_val["ui_type"] = value["type"]
            if "placeholder" in value:
                ret_val["placeholder"] = code_name_to_disp_name_eng[value["placeholder"]] if value["placeholder"] in code_name_to_disp_name_eng else 'unknown'
                ret_val["placeholder_en"] = code_name_to_disp_name_eng[value["placeholder"]] if value["placeholder"] in code_name_to_disp_name_eng else 'unknown'
                ret_val["placeholder_fi"] = code_name_to_disp_name_fin[value["placeholder"]] if value["placeholder"] in code_name_to_disp_name_fin else 'unknown'
        elif value["type"] == "numericInput":
            # TODO: Handle "min" and "max" and "step" (not all may be present)
            if "step" in value and value["step"] == 1:
                ret_val["type"] = "integer"
            else:
                ret_val["type"] = "number"
            if "min" in value:
                ret_val["minimum"] = value["min"]
            if "max" in value:
                ret_val["maximum"] = value["max"]
        elif value["type"] == "dateInput":
            ret_val["type"] = "string"
            ret_val["format"] = "date"
        elif value["type"] == "dateRangeInput":
            #TODO: "start_date": "2021-08-24",
            #"end_date": "2021-08-31",
            # Do this manually afterwards
            element["properties"][property] = {"todo": "fixme1"}
        elif value["type"] == "textOutput":
            element["description"] = code_name_to_disp_name_eng[value["code_name"]] if value["code_name"] in code_name_to_disp_name_eng else 'unknown'
            element["description_en"] = code_name_to_disp_name_eng[value["code_name"]] if value["code_name"] in code_name_to_disp_name_eng else 'unknown'
            element["description_fi"] = code_name_to_disp_name_fin[value["code_name"]] if value["code_name"] in code_name_to_disp_name_fin else 'unknown'
        else:
            element["properties"][property] = {"todo": "fixme2"}  
    else:
        return {"todo": "fixme3"}
    element["properties"][property] = ret_val

choices_appeared_in = {}

schema = {
    '$schema': 'https://json-schema.org/draft/2020-12/schema',
    'id': '#root',
    "title": "Management event",
    "oneOf" : [
    ],
    "$defs" : {        
    }
}

variable_names = csv #csv[csv['category'] == 'variable_name']
code_name_to_disp_name_eng = {}
code_name_to_disp_name_fin = {}
for index, row in variable_names.iterrows():
    code_name_to_disp_name_eng[row['code_name']] = row['disp_name_eng'].replace("“", "\"").replace("”", "\"")
    code_name_to_disp_name_fin[row['code_name']] = row['disp_name_fin'].replace("“", "\"").replace("”", "\"")

categories = csv[csv['category'] == 'mgmt_operations_event_choice']

#print("categories:")
#print(categories)

# Go through different choices for mgmt_operations_event, listed in the display names CSV
for index, row in categories.iterrows():
    # (index is not needed)
    # row is for example:
    # category,code_name,disp_name_eng,disp_name_fin
    # mgmt_operations_event_choice,planting,sowing,kylvö
    #
    # Create a sub-schema for this particular event type
    sub_schema = {
        'id': f"#{row['code_name']}",
        'title': row['disp_name_eng'],
        'title_en': row['disp_name_eng'],
        'title_fi': row['disp_name_fin'],
        'properties': { # Include some properties required for all event types
            "mgmt_operations_event": {
                "title": code_name_to_disp_name_eng["mgmt_operations_event"] if "mgmt_operations_event" in code_name_to_disp_name_eng else 'unknown',
                "title_en": code_name_to_disp_name_eng["mgmt_operations_event"] if "mgmt_operations_event" in code_name_to_disp_name_eng else 'unknown',
                "title_fi": code_name_to_disp_name_fin["mgmt_operations_event"] if "mgmt_operations_event" in code_name_to_disp_name_fin else 'unknown',
                "type": "string",
                "const": row['code_name']
            },
            "date": {
                "title": code_name_to_disp_name_eng["date"] if "date" in code_name_to_disp_name_eng else 'unknown',
                "title_en": code_name_to_disp_name_eng["date"] if "date" in code_name_to_disp_name_eng else 'unknown',
                "title_fi": code_name_to_disp_name_fin["date"] if "date" in code_name_to_disp_name_fin else 'unknown',
                "type": "string",
                "format": "date"
            },
            "mgmt_event_notes": {
                "title": code_name_to_disp_name_eng["mgmt_event_notes"] if "mgmt_event_notes" in code_name_to_disp_name_eng else 'unknown',
                "title_en": code_name_to_disp_name_eng["mgmt_event_notes"] if "mgmt_event_notes" in code_name_to_disp_name_eng else 'unknown',
                "title_fi": code_name_to_disp_name_fin["mgmt_event_notes"] if "mgmt_event_notes" in code_name_to_disp_name_fin else 'unknown',
                "type": "string"
            }
        },
        'type': 'object',
        "required": ['mgmt_operations_event', 'date'] # This list may be expanded further down
    }
    # Get the object describing this event type from the sub_elements list of mgmt_operations_event
    sub_element = ui_structure['form']['mgmt_operations_event']['sub_elements'][row['code_name']]
    # Loop through the properties of the event type specific object
    for sub_element_key, sub_element_value in sub_element.items():
        if "code_name" in sub_element_value:
            # If a property has a code_name then it will be a property in the JSON schema
            property = sub_element_value["code_name"] # Get property identifier
            # Parse choices for the property
            set_choices(sub_schema, property, sub_element_key, sub_element_value)
            # If the event's property has a property "multiple": true, then it may have a
            # property "sub_elements", which introduces additional dependent properties
            if "multiple" in sub_element_value and sub_element_value["multiple"] and "sub_elements" in sub_element_value:
                # "single" in "sub_elements" introduces new properties always present
                sub_elements = sub_element_value["sub_elements"]
                if "single" in sub_elements:
                    for element_of_single_key, element_of_single_value in sub_elements["single"].items():
                        if "code_name" in element_of_single_value:
                            set_choices(sub_schema, element_of_single_key, element_of_single_key, element_of_single_value)
                # "hidden" in "sub_elements" introduces new properties that MAY be present
                # Let's add them all anyhow
                if "hidden" in sub_elements:
                    for element_of_hidden_key, element_of_hidden_value in sub_elements["hidden"].items():
                        if "code_name" in element_of_hidden_value:
                            set_choices(sub_schema, element_of_hidden_key, element_of_hidden_key, element_of_hidden_value)
        elif "hidden" in sub_element:
            for element_of_hidden_key, element_of_hidden_value in sub_element["hidden"].items():
                if "code_name" in element_of_hidden_value:
                    set_choices(sub_schema, element_of_hidden_key, element_of_hidden_key, element_of_hidden_value)

    schema['oneOf'].append(sub_schema)

with open("management-event.schema.json", mode='w', encoding='utf-8') as f:
    json.dump(schema, f, indent=4, ensure_ascii = False)
