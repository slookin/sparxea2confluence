from sparx_lib import logger, single_search
from sparx_lib import open_repository, diagram_guids_by_name, diagram_guid_in_model_by_name, diagram2image, getInterfaceByID, getElementByID
from confluence.api import ConfluenceAPI
import configparser
import os
import json
import re
from mako.template import Template
import logging

logger = logging.getLogger("documentation")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('documentation.log')
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

c = configparser.ConfigParser()
c.read('documentation.cfg')

if os.environ['USERNAME'] == "slukin":
    config = c["PROD"]
else:
    config = c["TEST"]

FILE_PATH = config["FILE_PATH"]
MODEL = config["MODEL"]
DOC_RULES = config["DOC_RULES"]
CONFLUENCE_API = config["CONFLUENCE_API"]
CONFLUENCE_USER = config["CONFLUENCE_USER"]
CONFLUENCE_PASSWORD = config["CONFLUENCE_PASSWORD"]
CONFLUENCE_SPACE = config["CONFLUENCE_SPACE"]
TEMPLATE_PATH = config["TEMPLATE_PATH"]



eaRep = open_repository(MODEL, "readonly", "readonly")
logger.debug("eap opened")
models = eaRep.Models

api = ConfluenceAPI(url_api=CONFLUENCE_API, user=CONFLUENCE_USER, password=CONFLUENCE_PASSWORD, space_key=CONFLUENCE_SPACE)


with open(DOC_RULES) as f:
    rules = json.load(f)

for rule in rules:
    logger.debug("rule:"+str(rule))
    if "version" not in rule.keys():
        rule["version"] = ""

    if "type" in rule and rule["type"] == "diagram":
        guid = diagram_guid_in_model_by_name(eaRep, rule["diagram_name"], rule["model_name"])
        if guid is None:
            logger.warning("no diagram found, rule skipped")
            continue
        ea_diagram = eaRep.GetDiagramByGUID(guid)
        [path, filename] = diagram2image(eaRep, guid, FILE_PATH)
        page_id = api.page_id_by_title(rule["confluence"]["page_name"])
        page_obj = api.page_by_id(page_id)
        logger.debug("page_id: " + str(page_id))

        api.recreate_attachment(page_id=page_id, file_path=path, attachment_name=filename)
        diagram = {'image':filename, 'title': ea_diagram.Name,  'notes': ea_diagram.Notes, 'guid':re.sub("[{}]","",guid)}
        context={'diagram':diagram}
        template = Template(filename=TEMPLATE_PATH + rule["confluence"]["template_name"], input_encoding='utf-8')
        html = template.render(**context)
        version = int(page_obj["version"]["number"]) + 1
        api.page_update(id=page_id, title=rule["confluence"]["page_name"], version=version, html=html)

    if "type" in rule and rule["type"] == "diagram_list":
        page_id = api.page_id_by_title(rule["confluence"]["page_name"])
        page_obj = api.page_by_id(page_id)
        logger.debug("page_id: " + str(page_id))
        diagram_list=[]
        for diagram_name in rule["diagram_name"]:
            guid = diagram_guid_in_model_by_name(eaRep, diagram_name, rule["model_name"], rule["version"])
            ea_diagram = eaRep.GetDiagramByGUID(guid)
            [path, filename] = diagram2image(eaRep, guid, FILE_PATH)
            api.recreate_attachment(page_id=page_id, file_path=path, attachment_name=filename)
            diagram = {'image': filename, 'title': ea_diagram.Name, 'notes': ea_diagram.Notes,
                   'guid': re.sub("[{}]", "", guid)}
            diagram_list.append(diagram)

        context = {'diagram_list': diagram_list, 'page_title': rule["page_title"]}
        template = Template(filename=TEMPLATE_PATH + rule["confluence"]["template_name"], input_encoding='utf-8')
        html = template.render(**context)
        version = int(page_obj["version"]["number"]) + 1
        api.page_update(id=page_id, title=rule["confluence"]["page_name"], version=version, html=html)

    if "type" in rule and rule["type"] == "diagram_with_components":
        guid = diagram_guid_in_model_by_name(eaRep, rule["diagram_name"], rule["model_name"])
        ea_diagram = eaRep.GetDiagramByGUID(guid)
        [path, filename] = diagram2image(eaRep, guid, FILE_PATH)

        page_id = api.page_id_by_title(rule["confluence"]["page_name"])
        page_obj = api.page_by_id(page_id)
        logger.debug("page_id: " + str(page_id))

        api.recreate_attachment(page_id=page_id, file_path=path, attachment_name=filename)
        components = []
        for i in range(ea_diagram.DiagramObjects.Count):
            do = ea_diagram.DiagramObjects.getAt(i)
            element = getElementByID(eaRep, do.ElementID)
            if element["stereotype"] == 'microservice' or element["stereotype"] == 'microserviceUI':
                components.append(element)

        diagram = {'image': filename, 'title': ea_diagram.Name, 'notes': ea_diagram.Notes, 'guid': re.sub("[{}]","",guid), 'components':components}
        context = {'diagram': diagram}
        template = Template(filename=TEMPLATE_PATH + rule["confluence"]["template_name"], input_encoding='utf-8')

        html = template.render(**context)
        version = int(page_obj["version"]["number"]) + 1
        api.page_update(id=page_id, title=rule["confluence"]["page_name"], version=version, html=html)

    if page_obj and "_links" in page_obj.keys():
        print("page url: " + page_obj["_links"]["base"] + page_obj["_links"]["webui"])

try:
    eaRep.Exit()
except:
    pass



