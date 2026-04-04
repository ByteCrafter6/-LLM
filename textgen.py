import os
import random
from collections import defalutdict

#Calea catre folderul cu fisierele tale(inlocuieste cu calea ta)
folder_path= "calea_catre_folderul_tau"


#Citirea tuturor fiserelor text din folder
combined_text=""
for filename in os.listdir(folder_path):
    if filename.endswith('.txt'):
        with open(os.path.join(folder_path,filename),'r',encoding='utf-8') as f:
            combined_text+=f.read()+""