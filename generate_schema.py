import urllib.request
import pandas as pd
import json
import pyjson5
import pydash

# For validation use https://jsonschemalint.com/#!/version/draft-07/markup/json
# It gives useful validation error messages

banned_properties = {
    "fertilizer_element_table_title": True,
    "fertilizer_element_table": True,
    "soil_layer_count": True,
    "mowing_method": True, # TODO: Allow this? Removed because of an empty list of choices
    "soil_image": True
}

priority_properties = ['$id', 'title', 'title_en', 'title_fi', 'title_sv', 'title2', 'title2_fi', 'type', 'description', 'description_en', 'description_fi']

choice_list_name = {
    "CRID": "crop_ident_ICASA",
    "FEACD": "fertilizer_applic_method",
    "MLTP": "mulch_type"
}

property_lists = {
    "planting_list": ["planted_crop", "planting_material_weight", "planting_depth", "planting_material_source"],
    "harvest_list": ["harvest_crop", "harvest_yield_harvest_dw", "harv_yield_harv_f_wt", "yield_C_at_harvest", "harvest_moisture",  "harvest_method", "harvest_operat_component", "canopy_height_harvest", "harvest_cut_height", "plant_density_harvest", "harvest_residue_placement"],
    "soil_layer_list": ["soil_layer_top_depth", "soil_layer_base_depth", "soil_classification_by_layer"],
}

listed_properties = {}

# From FO ui with Swedish translations:

ap_plaintext = {
    "AP001": "Broadcast, not incorporated",
    "AP002": "Broadcast, incorporated",
    "AP003": "Banded on surface",
    "AP004": "Banded beneath surface",
    "AP005": "Applied in irrigation water",
    "AP006": "Foliar spray",
    "AP007": "Bottom of hole",
    "AP008": "On the seed",
    "AP009": "Injected",
    "AP011": "Broadcast on flooded/saturated soil, none in soil",
    "AP012": "Broadcast on flooded/saturated soil, 15%% in soil",
    "AP013": "Broadcast on flooded/saturated soil, 30%% in soil",
    "AP014": "Broadcast on flooded/saturated soil, 45%% in soil",
    "AP015": "Broadcast on flooded/saturated soil, 60%% in soil",
    "AP016": "Broadcast on flooded/saturated soil, 75%% in soil",
    "AP017": "Broadcast on flooded/saturated soil, 90%% in soil",
    "AP018": "Band on saturated soil, 2 cm flood, 92%% in soil",
    "AP019": "Deeply placed urea super granules/pellets, 95%% in soil",
    "AP020": "Deeply placed urea super granules/pellets, 100%% in soil",
    "AP999": "Unknown/not given",
    "AP999_fi": "Ei tiedossa",
    "AP999_sv": "Okänd metod"
}

crop_codes = {
    "FRG": "Timothy (Phleum pratense)",
    "FRG_fi": "Timotei (Phleum pratense)",
    "FRG_sv": "Timotej (Phleum pratense)",
    "WHT": "Wheat (Triticum spp.)",
    "WHT_fi": "Vehnä (Triticum spp.)",
    "WHT_sv": "Vete (Triticum spp.)",
    "OAT": "Oats (Avena sativa)",
    "OAT_fi": "Kaura (Avena sativa)",
    "OAT_sv": "Havre (Avena sativa)",
    "FEP": "Meadow fescue (Festuca pratensis)",
    "FEP_fi": "Nurminata (Festuca pratensis)",
    "FEP_sv": "Ängssvingel(Festuca pratensis)",
    "BAR": "Barley (Hordeum vulgare)",
    "BAR_fi": "Barley (Hordeum vulgare)",
    "BAR_sv": "Korn (Hordeum vulgare)"
}

mgmt_operations_event_choice_plaintext = {
    "planting": "Planting",
    "planting_fi": "Kylvö",
    "planting_sv": "Sådd",
    "fertilizer": "Fertilizer application",
    "fertilizer_fi": "Lannoitteen levitys",
    "fertilizer_sv": "Spridning av gödslingsmedel",
    "irrigation": "Irrigation application",
    "irrigation_fi": "Kastelu",
    "irrigation_sv": "Bevattning",
    "tillage": "Tillage application",
    "tillage_fi": "Maan muokkaus",
    "tillage_sv": "Markens bearbetning",
    "organic_material": "Organic material application",
    "organic_material_fi": "Eloperäisen aineen levitys",
    "organic_material_sv": "Applicering av organiskt material",
    "grazing": "Grazing",
    "grazing_fi": "Laidunnus",
    "grazing_sv": "Betning",
    "harvest": "Harvest",
    "harvest_fi": "Sadonkorjuu",
    "harvest_sv": "Skörd",
    "bed_prep": "Raised bed preparation",
    "bed_prep_fi": "Kohopenkki",
    "bed_prep_sv": "Upphöjd odlingsbädd",
    "inorg_mulch": "Placement of inorganic mulch",
    "inorg_mulch_fi": "Katteen levitys",
    "inorg_mulch_sv": "Applicering av oorganisk kompost",
    "Inorg_mul_rem": "Removal of inorganic mulch",
    "Inorg_mul_rem_fi": "Katteen poisto",
    "Inorg_mul_rem_sv": "Borttagning av oorganisk kompost",
    "chemicals": "Chemicals application",
    "chemicals_fi": "Kemikaalin levitys",
    "chemicals_sv": "Applicering av kemikalier",
    "mowing": "Mowing",
    "mowing_fi": "Ruohonleikkuu",
    "mowing_sv": "Gräsklippning",
    "observation": "Observation",
    "observation_fi": "Havainto",
    "observation_sv": "Observation",
    "weeding": "Mechanical extraction of weeds",
    "weeding_fi": "Rikkaruohojen kitkeminen",
    "weeding_sv": "Rensning av ogräs",
    "other": "Other management event",
    "other_fi": "Muu toimenpide",
    "other_sv": "Annan åtgärd"
}

