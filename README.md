# sparxea2confluence
automatization tool, allow to export diagrams from Sparx Enterprise Architect to Confluence

## configuration
### production / test enviroment
Use command line attribute "-prod" for enable production configuration
### documentation.cfg
- FILE_PATH - place for temporary files
- MODEL - full path to EA model (eap or feap or ODBC or HTTP link)
- DOC_RULES - list of pages in Confluence
- CONFLUENCE_USER
- CONFLUENCE_PASSWORD
- CONFLUENCE_API  - For exmaple: http://localhost:8090/rest/api/
- CONFLUENCE_SPACE - Confluence Space
- TEMPLATE_PATH  - full path to template folders

### DOC_RULES
* list of dict
* dict structure

```json
"type": one of ["diagram", "diagram_list", "diagram_with_components"]
      "diagram_name": name of diagram in Sparx EA model ,
      "model_name":  model name in Sparx,
	  "version" : optional, version of diagram
      "confluence": {
         "page_name": Page name,
         "space": confluence space,
         "template_name": page template
        }
    },
```


### Compatibilty
It was tested with Sparx EA 13.0, Sparx EA 13.5 and Sparx EA 15.0

Sparx EA 13.5 has a small problem with authentication in repositories.