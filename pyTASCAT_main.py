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

##################################################################
### Determine starting 5 for the 2 teams from box-score tables ###
##################################################################

thisUrlBoxscore = 'http://web.legabasket.it/game/1672352/acqua_s_bernardo_cant__-sidigas_avellino_83:73'
pBoxscore       = requests.get(thisUrlBoxscore)

if pBoxscore.status_code < 400:
    lpBoxscoreHomeTeam = []
    lpBoxscoreAwayTeam = []
    soupBoxscore       = BeautifulSoup(pBoxscore.text,'html.parser')
    tablepBoxscore     = soupBoxscore.find_all('table', attrs={'border':'1'})
    tableHomeTeam      = tablepBoxscore[0]
    tableAwayTeam      = tablepBoxscore[1]
    
    lpBoxscoreHomeTeam = []
    table_rows         = tableHomeTeam.find_all('tr')
    for tr in table_rows:
        td = tr.find_all('td')
        row = [tr.text for tr in td]
        if len(row)>0:
            lpBoxscoreHomeTeam.append(row) 
            
    dfHomeTeam = pd.DataFrame(np.array(lpBoxscoreHomeTeam))
    
    lpBoxscoreAwayTeam = []
    table_rows         = tableAwayTeam.find_all('tr')
    for tr in table_rows:
        td = tr.find_all('td')
        row = [tr.text for tr in td]
        if len(row)>0:
            lpBoxscoreAwayTeam.append(row) 
            
    dfAwayTeam = pd.DataFrame(np.array(lpBoxscoreAwayTeam))
    
#%%

# For the home team, find the starting five
starting_five_homeTeam = []
for i in range(0,int(len(dfHomeTeam))):
    if dfHomeTeam.loc[i][0] == '*':
        dummy  = dfHomeTeam.loc[i][2].encode('ascii','ignore')
        dummy2 = dummy.replace(' ','')
        starting_five_homeTeam.append(dummy2)
        
# For the away team, find the starting five
starting_five_awayTeam = []
for i in range(0,int(len(dfAwayTeam))):
    if dfAwayTeam.loc[i][0] == '*':
        dummy  = dfAwayTeam.loc[i][2].encode('ascii','ignore')
        dummy2 = dummy.replace(' ','')
        starting_five_awayTeam.append(dummy2)

# Check when the starting five of the home team is on/off the court
in_out_startingFive_homeTeam = []
for i in range(0,int(len(starting_five_homeTeam))):
    thisPlayer      = starting_five_homeTeam[i]
    thisPlayerOnOff = []
    for j in range(0,int(len(df))):
        if thisPlayer in df.loc[j][0] and 'sostituisce' in df.loc[j][0]:
            thisPlayerOnOff.append([df.loc[j][0],j])
    in_out_startingFive_homeTeam.append(thisPlayerOnOff)
    
# Check when the starting five of the away team is on/off the court
in_out_startingFive_awayTeam = []
for i in range(0,int(len(starting_five_awayTeam))):
    thisPlayer      = starting_five_awayTeam[i]
    thisPlayerOnOff = []
    for j in range(0,int(len(df))):
        if thisPlayer in df.loc[j][2] and 'sostituisce' in df.loc[j][2]:
            thisPlayerOnOff.append([df.loc[j][2],j])
    in_out_startingFive_awayTeam.append(thisPlayerOnOff)

starters_homeTeam_allPlays         = []
starters_homeTeam_allPlays_oppTeam = []

for i in range(0,int(len(starting_five_homeTeam))):
    this_starter_homeTeam_Plays         = []
    this_starter_homeTeam_Plays_oppTeam = []
    thisPlayerInOutAll                  = in_out_startingFive_homeTeam[i]
    thisPlayerInOut                     = []
    for j in range(0,int(len(thisPlayerInOutAll))):
        thisPlayerInOut.append(thisPlayerInOutAll[j][1])
        
    this_starter_homeTeam_Plays.append(list(df.loc[1:thisPlayerInOut[0]][0])) 
    this_starter_homeTeam_Plays_oppTeam.append(list(df.loc[1:thisPlayerInOut[0]][2]))
        
    # even number of out/in: the starting player ends the game as well
    if np.mod(int(len(thisPlayerInOut)),2) == 0:
        for j in range(0,int(len(thisPlayerInOut))):
            if np.mod(j,2) == 0:
                pass
            else:
                if j == int(len(thisPlayerInOut)-1):
                    this_starter_homeTeam_Plays.append(list(df.loc[thisPlayerInOut[j]:len(df)][0]))
                    this_starter_homeTeam_Plays_oppTeam.append(list(df.loc[thisPlayerInOut[j]:len(df)][2]))
                else:
                    this_starter_homeTeam_Plays.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][0]))
                    this_starter_homeTeam_Plays_oppTeam.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][2]))
    # odd number of out/in: the starting player does not end the game
    else:
        for j in range(0,int(len(thisPlayerInOut)-1)):
            if np.mod(j,2) == 0:
                pass
            else:
                this_starter_homeTeam_Plays.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][0]))
                this_starter_homeTeam_Plays_oppTeam.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][2]))
    starters_homeTeam_allPlays.append(this_starter_homeTeam_Plays)
    starters_homeTeam_allPlays_oppTeam.append(this_starter_homeTeam_Plays_oppTeam)
    