mgmt_operations_variable_name_plaintext = {
    "block": "Block",
    "block_fi": "Lohko",
    "block_sv": "Skifte",
    "mgmt_event_notes": "Description",
    "mgmt_event_notes_fi": "Kuvaus",
    "mgmt_event_notes_sv": "Beskrivning",
    "planted_crop": "Planted crop",
    "planted_crop_fi": "Kylvetty laji",
    "planted_crop_sv": "Sådd gröda",
    "planting_material_weight": "Planting material weight (kg/ha)",
    "planting_material_weight_fi": "Kylvetyn materiaalin paino (kg/ha)",
    "planting_material_weight_sv": "Vikt av sådd material (kg/ha)",
    "planting_depth": "Planting depth (mm)",
    "planting_depth_fi": "Kylvösyvyys (mm)",
    "planting_depth_fi": "Sådjup (mm)",
    "planting_material": "Planting material",
    "planting_material_fi": "Kylvetty materiaali",
    "planting_material_sv": "Sådd material",
    "planting_material_source": "Planting material source",
    "planting_material_source_fi": "Kylvetyn materiaalin alkuperä",
    "planting_material_source_sv": "Ursprung på sådda materialet",
    "planting_notes": "Planting notes",
    "planting_notes_fi": "Kylvömuistiinpanot",
    "planting_notes_sv": "Såddanteckningar",
    "harvest_area": "Harvest area (ha)",
    "harvest_area_fi": "Korjattu pinta-ala (ha)",
    "harvest_area_sv": "Skördat område (ha)",
    "harvest_crop": "Harvest crop",
    "harvest_crop_fi": "Korjattu laji",
    "harvest_crop_sv": "Skördad gröda",
    "harvest_operat_component": "Crop component harvested",
    "harvest_operat_component_fi": "Korjattu kasvinosa",
    "harvest_operat_component_sv": "Skördad växtdel",
    "harvest_residue_placement": "Harvest residue placement",
    "harvest_residue_placement_fi": "Korjatun kasvinosan sijoituspaikka",
    "canopy_height_harvest": "Canopy height (m)",
    "canopy_height_harvest_fi": "Kasvuston korkeus (m)",
    "canopy_height_harvest_sv": "Växtlighetens höjd (m)",
    "grazing_species": "Grazing species",
    "grazing_species_fi": "Laiduntava laji",
    "grazing_species_sv": "Betande art",
    "grazing_type": "Grazing type",
    "grazing_type_fi": "Laidunnuksen tyyppi",
    "grazing_type_sv": "Betstyp",
    "harvest_yield_harvest_dw": "Yield, dry weight (kg/ha)",
    "harvest_yield_harvest_dw_fi": "Sato, kuivapaino (kg/ha)",
    "harvest_yield_harvest_dw_sv": "Skörd, torrvikt (kg/ha)",
    "harvest_yield_harvest_dw_total": "Total yield, dry weight (kg/ha)",
    "harvest_yield_harvest_dw_total_fi": "Kokonaissato, kuivapaino (kg/ha)",
    "harvest_yield_harvest_dw_total_sv": "Totala skörden, torrvikt (kg/ha)",
    "harv_yield_harv_f_wt": "Yield, fresh weight (t/ha)",
    "harv_yield_harv_f_wt_fi": "Sato, tuorepaino (t/ha)",
    "harv_yield_harv_f_wt_sv": "Skörd, färskvikt (t/ha)",
    "harvest_method": "Harvest method",
    "harvest_method_fi": "Korjuutapa",
    "harvest_method_sv": "Skördemetod",
    "harvest_cut_height": "Height of cut (cm)",
    "harvest_cut_height_fi": "Leikkuukorkeus (cm)",
    "harvest_cut_height_sv": "Klipphöjd (cm)",
    "harvest_comments": "Comments",
    "harvest_comments_fi": "Sadonkorjuukommentit",
    "harvest_comments_sv": "Kommentarer",
    "harv_operat_size_categor": "Harvest operations size category",
    "harv_operat_size_categor_fi": "Sadonkorjuun laajuus",
    "harv_operat_size_categor_sv": "Skördens storlekskategori",
    "organic_material": "Organic material",
    "organic_material_fi": "Eloperäinen aine",
    "organic_material_sv": "Organisk material",
    "org_material_applic_meth": "Application method",
    "org_material_applic_meth_fi": "Eloperäisen aineen levitystapa",
    "org_material_applic_meth_sv": "Organiska materialets appliceringsmetod",
    "org_material_appl_depth": "Application depth (cm)",
    "org_material_appl_depth_fi": "Eloperäisen aineen levityssyvyys (cm)",
    "org_material_appl_depth_sv": "Organiska materialets appliceringsdjup (cm)",
    "org_material_notes": "Notes",
    "org_material_notes_fi": "Muistiinpanot",
    "org_material_notes_sv": "Anteckningar",
    "tillage_implement": "Tillage implement",
    "tillage_implement_fi": "Muokkausväline",
    "tillage_implement_sv": "Bearbetningsredskap",
    "tillage_operations_depth": "Tillage depth (cm)",
    "tillage_operations_depth_fi": "Muokkaussyvyys (cm)",
    "tillage_operations_depth_sv": "Bearbetningsdjup (cm)",
    "tillage_treatment_notes": "Tillage notes",
    "tillage_treatment_notes_fi": "Muistiinpanot muokkauksesta",
    "tillage_treatment_notes_sv": "Anteckningar på bearbetning",
    "org_material_applic_amnt": "Application amount, dry weight (kg/ha)",
    "org_material_applic_amnt_fi": "Levitetyn aineen kuivapaino (kg/ha)",
    "org_material_applic_amnt_sv": "Torrvikten av det applicerade materialet (kg/ha)",
    "org_matter_moisture_conc": "Moisture concentration (%%)",
    "org_matter_moisture_conc_fi": "Aineen kosteus (%%)",
    "org_matter_moisture_conc_sv": "Materialets fuktighet (%%)",
    "org_matter_carbon_conc": "Carbon (C) concentration (%%)",
    "org_matter_carbon_conc_fi": "Hiilen (C) määrä aineessa (%%)",
    "org_matter_carbon_conc_sv": "Mängden kol (C) (%%)",
    "organic_material_N_conc": "Nitrogen (N) concentration (%%)",
    "organic_material_N_conc_fi": "Typen (N) määrä aineessa (%%)",
    "organic_material_N_conc_sv": "Mängden kväve (N) (%%)",
    "org_material_c_to_n": "C:N ratio",
    "org_material_c_to_n_fi": "C:N suhde",
    "org_material_c_to_n_sv": "C:N förhållandet",
    "yield_C_at_harvest": "Carbon (C) in yield (kg/ha)",
    "yield_C_at_harvest_fi": "Hiilen (C) määrä sadossa (kg/ha)",
    "yield_C_at_harvest_sv": "Mängden kol (C) i skörden (kg/ha)",
    "yield_C_at_harvest_total": "Total carbon (C) in yield (kg/ha)",
    "yield_C_at_harvest_total_fi": "Hiilen (C) kokonaismäärä sadossa (kg/ha)",
    "yield_C_at_harvest_total_sv": "Totala mängden kol (C) i skörden (kg/ha)",
    "carbon_soil_tot": "Average Carbon in 1 m soil column (kg/m²)",
    "carbon_soil_tot_fi": "Hiiltä keskimäärin 1 m maakolonnissa (kg/m²)",
    "carbon_soil_tot_sv": "Kol i medeltal i 1 m markpelare (kg/m²)",
    "carbon_soil_tot_sd": "Standard deviation",
    "carbon_soil_tot_sd_fi": "Keskihajonta",
    "carbon_soil_tot_sd_sv": "Standardavvikelse",
    "fertilizer_total_amount": "Total amount of fertilizer (kg/ha)",
    "fertilizer_total_amount_fi": "Lannoitteen kokonaismäärä (kg/ha)",
    "fertilizer_total_amount_sv": "Totala mändgen gödsel (kg/ha)",
    "N_in_applied_fertilizer": "Amount of nitrogen (N) in fertilizer (kg/ha)",
    "N_in_applied_fertilizer_fi": "Typen (N) määrä lannoitteessa (kg/ha)",
    "N_in_applied_fertilizer_sv": "Mängden lväve (N) i gödseln (kg/ha)",
    "phosphorus_applied_fert": "Amount of phosphorus (P) in fertilizer (kg/ha)",
    "phosphorus_applied_fert_fi": "Fosforin (P) määrä lannoitteessa (kg/ha)",
    "phosphorus_applied_fert_sv": "Mängden fosfor (P) i gödseln (kg/ha)",
    "fertilizer_K_applied": "Amount of potassium (K) in fertilizer (kg/ha)",
    "fertilizer_K_applied_fi": "Kaliumin (K) määrä lannoitteessa (kg/ha)",
    "fertilizer_K_applied_sv": "Mängden kalium (K) i gödseln (kg/ha)"
}

