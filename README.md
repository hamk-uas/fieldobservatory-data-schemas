# fieldobservatory-data-schemas
This repository contains JSON data schemas for [Field Observatory](https://www.fieldobservatory.org/). Initially we implement a schema for farm management events using ICASA vocabulary.

Work in progress.

![image](https://user-images.githubusercontent.com/60920087/202477076-e5a7822f-7c86-4e7e-a6cf-add2cbb38b3e.png)
*Farm management event schema visualized using https://navneethg.github.io/jsonschemaviewer/*

![image](https://user-images.githubusercontent.com/60920087/203805362-5859b478-27f1-441b-be8b-cff8983075a1.png)
*Validation of a data file containing management events, using https://jsonschemalint.com/*

Visual Studio Code supports validation of JSON files being edited, using JSON schema files retrieved over http/https. It also supports validation of JSON files using a local JSON schema file which unfortunately will only work if there is no "$schema" property in the JSON file. Commenting it out as "//$schema" works but is. Also only a single schema can be associated with a JSON file. Sample settings.json:

![image](https://user-images.githubusercontent.com/60920087/203817321-801cd42a-edd7-484d-a1ac-229ead2c24cc.png)