###################################################
# Stats for the home team starting five (own stats)
###################################################
all_stats_homeTeam_startingFive         = []
for i in range(0,int(len(starting_five_homeTeam))):
    for j in range(0,int(len(starters_homeTeam_allPlays[i]))):
        _1p_made                  = 0
        _1p_attempted             = 0
        _2p_made                  = 0
        _2p_attempted             = 0
        dunk                      = 0
        _3p_made                  = 0
        _3p_attempted             = 0
        def_rebound               = 0
        off_rebound               = 0
        assist                    = 0
        steal                     = 0
        turnover                  = 0
        block_made                = 0
        block_received            = 0
        foul_made                 = 0
        foul_received             = 0
        for k in range(0,int(len(starters_homeTeam_allPlays[i][j]))):
            
            if 'Tiroliberosbagliato' in starters_homeTeam_allPlays[i][j][k]:
                _1p_attempted += 1
            elif 'Tiroliberosegnato' in starters_homeTeam_allPlays[i][j][k]:
                _1p_attempted += 1
                _1p_made += 1
            elif ('Tirosbagliatodasotto' in starters_homeTeam_allPlays[i][j][k]
                or 'Tirosbagliatodafuori' in starters_homeTeam_allPlays[i][j][k]):
                _2p_attempted += 1
            elif ('Canestrodasotto' in starters_homeTeam_allPlays[i][j][k]
                  or 'Canestrodafuori' in starters_homeTeam_allPlays[i][j][k]):
                _2p_attempted += 1
                _2p_made      += 1
            elif 'Schiacciata' in starters_homeTeam_allPlays[i][j][k]:
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            elif 'Tirosbagliatoda3punti' in starters_homeTeam_allPlays[i][j][k]:
                _3p_attempted += 1
            elif 'Canestroda3punti' in starters_homeTeam_allPlays[i][j][k]:
                _3p_attempted += 1
                _3p_made += 1
            elif 'Rimbalzodifensivo' in starters_homeTeam_allPlays[i][j][k]:
                def_rebound += 1
            elif 'Rimbalzooffensivo' in starters_homeTeam_allPlays[i][j][k]:
                off_rebound += 1
            elif 'Assist' in starters_homeTeam_allPlays[i][j][k]:
                assist += 1
            elif 'Pallarecuperata' in starters_homeTeam_allPlays[i][j][k]:
                steal += 1
            elif 'Pallapersa' in starters_homeTeam_allPlays[i][j][k]:
                turnover += 1
            elif 'Stoppata' in starters_homeTeam_allPlays[i][j][k]:
                block_made += 1 
            elif 'StoppataSubita' in starters_homeTeam_allPlays[i][j][k]:
                block_received += 1 
            elif 'Fallocommesso' in starters_homeTeam_allPlays[i][j][k]:
                foul_made += 1     
            elif 'Fallosubito' in starters_homeTeam_allPlays[i][j][k]:
                foul_received += 1 
        all_stats_homeTeam_startingFive.append([starting_five_homeTeam[i],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received])


df_homeTeam_startingFive_homeTeamStats = pd.DataFrame(np.array(all_stats_homeTeam_startingFive))
df_homeTeam_startingFive_homeTeamStats.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
              'dreb','oreb','ass','st','to','blk','blkag','f','frec']
df_homeTeam_startingFive_homeTeamStats.to_excel(os.path.join(cwd,'homeTeam_homeTeamStats_StartingFive.xlsx'),
      sheet_name='Sheet_name_1')

#############################################################
# Stats for the home team starting five (opposing team stats)
#############################################################
all_stats_homeTeam_startingFive_oppTeam = []
for i in range(0,int(len(starting_five_homeTeam))):
    for j in range(0,int(len(starters_homeTeam_allPlays_oppTeam[i]))):
        _1p_made                  = 0
        _1p_attempted             = 0
        _2p_made                  = 0
        _2p_attempted             = 0
        dunk                      = 0
        _3p_made                  = 0
        _3p_attempted             = 0
        def_rebound               = 0
        off_rebound               = 0
        assist                    = 0
        steal                     = 0
        turnover                  = 0
        block_made                = 0
        block_received            = 0
        foul_made                 = 0
        foul_received             = 0
        for k in range(0,int(len(starters_homeTeam_allPlays_oppTeam[i][j]))):
            
            if 'Tiroliberosbagliato' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                _1p_attempted += 1
            elif 'Tiroliberosegnato' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                _1p_attempted += 1
                _1p_made += 1
            elif ('Tirosbagliatodasotto' in starters_homeTeam_allPlays_oppTeam[i][j][k]
                or 'Tirosbagliatodafuori' in starters_homeTeam_allPlays_oppTeam[i][j][k]):
                _2p_attempted += 1
            elif ('Canestrodasotto' in starters_homeTeam_allPlays_oppTeam[i][j][k]
                  or 'Canestrodafuori' in starters_homeTeam_allPlays_oppTeam[i][j][k]):
                _2p_attempted += 1
                _2p_made      += 1
            elif 'Schiacciata' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            elif 'Tirosbagliatoda3punti' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                _3p_attempted += 1
            elif 'Canestroda3punti' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                _3p_attempted += 1
                _3p_made += 1
            elif 'Rimbalzodifensivo' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                def_rebound += 1
            elif 'Rimbalzooffensivo' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                off_rebound += 1
            elif 'Assist' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                assist += 1
            elif 'Pallarecuperata' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                steal += 1
            elif 'Pallapersa' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                turnover += 1
            elif 'Stoppata' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                block_made += 1 
            elif 'StoppataSubita' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                block_received += 1 
            elif 'Fallocommesso' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                foul_made += 1     
            elif 'Fallosubito' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                foul_received += 1 
        all_stats_homeTeam_startingFive_oppTeam.append([starting_five_homeTeam[i],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received])


df_homeTeam_startingFive_oppTeamStats = pd.DataFrame(np.array(all_stats_homeTeam_startingFive_oppTeam))
df_homeTeam_startingFive_oppTeamStats.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
              'dreb','oreb','ass','st','to','blk','blkag','f','frec']
df_homeTeam_startingFive_oppTeamStats.to_excel(os.path.join(cwd,'homeTeam_awayTeamStats_StartingFive.xlsx'),
      sheet_name='Sheet_name_1')

#################
### AWAY TEAM ###
#################
starters_awayTeam_allPlays         = []
starters_awayTeam_allPlays_oppTeam = []

for i in range(0,int(len(starting_five_awayTeam))):
    this_starter_awayTeam_Plays         = []
    this_starter_awayTeam_Plays_oppTeam = []
    thisPlayerInOutAll                  = in_out_startingFive_awayTeam[i]
    thisPlayerInOut                     = []
    for j in range(0,int(len(thisPlayerInOutAll))):
        thisPlayerInOut.append(thisPlayerInOutAll[j][1])
        
    this_starter_awayTeam_Plays.append(list(df.loc[1:thisPlayerInOut[0]][2])) 
    this_starter_awayTeam_Plays_oppTeam.append(list(df.loc[1:thisPlayerInOut[0]][0]))
        
    # even number of out/in: the starting player ends the game as well
    if np.mod(int(len(thisPlayerInOut)),2) == 0:
        for j in range(0,int(len(thisPlayerInOut))):
            if np.mod(j,2) == 0:
                pass
            else:
                if j == int(len(thisPlayerInOut)-1):
                    this_starter_awayTeam_Plays.append(list(df.loc[thisPlayerInOut[j]:len(df)][2]))
                    this_starter_awayTeam_Plays_oppTeam.append(list(df.loc[thisPlayerInOut[j]:len(df)][0]))
                else:
                    this_starter_awayTeam_Plays.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][2]))
                    this_starter_awayTeam_Plays_oppTeam.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][0]))
    # odd number of out/in: the starting player does not end the game
    else:
        for j in range(0,int(len(thisPlayerInOut)-1)):
            if np.mod(j,2) == 0:
                pass
            else:
                this_starter_awayTeam_Plays.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][2]))
                this_starter_awayTeam_Plays_oppTeam.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][0]))
    starters_awayTeam_allPlays.append(this_starter_awayTeam_Plays)
    starters_awayTeam_allPlays_oppTeam.append(this_starter_awayTeam_Plays_oppTeam)