mgmt_operations_value_plaintext = {
    "harvest_residue_placement": {
        "harvest_residue_placement_removed": "Removed from the field",
        "harvest_residue_placement_removed_fi": "Viety pois pellolta"
    },
    "grazing_species": {
        "grazing_species_cattle": "Cattle",
        "grazing_species_cattle_fi": "Nautakarja",
        "grazing_species_cattle_sv": "Nötkreatur"
    },
    "grazing_type": {
        "grazing_type_rotation": "Rotational",
        "grazing_type_rotation_fi": "Lohkosyöttö",
        "grazing_type_rotation_sv": "Rotationsbetning"
    },
    "harv_operat_size_categor": {
        "A": "All",
        "A_fi": "Kaikki",
        "A_sv": "Alla",
        "S": "Small - less than 1/3 full size",
        "S_fi": "Pieni - vähemmän kuin 1/3 kaikesta",
        "S_sv": "Liten - mindre än 1/3 av hela storleken",
        "M": "Medium - from 1/3 to 2/3 full size",
        "M_fi": "Keskiverto - 1/3 - 2/3 kaikesta",
        "M_sv": "Medium - 1/3 - 2/3 av hela storleken",
        "L": "Large - greater than 2/3 full size",
        "L": "Suuri - enemmän kuin 2/3 kaikesta",
        "L": "Stor - större än 2/3 av hela storleken"
    },
    "harvest_operat_component": {
        "canopy": "Canopy",
        "canopy_fi": "Latvusto",
        "canopy_sv": "Krontak",
        "leaf": "Leaves",
        "leaf_fi": "Lehdet",
        "leaf_sv": "Blad",
        "grain": "Grain, legume seeds",
        "grain_fi": "Jyvä, palkokasvin siemen",
        "grain_sv": "Korn, baljväxtens frö",
        "silage": "Silage",
        "silage_fi": "Säilörehu",
        "silage_sv": "Ensilage",
        "tuber": "Tuber, root, etc.",
        "tuber_fi": "Mukula, juuri, yms.",
        "tuber_sv": "Knöl, rot, etc.",
        "fruit": "Fruit",
        "fruit_fi": "Hedelmä",
        "fruit_sv": "Frukt",
        "fiber": "Fiber",
        "fiber_fi": "Kuitu",
        "fiber_sv": "Fiber",
        "seed_cotton": "Cotton boil, including lint",
        "stem": "Stem",
        "stem_fi": "Varsi",
        "stem_sv": "Stjälk"
    },

    "harvest_method": {
        "HM001": "Combined",
        "HM001_fi": "Leikkuupuimuri",
        "HM001_sv": "Skördetröska",
        "HM002": "Hand cut, machine threshed",
        "HM003": "Hand cut, hand threshed",
        "HM004": "Hand picked, no further processing",
        "HM004_fi": "Poimittu käsin, ei muuta prosessointia",
        "HM004_sv": "Handplockat, ingen övrig bearbetning",
        "HM005": "Hand picked, machine processing",
        "HM005_fi": "Poimittu käsin, prosessoitu koneella",
        "HM005_sv": "Handplockat, maskin bearbetat",
        "HM006": "Cotton stripper",
        "HM999": "Unknown/not given",
        "HM999_fi": "Tapa ei tiedossa",
        "HM999_sv": "Okänd metod"
    },

    "organic_material": {
        "RE001": "Generic crop residue",
        "RE001_fi": "Yleinen kasvijäte",
        "RE001_sv": "Allmänna växtrester",
        "RE002": "Green manure",
        "RE002_fi": "Viherlannoitus",
        "RE002_sv": "Gröngödsel",
        "RE003": "Barnyard manure",
        "RE003_fi": "Kuivalanta",
        "RE003_sv": "Gårdsgödsel",
        "RE004": "Liquid manure",
        "RE004_fi": "Lietelanta",
        "RE004_sv": "Slamgödsel",
        "RE005": "Compost",
        "RE005_fi": "Komposti",
        "RE005_sv": "Kompost",
        "RE006": "Bark",
        "RE006_fi": "Puun kuori",
        "RE006_sv": "Bark",
        "RE101": "Generic legume residue",
        "RE101_fi": "Palkokasvijäte",
        "RE101_sv": "Baljväxtrester",
        "RE102": "Cowpea residue",
        "RE103": "Mucuna residue",
        "RE104": "Peanut residue",
        "RE105": "Pigeon Pea residue",
        "RE106": "Soybean residue",
        "RE107": "Alfalfa residue",
        "RE108": "Chickpea forage",
        "RE109": "Faba bean",
        "RE109_fi": "Härkäpapu",
        "RE109_sv": "Bondböna",
        "RE110": "Pea residue",
        "RE110_fi": "Hernejäte",
        "RE110_sv": "Ärtavfall",
        "RE111": "Hairy vetch",
        "RE111_fi": "Ruisvirna",
        "RE111_sv": "Luddvicker",
        "RE201": "Generic cereal crop residue",
        "RE201_fi": "Viljakasvijäte",
        "RE201_sv": "Spannmålsavfall",
        "RE202": "Pearl millet residue",
        "RE203": "Maize residue",
        "RE204": "Sorghum residue",
        "RE205": "Wheat residue",
        "RE205_fi": "Vehnäjäte",
        "RE205_sv": "Veteavfall",
        "RE206": "Barley",
        "RE206_fi": "Ohra",
        "RE206_sv": "Korn",
        "RE207": "Rice",
        "RE208": "Rye",
        "RE208_fi": "Ruis",
        "RE208_sv": "Råg",
        "RE301": "Generic grass",
        "RE301_fi": "Ruohokasvi",
        "RE301_sv": "Gräsväxti",
        "RE302": "Bahiagrass",
        "RE303": "Bermudagrass",
        "RE303_fi": "Varvasheinä",
        "RE303_sv": "Hundtandsgräs",
        "RE304": "Switchgrass",
        "RE304_fi": "Lännenhirssi",
        "RE304_sv": "Jungfruhirs",
        "RE305": "brachiaria",
        "RE305_fi": "Viittaheinät",
        "RE305_sv": "Brachiaria",
        "RE306": "forage grasses",
        "RE306_fi": "Nurmikasvit",
        "RE306_sv": "Vallväxter",
        "RE401": "Bush fallow residue",
        "RE402": "Sugarcane",
        "RE403": "Pineapple",
        "RE999": "Decomposed crop residue",
        "RE999_fi": "Maatunut kasvijäte",
        "RE999_sv": "Nedbrutet växtavfall"
    },

    "tillage_implement": {
        "TI001": "V-Ripper",
        "TI002": "Subsoiler",
        "TI002_fi": "Jankkuri",
        "TI002_sv": "Djupluckrare",
        "TI003": "Mould-board plow",
        "TI003_fi": "Kyntöaura",
        "TI003_sv": "Plöja",
        "TI004": "Chisel plow, sweeps",
        "TI005": "Chisel plow, straight point",
        "TI006": "Chisel plow, twisted shovels",
        "TI007": "Disk plow",
        "TI008": "Disk, 1-way",
        "TI009": "Disk, tandem",
        "TI009_fi": "Lautasäes",
        "TI009_sv": "Tallriksharv",
        "TI010": "Disk, double disk",
        "TI011": "Cultivator, field",
        "TI011_fi": "Kultivaattori",
        "TI011_sv": "Kultivator",
        "TI012": "Cultivator, row",
        "TI013": "Cultivator, ridge till",
        "TI014": "Harrow, spike",
        "TI015": "Harrow, tine",
        "TI015_fi": "Joustopiikkiäes",
        "TI015_sv": "S-pinne harv",
        "TI016": "Lister",
        "TI016_fi": "Multain",
        #"TI016_sv": "Multain",
        "TI017": "Bedder",
        "TI018": "Blade cultivator",
        "TI018_fi": "Rivivälihara",
        "TI018_sv": "Radhacka",
        "TI019": "Fertilizer applicator, anhydr",
        "TI020": "Manure injector",
        "TI020_fi": "Lietelannan sijoitusmultain",
        "TI020_sv": "Flytgödsel injektor",
        "TI022": "Mulch treader",
        "TI023": "Plank",
        "TI024": "Roller packer",
        "TI024_fi": "Jyrä",
        "TI024_sv": "Vält",
        "TI025": "Drill, double-disk",
        "TI025_fi": "Kylvökone, kaksoiskiekot",
        "TI025_sv": "Såmaskin, dubbeldisk",
        "TI026": "Drill, deep furrow",
        "TI031": "Drill, no-till",
        "TI031_fi": "Kylvökone, ei muokkausta",
        "TI031_sv": "Såmaskin, ingen bearbetning ?",
        "TI032": "Drill, no-till (into sod)",
        "TI033": "Planter, row",
        "TI033_fi": " Tarkkuuskylvökone",
        #"TI033_sv": "?",
        "TI034": "Planter, no-till",
        "TI035": "Planting stick (hand)",
        "TI036": "Matraca hand planter",
        "TI037": "Rod weeder",
        "TI038": "Rotary hoe",
        "TI038_fi": "Rotary hoe (maajyrsin?)",
        #"TI038_sv": "Åkervält?",
        "TI039": "Roller harrow, cultipacker",
        "TI041": "Moldboard plow 25 cm",
        "TI042": "Moldboard plow 30 cm",
        "TI043": "Strip tillage",
        "TI044": "Tine weeder",
        "TI044_fi": "Rikkaäes",
        #"TI044_sv": "",
        "TI999": "Other",
        "TI999_fi": "Muu",
        "TI999_sv": "Övrig"
    },

    "fertilizer": ap_plaintext,
    "irrigation": ap_plaintext,
    "tillage": ap_plaintext,
    "chemicals": ap_plaintext,
    "org_material_appl_depth": ap_plaintext,

    "planted_crop": crop_codes,
    "harvest_crop": crop_codes
}

