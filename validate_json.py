import json
import jsonschema
from jsonschema import validate

f = open('management-event-sample.json')
json_to_validate = json.load(f)
  
f = open('management-event.schema.json')
json_schema = json.load(f)

def validateJson():
    try:
        validate(instance=json_to_validate, schema=json_schema)
    except jsonschema.exceptions.ValidationError as err:
        return False
    return True

if validateJson():
    print("Validation OK")
else:
    print("Validation ERROR")