###################################################
# Stats for the away team starting five (own stats)
###################################################
all_stats_awayTeam_startingFive         = []
for i in range(0,int(len(starting_five_awayTeam))):
    for j in range(0,int(len(starters_awayTeam_allPlays[i]))):
        _1p_made                  = 0
        _1p_attempted             = 0
        _2p_made                  = 0
        _2p_attempted             = 0
        dunk                      = 0
        _3p_made                  = 0
        _3p_attempted             = 0
        def_rebound               = 0
        off_rebound               = 0
        assist                    = 0
        steal                     = 0
        turnover                  = 0
        block_made                = 0
        block_received            = 0
        foul_made                 = 0
        foul_received             = 0
        for k in range(0,int(len(starters_awayTeam_allPlays[i][j]))):
            
            if 'Tiroliberosbagliato' in starters_awayTeam_allPlays[i][j][k]:
                _1p_attempted += 1
            elif 'Tiroliberosegnato' in starters_awayTeam_allPlays[i][j][k]:
                _1p_attempted += 1
                _1p_made += 1
            elif ('Tirosbagliatodasotto' in starters_awayTeam_allPlays[i][j][k]
                or 'Tirosbagliatodafuori' in starters_awayTeam_allPlays[i][j][k]):
                _2p_attempted += 1
            elif ('Canestrodasotto' in starters_awayTeam_allPlays[i][j][k]
                  or 'Canestrodafuori' in starters_awayTeam_allPlays[i][j][k]):
                _2p_attempted += 1
                _2p_made      += 1
            elif 'Schiacciata' in starters_awayTeam_allPlays[i][j][k]:
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            elif 'Tirosbagliatoda3punti' in starters_awayTeam_allPlays[i][j][k]:
                _3p_attempted += 1
            elif 'Canestroda3punti' in starters_awayTeam_allPlays[i][j][k]:
                _3p_attempted += 1
                _3p_made += 1
            elif 'Rimbalzodifensivo' in starters_awayTeam_allPlays[i][j][k]:
                def_rebound += 1
            elif 'Rimbalzooffensivo' in starters_awayTeam_allPlays[i][j][k]:
                off_rebound += 1
            elif 'Assist' in starters_awayTeam_allPlays[i][j][k]:
                assist += 1
            elif 'Pallarecuperata' in starters_awayTeam_allPlays[i][j][k]:
                steal += 1
            elif 'Pallapersa' in starters_awayTeam_allPlays[i][j][k]:
                turnover += 1
            elif 'Stoppata' in starters_awayTeam_allPlays[i][j][k]:
                block_made += 1 
            elif 'StoppataSubita' in starters_awayTeam_allPlays[i][j][k]:
                block_received += 1 
            elif 'Fallocommesso' in starters_awayTeam_allPlays[i][j][k]:
                foul_made += 1     
            elif 'Fallosubito' in starters_awayTeam_allPlays[i][j][k]:
                foul_received += 1 
        all_stats_awayTeam_startingFive.append([starting_five_awayTeam[i],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received])


df_awayTeam_startingFive_awayTeamStats = pd.DataFrame(np.array(all_stats_awayTeam_startingFive))
df_awayTeam_startingFive_awayTeamStats.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
              'dreb','oreb','ass','st','to','blk','blkag','f','frec']
df_awayTeam_startingFive_awayTeamStats.to_excel(os.path.join(cwd,'awayTeam_awayTeamStats_StartingFive.xlsx'),
      sheet_name='Sheet_name_1')

#############################################################
# Stats for the away team starting five (opposing team stats)
#############################################################
all_stats_awayTeam_startingFive_oppTeam         = []
for i in range(0,int(len(starting_five_awayTeam))):
    for j in range(0,int(len(starters_awayTeam_allPlays_oppTeam[i]))):
        _1p_made                  = 0
        _1p_attempted             = 0
        _2p_made                  = 0
        _2p_attempted             = 0
        dunk                      = 0
        _3p_made                  = 0
        _3p_attempted             = 0
        def_rebound               = 0
        off_rebound               = 0
        assist                    = 0
        steal                     = 0
        turnover                  = 0
        block_made                = 0
        block_received            = 0
        foul_made                 = 0
        foul_received             = 0
        for k in range(0,int(len(starters_awayTeam_allPlays_oppTeam[i][j]))):
            
            if 'Tiroliberosbagliato' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                _1p_attempted += 1
            elif 'Tiroliberosegnato' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                _1p_attempted += 1
                _1p_made += 1
            elif ('Tirosbagliatodasotto' in starters_awayTeam_allPlays_oppTeam[i][j][k]
                or 'Tirosbagliatodafuori' in starters_awayTeam_allPlays_oppTeam[i][j][k]):
                _2p_attempted += 1
            elif ('Canestrodasotto' in starters_awayTeam_allPlays_oppTeam[i][j][k]
                  or 'Canestrodafuori' in starters_awayTeam_allPlays_oppTeam[i][j][k]):
                _2p_attempted += 1
                _2p_made      += 1
            elif 'Schiacciata' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            elif 'Tirosbagliatoda3punti' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                _3p_attempted += 1
            elif 'Canestroda3punti' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                _3p_attempted += 1
                _3p_made += 1
            elif 'Rimbalzodifensivo' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                def_rebound += 1
            elif 'Rimbalzooffensivo' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                off_rebound += 1
            elif 'Assist' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                assist += 1
            elif 'Pallarecuperata' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                steal += 1
            elif 'Pallapersa' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                turnover += 1
            elif 'Stoppata' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                block_made += 1 
            elif 'StoppataSubita' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                block_received += 1 
            elif 'Fallocommesso' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                foul_made += 1     
            elif 'Fallosubito' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                foul_received += 1 
        all_stats_awayTeam_startingFive_oppTeam.append([starting_five_awayTeam[i],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received])


df_awayTeam_startingFive_homeTeamStats = pd.DataFrame(np.array(all_stats_awayTeam_startingFive_oppTeam))
df_awayTeam_startingFive_homeTeamStats.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
              'dreb','oreb','ass','st','to','blk','blkag','f','frec']
df_awayTeam_startingFive_homeTeamStats.to_excel(os.path.join(cwd,'awayTeam_homeTeamStats_StartingFive.xlsx'),
      sheet_name='Sheet_name_1')

#####################
### BENCH PLAYERS ###
#####################