for property_list_key, property_list in property_lists.items():
    for property in property_list:
        listed_properties[property] = property_list_key

# Read CSV
csv = pd.read_csv('https://raw.githubusercontent.com/PecanProject/fieldactivity/dev/inst/extdata/display_names.csv', comment='#', usecols=[0, 1, 2, 3])
#print("csv:")
#print(csv)

# Read JSON
with urllib.request.urlopen('https://raw.githubusercontent.com/PecanProject/fieldactivity/dev/inst/extdata/ui_structure.json') as url:
    ui_structure = pyjson5.load(url)

#print("ui_structure:")
#print(json.dumps(ui_structure, indent=4))

def set_choices(target_schema, property):
    property_id = property["code_name"]
    if property_id == "observation_type_vegetation": #and property["code_name"] == "canopy_height":
        print("target_schema:")
        print(target_schema)
        print("property_id:")
        print(property_id)
        print("property:")
        print(property)
        print("")
    # Ignore for now: property["type"] == "fileInput", because we don't yet store the image links in the data
    if "required" in property and property["required"]:
        if "required" not in target_schema:
            target_schema["required"] = []
        target_schema["required"].append(property_id)
    if property_id in banned_properties:
        return
    if "type" in property:
        new_property = {}

        for language_ext, title_dict in [("", code_name_to_disp_name_eng), ("_fi", code_name_to_disp_name_fin), ("_sv", None)]:
            if (title_dict is not None) and (property_id in title_dict):
                new_property[f"title{language_ext}"] = title_dict[property_id]
            if f"{property_id}{language_ext}" in mgmt_operations_variable_name_plaintext:
                fo_title = pydash.lower_first(mgmt_operations_variable_name_plaintext[f"{property_id}{language_ext}"])
                if not (f"title{language_ext}" in new_property):
                    new_property[f"title{language_ext}"] = fo_title
                elif new_property[f"title{language_ext}"] != fo_title:
                    new_property[f"title2{language_ext}"] = fo_title
                
        if property["type"] == "selectInput":
            if type(property['choices']) == list:
                choices = property['choices']
            else:
                choices = csv[csv['category'] == property['choices']]['code_name']
            if type(property['choices']) != list and property['choices'] in choices_appeared_in:
                other = choices_appeared_in[property['choices']]
                if "type" in other:
                    schema["$defs"][choice_list_name[property['choices']]] = {
                        "type": other["type"],
                        "oneOf": other["oneOf"]
                    }
                    other.pop("type")
                    other.pop("oneOf")
                    other["$ref"] = f"#/$defs/{choice_list_name[property['choices']]}"
                new_property["$ref"] = f"#/$defs/{choice_list_name[property['choices']]}"
            else:
                new_property["type"] = "string"
                new_property["oneOf"] = []
                for choice in choices:
                    new_choice = {
                        "const": choice
                    }
                    for language_ext, title_dict in [("", code_name_to_disp_name_eng), ("_fi", code_name_to_disp_name_fin), ("_sv", None)]:
                        if (title_dict is not None) and (choice in title_dict):
                            new_choice[f"title{language_ext}"] = title_dict[choice]
                        if property_id in mgmt_operations_value_plaintext and f"{property_id}{language_ext}" in mgmt_operations_value_plaintext[property_id]:
                            fo_title = pydash.lower_first(mgmt_operations_value_plaintext[property_id][f"{choice}{language_ext}"])
                            if not (f"title{language_ext}" in new_choice):
                                new_choice[f"title{language_ext}"] = fo_title
                            elif new_choice[f"title{language_ext}"] != fo_title:
                                new_choice[f"title2{language_ext}"] = fo_title

                    new_property["oneOf"].append(new_choice)

                if type(property['choices']) != list:
                    choices_appeared_in[property['choices']] = new_property
        elif property["type"] == "textInput" or property["type"] == "textAreaInput":
            new_property["type"] = "string"
            if "placeholder" in property:
                if "x-ui" not in new_property:
                    new_property["x-ui"] = {}
                new_property["x-ui"]["form-type"] = property["type"]
                new_property["x-ui"]["form-placeholder"] = code_name_to_disp_name_eng[property["placeholder"]] if property["placeholder"] in code_name_to_disp_name_eng else 'unknown'
                new_property["x-ui"]["form-placeholder_en"] = code_name_to_disp_name_eng[property["placeholder"]] if property["placeholder"] in code_name_to_disp_name_eng else 'unknown'
                new_property["x-ui"]["form-placeholder_fi"] = code_name_to_disp_name_fin[property["placeholder"]] if property["placeholder"] in code_name_to_disp_name_fin else 'unknown'
        elif property["type"] == "numericInput":
            # TODO: Handle "min" and "max" and "step" (not all may be present)
            if "step" in property and property["step"] == 1:
                new_property["type"] = "integer"
            else:
                new_property["type"] = "number"
            if "min" in property:
                new_property["minimum"] = property["min"]
            if "max" in property:
                new_property["maximum"] = property["max"]
        elif property["type"] == "dateInput": # TODO: Should these be datetimes?
            new_property["type"] = "string"
            new_property["format"] = "date"
        elif property["type"] == "dateRangeInput": # TODO: Should these be datetimes?
            new_property["properties"] = {
                "start_date": {
                    "title": "start date",
                    "title_fi": "alkamispäivä",
                    "title_sv": "startdatum",
                    "type": "string",
                    "format": "date"
                },
                "end_date": {
                    "title": "end date",
                    "title_fi": "päättymispäivä",
                    "title_sv": "slutdatum",
                    "type": "string",
                    "format": "date"
                }
            }
        elif property["type"] == "textOutput":
            target_schema["description"] = code_name_to_disp_name_eng[property["code_name"]] if property["code_name"] in code_name_to_disp_name_eng else 'unknown'
            target_schema["description_en"] = code_name_to_disp_name_eng[property["code_name"]] if property["code_name"] in code_name_to_disp_name_eng else 'unknown'
            target_schema["description_fi"] = code_name_to_disp_name_fin[property["code_name"]] if property["code_name"] in code_name_to_disp_name_fin else 'unknown'
        else:
            target_schema["properties"][property_id] = {"todo": "fixme2"}  
        if new_property:
            target_schema["properties"][property_id] = new_property
    else:
        print("TODO FIXME 3")

