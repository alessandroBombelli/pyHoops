# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 15:36:40 2019

@author: abombelli
"""

################################################################
### Web parsing routine to access and store the play-by-play ###
### report of basketball games of the Italian LBA            ###
################################################################

import numpy as np
import requests
from bs4 import BeautifulSoup
import lxml.html as lh
from lxml import etree
import pandas as pd
import os
import openpyxl

cwd         = os.getcwd() 

thisUrl = 'http://web.legabasket.it/game/1672352/acqua_s_bernardo_cant__-sidigas_avellino_83:73/pbp'
        
    
p    = requests.get(thisUrl)

if p.status_code < 400:
    l = []
    soup = BeautifulSoup(p.text,'html.parser')
    table = soup.find('table', attrs={'border':'0'})
    
    table_rows = table.find_all('tr')
    for tr in table_rows:
        td = tr.find_all('td')
        row = [tr.text for tr in td]
        if len(row)>0 and len(row)==3:
            l.append(row)
            
df = pd.DataFrame(np.array(l))


for i in range(0,int(len(df))):
    for j in range(0,int(len(df.loc[i]))):
        df.loc[i][j] = df.loc[i][j].encode('ascii','ignore')
        df.loc[i][j] = df.loc[i][j].replace(' ','')
    
df.to_excel(l[0][0] + '_' + l[0][2] + '.xlsx',sheet_name='Sheet_name_1')