# For the home team, find the bench players
bench_homeTeam_all = []
for i in range(0,int(len(dfHomeTeam))):
    if (dfHomeTeam.loc[i][0] == '' and dfHomeTeam.loc[i][2] != 'Squadra'
        and dfHomeTeam.loc[i][2] != 'Totali'):
        dummy  = dfHomeTeam.loc[i][2].encode('ascii','ignore')
        dummy2 = dummy.replace(' ','')
        bench_homeTeam_all.append(dummy2)
        
# For the away team, find the bench players
bench_awayTeam_all = []
for i in range(0,int(len(dfAwayTeam))):
    if (dfAwayTeam.loc[i][0] == '' and dfAwayTeam.loc[i][2] != 'Squadra'
        and dfAwayTeam.loc[i][2] != 'Totali'):
        dummy  = dfAwayTeam.loc[i][2].encode('ascii','ignore')
        dummy2 = dummy.replace(' ','')
        bench_awayTeam_all.append(dummy2)

# Check when the bench of the home team is on/off the court
bench_homeTeam        = []
in_out_bench_homeTeam = []
for i in range(0,int(len(bench_homeTeam_all))):
    thisPlayer      = bench_homeTeam_all[i]
    thisPlayerOnOff = []
    for j in range(0,int(len(df))):
        if thisPlayer in df.loc[j][0] and 'sostituisce' in df.loc[j][0]:
            thisPlayerOnOff.append([df.loc[j][0],j])
    if len(thisPlayerOnOff)>0:
        bench_homeTeam.append(bench_homeTeam_all[i])
        in_out_bench_homeTeam.append(thisPlayerOnOff)
    
# Check when the bench of the away team is on/off the court
bench_awayTeam        = []
in_out_bench_awayTeam = []
for i in range(0,int(len(bench_awayTeam_all))):
    thisPlayer      = bench_awayTeam_all[i]
    thisPlayerOnOff = []
    for j in range(0,int(len(df))):
        if thisPlayer in df.loc[j][2] and 'sostituisce' in df.loc[j][2]:
            thisPlayerOnOff.append([df.loc[j][2],j])
    if len(thisPlayerOnOff)>0:
        bench_awayTeam.append(bench_awayTeam_all[i])
        in_out_bench_awayTeam.append(thisPlayerOnOff)
        

bench_homeTeam_allPlays         = []
bench_homeTeam_allPlays_oppTeam = []

for i in range(0,int(len(bench_homeTeam))):
    this_bench_homeTeam_Plays           = []
    this_bench_homeTeam_Plays_oppTeam   = []
    thisPlayerInOutAll                  = in_out_bench_homeTeam[i]
    thisPlayerInOut                     = []
    for j in range(0,int(len(thisPlayerInOutAll))):
        thisPlayerInOut.append(thisPlayerInOutAll[j][1])
        
    # odd number of out/in: the bench player ends the game
    if np.mod(int(len(thisPlayerInOut)),2) != 0:
        for j in range(0,int(len(thisPlayerInOut))):
            if np.mod(j,2) != 0:
                pass
            else:
                if j == int(len(thisPlayerInOut)-1):
                    this_bench_homeTeam_Plays.append(list(df.loc[thisPlayerInOut[j]:len(df)][0]))
                    this_bench_homeTeam_Plays_oppTeam.append(list(df.loc[thisPlayerInOut[j]:len(df)][2]))
                else:
                    this_bench_homeTeam_Plays.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][0]))
                    this_bench_homeTeam_Plays_oppTeam.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][2]))
    # even number of out/in: the starting player does not end the game
    else:
        for j in range(0,int(len(thisPlayerInOut)-1)):
            if np.mod(j,2) != 0:
                pass
            else:
                this_bench_homeTeam_Plays.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][0]))
                this_bench_homeTeam_Plays_oppTeam.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][2]))
    bench_homeTeam_allPlays.append(this_bench_homeTeam_Plays)
    bench_homeTeam_allPlays_oppTeam.append(this_bench_homeTeam_Plays_oppTeam)

###########################################
# Stats for the home team bench (own stats)
###########################################
all_stats_homeTeam_bench         = []
for i in range(0,int(len(bench_homeTeam))):
    for j in range(0,int(len(bench_homeTeam_allPlays[i]))):
        _1p_made                  = 0
        _1p_attempted             = 0
        _2p_made                  = 0
        _2p_attempted             = 0
        dunk                      = 0
        _3p_made                  = 0
        _3p_attempted             = 0
        def_rebound               = 0
        off_rebound               = 0
        assist                    = 0
        steal                     = 0
        turnover                  = 0
        block_made                = 0
        block_received            = 0
        foul_made                 = 0
        foul_received             = 0
        for k in range(0,int(len(bench_homeTeam_allPlays[i][j]))):
            
            if 'Tiroliberosbagliato' in bench_homeTeam_allPlays[i][j][k]:
                _1p_attempted += 1
            elif 'Tiroliberosegnato' in bench_homeTeam_allPlays[i][j][k]:
                _1p_attempted += 1
                _1p_made += 1
            elif ('Tirosbagliatodasotto' in bench_homeTeam_allPlays[i][j][k]
                or 'Tirosbagliatodafuori' in bench_homeTeam_allPlays[i][j][k]):
                _2p_attempted += 1
            elif ('Canestrodasotto' in bench_homeTeam_allPlays[i][j][k]
                  or 'Canestrodafuori' in bench_homeTeam_allPlays[i][j][k]):
                _2p_attempted += 1
                _2p_made      += 1
            elif 'Schiacciata' in bench_homeTeam_allPlays[i][j][k]:
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            elif 'Tirosbagliatoda3punti' in bench_homeTeam_allPlays[i][j][k]:
                _3p_attempted += 1
            elif 'Canestroda3punti' in bench_homeTeam_allPlays[i][j][k]:
                _3p_attempted += 1
                _3p_made += 1
            elif 'Rimbalzodifensivo' in bench_homeTeam_allPlays[i][j][k]:
                def_rebound += 1
            elif 'Rimbalzooffensivo' in bench_homeTeam_allPlays[i][j][k]:
                off_rebound += 1
            elif 'Assist' in bench_homeTeam_allPlays[i][j][k]:
                assist += 1
            elif 'Pallarecuperata' in bench_homeTeam_allPlays[i][j][k]:
                steal += 1
            elif 'Pallapersa' in bench_homeTeam_allPlays[i][j][k]:
                turnover += 1
            elif 'Stoppata' in bench_homeTeam_allPlays[i][j][k]:
                block_made += 1 
            elif 'StoppataSubita' in bench_homeTeam_allPlays[i][j][k]:
                block_received += 1 
            elif 'Fallocommesso' in bench_homeTeam_allPlays[i][j][k]:
                foul_made += 1     
            elif 'Fallosubito' in bench_homeTeam_allPlays[i][j][k]:
                foul_received += 1 
        all_stats_homeTeam_bench.append([bench_homeTeam[i],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received])