choices_appeared_in = {}

schema = {
    "$schema": "http://json-schema.org/draft-07/schema", #"https://json-schema.org/draft/2020-12/schema",
    "$id": "https://raw.githubusercontent.com/hamk-uas/fieldobservatory-data-schemas/main/management-event.schema.json", # Was: "#root"
    "@context": { # See https://www.w3.org/TR/json-ld/#string-internationalization
        "@language": "en",
        "title": { "@id": "dc:title", "@language": "en" }, # TODO: Not at all sure about dc
        "title_fi": { "@id": "dc:title", "@language": "fi" },
        "title_sv": { "@id": "dc:title", "@language": "sv" },
        "description": { "@id": "dc:description", "@language": "en" }, # TODO: Not at all sure about dc
        "description_fi": { "@id": "dc:description", "@language": "fi" },
        "description_sv": { "@id": "dc:description", "@language": "sv" },
        "form-placeholder": { "@id": "fo:form-placeholder", "@language": "en" }, # TODO: Not at all sure about fo
        "form-placeholder_fi": { "@id": "fo:form-placeholder", "@language": "fi" },
        "form-placeholder_sv": { "@id": "fo:form-placeholder", "@language": "sv" }
    },
    "title": "management event",
    'type': 'object',
    "properties": {
        "$schema": {
            "type": "string",
            "format": "url",
            "const": "https://raw.githubusercontent.com/hamk-uas/fieldobservatory-data-schemas/main/management-event.schema.json"
        }        
    },
    "oneOf" : [
    ],
    "$defs" : {        
    },
    "required" : ["$schema"]
}

