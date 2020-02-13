import requests
import json
import base64
import logging

logger = logging.getLogger("confluence_api")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('confluence_api.log')
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


class ConfluenceAPI:

    def __init__(self, url_api, user, password, space_key):
        self.url_api = url_api
        self.url_content = self.url_api +"content"
        self.user = user
        self.password = password
        self.space_key = space_key

    # Create the basic auth for use in the authentication header
    def auth_header(self):
        auth = base64.b64encode(bytes('{}:{}'.format(self.user, self.password), "utf-8"))
        return {'Authorization': 'Basic '+auth.decode('ascii')}

    def page_id_by_title(self, title):
        headers = self.auth_header()
        headers['Content-Type'] = 'application/json'
        params = {"title":title}
        r = requests.get(url=self.url_content, params=params, headers=headers)
    #    print(r.url)
     #   print(r.text)
      #  print(r)
        obj = json.loads(r.text)
        return obj["results"][0]["id"]

    def page_by_id(self, id):
        headers = self.auth_header()
        headers['Content-Type'] = 'application/json'
        r = requests.get(url=self.url_content+"/"+str(id),headers=headers)
        return json.loads(r.text)

    def create_page(self, page_title, parent_page_id,  page_html):
        headers = self.auth_header()
        headers['Content-Type'] = 'application/json'
        data = {
            'type': 'page',
            'title': page_title,
            'ancestors': [{'id': parent_page_id}],
            'space': {'key': self.space_key},
            'body': {
                'storage': {
                    'value': page_html,
                    'representation': 'storage',
                }
            }
        }
        r = requests.post(url=self.url_content, data=json.dumps(data), headers=headers)
        #Consider any status other than 2xx an error
        if not r.status_code // 100 == 2:
            logger.error("Error: Unexpected response {}".format(r))
        else:
            logger.debug('Page Created!')

    def page_update(self, id, title, version, html):
        headers = self.auth_header()
        headers['Content-Type'] = 'application/json'
        data = {
            'type': 'page',
            'id': id,
            'title': title,
            'space': {'key': self.space_key},
            'version': {'number': version},
            'body': {
                'storage': {
                    'value': html,
                    'representation': 'storage',
                }
            }
        }
        #print(json.dumps(data))
        r = requests.put(url=self.url_content + "/" + str(id), data=json.dumps(data), headers=headers)
        #print(r.url)
        #print(r.request.headers)
        #print(r.text)
        if not r.status_code // 100 == 2:
            logger.error("Error: Unexpected response {}".format(r))
        else:
            logger.debug('Page Updated!')

    def recreate_attachment(self, page_id, file_path, attachment_name):
        headers = self.auth_header()
        headers["X-Atlassian-Token"] = "nocheck"

        response = requests.get(self.url_content + "/" + page_id + "/child/attachment", headers=headers)
        if 'results' in json.loads(response.text):
         for attachment in json.loads(response.text)['results']:
                if attachment['title'] == attachment_name:
                    requests.delete(self.url_content + "/" + attachment['id'], headers=headers)
        files = {'file': (attachment_name, open(file_path, 'rb'))}
        r = requests.post(url=self.url_content + "/" + str(page_id) + "/child/attachment", files=files, headers=headers)
        #print(r.url)
        #print(r.request.headers)
        #print(r.text)
        # r.raise_for_status()

        if not r.status_code // 100 == 2:
            logger.error("Error: Unexpected response {}".format(r))
        else:
            logger.debug('attach created')