df_homeTeam_bench_homeTeamStats = pd.DataFrame(np.array(all_stats_homeTeam_bench))
df_homeTeam_bench_homeTeamStats.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
              'dreb','oreb','ass','st','to','blk','blkag','f','frec']
df_homeTeam_bench_homeTeamStats.to_excel(os.path.join(cwd,'homeTeam_homeTeamStats_Bench.xlsx'),
      sheet_name='Sheet_name_1')

#############################################################
# Stats for the home team starting five (opposing team stats)
#############################################################
all_stats_homeTeam_bench_oppTeam = []
for i in range(0,int(len(bench_homeTeam))):
    for j in range(0,int(len(bench_homeTeam_allPlays_oppTeam[i]))):
        _1p_made                  = 0
        _1p_attempted             = 0
        _2p_made                  = 0
        _2p_attempted             = 0
        dunk                      = 0
        _3p_made                  = 0
        _3p_attempted             = 0
        def_rebound               = 0
        off_rebound               = 0
        assist                    = 0
        steal                     = 0
        turnover                  = 0
        block_made                = 0
        block_received            = 0
        foul_made                 = 0
        foul_received             = 0
        for k in range(0,int(len(bench_homeTeam_allPlays_oppTeam[i][j]))):
            
            if 'Tiroliberosbagliato' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                _1p_attempted += 1
            elif 'Tiroliberosegnato' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                _1p_attempted += 1
                _1p_made += 1
            elif ('Tirosbagliatodasotto' in bench_homeTeam_allPlays_oppTeam[i][j][k]
                or 'Tirosbagliatodafuori' in bench_homeTeam_allPlays_oppTeam[i][j][k]):
                _2p_attempted += 1
            elif ('Canestrodasotto' in bench_homeTeam_allPlays_oppTeam[i][j][k]
                  or 'Canestrodafuori' in bench_homeTeam_allPlays_oppTeam[i][j][k]):
                _2p_attempted += 1
                _2p_made      += 1
            elif 'Schiacciata' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            elif 'Tirosbagliatoda3punti' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                _3p_attempted += 1
            elif 'Canestroda3punti' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                _3p_attempted += 1
                _3p_made += 1
            elif 'Rimbalzodifensivo' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                def_rebound += 1
            elif 'Rimbalzooffensivo' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                off_rebound += 1
            elif 'Assist' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                assist += 1
            elif 'Pallarecuperata' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                steal += 1
            elif 'Pallapersa' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                turnover += 1
            elif 'Stoppata' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                block_made += 1 
            elif 'StoppataSubita' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                block_received += 1 
            elif 'Fallocommesso' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                foul_made += 1     
            elif 'Fallosubito' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                foul_received += 1 
        all_stats_homeTeam_bench_oppTeam.append([bench_homeTeam[i],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received])


df_homeTeam_bench_oppTeamStats = pd.DataFrame(np.array(all_stats_homeTeam_bench_oppTeam))
df_homeTeam_bench_oppTeamStats.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
              'dreb','oreb','ass','st','to','blk','blkag','f','frec']
df_homeTeam_bench_oppTeamStats.to_excel(os.path.join(cwd,'homeTeam_awayTeamStats_bench.xlsx'),
      sheet_name='Sheet_name_1') 

#################
### AWAY TEAM ###
#################
bench_awayTeam_allPlays         = []
bench_awayTeam_allPlays_oppTeam = []

for i in range(0,int(len(bench_awayTeam))):
    this_bench_awayTeam_Plays         = []
    this_bench_awayTeam_Plays_oppTeam = []
    thisPlayerInOutAll                  = in_out_bench_awayTeam[i]
    thisPlayerInOut                     = []
    for j in range(0,int(len(thisPlayerInOutAll))):
        thisPlayerInOut.append(thisPlayerInOutAll[j][1])

        
    # odd number of out/in: the bench player ends the game
    if np.mod(int(len(thisPlayerInOut)),2) != 0:
        for j in range(0,int(len(thisPlayerInOut))):
            if np.mod(j,2) != 0:
                pass
            else:
                if j == int(len(thisPlayerInOut)-1):
                    this_bench_awayTeam_Plays.append(list(df.loc[thisPlayerInOut[j]:len(df)][2]))
                    this_bench_awayTeam_Plays_oppTeam.append(list(df.loc[thisPlayerInOut[j]:len(df)][0]))
                else:
                    this_bench_awayTeam_Plays.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][2]))
                    this_bench_awayTeam_Plays_oppTeam.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][0]))
    # even number of out/in: the starting player does not end the game
    else:
        for j in range(0,int(len(thisPlayerInOut)-1)):
            if np.mod(j,2) != 0:
                pass
            else:
                this_bench_awayTeam_Plays.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][2]))
                this_bench_awayTeam_Plays_oppTeam.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][0]))
    bench_awayTeam_allPlays.append(this_bench_awayTeam_Plays)
    bench_awayTeam_allPlays_oppTeam.append(this_bench_awayTeam_Plays_oppTeam)

###########################################
# Stats for the away team bench (own stats)
###########################################
all_stats_awayTeam_bench         = []
for i in range(0,int(len(bench_awayTeam))):
    for j in range(0,int(len(bench_awayTeam_allPlays[i]))):
        _1p_made                  = 0
        _1p_attempted             = 0
        _2p_made                  = 0
        _2p_attempted             = 0
        dunk                      = 0
        _3p_made                  = 0
        _3p_attempted             = 0
        def_rebound               = 0
        off_rebound               = 0
        assist                    = 0
        steal                     = 0
        turnover                  = 0
        block_made                = 0
        block_received            = 0
        foul_made                 = 0
        foul_received             = 0
        for k in range(0,int(len(bench_awayTeam_allPlays[i][j]))):
            
            if 'Tiroliberosbagliato' in bench_awayTeam_allPlays[i][j][k]:
                _1p_attempted += 1
            elif 'Tiroliberosegnato' in bench_awayTeam_allPlays[i][j][k]:
                _1p_attempted += 1
                _1p_made += 1
            elif ('Tirosbagliatodasotto' in bench_awayTeam_allPlays[i][j][k]
                or 'Tirosbagliatodafuori' in bench_awayTeam_allPlays[i][j][k]):
                _2p_attempted += 1
            elif ('Canestrodasotto' in bench_awayTeam_allPlays[i][j][k]
                  or 'Canestrodafuori' in bench_awayTeam_allPlays[i][j][k]):
                _2p_attempted += 1
                _2p_made      += 1
            elif 'Schiacciata' in bench_awayTeam_allPlays[i][j][k]:
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            elif 'Tirosbagliatoda3punti' in bench_awayTeam_allPlays[i][j][k]:
                _3p_attempted += 1
            elif 'Canestroda3punti' in bench_awayTeam_allPlays[i][j][k]:
                _3p_attempted += 1
                _3p_made += 1
            elif 'Rimbalzodifensivo' in bench_awayTeam_allPlays[i][j][k]:
                def_rebound += 1
            elif 'Rimbalzooffensivo' in bench_awayTeam_allPlays[i][j][k]:
                off_rebound += 1
            elif 'Assist' in bench_awayTeam_allPlays[i][j][k]:
                assist += 1
            elif 'Pallarecuperata' in bench_awayTeam_allPlays[i][j][k]:
                steal += 1
            elif 'Pallapersa' in bench_awayTeam_allPlays[i][j][k]:
                turnover += 1
            elif 'Stoppata' in bench_awayTeam_allPlays[i][j][k]:
                block_made += 1 
            elif 'StoppataSubita' in bench_awayTeam_allPlays[i][j][k]:
                block_received += 1 
            elif 'Fallocommesso' in bench_awayTeam_allPlays[i][j][k]:
                foul_made += 1     
            elif 'Fallosubito' in bench_awayTeam_allPlays[i][j][k]:
                foul_received += 1 
        all_stats_awayTeam_bench.append([bench_awayTeam[i],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received])