variable_names = csv #csv[csv['category'] == 'variable_name']
code_name_to_disp_name_eng = {}
code_name_to_disp_name_fin = {}
for index, row in variable_names.iterrows():
    code_name_to_disp_name_eng[row['code_name']] = row['disp_name_eng'].replace("“", "\"").replace("”", "\"").strip()
    code_name_to_disp_name_fin[row['code_name']] = row['disp_name_fin'].replace("“", "\"").replace("”", "\"").strip()
    if (not code_name_to_disp_name_eng[row['code_name']].endswith('.')) or code_name_to_disp_name_eng[row['code_name']].endswith('etc.'):
        code_name_to_disp_name_eng[row['code_name']] = pydash.lower_first(code_name_to_disp_name_eng[row['code_name']])
        code_name_to_disp_name_fin[row['code_name']] = pydash.lower_first(code_name_to_disp_name_fin[row['code_name']])

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
    # Create a sub schema for this particular event type

    sub_schema_title_translations = {}

    for language_ext, title_dict in [("", code_name_to_disp_name_eng), ("_fi", code_name_to_disp_name_fin), ("_sv", None)]:
        if (title_dict is not None) and (row['code_name'] in title_dict):
            sub_schema_title_translations[f"title{language_ext}"] = title_dict[row['code_name']]
        if f"{row['code_name']}{language_ext}" in mgmt_operations_event_choice_plaintext:
            fo_title = pydash.lower_first(mgmt_operations_event_choice_plaintext[f"{row['code_name']}{language_ext}"])
            if not (f"title{language_ext}" in sub_schema_title_translations):
                sub_schema_title_translations[f"title{language_ext}"] = fo_title
            elif sub_schema_title_translations[f"title{language_ext}"] != fo_title:
                sub_schema_title_translations[f"title2{language_ext}"] = fo_title
    
    sub_schema = {
        '$id': f"#{row['code_name']}",
        'title': pydash.lower_first(row['disp_name_eng'].strip()),
        **sub_schema_title_translations,
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
        "required": ['mgmt_operations_event', 'date'] # This list may be expanded further down
    }
    # Get the object describing this event type from the sub_elements list of mgmt_operations_event
    sub_element = ui_structure['form']['mgmt_operations_event']['sub_elements'][row['code_name']]
    # Loop through the properties of the event type specific object
    for sub_element_key, sub_element_value in sub_element.items():
        if "code_name" in sub_element_value:
            # If a property has a code_name then it will be a property in the JSON schema
            property_id = sub_element_value["code_name"] # Get property_id
            # Parse choices for the property
            set_choices(sub_schema, sub_element_value)
            # If the event's property has a property "multiple": true, then it may have a
            # property "sub_elements", which introduces additional dependent properties
            if "multiple" in sub_element_value and sub_element_value["multiple"] and "sub_elements" in sub_element_value:
                # "single" in "sub_elements" introduces new properties always present
                sub_elements = sub_element_value["sub_elements"]
                if "single" in sub_elements:
                    for element_of_single_key, element_of_single_value in sub_elements["single"].items():
                        if "code_name" in element_of_single_value:
                            set_choices(sub_schema, element_of_single_value)
                # "hidden" in "sub_elements" introduces new properties that MAY be present
                # Let's add them all anyhow
                if "hidden" in sub_elements:
                    for element_of_hidden_key, element_of_hidden_value in sub_elements["hidden"].items():
                        if "code_name" in element_of_hidden_value:
                            set_choices(sub_schema, element_of_hidden_value)
        elif "hidden" in sub_element:
            for element_of_hidden_key, element_of_hidden_value in sub_element["hidden"].items():
                if "code_name" in element_of_hidden_value:
                    set_choices(sub_schema, element_of_hidden_value)
        elif row["code_name"] == "observation" and sub_element_key != "condition":
            #print(f"{row['code_name']} {sub_element_key}")
            dummy,conditioning_value,dummy = sub_element_value['condition'].split("'")
            #print(conditioning_value)
            #print(sub_element_value)
            if "allOf" not in sub_schema:
                sub_schema["allOf"] = []
            condition = {
                "if": {
                    "properties": {
                        "observation_type": {
                            "const": conditioning_value
                        }
                    }#,
                    #"required": ["observation_type"]
                },
                "then": {
                    "properties": {}
                }
            }
            sub_schema["allOf"].append(condition)
            for property_id, property in sub_element_value.items():
                if "code_name" in property:
                    set_choices(condition["then"], property)
        else:
            None
            # print(f"{row['code_name']} {sub_element_key}") # TODO handle this
    schema['oneOf'].append(sub_schema)

