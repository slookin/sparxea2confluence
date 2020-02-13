import win32com.client
import logging
import re

logger_mapping = logging.getLogger("mapping")
logger_mapping.setLevel(logging.INFO)
fh = logging.FileHandler('mapping.log')
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger_mapping.addHandler(fh)
logger_mapping.addHandler(ch)

logger_revision_mapping = logging.getLogger("rev_mapping")
logger_revision_mapping .setLevel(logging.INFO)
fh = logging.FileHandler('mapping.log')
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger_revision_mapping.addHandler(fh)
logger_revision_mapping.addHandler(ch)

logger = logging.getLogger("sparx_api")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('html_report.log')
fh.setLevel(logging.DEBUG)

fh_api = logging.FileHandler('sparx_api.log')
fh_api.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
fh_api.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(fh_api)
logger.addHandler(ch)


class EAComponent(dict):
    MANDATORY_TAGS_LIST = ['domain', 'git repository', 'wiki']

    def __repr__(self):
        return 'EA Component '+self["name"]


def open_repository(path, login, password):
    eaApp = win32com.client.Dispatch("EA.App")
    logger.debug("eaApp type: " + str(eaApp))
    eaRep = eaApp.Repository
    if login:
        eaRep.SuppressSecurityDialog = True
        eaRep.OpenFile2(path, login, password)
    else:
        #eaRep.ChangeLoginUser(login,password)
        eaRep.OpenFile(path)
    return eaRep

def single_search(eaRep, term, search_type):
    search_res = eaRep.GetElementsByQuery(search_type, term)
    if search_res.Count == 1:
        element = search_res.GetAt(0)
    else:
        logger.warning("term: "+term+" not found or found multipletimes")
        raise ValueError("term: "+term+" not found or found multipletimes")
    return element

def diagram2image(eaRep, guid, filepath, filename=""):
    if filename=="":
        filename=guid+".png"
    diagram = eaRep.GetDiagramByGUID(guid)
    eaRep.OpenDiagram(diagram.DiagramID)
    full_path = filepath+'\\'+filename
    eaRep.GetProjectInterface().SaveDiagramImageToFile(full_path)
    logger.debug("image exported: "+full_path)
    return [full_path,filename]

# return list of names of parents packages. input package ID (not guid)
def recursive_list_parents(eaRep, package_id):
    list = []
    pkg = eaRep.GetPackageByID(package_id)
    list.append(pkg.Name)
    while pkg.ParentID != 0:
        pkg = eaRep.GetPackageByID(pkg.ParentID)
        list.append(pkg.Name)
    return list


# return list of diagram guid by name
def diagram_guids_by_name(eaRep, name):
    res = eaRep.SQLQuery("SELECT ea_guid FROM t_diagram WHERE Name='"+name+"'") #@TODO !!!! SQL injection
    return re.findall('<EA_GUID>(.*?)<', res, re.IGNORECASE)


# return first diagram in model by name
def diagram_guid_in_model_by_name(eaRep, diagram_name, model_name, version=""):
    dia_list = diagram_guids_by_name(eaRep, diagram_name)
    logger.debug("found list of guids:" + str(dia_list))
    if len(dia_list)==0:
        logger.error("Digram not found: "+diagram_name)
    for guid in dia_list:
        dia = eaRep.GetDiagramByGuid(guid)
        if model_name == recursive_list_parents(eaRep, dia.PackageID)[-1]:
            if version != "":
                if dia.version == version:
                    return guid
            else:
                return guid
    return None

def getInterfaceByID(eaRep, id):
    target_element = eaRep.getElementByID(id)
    service = {}
    service["reference"] = target_element.Name
    service["description"] = target_element.Notes
    service["type"] = target_element.Stereotype
    return service

def getElementByID(eaRep, id, services = True):
    element = eaRep.getElementByID(id)
    logger.debug("element.Name: " + str(element.Name))
    component = EAComponent()
    component["id"] = element.ElementID
    component["guid"] = element.ElementGUID
    component["type"] = element.Type
    component["version"] = element.Version
    component["title"] = element.Name
    component["alias"] = component["name"] = element.Alias
    component["description"] = element.Notes
    component["stereotype"] = element.Stereotype


    tags = element.TaggedValues
    for tag_name in component.MANDATORY_TAGS_LIST:
        ea_tag = tags.GetByName(tag_name)
        if ea_tag:
            component[tag_name] = ea_tag.Value
        else:
            component[tag_name] = ""
            # logger.warning("element :" + component["title"] + "  has no tag: "+ tag_name)
    component["provided-services"] = []
    component["dependencies"] = []
    if services:
        for k in range(element.Connectors.Count):
            connector = element.Connectors.getAt(k)
            service = getInterfaceByID(eaRep, connector.SupplierID)
            if connector.Type == 'Realisation':
                component["provided-services"].append(service)
                if connector.Type == 'Usage':
                    component["dependencies"].append(service)
    return component