df_awayTeam_bench_awayTeamStats = pd.DataFrame(np.array(all_stats_awayTeam_bench))
df_awayTeam_bench_awayTeamStats.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
              'dreb','oreb','ass','st','to','blk','blkag','f','frec']
df_awayTeam_bench_awayTeamStats.to_excel(os.path.join(cwd,'awayTeam_awayTeamStats_Bench.xlsx'),
      sheet_name='Sheet_name_1')

#####################################################
# Stats for the away team bench (opposing team stats)
#####################################################
all_stats_awayTeam_bench_oppTeam = []
for i in range(0,int(len(bench_awayTeam))):
    for j in range(0,int(len(bench_awayTeam_allPlays_oppTeam[i]))):
        _1p_made                  = 0
        _1p_attempted             = 0
        _2p_made                  = 0
        _2p_attempted             = 0
        dunk                      = 0
        _3p_made                  = 0
        _3p_attempted             = 0
        def_rebound               = 0
        off_rebound               = 0
        assist                    = 0
        steal                     = 0
        turnover                  = 0
        block_made                = 0
        block_received            = 0
        foul_made                 = 0
        foul_received             = 0
        for k in range(0,int(len(bench_awayTeam_allPlays_oppTeam[i][j]))):
            
            if 'Tiroliberosbagliato' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                _1p_attempted += 1
            elif 'Tiroliberosegnato' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                _1p_attempted += 1
                _1p_made += 1
            elif ('Tirosbagliatodasotto' in bench_awayTeam_allPlays_oppTeam[i][j][k]
                or 'Tirosbagliatodafuori' in bench_awayTeam_allPlays_oppTeam[i][j][k]):
                _2p_attempted += 1
            elif ('Canestrodasotto' in bench_awayTeam_allPlays_oppTeam[i][j][k]
                  or 'Canestrodafuori' in bench_awayTeam_allPlays_oppTeam[i][j][k]):
                _2p_attempted += 1
                _2p_made      += 1
            elif 'Schiacciata' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            elif 'Tirosbagliatoda3punti' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                _3p_attempted += 1
            elif 'Canestroda3punti' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                _3p_attempted += 1
                _3p_made += 1
            elif 'Rimbalzodifensivo' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                def_rebound += 1
            elif 'Rimbalzooffensivo' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                off_rebound += 1
            elif 'Assist' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                assist += 1
            elif 'Pallarecuperata' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                steal += 1
            elif 'Pallapersa' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                turnover += 1
            elif 'Stoppata' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                block_made += 1 
            elif 'StoppataSubita' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                block_received += 1 
            elif 'Fallocommesso' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                foul_made += 1     
            elif 'Fallosubito' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                foul_received += 1 
        all_stats_awayTeam_bench_oppTeam.append([bench_awayTeam[i],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received])


df_awayTeam_bench_oppTeamStats = pd.DataFrame(np.array(all_stats_awayTeam_bench_oppTeam))
df_awayTeam_bench_oppTeamStats.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
              'dreb','oreb','ass','st','to','blk','blkag','f','frec']
df_awayTeam_bench_oppTeamStats.to_excel(os.path.join(cwd,'awayTeam_homeTeamStats_bench.xlsx'),
      sheet_name='Sheet_name_1')

#%%
###############################################################
### FOCUS ON DIFFERENT LINEUPS: STORE STATISTICS PER LINEUP ###
###############################################################



##############
### Home team
##############

all_players_homeTeam = starting_five_homeTeam + bench_homeTeam
all_lineups_homeTeam = []
all_lineups_homeTeam.append([sorted(starting_five_homeTeam),0])
current_lineup = starting_five_homeTeam
current_bench  = list(set(all_players_homeTeam) - set(current_lineup))
for j in range(0,int(len(df))):
    if 'sostituisce' in df.loc[j][0]:
        for cont in range(0,int(len(current_bench))):
            if current_bench[cont] in df.loc[j][0]:
                new_player_onField = current_bench[cont]
                break
        for cont in range(0,int(len(current_lineup))):
            if current_lineup[cont] in df.loc[j][0]:
                new_player_offField = current_lineup[cont]
                break
        current_lineup = list(set(current_lineup) - set([new_player_offField]))
        current_lineup = current_lineup + [new_player_onField]
        current_bench = list(set(current_bench) - set([new_player_onField]))
        current_bench = current_bench + [new_player_offField]
        
        all_lineups_homeTeam.append([sorted(current_lineup),j])

##############
### Away team
##############

all_players_awayTeam = starting_five_awayTeam + bench_awayTeam
all_lineups_awayTeam = []
all_lineups_awayTeam.append([sorted(starting_five_awayTeam),0])
current_lineup = starting_five_awayTeam
current_bench  = list(set(all_players_awayTeam) - set(current_lineup))
for j in range(0,int(len(df))):
    if 'sostituisce' in df.loc[j][2]:
        for cont in range(0,int(len(current_bench))):
            if current_bench[cont] in df.loc[j][2]:
                new_player_onField = current_bench[cont]
                break
        for cont in range(0,int(len(current_lineup))):
            if current_lineup[cont] in df.loc[j][2]:
                new_player_offField = current_lineup[cont]
                break
        current_lineup = list(set(current_lineup) - set([new_player_offField]))
        current_lineup = current_lineup + [new_player_onField]
        current_bench = list(set(current_bench) - set([new_player_onField]))
        current_bench = current_bench + [new_player_offField]
        
        all_lineups_awayTeam.append([sorted(current_lineup),j])