# Reorder keys in sub schemas
for sub_schema_index, sub_schema in enumerate(schema['oneOf']):
    sub_schema_copy = {}
    for sub_schema_property_id, sub_schema_property in sub_schema.items():
        if sub_schema_property_id in priority_properties:
            sub_schema_copy[sub_schema_property_id] = sub_schema_property
    for sub_schema_property_id, sub_schema_property in sub_schema.items():
        if not (sub_schema_property_id in priority_properties):
            sub_schema_copy[sub_schema_property_id] = sub_schema_property
    schema['oneOf'][sub_schema_index] = sub_schema_copy

# Collect certain properties of sub schemas into lists of objects
for sub_schema_index, sub_schema in enumerate(schema['oneOf']):
    sub_schema_properties_copy = {}
    for property_id, property in sub_schema["properties"].items():
        if property_id in listed_properties:
            list_id = listed_properties[property_id]
            if not (list_id in sub_schema_properties_copy):
                sub_schema_properties_copy[list_id] = {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {}
                    }
                }
            sub_schema_properties_copy[list_id]["items"]["properties"][property_id] = property
            if "required" in sub_schema and property_id in sub_schema["required"]:
                sub_schema["required"].remove(property_id)
                if "required" not in sub_schema_properties_copy[list_id]["items"]:
                    sub_schema_properties_copy[list_id]["items"]["required"] = []
                sub_schema_properties_copy[list_id]["items"]["required"].append(property_id)
                sub_schema_properties_copy[list_id]["minItems"] = 1
                sub_schema["required"].append(list_id)
        else:
            sub_schema_properties_copy[property_id] = property
    schema['oneOf'][sub_schema_index]["properties"] = sub_schema_properties_copy

with open("management-event.schema.json", mode='w', encoding='utf-8') as f:
    json.dump(schema, f, indent=4, ensure_ascii = False)
