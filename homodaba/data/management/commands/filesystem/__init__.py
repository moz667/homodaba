import re

"""
Los caracteres no permitidos en sistemas de archivos de windows son: 
" \ / : | < > * ?
Para mas info mirar en: 
https://docs.microsoft.com/en-us/rest/api/storageservices/naming-and-referencing-shares--directories--files--and-metadata#directory-and-file-names
"""
def clean_filename_for_samba_share(filename):
    return re.sub(r'["\\\/:|<>\*\?]', '', filename)