#%%

####################################
# Find unique lineups for home team
####################################

idx_unique_lineups_homeTeam = []
for i in range(0,int(len(all_lineups_homeTeam))):
    this_lineup_idx = []
    for j in range(0,int(len(all_lineups_homeTeam))):
        if all_lineups_homeTeam[j][0] == all_lineups_homeTeam[i][0]:
            this_lineup_idx.append(j)
    idx_unique_lineups_homeTeam.append(this_lineup_idx)

idx_unique_lineups_homeTeam  = list(np.unique(np.array(idx_unique_lineups_homeTeam)))

startEnd_unique_lineups_homeTeam = []
for i in range(0,int(len(idx_unique_lineups_homeTeam))):
    this_startEnd_unique_lineups_homeTeam = []
    for j in range(0,int(len(idx_unique_lineups_homeTeam[i]))):
        thisIdx   = idx_unique_lineups_homeTeam[i][j]
        start_row = all_lineups_homeTeam[thisIdx][1]
        if thisIdx != len(all_lineups_homeTeam)-1:
            end_row   = all_lineups_homeTeam[thisIdx+1][1]
        else:
            end_row   = len(df)-1
        this_startEnd_unique_lineups_homeTeam.append([start_row,end_row])
    startEnd_unique_lineups_homeTeam.append(this_startEnd_unique_lineups_homeTeam)

#######################################################
# Stats for the home team different lineups (own stats)
#######################################################
all_stats_homeTeam_lineups         = []
for i in range(0,int(len(startEnd_unique_lineups_homeTeam))):
    for j in range(0,int(len(startEnd_unique_lineups_homeTeam[i]))):
        _1p_made                  = 0
        _1p_attempted             = 0
        _2p_made                  = 0
        _2p_attempted             = 0
        dunk                      = 0
        _3p_made                  = 0
        _3p_attempted             = 0
        def_rebound               = 0
        off_rebound               = 0
        assist                    = 0
        steal                     = 0
        turnover                  = 0
        block_made                = 0
        block_received            = 0
        foul_made                 = 0
        foul_received             = 0
        for k in range(0,int(len(df.loc[startEnd_unique_lineups_homeTeam[i][j][0]:startEnd_unique_lineups_homeTeam[i][j][1]]))):
            
            if 'Tiroliberosbagliato' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                _1p_attempted += 1
            elif 'Tiroliberosegnato' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                _1p_attempted += 1
                _1p_made += 1
            elif ('Tirosbagliatodasotto' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]
                or 'Tirosbagliatodafuori' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]):
                _2p_attempted += 1
            elif ('Canestrodasotto' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]
                  or 'Canestrodafuori' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]):
                _2p_attempted += 1
                _2p_made      += 1
            elif 'Schiacciata' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            elif 'Tirosbagliatoda3punti' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                _3p_attempted += 1
            elif 'Canestroda3punti' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                _3p_attempted += 1
                _3p_made += 1
            elif 'Rimbalzodifensivo' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                def_rebound += 1
            elif 'Rimbalzooffensivo' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                off_rebound += 1
            elif 'Assist' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                assist += 1
            elif 'Pallarecuperata' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                steal += 1
            elif 'Pallapersa' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                turnover += 1
            elif 'Stoppata' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                block_made += 1 
            elif 'StoppataSubita' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                block_received += 1 
            elif 'Fallocommesso' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                foul_made += 1     
            elif 'Fallosubito' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                foul_received += 1 
        all_stats_homeTeam_lineups.append([all_lineups_homeTeam[idx_unique_lineups_homeTeam[i][j]][0],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received])


df_homeTeam_lineups = pd.DataFrame(np.array(all_stats_homeTeam_lineups))
df_homeTeam_lineups.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
              'dreb','oreb','ass','st','to','blk','blkag','f','frec']
df_homeTeam_lineups.to_excel(os.path.join(cwd,'homeTeam_lineups_stats.xlsx'),
      sheet_name='Sheet_name_1') 

#############################################################
# Stats for the home team different lineups (opp. team stats)
#############################################################
all_stats_homeTeam_lineups_oppTeam         = []
for i in range(0,int(len(startEnd_unique_lineups_homeTeam))):
    for j in range(0,int(len(startEnd_unique_lineups_homeTeam[i]))):
        _1p_made                  = 0
        _1p_attempted             = 0
        _2p_made                  = 0
        _2p_attempted             = 0
        dunk                      = 0
        _3p_made                  = 0
        _3p_attempted             = 0
        def_rebound               = 0
        off_rebound               = 0
        assist                    = 0
        steal                     = 0
        turnover                  = 0
        block_made                = 0
        block_received            = 0
        foul_made                 = 0
        foul_received             = 0
        for k in range(0,int(len(df.loc[startEnd_unique_lineups_homeTeam[i][j][0]:startEnd_unique_lineups_homeTeam[i][j][1]]))):
            
            if 'Tiroliberosbagliato' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                _1p_attempted += 1
            elif 'Tiroliberosegnato' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                _1p_attempted += 1
                _1p_made += 1
            elif ('Tirosbagliatodasotto' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]
                or 'Tirosbagliatodafuori' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]):
                _2p_attempted += 1
            elif ('Canestrodasotto' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]
                  or 'Canestrodafuori' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]):
                _2p_attempted += 1
                _2p_made      += 1
            elif 'Schiacciata' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            elif 'Tirosbagliatoda3punti' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                _3p_attempted += 1
            elif 'Canestroda3punti' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                _3p_attempted += 1
                _3p_made += 1
            elif 'Rimbalzodifensivo' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                def_rebound += 1
            elif 'Rimbalzooffensivo' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                off_rebound += 1
            elif 'Assist' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                assist += 1
            elif 'Pallarecuperata' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                steal += 1
            elif 'Pallapersa' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                turnover += 1
            elif 'Stoppata' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                block_made += 1 
            elif 'StoppataSubita' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                block_received += 1 
            elif 'Fallocommesso' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                foul_made += 1     
            elif 'Fallosubito' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                foul_received += 1 
        all_stats_homeTeam_lineups_oppTeam.append([all_lineups_homeTeam[idx_unique_lineups_homeTeam[i][j]][0],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received])


df_homeTeam_lineups_oppTeam = pd.DataFrame(np.array(all_stats_homeTeam_lineups_oppTeam))
df_homeTeam_lineups_oppTeam.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
              'dreb','oreb','ass','st','to','blk','blkag','f','frec']
df_homeTeam_lineups_oppTeam.to_excel(os.path.join(cwd,'homeTeam_lineups_stats_oppTeam.xlsx'),
      sheet_name='Sheet_name_1')

#%%

####################################
# Find unique lineups for away team
####################################

idx_unique_lineups_awayTeam = []
for i in range(0,int(len(all_lineups_awayTeam))):
    this_lineup_idx = []
    for j in range(0,int(len(all_lineups_awayTeam))):
        if all_lineups_awayTeam[j][0] == all_lineups_awayTeam[i][0]:
            this_lineup_idx.append(j)
    idx_unique_lineups_awayTeam.append(this_lineup_idx)

idx_unique_lineups_awayTeam  = list(np.unique(np.array(idx_unique_lineups_awayTeam)))

startEnd_unique_lineups_awayTeam = []
for i in range(0,int(len(idx_unique_lineups_awayTeam))):
    this_startEnd_unique_lineups_awayTeam = []
    for j in range(0,int(len(idx_unique_lineups_awayTeam[i]))):
        thisIdx   = idx_unique_lineups_awayTeam[i][j]
        start_row = all_lineups_awayTeam[thisIdx][1]
        if thisIdx != len(all_lineups_awayTeam)-1:
            end_row   = all_lineups_awayTeam[thisIdx+1][1]
        else:
            end_row   = len(df)-1
        this_startEnd_unique_lineups_awayTeam.append([start_row,end_row])
    startEnd_unique_lineups_awayTeam.append(this_startEnd_unique_lineups_awayTeam)  
    
#######################################################
# Stats for the away team different lineups (own stats)
#######################################################
all_stats_awayTeam_lineups         = []
for i in range(0,int(len(startEnd_unique_lineups_awayTeam))):
    for j in range(0,int(len(startEnd_unique_lineups_awayTeam[i]))):
        _1p_made                  = 0
        _1p_attempted             = 0
        _2p_made                  = 0
        _2p_attempted             = 0
        dunk                      = 0
        _3p_made                  = 0
        _3p_attempted             = 0
        def_rebound               = 0
        off_rebound               = 0
        assist                    = 0
        steal                     = 0
        turnover                  = 0
        block_made                = 0
        block_received            = 0
        foul_made                 = 0
        foul_received             = 0
        for k in range(0,int(len(df.loc[startEnd_unique_lineups_awayTeam[i][j][0]:startEnd_unique_lineups_awayTeam[i][j][1]]))):
            
            if 'Tiroliberosbagliato' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                _1p_attempted += 1
            elif 'Tiroliberosegnato' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                _1p_attempted += 1
                _1p_made += 1
            elif ('Tirosbagliatodasotto' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]
                or 'Tirosbagliatodafuori' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]):
                _2p_attempted += 1
            elif ('Canestrodasotto' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]
                  or 'Canestrodafuori' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]):
                _2p_attempted += 1
                _2p_made      += 1
            elif 'Schiacciata' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            elif 'Tirosbagliatoda3punti' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                _3p_attempted += 1
            elif 'Canestroda3punti' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                _3p_attempted += 1
                _3p_made += 1
            elif 'Rimbalzodifensivo' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                def_rebound += 1
            elif 'Rimbalzooffensivo' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                off_rebound += 1
            elif 'Assist' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                assist += 1
            elif 'Pallarecuperata' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                steal += 1
            elif 'Pallapersa' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                turnover += 1
            elif 'Stoppata' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                block_made += 1 
            elif 'StoppataSubita' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                block_received += 1 
            elif 'Fallocommesso' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                foul_made += 1     
            elif 'Fallosubito' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                foul_received += 1 
        all_stats_awayTeam_lineups.append([all_lineups_awayTeam[idx_unique_lineups_awayTeam[i][j]][0],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received])


df_awayTeam_lineups = pd.DataFrame(np.array(all_stats_awayTeam_lineups))
df_awayTeam_lineups.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
              'dreb','oreb','ass','st','to','blk','blkag','f','frec']
df_awayTeam_lineups.to_excel(os.path.join(cwd,'awayTeam_lineups_stats.xlsx'),
      sheet_name='Sheet_name_1')

############################################################
# Stats for the away team different lineups (opp.team stats)
############################################################
all_stats_awayTeam_lineups_oppTeam         = []
for i in range(0,int(len(startEnd_unique_lineups_awayTeam))):
    for j in range(0,int(len(startEnd_unique_lineups_awayTeam[i]))):
        _1p_made                  = 0
        _1p_attempted             = 0
        _2p_made                  = 0
        _2p_attempted             = 0
        dunk                      = 0
        _3p_made                  = 0
        _3p_attempted             = 0
        def_rebound               = 0
        off_rebound               = 0
        assist                    = 0
        steal                     = 0
        turnover                  = 0
        block_made                = 0
        block_received            = 0
        foul_made                 = 0
        foul_received             = 0
        for k in range(0,int(len(df.loc[startEnd_unique_lineups_awayTeam[i][j][0]:startEnd_unique_lineups_awayTeam[i][j][1]]))):
            
            if 'Tiroliberosbagliato' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                _1p_attempted += 1
            elif 'Tiroliberosegnato' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                _1p_attempted += 1
                _1p_made += 1
            elif ('Tirosbagliatodasotto' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]
                or 'Tirosbagliatodafuori' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]):
                _2p_attempted += 1
            elif ('Canestrodasotto' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]
                  or 'Canestrodafuori' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]):
                _2p_attempted += 1
                _2p_made      += 1
            elif 'Schiacciata' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            elif 'Tirosbagliatoda3punti' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                _3p_attempted += 1
            elif 'Canestroda3punti' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                _3p_attempted += 1
                _3p_made += 1
            elif 'Rimbalzodifensivo' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                def_rebound += 1
            elif 'Rimbalzooffensivo' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                off_rebound += 1
            elif 'Assist' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                assist += 1
            elif 'Pallarecuperata' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                steal += 1
            elif 'Pallapersa' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                turnover += 1
            elif 'Stoppata' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                block_made += 1 
            elif 'StoppataSubita' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                block_received += 1 
            elif 'Fallocommesso' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                foul_made += 1     
            elif 'Fallosubito' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                foul_received += 1 
        all_stats_awayTeam_lineups_oppTeam.append([all_lineups_awayTeam[idx_unique_lineups_awayTeam[i][j]][0],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received])


df_awayTeam_lineups_oppTeam = pd.DataFrame(np.array(all_stats_awayTeam_lineups_oppTeam))
df_awayTeam_lineups_oppTeam.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
              'dreb','oreb','ass','st','to','blk','blkag','f','frec']
df_awayTeam_lineups_oppTeam.to_excel(os.path.join(cwd,'awayTeam_lineups_stats_oppTeam.xlsx'),
      sheet_name='Sheet_name_1')