#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 30 12:06:19 2019
@author: alessandro
"""

#################################################
### pyHoops: a Python package to web-parse
### basketball games' play-by-play info
### and, using basketball data analytics,
### determine the effect of a player or a lineup
### on the game
#################################################

import numpy as np
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import sys
import matplotlib.pyplot as plt
from matplotlib.cbook import get_sample_data
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import random
import re
import itertools
import unicodedata

# Input  : url pointing to the play-by-play webpage of the game of interest
# Output : dataframe replicating the play-by-play table. To avoid issues with
# special characters, accents, etc, they are replaced, while spaces are eliminated

# Note: in the Italian Basketball Leaghe, the play-by-play table has three columns,
# reporting respectively home team info, minute of the game or score, away team
# info. For other leagues (e.g., Euroleague), ther emight be more columns,
# and the web-parsing procedure should be slightly changed accordingly.



def web_parse_playbyplay(thisUrl):
    p    = requests.get(thisUrl)
    
    if p.status_code < 400:
        l = []
        soup = BeautifulSoup(p.text,'html.parser')
        table = soup.find('table', attrs={'border':'0'})
        
        table_rows = table.find_all('tr')
        for tr in table_rows:
            td = tr.find_all('td')
            row = [tr.text.lower() for tr in td]
            if len(row)>0 and len(row)==3:
                l.append(row)
                
    df = pd.DataFrame(np.array(l))
    
    
    for i in range(0,int(len(df))):
        for j in range(0,int(len(df.loc[i]))):
            s             = df.loc[i][j]
            s_mod         = ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))
            s_mod_noAp    = s_mod.replace('\'','')
            s_mod_noSpace = s_mod_noAp.replace(' ','')
            df.loc[i][j]  = s_mod_noSpace
            
            
        
    df.to_excel(l[0][0] + '_' + l[0][2] + '.xlsx',sheet_name='Sheet_name_1')
    
    return df,l[0][0],l[0][2] 

# Input  : dataframe with play-by-play
# Output : command window print of the game analyzed
def print_game_analyzed(homeTeam,awayTeam):
    # Python 3.X is running
    if sys.version[0] == '3':
        print('###########################################################')
        print('Game analyzed is: ' + str(homeTeam) + ' vs ' + str(awayTeam))
        print('###########################################################')

# Input  : string identifying home team, string identifying away team, 
#          list of available teams
# Output : index of the logo that represents the home team and away team.
#          If a team is not recognized in the list of teams available,
#          it is assigned a default generic logo
def determine_team_logo(string_homeTeam,string_awayTeam,team_list):
    idx_logo_homeTeam = np.nan
    for i in range(0,int(len(team_list))):
        if team_list[i] in string_homeTeam:
            idx_logo_homeTeam = i
            break
    if np.isnan(idx_logo_homeTeam):
        idx_logo_homeTeam = int(len(team_list))
    
    idx_logo_awayTeam = np.nan
    for i in range(0,int(len(team_list))):
        if team_list[i] in string_awayTeam:
            idx_logo_awayTeam = i
            break
    if np.isnan(idx_logo_awayTeam):
        idx_logo_awayTeam = int(len(team_list))
        
    return idx_logo_homeTeam,idx_logo_awayTeam

# Input  : url pointing to the boxscore webpage of the game of interest
# Output : dataframes replicating the boxscore for the home and away team
    
# Note: same note as above. Boxscores for different leagues might and 
# generally be slightly different, and the web-parsing procedure should
# be changed accordingly
def web_parse_boxscores(thisUrlBoxscore):
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
            row = [tr.text.lower() for tr in td]
            if len(row)>0:
                lpBoxscoreHomeTeam.append(row) 
                
        dfHomeTeam = pd.DataFrame(np.array(lpBoxscoreHomeTeam))
        
        lpBoxscoreAwayTeam = []
        table_rows         = tableAwayTeam.find_all('tr')
        for tr in table_rows:
            td = tr.find_all('td')
            row = [tr.text.lower() for tr in td]
            if len(row)>0:
                lpBoxscoreAwayTeam.append(row) 
                
        dfAwayTeam = pd.DataFrame(np.array(lpBoxscoreAwayTeam))
        
        return dfHomeTeam,dfAwayTeam
    
# Input  : play-by-play dataframe
# Output : list of indices associated with a change in the minute of
#          of the game (e.g., when the game switched from min. 24 to min. 25).
#          If not all 40 minutes are found (considering European basketball),
#          which is the case in some faulty play-by-play tables, the flag 
#          all_minutes_found is set to zero
#          will
def find_indices_minutes(df):
    centralColumn = []    
    for i in range(0,int(len(df))):
        centralColumn.append(df.loc[i][1])
    
    all_minutes_found = 1    
    
    idxMinutes = [0]            
    for i in range(2,int(41)):
        if len(np.where(np.array(centralColumn)==str(int(i))+'.min')[0])>0:
            idxMinutes.append(np.where(np.array(centralColumn)==str(int(i))+'.min')[0][0])
        else:
            idxMinutes = []
            for k in range(0,42):
                idxMinutes.append(0)
            all_minutes_found = 0
            break
    if all_minutes_found:
        idxMinutes.append(int(len(df)-1))
    
    return idxMinutes, all_minutes_found


# Input  : play-by-play dataframe (df), home team dataframe (dfHomeTeam), 
#          list of indices reporting
#          changes in the minute of the game in the play-by-play dataframe (idxMinutes),
#          flag highlighting if idxMinutes has been calculated for all 40
#          minutes or not (all_minutes_found), path to current folder (cwd)
# Output : dataframes containing all relevant info (1p,2p,3p attemped and made),
#          defensive and offensive rebounds, assists etc, at the team level
#          (both for the own team and the opposing team) for each player of the home team. 
#          It is important to highlight that stats 
#          are aggregated at the team level. As example, a row corresponding
#          to a specific player contains all the info that his/her team or the
#          opposing team generated while the specific player was on the court     
def get_homeTeam_stats_perPlayer(df,dfHomeTeam,idxMinutes,all_minutes_found,cwd):
    
    ###############
    # STARTING FIVE
    ###############
    orig_idx_starting_five_homeTeam = []
    # For the home team, find the starting five
    starting_five_homeTeam                    = []
    all_possible_names_starting_five_homeTeam = []
    for i in range(0,int(len(dfHomeTeam))):
        # In the LegaBasket boxscore table, starters are identified with a *
        if dfHomeTeam.loc[i][0] == '*':
            
            # Clean the full name of the player by getting rid of special
            # characters, spaces, etc
            s             = dfHomeTeam.loc[i][2]
            ccc           = ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))
            ccc           = ccc.replace(u'\xa0', u' ')
            ccc           = ccc.replace('\'','')
            s_mod_noSpace = ccc.replace(' ','')
            
            starting_five_homeTeam.append(s_mod_noSpace)
            orig_idx_starting_five_homeTeam.append(i)
            idx_space = [x.start() for x in re.finditer(' ', ccc)]
            
            # Find combinations of last name and first names to avoid
            # inconsistencies where the play-by-play reports the complete
            # name of a player, while the boxscore only one of the (more than one)
            # first names of a certain player
            last_name     = ccc[0:idx_space[0]]
            n_first_names = len(idx_space)
            first_names   = []
            
            for ii in range(0,int(n_first_names)):
                if ii != int(n_first_names)-1:
                    first_names.append(ccc[idx_space[ii]+1:idx_space[ii+1]])
                else:
                    first_names.append(ccc[idx_space[ii]+1:len(ccc)])
            
            all_combinations = []    
            for ii in range(1, len(first_names) + 1):
                for p in itertools.permutations(first_names, ii):
                    all_combinations.append(last_name+str("".join(p)))
            
            n_init_combinations = int(len(all_combinations))
            for ii in range(0,n_init_combinations):
                all_combinations.append(all_combinations[ii][0:int(np.ceil(len(all_combinations[ii])*0.8))])
            
            all_possible_names_starting_five_homeTeam.append(all_combinations)
 
    # Check when the starting five of the home team is on/off the court
    in_out_startingFive_homeTeam = []
    for i in range(0,int(len(starting_five_homeTeam))):
        thisPlayerOnOff = []
        for j in range(0,int(len(df))):
            if any(k in df.loc[j][0] for k in all_possible_names_starting_five_homeTeam[i]) and 'sostituisce' in df.loc[j][0]:
                thisPlayerOnOff.append([df.loc[j][0],j])
        in_out_startingFive_homeTeam.append(thisPlayerOnOff)

    
    starters_homeTeam_allPlays         = []
    starters_homeTeam_allPlays_oppTeam = []
    starters_homeTeam_timeOnCourt      = []
    
    for i in range(0,int(len(starting_five_homeTeam))):
        this_starter_homeTeam_Plays         = []
        this_starter_homeTeam_timeOnCourt   = []
        this_starter_homeTeam_Plays_oppTeam = []
        thisPlayerInOutAll                  = in_out_startingFive_homeTeam[i]
        thisPlayerInOut                     = []
        for j in range(0,int(len(thisPlayerInOutAll))):
            thisPlayerInOut.append(thisPlayerInOutAll[j][1])
            
        this_starter_homeTeam_Plays.append(list(df.loc[0:thisPlayerInOut[0]][0])) 
        this_starter_homeTeam_Plays_oppTeam.append(list(df.loc[0:thisPlayerInOut[0]][2]))
        # Find minute when starter exits for first time
        if all_minutes_found:
            minFirstExit = np.where(np.array(idxMinutes)>=thisPlayerInOut[0])[0][0]
            this_starter_homeTeam_timeOnCourt.append(minFirstExit)
        else:
            this_starter_homeTeam_timeOnCourt.append(0)
            
        # even number of out/in: the starting player ends the game as well.
        # The sequence is in fact O-I-O-I as example (I=in, O=out)
        if np.mod(int(len(thisPlayerInOut)),2) == 0:
            for j in range(0,int(len(thisPlayerInOut))):
                if np.mod(j,2) == 0:
                    pass
                else:
                    if j == int(len(thisPlayerInOut)-1):
                        this_starter_homeTeam_Plays.append(list(df.loc[thisPlayerInOut[j]:len(df)][0]))
                        this_starter_homeTeam_Plays_oppTeam.append(list(df.loc[thisPlayerInOut[j]:len(df)][2]))
                        if all_minutes_found:
                            entryMin = np.where(np.array(idxMinutes)>=thisPlayerInOut[j])[0][0]
                            exitMin  = np.where(np.array(idxMinutes)>=len(df)-1)[0][0]
                            this_starter_homeTeam_timeOnCourt.append(np.max([1,exitMin-entryMin]))
                        else:
                            this_starter_homeTeam_timeOnCourt.append(0)
                    else:
                        this_starter_homeTeam_Plays.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][0]))
                        this_starter_homeTeam_Plays_oppTeam.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][2]))
                        if all_minutes_found:
                            entryMin = np.where(np.array(idxMinutes)>=thisPlayerInOut[j])[0][0]
                            exitMin  = np.where(np.array(idxMinutes)>=len(df)-1)[0][0]
                            this_starter_homeTeam_timeOnCourt.append(np.max([1,exitMin-entryMin]))
                        else:
                            this_starter_homeTeam_timeOnCourt.append(0)
        # odd number of out/in: the starting player does not end the game.
        # The sequence is in fact O-I-O-I-O as example (I=in, O=out)
        else:
            for j in range(0,int(len(thisPlayerInOut)-1)):
                if np.mod(j,2) == 0:
                    pass
                else:
                    this_starter_homeTeam_Plays.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][0]))
                    this_starter_homeTeam_Plays_oppTeam.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][2]))
                    if all_minutes_found:
                        entryMin = np.where(np.array(idxMinutes)>=thisPlayerInOut[j])[0][0]
                        exitMin  = np.where(np.array(idxMinutes)>=len(df)-1)[0][0]
                        this_starter_homeTeam_timeOnCourt.append(np.max([1,exitMin-entryMin]))
                    else:
                        this_starter_homeTeam_timeOnCourt.append(0)
        starters_homeTeam_allPlays.append(this_starter_homeTeam_Plays)
        starters_homeTeam_allPlays_oppTeam.append(this_starter_homeTeam_Plays_oppTeam)
        starters_homeTeam_timeOnCourt.append(this_starter_homeTeam_timeOnCourt)
        
    ###################################################
    # Stats for the home team starting five (own stats)
    ###################################################
    # Note: the way information is retrieved is specific for the Italian League,
    # as there is no easy way to automatize the process, since every different 
    # play-by-play might have a different language and different notation.
    # If pyHoops should be used for other leagues, this part of the code 
    # (and all the equivalent parts below) should be changed accordingly
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
                
                if 'tiroliberosbagliato' in starters_homeTeam_allPlays[i][j][k]:
                    _1p_attempted += 1
                elif 'tiroliberosegnato' in starters_homeTeam_allPlays[i][j][k]:
                    _1p_attempted += 1
                    _1p_made += 1
                elif ('tirosbagliatodasotto' in starters_homeTeam_allPlays[i][j][k]
                    or 'tirosbagliatodafuori' in starters_homeTeam_allPlays[i][j][k]):
                    _2p_attempted += 1
                elif ('canestrodasotto' in starters_homeTeam_allPlays[i][j][k]
                      or 'canestrodafuori' in starters_homeTeam_allPlays[i][j][k]):
                    _2p_attempted += 1
                    _2p_made      += 1
                elif 'schiacciata' in starters_homeTeam_allPlays[i][j][k]:
                    _2p_attempted += 1
                    _2p_made      += 1
                    dunk          += 1
                elif 'tirosbagliatoda3punti' in starters_homeTeam_allPlays[i][j][k]:
                    _3p_attempted += 1
                elif 'canestroda3punti' in starters_homeTeam_allPlays[i][j][k]:
                    _3p_attempted += 1
                    _3p_made += 1
                elif 'rimbalzodifensivo' in starters_homeTeam_allPlays[i][j][k]:
                    def_rebound += 1
                elif 'rimbalzooffensivo' in starters_homeTeam_allPlays[i][j][k]:
                    off_rebound += 1
                elif 'assist' in starters_homeTeam_allPlays[i][j][k]:
                    assist += 1
                elif 'pallarecuperata' in starters_homeTeam_allPlays[i][j][k]:
                    steal += 1
                elif 'pallapersa' in starters_homeTeam_allPlays[i][j][k]:
                    turnover += 1
                elif 'stoppata' in starters_homeTeam_allPlays[i][j][k]:
                    block_made += 1 
                elif 'stoppatasubita' in starters_homeTeam_allPlays[i][j][k]:
                    block_received += 1 
                elif 'fallocommesso' in starters_homeTeam_allPlays[i][j][k]:
                    foul_made += 1     
                elif 'fallosubito' in starters_homeTeam_allPlays[i][j][k]:
                    foul_received += 1 
            all_stats_homeTeam_startingFive.append([starting_five_homeTeam[i],_1p_made,
              _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
              def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
               foul_made,foul_received,starters_homeTeam_timeOnCourt[i][j]])
    
    # Save data to dataframe and to spreadsheet
    df_homeTeam_startingFive_homeTeamStats = pd.DataFrame(np.array(all_stats_homeTeam_startingFive))
    df_homeTeam_startingFive_homeTeamStats.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_homeTeam_startingFive_homeTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_homeTeam_startingFive_homeTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
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
                
                if 'tiroliberosbagliato' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                    _1p_attempted += 1
                elif 'tiroliberosegnato' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                    _1p_attempted += 1
                    _1p_made += 1
                elif ('tirosbagliatodasotto' in starters_homeTeam_allPlays_oppTeam[i][j][k]
                    or 'tirosbagliatodafuori' in starters_homeTeam_allPlays_oppTeam[i][j][k]):
                    _2p_attempted += 1
                elif ('canestrodasotto' in starters_homeTeam_allPlays_oppTeam[i][j][k]
                      or 'canestrodafuori' in starters_homeTeam_allPlays_oppTeam[i][j][k]):
                    _2p_attempted += 1
                    _2p_made      += 1
                elif 'schiacciata' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                    _2p_attempted += 1
                    _2p_made      += 1
                    dunk          += 1
                elif 'tirosbagliatoda3punti' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                    _3p_attempted += 1
                elif 'canestroda3punti' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                    _3p_attempted += 1
                    _3p_made += 1
                elif 'rimbalzodifensivo' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                    def_rebound += 1
                elif 'rimbalzooffensivo' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                    off_rebound += 1
                elif 'assist' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                    assist += 1
                elif 'pallarecuperata' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                    steal += 1
                elif 'pallapersa' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                    turnover += 1
                elif 'stoppata' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                    block_made += 1 
                elif 'stoppatasubita' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                    block_received += 1 
                elif 'fallocommesso' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                    foul_made += 1     
                elif 'fallosubito' in starters_homeTeam_allPlays_oppTeam[i][j][k]:
                    foul_received += 1 
            all_stats_homeTeam_startingFive_oppTeam.append([starting_five_homeTeam[i],_1p_made,
              _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
              def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
               foul_made,foul_received,starters_homeTeam_timeOnCourt[i][j]])
    
    # Save data to dataframe and to spreadsheet
    df_homeTeam_startingFive_oppTeamStats = pd.DataFrame(np.array(all_stats_homeTeam_startingFive_oppTeam))
    df_homeTeam_startingFive_oppTeamStats.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_homeTeam_startingFive_oppTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_homeTeam_startingFive_oppTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_homeTeam_startingFive_oppTeamStats.to_excel(os.path.join(cwd,'homeTeam_awayTeamStats_StartingFive.xlsx'),
          sheet_name='Sheet_name_1')
    
    #####################
    ### BENCH PLAYERS ###
    #####################
    
    # For the home team, find the bench players
    bench_homeTeam_all                = []
    orig_idx_bench_homeTeam_all       = []
    all_possible_names_bench_homeTeam = []
    for i in range(0,int(len(dfHomeTeam))):
        # Bench players do not have a * in the first column
        if (dfHomeTeam.loc[i][0] == '' and dfHomeTeam.loc[i][2] != 'squadra'
            and dfHomeTeam.loc[i][2] != 'totali'):
            
            s             = dfHomeTeam.loc[i][2]
            ccc           = ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))
            ccc           = ccc.replace(u'\xa0', u' ')
            ccc           = ccc.replace('\'','')
            s_mod_noSpace = ccc.replace(' ','')
            
            bench_homeTeam_all.append(s_mod_noSpace)
            orig_idx_bench_homeTeam_all.append(i)
            idx_space = [x.start() for x in re.finditer(' ', ccc)]
            
            last_name     = ccc[0:idx_space[0]]
            n_first_names = len(idx_space)
            first_names   = []
            for ii in range(0,int(n_first_names)):
                if ii != int(n_first_names)-1:
                    first_names.append(ccc[idx_space[ii]+1:idx_space[ii+1]])
                else:
                    first_names.append(ccc[idx_space[ii]+1:len(ccc)])
            
            all_combinations = []    
            for ii in range(1, len(first_names) + 1):
                for p in itertools.permutations(first_names, ii):
                    all_combinations.append(last_name+str("".join(p)))
            
            n_init_combinations = int(len(all_combinations))
            for ii in range(0,n_init_combinations):
                all_combinations.append(all_combinations[ii][0:int(np.ceil(len(all_combinations[ii])*0.8))])
            
            all_possible_names_bench_homeTeam.append(all_combinations)
            
    # Check when the bench of the home team is on/off the court
    bench_homeTeam          = []
    in_out_bench_homeTeam   = []
    orig_idx_bench_homeTeam = []
    for i in range(0,int(len(bench_homeTeam_all))):
        thisPlayerOnOff = []
        for j in range(0,int(len(df))):
            if any(k in df.loc[j][0] for k in all_possible_names_bench_homeTeam[i]) and 'sostituisce' in df.loc[j][0]:
                thisPlayerOnOff.append([df.loc[j][0],j])
        if len(thisPlayerOnOff)>0:
            bench_homeTeam.append(bench_homeTeam_all[i])
            in_out_bench_homeTeam.append(thisPlayerOnOff)
            orig_idx_bench_homeTeam.append(orig_idx_bench_homeTeam_all[i])
        
    bench_homeTeam_allPlays         = []
    bench_homeTeam_allPlays_oppTeam = []
    bench_homeTeam_timeOnCourt      = []
    
    for i in range(0,int(len(bench_homeTeam))):
        this_bench_homeTeam_Plays           = []
        this_bench_homeTeam_Plays_oppTeam   = []
        this_bench_homeTeam_timeOnCourt     = []
        thisPlayerInOutAll                  = in_out_bench_homeTeam[i]
        thisPlayerInOut                     = []
        for j in range(0,int(len(thisPlayerInOutAll))):
            thisPlayerInOut.append(thisPlayerInOutAll[j][1])
            
        # odd number of out/in: the bench player ends the game
        # This is the inverse reasoning w.r.t. starting players, since
        # the first time a bench players appears in the play-by-play, he/she is
        # subbing in and not out.
        # Hence, for an odd number of occurrences we have ad example
        # I-O-I-O-I
        if np.mod(int(len(thisPlayerInOut)),2) != 0:
            for j in range(0,int(len(thisPlayerInOut))):
                if np.mod(j,2) != 0:
                    pass
                else:
                    if j == int(len(thisPlayerInOut)-1):
                        this_bench_homeTeam_Plays.append(list(df.loc[thisPlayerInOut[j]:len(df)][0]))
                        this_bench_homeTeam_Plays_oppTeam.append(list(df.loc[thisPlayerInOut[j]:len(df)][2]))
                        if all_minutes_found:
                            entryMin = np.where(np.array(idxMinutes)>=thisPlayerInOut[j])[0][0]
                            exitMin  = np.where(np.array(idxMinutes)>=len(df)-1)[0][0]
                            this_bench_homeTeam_timeOnCourt.append(np.max([1,exitMin-entryMin]))
                        else:
                            this_bench_homeTeam_timeOnCourt.append(0)   
                        
                    else:
                        this_bench_homeTeam_Plays.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][0]))
                        this_bench_homeTeam_Plays_oppTeam.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][2]))
                        if all_minutes_found:
                            entryMin = np.where(np.array(idxMinutes)>=thisPlayerInOut[j])[0][0]
                            exitMin  = np.where(np.array(idxMinutes)>=thisPlayerInOut[j+1])[0][0]
                            this_bench_homeTeam_timeOnCourt.append(np.max([1,exitMin-entryMin]))
                        else:
                            this_bench_homeTeam_timeOnCourt.append(0)
        # even number of out/in: the starting player does not end the game
        # This is the inverse reasoning w.r.t. starting players, since
        # the first time a bench players appears in the play-by-play, he/she is
        # subbing in and not out.
        # Hence, for an odd number of occurrences we have ad example
        # I-O-I-O
        else:
            for j in range(0,int(len(thisPlayerInOut)-1)):
                if np.mod(j,2) != 0:
                    pass
                else:
                    this_bench_homeTeam_Plays.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][0]))
                    this_bench_homeTeam_Plays_oppTeam.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][2]))
                    if all_minutes_found:
                        entryMin = np.where(np.array(idxMinutes)>=thisPlayerInOut[j])[0][0]
                        exitMin  = np.where(np.array(idxMinutes)>=thisPlayerInOut[j+1])[0][0]
                        this_bench_homeTeam_timeOnCourt.append(np.max([1,exitMin-entryMin]))
                    else:
                        this_bench_homeTeam_timeOnCourt.append(0)
        bench_homeTeam_allPlays.append(this_bench_homeTeam_Plays)
        bench_homeTeam_allPlays_oppTeam.append(this_bench_homeTeam_Plays_oppTeam)
        bench_homeTeam_timeOnCourt.append(this_bench_homeTeam_timeOnCourt)
    
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
                
                if 'tiroliberosbagliato' in bench_homeTeam_allPlays[i][j][k]:
                    _1p_attempted += 1
                elif 'tiroliberosegnato' in bench_homeTeam_allPlays[i][j][k]:
                    _1p_attempted += 1
                    _1p_made += 1
                elif ('tirosbagliatodasotto' in bench_homeTeam_allPlays[i][j][k]
                    or 'tirosbagliatodafuori' in bench_homeTeam_allPlays[i][j][k]):
                    _2p_attempted += 1
                elif ('canestrodasotto' in bench_homeTeam_allPlays[i][j][k]
                      or 'canestrodafuori' in bench_homeTeam_allPlays[i][j][k]):
                    _2p_attempted += 1
                    _2p_made      += 1
                elif 'schiacciata' in bench_homeTeam_allPlays[i][j][k]:
                    _2p_attempted += 1
                    _2p_made      += 1
                    dunk          += 1
                elif 'tirosbagliatoda3punti' in bench_homeTeam_allPlays[i][j][k]:
                    _3p_attempted += 1
                elif 'canestroda3punti' in bench_homeTeam_allPlays[i][j][k]:
                    _3p_attempted += 1
                    _3p_made += 1
                elif 'rimbalzodifensivo' in bench_homeTeam_allPlays[i][j][k]:
                    def_rebound += 1
                elif 'rimbalzooffensivo' in bench_homeTeam_allPlays[i][j][k]:
                    off_rebound += 1
                elif 'assist' in bench_homeTeam_allPlays[i][j][k]:
                    assist += 1
                elif 'pallarecuperata' in bench_homeTeam_allPlays[i][j][k]:
                    steal += 1
                elif 'pallapersa' in bench_homeTeam_allPlays[i][j][k]:
                    turnover += 1
                elif 'stoppata' in bench_homeTeam_allPlays[i][j][k]:
                    block_made += 1 
                elif 'stoppatasubita' in bench_homeTeam_allPlays[i][j][k]:
                    block_received += 1 
                elif 'fallocommesso' in bench_homeTeam_allPlays[i][j][k]:
                    foul_made += 1     
                elif 'fallosubito' in bench_homeTeam_allPlays[i][j][k]:
                    foul_received += 1 
            all_stats_homeTeam_bench.append([bench_homeTeam[i],_1p_made,
              _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
              def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
               foul_made,foul_received,bench_homeTeam_timeOnCourt[i][j]])
    
    # Save data to dataframe and to spreadsheet
    df_homeTeam_bench_homeTeamStats = pd.DataFrame(np.array(all_stats_homeTeam_bench))
    df_homeTeam_bench_homeTeamStats.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_homeTeam_bench_homeTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_homeTeam_bench_homeTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_homeTeam_bench_homeTeamStats.to_excel(os.path.join(cwd,'homeTeam_homeTeamStats_Bench.xlsx'),
          sheet_name='Sheet_name_1')
    
    #############################################################
    # Stats for the home team bench (opposing team stats)
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
                
                if 'tiroliberosbagliato' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                    _1p_attempted += 1
                elif 'tiroliberosegnato' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                    _1p_attempted += 1
                    _1p_made += 1
                elif ('tirosbagliatodasotto' in bench_homeTeam_allPlays_oppTeam[i][j][k]
                    or 'Tirosbagliatodafuori' in bench_homeTeam_allPlays_oppTeam[i][j][k]):
                    _2p_attempted += 1
                elif ('canestrodasotto' in bench_homeTeam_allPlays_oppTeam[i][j][k]
                      or 'canestrodafuori' in bench_homeTeam_allPlays_oppTeam[i][j][k]):
                    _2p_attempted += 1
                    _2p_made      += 1
                elif 'schiacciata' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                    _2p_attempted += 1
                    _2p_made      += 1
                    dunk          += 1
                elif 'tirosbagliatoda3punti' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                    _3p_attempted += 1
                elif 'canestroda3punti' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                    _3p_attempted += 1
                    _3p_made += 1
                elif 'rimbalzodifensivo' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                    def_rebound += 1
                elif 'rimbalzooffensivo' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                    off_rebound += 1
                elif 'assist' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                    assist += 1
                elif 'pallarecuperata' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                    steal += 1
                elif 'pallapersa' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                    turnover += 1
                elif 'stoppata' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                    block_made += 1 
                elif 'stoppatasubita' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                    block_received += 1 
                elif 'fallocommesso' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                    foul_made += 1     
                elif 'fallosubito' in bench_homeTeam_allPlays_oppTeam[i][j][k]:
                    foul_received += 1 
            all_stats_homeTeam_bench_oppTeam.append([bench_homeTeam[i],_1p_made,
              _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
              def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
               foul_made,foul_received,bench_homeTeam_timeOnCourt[i][j]])
    
    # Save data to dataframe and to spreadsheet
    df_homeTeam_bench_oppTeamStats = pd.DataFrame(np.array(all_stats_homeTeam_bench_oppTeam))
    df_homeTeam_bench_oppTeamStats.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_homeTeam_bench_oppTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_homeTeam_bench_oppTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_homeTeam_bench_oppTeamStats.to_excel(os.path.join(cwd,'homeTeam_awayTeamStats_bench.xlsx'),
          sheet_name='Sheet_name_1')
    
    df_homeTeam_startingPlusBench_ownStats = pd.concat([df_homeTeam_startingFive_homeTeamStats,
                                                    df_homeTeam_bench_homeTeamStats], ignore_index=True)
    df_homeTeam_startingPlusBench_ownStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_homeTeam_startingPlusBench_ownStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_homeTeam_startingPlusBench_ownStats_aggr = df_homeTeam_startingPlusBench_ownStats.groupby('Player',as_index=False).sum()
    
    df_homeTeam_startingPlusBench_oppTeamStats = pd.concat([df_homeTeam_startingFive_oppTeamStats,
                                                        df_homeTeam_bench_oppTeamStats], ignore_index=True)
    df_homeTeam_startingPlusBench_oppTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_homeTeam_startingPlusBench_oppTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_homeTeam_startingPlusBench_oppTeamStats_aggr = df_homeTeam_startingPlusBench_oppTeamStats.groupby('Player',as_index=False).sum()
    
    return (df_homeTeam_startingFive_homeTeamStats,
           df_homeTeam_startingFive_oppTeamStats,
           df_homeTeam_bench_homeTeamStats,
           df_homeTeam_bench_oppTeamStats,
           df_homeTeam_startingPlusBench_ownStats_aggr,
           df_homeTeam_startingPlusBench_oppTeamStats_aggr,
           starting_five_homeTeam,
           bench_homeTeam,
           orig_idx_starting_five_homeTeam,orig_idx_bench_homeTeam,
           all_possible_names_starting_five_homeTeam)

# Input  : play-by-play dataframe (df), home team dataframe (dfAwayTeam), 
#          list of indices reporting
#          changes in the minute of the game in the play-by-play dataframe (idxMinutes),
#          flag highlighting if idxMinutes has been calculated for all 40
#          minutes or not (all_minutes_found), path to current folder (cwd)
# Output : dataframes containing all relevant info (1p,2p,3p attemped and made),
#          defensive and offensive rebounds, assists etc, at the team level
#          (both for the own team and the opposing team) for each player of the away team. 
#          It is important to highlight that stats 
#          are aggregated at the team level. As example, a row corresponding
#          to a specific player contains all the info that his/her team or the
#          opposing team generated while the specific player was on the court 
def get_awayTeam_stats_perPlayer(df,dfAwayTeam,idxMinutes,all_minutes_found,cwd):
    
    ###############
    # STARTING FIVE
    ###############
    orig_idx_starting_five_awayTeam = []
    # For the away team, find the starting five
    starting_five_awayTeam = []
    all_possible_names_starting_five_awayTeam = []
    for i in range(0,int(len(dfAwayTeam))):
        if dfAwayTeam.loc[i][0] == '*':
            
            s             = dfAwayTeam.loc[i][2]
            ccc           = ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))
            ccc           = ccc.replace(u'\xa0', u' ')
            ccc           = ccc.replace('\'','')
            s_mod_noSpace = ccc.replace(' ','')
            
            starting_five_awayTeam.append(s_mod_noSpace)
            orig_idx_starting_five_awayTeam.append(i)
            idx_space = [x.start() for x in re.finditer(' ', ccc)]
            
            last_name     = ccc[0:idx_space[0]]
            n_first_names = len(idx_space)
            first_names   = []
            
            for ii in range(0,int(n_first_names)):
                if ii != int(n_first_names)-1:
                    first_names.append(ccc[idx_space[ii]+1:idx_space[ii+1]])
                else:
                    first_names.append(ccc[idx_space[ii]+1:len(ccc)])
            
            all_combinations = []    
            for ii in range(1, len(first_names) + 1):
                for p in itertools.permutations(first_names, ii):
                    all_combinations.append(last_name+str("".join(p)))
            
            n_init_combinations = int(len(all_combinations))
            for ii in range(0,n_init_combinations):
                all_combinations.append(all_combinations[ii][0:int(np.ceil(len(all_combinations[ii])*0.8))])
            
            all_possible_names_starting_five_awayTeam.append(all_combinations)
    
  
    # Check when the starting five of the away team is on/off the court
    in_out_startingFive_awayTeam = []
    for i in range(0,int(len(starting_five_awayTeam))):
        thisPlayerOnOff = []
        for j in range(0,int(len(df))):
            if any(k in df.loc[j][2] for k in all_possible_names_starting_five_awayTeam[i]) and 'sostituisce' in df.loc[j][2]: 
            #if thisPlayer in df.loc[j][2] and 'sostituisce' in df.loc[j][2]:
                thisPlayerOnOff.append([df.loc[j][2],j])
        in_out_startingFive_awayTeam.append(thisPlayerOnOff)
        

    
    starters_awayTeam_allPlays         = []
    starters_awayTeam_allPlays_oppTeam = []
    starters_awayTeam_timeOnCourt      = []
    
    for i in range(0,int(len(starting_five_awayTeam))):
        this_starter_awayTeam_Plays         = []
        this_starter_awayTeam_timeOnCourt   = []
        this_starter_awayTeam_Plays_oppTeam = []
        thisPlayerInOutAll                  = in_out_startingFive_awayTeam[i]
        thisPlayerInOut                     = []
        for j in range(0,int(len(thisPlayerInOutAll))):
            thisPlayerInOut.append(thisPlayerInOutAll[j][1])
            
        this_starter_awayTeam_Plays.append(list(df.loc[0:thisPlayerInOut[0]][2])) 
        this_starter_awayTeam_Plays_oppTeam.append(list(df.loc[0:thisPlayerInOut[0]][0]))
        # Find minute when starter exits for first time
        if all_minutes_found:
            minFirstExit = np.where(np.array(idxMinutes)>=thisPlayerInOut[0])[0][0]
            this_starter_awayTeam_timeOnCourt.append(minFirstExit)
        else:
            this_starter_awayTeam_timeOnCourt.append(0)
            
        # even number of out/in: the starting player ends the game as well
        if np.mod(int(len(thisPlayerInOut)),2) == 0:
            for j in range(0,int(len(thisPlayerInOut))):
                if np.mod(j,2) == 0:
                    pass
                else:
                    if j == int(len(thisPlayerInOut)-1):
                        this_starter_awayTeam_Plays.append(list(df.loc[thisPlayerInOut[j]:len(df)][2]))
                        this_starter_awayTeam_Plays_oppTeam.append(list(df.loc[thisPlayerInOut[j]:len(df)][0]))
                        if all_minutes_found:
                            entryMin = np.where(np.array(idxMinutes)>=thisPlayerInOut[j])[0][0]
                            exitMin  = np.where(np.array(idxMinutes)>=len(df)-1)[0][0]
                            this_starter_awayTeam_timeOnCourt.append(np.max([1,exitMin-entryMin]))
                        else:
                            this_starter_awayTeam_timeOnCourt.append(0)
                    else:
                        this_starter_awayTeam_Plays.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][2]))
                        this_starter_awayTeam_Plays_oppTeam.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][0]))
                        if all_minutes_found:
                            entryMin = np.where(np.array(idxMinutes)>=thisPlayerInOut[j])[0][0]
                            exitMin  = np.where(np.array(idxMinutes)>=len(df)-1)[0][0]
                            this_starter_awayTeam_timeOnCourt.append(np.max([1,exitMin-entryMin]))
                        else:
                            this_starter_awayTeam_timeOnCourt.append(0)
        # odd number of out/in: the starting player does not end the game
        else:
            for j in range(0,int(len(thisPlayerInOut)-1)):
                if np.mod(j,2) == 0:
                    pass
                else:
                    this_starter_awayTeam_Plays.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][2]))
                    this_starter_awayTeam_Plays_oppTeam.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][0]))
                    if all_minutes_found:
                        entryMin = np.where(np.array(idxMinutes)>=thisPlayerInOut[j])[0][0]
                        exitMin  = np.where(np.array(idxMinutes)>=len(df)-1)[0][0]
                        this_starter_awayTeam_timeOnCourt.append(np.max([1,exitMin-entryMin]))
                    else:
                        this_starter_awayTeam_timeOnCourt.append(0)
        starters_awayTeam_allPlays.append(this_starter_awayTeam_Plays)
        starters_awayTeam_allPlays_oppTeam.append(this_starter_awayTeam_Plays_oppTeam)
        starters_awayTeam_timeOnCourt.append(this_starter_awayTeam_timeOnCourt)
        
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
                
                if 'tiroliberosbagliato' in starters_awayTeam_allPlays[i][j][k]:
                    _1p_attempted += 1
                elif 'tiroliberosegnato' in starters_awayTeam_allPlays[i][j][k]:
                    _1p_attempted += 1
                    _1p_made += 1
                elif ('tirosbagliatodasotto' in starters_awayTeam_allPlays[i][j][k]
                    or 'tirosbagliatodafuori' in starters_awayTeam_allPlays[i][j][k]):
                    _2p_attempted += 1
                elif ('canestrodasotto' in starters_awayTeam_allPlays[i][j][k]
                      or 'canestrodafuori' in starters_awayTeam_allPlays[i][j][k]):
                    _2p_attempted += 1
                    _2p_made      += 1
                elif 'schiacciata' in starters_awayTeam_allPlays[i][j][k]:
                    _2p_attempted += 1
                    _2p_made      += 1
                    dunk          += 1
                elif 'tirosbagliatoda3punti' in starters_awayTeam_allPlays[i][j][k]:
                    _3p_attempted += 1
                elif 'canestroda3punti' in starters_awayTeam_allPlays[i][j][k]:
                    _3p_attempted += 1
                    _3p_made += 1
                elif 'rimbalzodifensivo' in starters_awayTeam_allPlays[i][j][k]:
                    def_rebound += 1
                elif 'rimbalzooffensivo' in starters_awayTeam_allPlays[i][j][k]:
                    off_rebound += 1
                elif 'assist' in starters_awayTeam_allPlays[i][j][k]:
                    assist += 1
                elif 'pallarecuperata' in starters_awayTeam_allPlays[i][j][k]:
                    steal += 1
                elif 'pallapersa' in starters_awayTeam_allPlays[i][j][k]:
                    turnover += 1
                elif 'stoppata' in starters_awayTeam_allPlays[i][j][k]:
                    block_made += 1 
                elif 'stoppatasubita' in starters_awayTeam_allPlays[i][j][k]:
                    block_received += 1 
                elif 'fallocommesso' in starters_awayTeam_allPlays[i][j][k]:
                    foul_made += 1     
                elif 'fallosubito' in starters_awayTeam_allPlays[i][j][k]:
                    foul_received += 1 
            all_stats_awayTeam_startingFive.append([starting_five_awayTeam[i],_1p_made,
              _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
              def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
               foul_made,foul_received,starters_awayTeam_timeOnCourt[i][j]])
    
    # Save data to dataframe and to spreadsheet
    df_awayTeam_startingFive_ownTeamStats = pd.DataFrame(np.array(all_stats_awayTeam_startingFive))
    df_awayTeam_startingFive_ownTeamStats.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_awayTeam_startingFive_ownTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_awayTeam_startingFive_ownTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_awayTeam_startingFive_ownTeamStats.to_excel(os.path.join(cwd,'awayTeam_awayTeamStats_StartingFive.xlsx'),
          sheet_name='Sheet_name_1')
    
    #############################################################
    # Stats for the away team starting five (opposing team stats)
    #############################################################
    all_stats_awayTeam_startingFive_oppTeam = []
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
                
                if 'tiroliberosbagliato' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                    _1p_attempted += 1
                elif 'tiroliberosegnato' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                    _1p_attempted += 1
                    _1p_made += 1
                elif ('tirosbagliatodasotto' in starters_awayTeam_allPlays_oppTeam[i][j][k]
                    or 'tirosbagliatodafuori' in starters_awayTeam_allPlays_oppTeam[i][j][k]):
                    _2p_attempted += 1
                elif ('canestrodasotto' in starters_awayTeam_allPlays_oppTeam[i][j][k]
                      or 'canestrodafuori' in starters_awayTeam_allPlays_oppTeam[i][j][k]):
                    _2p_attempted += 1
                    _2p_made      += 1
                elif 'schiacciata' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                    _2p_attempted += 1
                    _2p_made      += 1
                    dunk          += 1
                elif 'tirosbagliatoda3punti' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                    _3p_attempted += 1
                elif 'canestroda3punti' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                    _3p_attempted += 1
                    _3p_made += 1
                elif 'rimbalzodifensivo' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                    def_rebound += 1
                elif 'rimbalzooffensivo' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                    off_rebound += 1
                elif 'assist' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                    assist += 1
                elif 'pallarecuperata' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                    steal += 1
                elif 'pallapersa' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                    turnover += 1
                elif 'stoppata' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                    block_made += 1 
                elif 'stoppatasubita' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                    block_received += 1 
                elif 'fallocommesso' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                    foul_made += 1     
                elif 'fallosubito' in starters_awayTeam_allPlays_oppTeam[i][j][k]:
                    foul_received += 1 
            all_stats_awayTeam_startingFive_oppTeam.append([starting_five_awayTeam[i],_1p_made,
              _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
              def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
               foul_made,foul_received,starters_awayTeam_timeOnCourt[i][j]])
    
    # Save data to dataframe and to spreadsheet
    df_awayTeam_startingFive_oppTeamStats = pd.DataFrame(np.array(all_stats_awayTeam_startingFive_oppTeam))
    df_awayTeam_startingFive_oppTeamStats.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_awayTeam_startingFive_oppTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_awayTeam_startingFive_oppTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_awayTeam_startingFive_oppTeamStats.to_excel(os.path.join(cwd,'awayTeam_oppTeamStats_StartingFive.xlsx'),
          sheet_name='Sheet_name_1')
    
    #####################
    ### BENCH PLAYERS ###
    #####################
    
    # For the home team, find the bench players
    bench_awayTeam_all                = []
    orig_idx_bench_awayTeam_all       = []
    all_possible_names_bench_awayTeam = []
    
    for i in range(0,int(len(dfAwayTeam))):
        if (dfAwayTeam.loc[i][0] == '' and dfAwayTeam.loc[i][2] != 'squadra'
            and dfAwayTeam.loc[i][2] != 'totali'):
            

            s             = dfAwayTeam.loc[i][2]
            ccc           = ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))
            ccc           = ccc.replace(u'\xa0', u' ')
            ccc           = ccc.replace('\'','')
            s_mod_noSpace = ccc.replace(' ','')
            
            bench_awayTeam_all.append(s_mod_noSpace)
            orig_idx_bench_awayTeam_all.append(i)
            idx_space = [x.start() for x in re.finditer(' ', ccc)]
            
            last_name     = ccc[0:idx_space[0]]
            n_first_names = len(idx_space)
            first_names   = []
            
            for ii in range(0,int(n_first_names)):
                if ii != int(n_first_names)-1:
                    first_names.append(ccc[idx_space[ii]+1:idx_space[ii+1]])
                else:
                    first_names.append(ccc[idx_space[ii]+1:len(ccc)])
            
            all_combinations = []    
            for ii in range(1, len(first_names) + 1):
                for p in itertools.permutations(first_names, ii):
                    all_combinations.append(last_name+str("".join(p)))
            
            n_init_combinations = int(len(all_combinations))
            for ii in range(0,n_init_combinations):
                all_combinations.append(all_combinations[ii][0:int(np.ceil(len(all_combinations[ii])*0.8))])
            
            all_possible_names_bench_awayTeam.append(all_combinations)


    # Check when the bench of the home team is on/off the court
    bench_awayTeam          = []
    in_out_bench_awayTeam   = []
    orig_idx_bench_awayTeam = []
    for i in range(0,int(len(bench_awayTeam_all))):
        thisPlayerOnOff = []
        for j in range(0,int(len(df))):
            if any(k in df.loc[j][2] for k in all_possible_names_bench_awayTeam[i]) and 'sostituisce' in df.loc[j][2]:
                thisPlayerOnOff.append([df.loc[j][0],j])
        if len(thisPlayerOnOff)>0:
            bench_awayTeam.append(bench_awayTeam_all[i])
            in_out_bench_awayTeam.append(thisPlayerOnOff)
            orig_idx_bench_awayTeam.append(orig_idx_bench_awayTeam_all[i])
        
    bench_awayTeam_allPlays         = []
    bench_awayTeam_allPlays_oppTeam = []
    bench_awayTeam_timeOnCourt      = []
    
    for i in range(0,int(len(bench_awayTeam))):
        this_bench_awayTeam_Plays           = []
        this_bench_awayTeam_Plays_oppTeam   = []
        this_bench_awayTeam_timeOnCourt     = []
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
                        if all_minutes_found:
                            entryMin = np.where(np.array(idxMinutes)>=thisPlayerInOut[j])[0][0]
                            exitMin  = np.where(np.array(idxMinutes)>=len(df)-1)[0][0]
                            this_bench_awayTeam_timeOnCourt.append(np.max([1,exitMin-entryMin]))
                        else:
                            this_bench_awayTeam_timeOnCourt.append(0)   
                        
                    else:
                        this_bench_awayTeam_Plays.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][2]))
                        this_bench_awayTeam_Plays_oppTeam.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][0]))
                        if all_minutes_found:
                            entryMin = np.where(np.array(idxMinutes)>=thisPlayerInOut[j])[0][0]
                            exitMin  = np.where(np.array(idxMinutes)>=thisPlayerInOut[j+1])[0][0]
                            this_bench_awayTeam_timeOnCourt.append(np.max([1,exitMin-entryMin]))
                        else:
                            this_bench_awayTeam_timeOnCourt.append(0)
        # even number of out/in: the starting player does not end the game
        else:
            for j in range(0,int(len(thisPlayerInOut)-1)):
                if np.mod(j,2) != 0:
                    pass
                else:
                    this_bench_awayTeam_Plays.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][2]))
                    this_bench_awayTeam_Plays_oppTeam.append(list(df.loc[thisPlayerInOut[j]:thisPlayerInOut[j+1]][0]))
                    if all_minutes_found:
                        entryMin = np.where(np.array(idxMinutes)>=thisPlayerInOut[j])[0][0]
                        exitMin  = np.where(np.array(idxMinutes)>=thisPlayerInOut[j+1])[0][0]
                        this_bench_awayTeam_timeOnCourt.append(np.max([1,exitMin-entryMin]))
                    else:
                        this_bench_awayTeam_timeOnCourt.append(0)
        bench_awayTeam_allPlays.append(this_bench_awayTeam_Plays)
        bench_awayTeam_allPlays_oppTeam.append(this_bench_awayTeam_Plays_oppTeam)
        bench_awayTeam_timeOnCourt.append(this_bench_awayTeam_timeOnCourt)
    
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
                
                if 'tiroliberosbagliato' in bench_awayTeam_allPlays[i][j][k]:
                    _1p_attempted += 1
                elif 'tiroliberosegnato' in bench_awayTeam_allPlays[i][j][k]:
                    _1p_attempted += 1
                    _1p_made += 1
                elif ('tirosbagliatodasotto' in bench_awayTeam_allPlays[i][j][k]
                    or 'tirosbagliatodafuori' in bench_awayTeam_allPlays[i][j][k]):
                    _2p_attempted += 1
                elif ('canestrodasotto' in bench_awayTeam_allPlays[i][j][k]
                      or 'canestrodafuori' in bench_awayTeam_allPlays[i][j][k]):
                    _2p_attempted += 1
                    _2p_made      += 1
                elif 'schiacciata' in bench_awayTeam_allPlays[i][j][k]:
                    _2p_attempted += 1
                    _2p_made      += 1
                    dunk          += 1
                elif 'tirosbagliatoda3punti' in bench_awayTeam_allPlays[i][j][k]:
                    _3p_attempted += 1
                elif 'canestroda3punti' in bench_awayTeam_allPlays[i][j][k]:
                    _3p_attempted += 1
                    _3p_made += 1
                elif 'rimbalzodifensivo' in bench_awayTeam_allPlays[i][j][k]:
                    def_rebound += 1
                elif 'rimbalzooffensivo' in bench_awayTeam_allPlays[i][j][k]:
                    off_rebound += 1
                elif 'assist' in bench_awayTeam_allPlays[i][j][k]:
                    assist += 1
                elif 'pallarecuperata' in bench_awayTeam_allPlays[i][j][k]:
                    steal += 1
                elif 'pallapersa' in bench_awayTeam_allPlays[i][j][k]:
                    turnover += 1
                elif 'stoppata' in bench_awayTeam_allPlays[i][j][k]:
                    block_made += 1 
                elif 'stoppatasubita' in bench_awayTeam_allPlays[i][j][k]:
                    block_received += 1 
                elif 'fallocommesso' in bench_awayTeam_allPlays[i][j][k]:
                    foul_made += 1     
                elif 'fallosubito' in bench_awayTeam_allPlays[i][j][k]:
                    foul_received += 1 
            all_stats_awayTeam_bench.append([bench_awayTeam[i],_1p_made,
              _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
              def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
               foul_made,foul_received,bench_awayTeam_timeOnCourt[i][j]])
    
    # Save data to dataframe and to spreadsheet
    df_awayTeam_bench_ownTeamStats = pd.DataFrame(np.array(all_stats_awayTeam_bench))
    df_awayTeam_bench_ownTeamStats.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_awayTeam_bench_ownTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_awayTeam_bench_ownTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_awayTeam_bench_ownTeamStats.to_excel(os.path.join(cwd,'awayTeam_ownStats_Bench.xlsx'),
          sheet_name='Sheet_name_1')
    
    #############################################################
    # Stats for the home team bench (opposing team stats)
    #############################################################
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
                
                if 'tiroliberosbagliato' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                    _1p_attempted += 1
                elif 'tiroliberosegnato' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                    _1p_attempted += 1
                    _1p_made += 1
                elif ('tirosbagliatodasotto' in bench_awayTeam_allPlays_oppTeam[i][j][k]
                    or 'Tirosbagliatodafuori' in bench_awayTeam_allPlays_oppTeam[i][j][k]):
                    _2p_attempted += 1
                elif ('canestrodasotto' in bench_awayTeam_allPlays_oppTeam[i][j][k]
                      or 'canestrodafuori' in bench_awayTeam_allPlays_oppTeam[i][j][k]):
                    _2p_attempted += 1
                    _2p_made      += 1
                elif 'schiacciata' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                    _2p_attempted += 1
                    _2p_made      += 1
                    dunk          += 1
                elif 'tirosbagliatoda3punti' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                    _3p_attempted += 1
                elif 'canestroda3punti' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                    _3p_attempted += 1
                    _3p_made += 1
                elif 'rimbalzodifensivo' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                    def_rebound += 1
                elif 'rimbalzooffensivo' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                    off_rebound += 1
                elif 'assist' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                    assist += 1
                elif 'pallarecuperata' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                    steal += 1
                elif 'pallapersa' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                    turnover += 1
                elif 'stoppata' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                    block_made += 1 
                elif 'stoppatasubita' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                    block_received += 1 
                elif 'fallocommesso' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                    foul_made += 1     
                elif 'fallosubito' in bench_awayTeam_allPlays_oppTeam[i][j][k]:
                    foul_received += 1 
            all_stats_awayTeam_bench_oppTeam.append([bench_awayTeam[i],_1p_made,
              _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
              def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
               foul_made,foul_received,bench_awayTeam_timeOnCourt[i][j]])
    
    # Save data to dataframe and to spreadsheet
    df_awayTeam_bench_oppTeamStats = pd.DataFrame(np.array(all_stats_awayTeam_bench_oppTeam))
    df_awayTeam_bench_oppTeamStats.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_awayTeam_bench_oppTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_awayTeam_bench_oppTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_awayTeam_bench_oppTeamStats.to_excel(os.path.join(cwd,'awayTeam_oppTeamStats_bench.xlsx'),
          sheet_name='Sheet_name_1')
    
    df_awayTeam_startingPlusBench_ownStats = pd.concat([df_awayTeam_startingFive_ownTeamStats,
                                                    df_awayTeam_bench_oppTeamStats], ignore_index=True)
    df_awayTeam_startingPlusBench_ownStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_awayTeam_startingPlusBench_ownStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_awayTeam_startingPlusBench_ownTeamStats_aggr = df_awayTeam_startingPlusBench_ownStats.groupby('Player',as_index=False).sum()
    
    df_awayTeam_startingPlusBench_oppTeamStats = pd.concat([df_awayTeam_startingFive_oppTeamStats,
                                                        df_awayTeam_bench_oppTeamStats], ignore_index=True)
    df_awayTeam_startingPlusBench_oppTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_awayTeam_startingPlusBench_oppTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_awayTeam_startingPlusBench_oppTeamStats_aggr = df_awayTeam_startingPlusBench_oppTeamStats.groupby('Player',as_index=False).sum()
    
    return (df_awayTeam_startingFive_ownTeamStats,
           df_awayTeam_startingFive_oppTeamStats,
           df_awayTeam_bench_ownTeamStats,
           df_awayTeam_bench_oppTeamStats,
           df_awayTeam_startingPlusBench_ownTeamStats_aggr,
           df_awayTeam_startingPlusBench_oppTeamStats_aggr,
           starting_five_awayTeam,
           bench_awayTeam,
           orig_idx_starting_five_awayTeam,orig_idx_bench_awayTeam,
           all_possible_names_starting_five_awayTeam)

# Input  : play-by-play dataframe (df), home team dataframe (dfHomeTeam),
#          starting five players (starting_five_homeTeam), bench players who
#          played (bench_homeTeam),  
#          list of indices reporting
#          changes in the minute of the game in the play-by-play dataframe (idxMinutes),
#          flag highlighting if idxMinutes has been calculated for all 40
#          minutes or not (all_minutes_found), path to current folder (cwd)
# Output : dataframes containing all relevant info (1p,2p,3p attemped and made),
#          defensive and offensive rebounds, assists etc, at the team level
#          (both for the own team and the opposing team) for each lineup of the home team. 
#          It is important to highlight that stats 
#          are aggregated at the team level. As example, a row corresponding
#          to a specific lineup contains all the info that its team or the
#          opposing team generated while the specific lineup was on the court     
def get_homeTeam_stats_perLineup(df,dfHomeTeam,starting_five_homeTeam,bench_homeTeam,idxMinutes,all_minutes_found,cwd):
    all_players_homeTeam = starting_five_homeTeam + bench_homeTeam
    
    all_lineups_homeTeam = []
    all_lineups_homeTeam.append([sorted(starting_five_homeTeam),0])
    current_lineup = starting_five_homeTeam
    current_bench  = list(set(all_players_homeTeam) - set(current_lineup))
    
    perc_string_to_match = 0.8
    
    # determine all different lineups by replacing the current exiting player
    # with the current entering player and updating the current lineup. Then,
    # find all unique entries (clearly, the same lineup might appear more
    # than once during a game)
    for j in range(0,int(len(df))):
        if 'sostituisce' in df.loc[j][0]:
            found_bench_player_in = 0
            for cont in range(0,int(len(current_bench))):
                if current_bench[cont][0:int(len(current_bench[cont])*perc_string_to_match)] in df.loc[j][0]:
                    new_player_onField    = current_bench[cont]
                    found_bench_player_in = 1
                    break
            found_lineup_player_out = 0
            for cont in range(0,int(len(current_lineup))):
                if current_lineup[cont][0:int(len(current_lineup[cont])*perc_string_to_match)] in df.loc[j][0]:
                    new_player_offField     = current_lineup[cont]
                    found_lineup_player_out = 1
                    break
            if found_bench_player_in*found_lineup_player_out == 1:
                current_lineup = list(set(current_lineup) - set([new_player_offField]))
                current_lineup = current_lineup + [new_player_onField]
                current_bench = list(set(current_bench) - set([new_player_onField]))
                current_bench = current_bench + [new_player_offField]
                
                all_lineups_homeTeam.append([sorted(current_lineup),j])
            
    idx_unique_lineups_homeTeam = []
    for i in range(0,int(len(all_lineups_homeTeam))):
        this_lineup_idx = []
        for j in range(0,int(len(all_lineups_homeTeam))):
            if all_lineups_homeTeam[j][0] == all_lineups_homeTeam[i][0]:
                this_lineup_idx.append(j)
        idx_unique_lineups_homeTeam.append(this_lineup_idx)
    
    if max(len(l) for l in idx_unique_lineups_homeTeam) > 1:
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
                if all_minutes_found:
                    entryMin         = np.where(np.array(idxMinutes)>=startEnd_unique_lineups_homeTeam[i][j][0])[0][0]
                    exitMin          = np.where(np.array(idxMinutes)>=startEnd_unique_lineups_homeTeam[i][j][1])[0][0]
                    this_timeOnCourt = np.max([1,exitMin-entryMin])
                else:
                    this_timeOnCourt = 0
                
                if 'tiroliberosbagliato' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                    _1p_attempted += 1
                elif 'tiroliberosegnato' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                    _1p_attempted += 1
                    _1p_made += 1
                elif ('tirosbagliatodasotto' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]
                    or 'tirosbagliatodafuori' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]):
                    _2p_attempted += 1
                elif ('canestrodasotto' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]
                      or 'canestrodafuori' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]):
                    _2p_attempted += 1
                    _2p_made      += 1
                elif 'schiacciata' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                    _2p_attempted += 1
                    _2p_made      += 1
                    dunk          += 1
                elif 'tirosbagliatoda3punti' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                    _3p_attempted += 1
                elif 'canestroda3punti' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                    _3p_attempted += 1
                    _3p_made += 1
                elif 'rimbalzodifensivo' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                    def_rebound += 1
                elif 'rimbalzooffensivo' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                    off_rebound += 1
                elif 'assist' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                    assist += 1
                elif 'pallarecuperata' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                    steal += 1
                elif 'pallapersa' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                    turnover += 1
                elif 'stoppata' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                    block_made += 1 
                elif 'stoppataSubita' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                    block_received += 1 
                elif 'fallocommesso' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                    foul_made += 1     
                elif 'fallosubito' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][0]:
                    foul_received += 1 
            all_stats_homeTeam_lineups.append([all_lineups_homeTeam[idx_unique_lineups_homeTeam[i][j]][0],_1p_made,
              _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
              def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
               foul_made,foul_received,this_timeOnCourt])
    
    # Save data to dataframe and to spreadsheet
    df_homeTeam_lineups_ownTeamStats = pd.DataFrame(np.array(all_stats_homeTeam_lineups))
    df_homeTeam_lineups_ownTeamStats.columns = ['Lineup','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_homeTeam_lineups_ownTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_homeTeam_lineups_ownTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_homeTeam_lineups_ownTeamStats.to_excel(os.path.join(cwd,'homeTeam_lineups_stats.xlsx'),
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
                
                if all_minutes_found:
                    entryMin         = np.where(np.array(idxMinutes)>=startEnd_unique_lineups_homeTeam[i][j][0])[0][0]
                    exitMin          = np.where(np.array(idxMinutes)>=startEnd_unique_lineups_homeTeam[i][j][1])[0][0]
                    this_timeOnCourt = np.max([1,exitMin-entryMin])
                else:
                    this_timeOnCourt = 0
                
                if 'tiroliberosbagliato' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                    _1p_attempted += 1
                elif 'tiroliberosegnato' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                    _1p_attempted += 1
                    _1p_made += 1
                elif ('tirosbagliatodasotto' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]
                    or 'tirosbagliatodafuori' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]):
                    _2p_attempted += 1
                elif ('canestrodasotto' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]
                      or 'canestrodafuori' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]):
                    _2p_attempted += 1
                    _2p_made      += 1
                elif 'schiacciata' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                    _2p_attempted += 1
                    _2p_made      += 1
                    dunk          += 1
                elif 'tirosbagliatoda3punti' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                    _3p_attempted += 1
                elif 'canestroda3punti' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                    _3p_attempted += 1
                    _3p_made += 1
                elif 'rimbalzodifensivo' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                    def_rebound += 1
                elif 'rimbalzooffensivo' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                    off_rebound += 1
                elif 'assist' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                    assist += 1
                elif 'pallarecuperata' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                    steal += 1
                elif 'pallapersa' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                    turnover += 1
                elif 'stoppata' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                    block_made += 1 
                elif 'stoppataSubita' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                    block_received += 1 
                elif 'fallocommesso' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                    foul_made += 1     
                elif 'fallosubito' in df.loc[startEnd_unique_lineups_homeTeam[i][j][0]+k][2]:
                    foul_received += 1 
            all_stats_homeTeam_lineups_oppTeam.append([all_lineups_homeTeam[idx_unique_lineups_homeTeam[i][j]][0],_1p_made,
              _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
              def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
               foul_made,foul_received,this_timeOnCourt])
    
    # Save data to dataframe and to spreadsheet
    df_homeTeam_lineups_oppTeamStats = pd.DataFrame(np.array(all_stats_homeTeam_lineups_oppTeam))
    df_homeTeam_lineups_oppTeamStats.columns = ['Lineup','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_homeTeam_lineups_oppTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_homeTeam_lineups_oppTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_homeTeam_lineups_oppTeamStats.to_excel(os.path.join(cwd,'homeTeam_lineups_stats_oppTeam.xlsx'),
          sheet_name='Sheet_name_1')
    
    ##########################################
    ### Aggregate results for repeated lineups
    ##########################################
    
    for i in range(0,int(len(df_homeTeam_lineups_ownTeamStats))):
        lineup_string = ''
        for j in range(0,int(len(df_homeTeam_lineups_ownTeamStats.loc[i]['Lineup']))):
            lineup_string += df_homeTeam_lineups_ownTeamStats.loc[i]['Lineup'][j]
        df_homeTeam_lineups_ownTeamStats.at[i,'Lineup'] = lineup_string
        
    df_homeTeam_lineups_ownTeamStats_aggr = df_homeTeam_lineups_ownTeamStats.groupby('Lineup',as_index=False).sum()
    
    for i in range(0,int(len(df_homeTeam_lineups_oppTeamStats))):
        lineup_string = ''
        for j in range(0,int(len(df_homeTeam_lineups_oppTeamStats.loc[i]['Lineup']))):
            lineup_string += df_homeTeam_lineups_oppTeamStats.loc[i]['Lineup'][j]
        df_homeTeam_lineups_oppTeamStats.at[i,'Lineup'] = lineup_string
        
    df_homeTeam_lineups_oppTeamStats_aggr = df_homeTeam_lineups_oppTeamStats.groupby('Lineup',as_index=False).sum()
            
    return (df_homeTeam_lineups_ownTeamStats,
            df_homeTeam_lineups_oppTeamStats,
            df_homeTeam_lineups_ownTeamStats_aggr,
            df_homeTeam_lineups_oppTeamStats_aggr)

# Input  : play-by-play dataframe (df), home team dataframe (dfHomeTeam),
#          starting five players (starting_five_awayTeam), bench players who
#          played (bench_awayTeam),  
#          list of indices reporting
#          changes in the minute of the game in the play-by-play dataframe (idxMinutes),
#          flag highlighting if idxMinutes has been calculated for all 40
#          minutes or not (all_minutes_found), path to current folder (cwd)
# Output : dataframes containing all relevant info (1p,2p,3p attemped and made),
#          defensive and offensive rebounds, assists etc, at the team level
#          (both for the own team and the opposing team) for each lineup of the away team. 
#          It is important to highlight that stats 
#          are aggregated at the team level. As example, a row corresponding
#          to a specific lineup contains all the info that its team or the
#          opposing team generated while the specific lineup was on the court     
def get_awayTeam_stats_perLineup(df,dfawayTeam,
                                 starting_five_awayTeam,bench_awayTeam,idxMinutes,all_minutes_found,cwd):
    all_players_awayTeam = starting_five_awayTeam + bench_awayTeam
    
    all_lineups_awayTeam = []
    all_lineups_awayTeam.append([sorted(starting_five_awayTeam),0])
    current_lineup = starting_five_awayTeam
    current_bench  = list(set(all_players_awayTeam) - set(current_lineup))
    perc_string_to_match = 0.8
    
    for j in range(0,int(len(df))):
        if 'sostituisce' in df.loc[j][2]:
            found_bench_player_in = 0
            for cont in range(0,int(len(current_bench))):
                if current_bench[cont][0:int(len(current_bench[cont])*perc_string_to_match)] in df.loc[j][2]:
                    new_player_onField    = current_bench[cont]
                    found_bench_player_in = 1
                    break
            found_lineup_player_out = 0
            for cont in range(0,int(len(current_lineup))):
                if current_lineup[cont][0:int(len(current_lineup[cont])*perc_string_to_match)] in df.loc[j][2]:
                    new_player_offField     = current_lineup[cont]
                    found_lineup_player_out = 1
                    break
            
            if found_bench_player_in*found_lineup_player_out == 1:
                current_lineup = list(set(current_lineup) - set([new_player_offField]))
                current_lineup = current_lineup + [new_player_onField]
                current_bench = list(set(current_bench) - set([new_player_onField]))
                current_bench = current_bench + [new_player_offField]
                
                all_lineups_awayTeam.append([sorted(current_lineup),j])
    
    idx_unique_lineups_awayTeam = []
    for i in range(0,int(len(all_lineups_awayTeam))):
        this_lineup_idx = []
        for j in range(0,int(len(all_lineups_awayTeam))):
            if all_lineups_awayTeam[j][0] == all_lineups_awayTeam[i][0]:
                this_lineup_idx.append(j)
        idx_unique_lineups_awayTeam.append(this_lineup_idx)

    
    if max(len(l) for l in idx_unique_lineups_awayTeam) > 1:
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
    # Stats for the home team different lineups (own stats)
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
                if all_minutes_found:
                    entryMin         = np.where(np.array(idxMinutes)>=startEnd_unique_lineups_awayTeam[i][j][0])[0][0]
                    exitMin          = np.where(np.array(idxMinutes)>=startEnd_unique_lineups_awayTeam[i][j][1])[0][0]
                    this_timeOnCourt = np.max([1,exitMin-entryMin])
                else:
                    this_timeOnCourt = 0
                
                if 'tiroliberosbagliato' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                    _1p_attempted += 1
                elif 'tiroliberosegnato' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                    _1p_attempted += 1
                    _1p_made += 1
                elif ('tirosbagliatodasotto' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]
                    or 'tirosbagliatodafuori' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]):
                    _2p_attempted += 1
                elif ('canestrodasotto' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]
                      or 'canestrodafuori' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]):
                    _2p_attempted += 1
                    _2p_made      += 1
                elif 'schiacciata' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                    _2p_attempted += 1
                    _2p_made      += 1
                    dunk          += 1
                elif 'tirosbagliatoda3punti' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                    _3p_attempted += 1
                elif 'canestroda3punti' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                    _3p_attempted += 1
                    _3p_made += 1
                elif 'rimbalzodifensivo' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                    def_rebound += 1
                elif 'rimbalzooffensivo' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                    off_rebound += 1
                elif 'assist' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                    assist += 1
                elif 'pallarecuperata' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                    steal += 1
                elif 'pallapersa' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                    turnover += 1
                elif 'stoppata' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                    block_made += 1 
                elif 'stoppataSubita' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                    block_received += 1 
                elif 'fallocommesso' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                    foul_made += 1     
                elif 'fallosubito' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][2]:
                    foul_received += 1 
            all_stats_awayTeam_lineups.append([all_lineups_awayTeam[idx_unique_lineups_awayTeam[i][j]][0],_1p_made,
              _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
              def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
               foul_made,foul_received,this_timeOnCourt])
    
    # Save data to dataframe and to spreadsheet
    df_awayTeam_lineups_ownTeamStats = pd.DataFrame(np.array(all_stats_awayTeam_lineups))
    df_awayTeam_lineups_ownTeamStats.columns = ['Lineup','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_awayTeam_lineups_ownTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_awayTeam_lineups_ownTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_awayTeam_lineups_ownTeamStats.to_excel(os.path.join(cwd,'awayTeam_lineups_ownTeamStats.xlsx'),
          sheet_name='Sheet_name_1') 
    
    #############################################################
    # Stats for the home team different lineups (opp. team stats)
    #############################################################
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
                
                if all_minutes_found:
                    entryMin         = np.where(np.array(idxMinutes)>=startEnd_unique_lineups_awayTeam[i][j][0])[0][0]
                    exitMin          = np.where(np.array(idxMinutes)>=startEnd_unique_lineups_awayTeam[i][j][1])[0][0]
                    this_timeOnCourt = np.max([1,exitMin-entryMin])
                else:
                    this_timeOnCourt = 0
                
                if 'tiroliberosbagliato' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                    _1p_attempted += 1
                elif 'tiroliberosegnato' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                    _1p_attempted += 1
                    _1p_made += 1
                elif ('tirosbagliatodasotto' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]
                    or 'tirosbagliatodafuori' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]):
                    _2p_attempted += 1
                elif ('canestrodasotto' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]
                      or 'canestrodafuori' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]):
                    _2p_attempted += 1
                    _2p_made      += 1
                elif 'schiacciata' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                    _2p_attempted += 1
                    _2p_made      += 1
                    dunk          += 1
                elif 'tirosbagliatoda3punti' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                    _3p_attempted += 1
                elif 'canestroda3punti' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                    _3p_attempted += 1
                    _3p_made += 1
                elif 'rimbalzodifensivo' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                    def_rebound += 1
                elif 'rimbalzooffensivo' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                    off_rebound += 1
                elif 'assist' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                    assist += 1
                elif 'pallarecuperata' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                    steal += 1
                elif 'pallapersa' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                    turnover += 1
                elif 'stoppata' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                    block_made += 1 
                elif 'stoppataSubita' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                    block_received += 1 
                elif 'fallocommesso' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                    foul_made += 1     
                elif 'fallosubito' in df.loc[startEnd_unique_lineups_awayTeam[i][j][0]+k][0]:
                    foul_received += 1 
            all_stats_awayTeam_lineups_oppTeam.append([all_lineups_awayTeam[idx_unique_lineups_awayTeam[i][j]][0],_1p_made,
              _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
              def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
               foul_made,foul_received,this_timeOnCourt])
    
    # Save data to dataframe and to spreadsheet
    df_awayTeam_lineups_oppTeamStats = pd.DataFrame(np.array(all_stats_awayTeam_lineups_oppTeam))
    df_awayTeam_lineups_oppTeamStats.columns = ['Lineup','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_awayTeam_lineups_oppTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_awayTeam_lineups_oppTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_awayTeam_lineups_oppTeamStats.to_excel(os.path.join(cwd,'awayTeam_lineups_oppTeamstats.xlsx'),
          sheet_name='Sheet_name_1')
    
    ##########################################
    ### Aggregate results for repeated lineups
    ##########################################
    
    for i in range(0,int(len(df_awayTeam_lineups_ownTeamStats))):
        lineup_string = ''
        for j in range(0,int(len(df_awayTeam_lineups_ownTeamStats.loc[i]['Lineup']))):
            lineup_string += df_awayTeam_lineups_ownTeamStats.loc[i]['Lineup'][j]
        df_awayTeam_lineups_ownTeamStats.at[i,'Lineup'] = lineup_string
        
    df_awayTeam_lineups_ownTeamStats_aggr = df_awayTeam_lineups_ownTeamStats.groupby('Lineup',as_index=False).sum()
    
    for i in range(0,int(len(df_awayTeam_lineups_oppTeamStats))):
        lineup_string = ''
        for j in range(0,int(len(df_awayTeam_lineups_oppTeamStats.loc[i]['Lineup']))):
            lineup_string += df_awayTeam_lineups_oppTeamStats.loc[i]['Lineup'][j]
        df_awayTeam_lineups_oppTeamStats.at[i,'Lineup'] = lineup_string
        
    df_awayTeam_lineups_oppTeamStats_aggr = df_awayTeam_lineups_oppTeamStats.groupby('Lineup',as_index=False).sum()
            
    return (df_awayTeam_lineups_ownTeamStats,
            df_awayTeam_lineups_oppTeamStats,
            df_awayTeam_lineups_ownTeamStats_aggr,
            df_awayTeam_lineups_oppTeamStats_aggr)

#############################################################################
# Plotting Figures and generating Figure-related dataframes for a team
#############################################################################    
# Input  : all relevant dataframes, logo of the home team, name of the
#          team, position (pos_logo=[bottom,left,width,height]) of the team logo,
#          and axis font specs 
# Output : Figures and associated dataframes    
def plot_team_statistics(df_homeTeam_lineups_ownTeamStats_aggr,
                             df_homeTeam_lineups_oppTeamStats_aggr,
                             df_homeTeam_startingPlusBench_ownTeamStats_aggr,
                             df_homeTeam_startingPlusBench_oppTeamStats_aggr,
                             cwd,
                             team_list_logos,idx_logo_homeTeam,dfHomeTeam,
                             starting_five_homeTeam,
                             bench_homeTeam,
                             orig_idx_starting_five_homeTeam,
                             orig_idx_bench_homeTeam,string_team,pos_logo,axis_font):
    
    ######################
    ### 2P% per lineup ###
    ######################
    df_2p_perc_homeTeam_lineups_ownTeamStats_aggr        = df_homeTeam_lineups_ownTeamStats_aggr[['2pm','2pa']]
    df_2p_perc_homeTeam_lineups_ownTeamStats_aggr['2pp'] = df_2p_perc_homeTeam_lineups_ownTeamStats_aggr['2pm']/df_2p_perc_homeTeam_lineups_ownTeamStats_aggr['2pa']
    df_2p_perc_homeTeam_lineups_ownTeamStats_aggr['2pp'].fillna(0, inplace=True)
    
    df_2p_perc_homeTeam_lineups_oppTeamStats_aggr        = df_homeTeam_lineups_oppTeamStats_aggr[['2pm','2pa']]
    df_2p_perc_homeTeam_lineups_oppTeamStats_aggr['2pp'] = df_2p_perc_homeTeam_lineups_oppTeamStats_aggr['2pm']/df_2p_perc_homeTeam_lineups_oppTeamStats_aggr['2pa']
    df_2p_perc_homeTeam_lineups_oppTeamStats_aggr['2pp'].fillna(0, inplace=True)
    

    pathsBasketball = []
    for i in range(0,int(len(df_2p_perc_homeTeam_lineups_ownTeamStats_aggr['2pp']))):
        pathsBasketball.append(os.path.join(cwd,'basketball.png'))
    
    fig,ax = plt.subplots()
    plt.plot(df_2p_perc_homeTeam_lineups_ownTeamStats_aggr['2pp'],
             df_2p_perc_homeTeam_lineups_oppTeamStats_aggr['2pp'],c='r',marker='>',
             markersize=1,linestyle='')
    
    def getImage(path):
        return OffsetImage(plt.imread(path),zoom=0.01)
    

    for x0, y0, path in zip(df_2p_perc_homeTeam_lineups_ownTeamStats_aggr['2pp'], 
                            df_2p_perc_homeTeam_lineups_oppTeamStats_aggr['2pp']
                            , pathsBasketball):
        ab = AnnotationBbox(getImage(path), (x0, y0), frameon=False)
        ax.add_artist(ab)

        
    ax.fill([0.5,1,1,0.5,0.5],[0,0,0.5,0.5,0],facecolor='lightsalmon',edgecolor='orangered',alpha=0.2,linewidth=3)
    ax.fill([0,0.5,0.5,0,0],[0.5,0.5,1,1,0.5],facecolor='lightsalmon',edgecolor='orangered',alpha=0.2,linewidth=3)
  
    offset_lb = -0.05
    offset_ub = 0.05
    
    for i in range(0,int(len(df_2p_perc_homeTeam_lineups_ownTeamStats_aggr))):
        if (df_2p_perc_homeTeam_lineups_oppTeamStats_aggr['2pp'][i] != 0 or
            df_2p_perc_homeTeam_lineups_oppTeamStats_aggr['2pp'][i] != 0):
            plt.text(offset_lb + (offset_ub-offset_lb)*random.random() + df_2p_perc_homeTeam_lineups_ownTeamStats_aggr['2pp'][i],
                     offset_lb + (offset_ub-offset_lb)*random.random() +df_2p_perc_homeTeam_lineups_oppTeamStats_aggr['2pp'][i],str(i+1),
                     fontsize=15,zorder=100)

    ax.set_xlabel('Team 2p%',**axis_font)
    ax.set_ylabel('Opposing team 2P%',**axis_font)
    ax.set_title('Team 2P% per lineup',**axis_font)
    
    im = plt.imread(get_sample_data(os.path.join(cwd,'team_logos',team_list_logos[idx_logo_homeTeam])))
    newax = fig.add_axes(pos_logo, anchor='E', zorder=3)
    newax.imshow(im)
    newax.axis('off')
    
    ax.grid(True)
    plt.show()
    plt.savefig(os.path.join(cwd,'2p_perLineup_'+string_team+'.png'),dpi=500,bbox_inches='tight', 
                   transparent=True,
                   pad_inches=0.1)
    
    ######################
    ### 2P% per player ###
    ######################
    df_2p_perc_homeTeam_player_ownTeamStats_aggr        = df_homeTeam_startingPlusBench_ownTeamStats_aggr[['2pm','2pa']]
    df_2p_perc_homeTeam_player_ownTeamStats_aggr['2pp'] = (df_homeTeam_startingPlusBench_ownTeamStats_aggr['2pm']
                                              /df_homeTeam_startingPlusBench_ownTeamStats_aggr['2pa'])
    df_2p_perc_homeTeam_player_ownTeamStats_aggr['2pp'].fillna(0, inplace=True)
    
    df_2p_perc_homeTeam_player_oppTeamStats_aggr        = df_homeTeam_startingPlusBench_oppTeamStats_aggr[['2pm','2pa']]
    df_2p_perc_homeTeam_player_oppTeamStats_aggr['2pp'] = (df_homeTeam_startingPlusBench_oppTeamStats_aggr['2pm']
                                                      /df_homeTeam_startingPlusBench_oppTeamStats_aggr['2pa'])
    df_2p_perc_homeTeam_player_oppTeamStats_aggr['2pp'].fillna(0, inplace=True)
    
    orig_idx_homeTeam      = orig_idx_starting_five_homeTeam+orig_idx_bench_homeTeam
    names_homeTeam         = starting_five_homeTeam + bench_homeTeam 
    
    idx_names_homeTeam_srt = sorted(range(len(names_homeTeam)), key=lambda k: names_homeTeam[k], reverse=False)
    orig_idx_homeTeam_srt  = []
    for i in range(0,int(len(idx_names_homeTeam_srt))):
        orig_idx_homeTeam_srt.append(orig_idx_homeTeam[idx_names_homeTeam_srt[i]])

    
    fig,ax = plt.subplots()
    plt.plot(df_2p_perc_homeTeam_player_ownTeamStats_aggr['2pp'],
             df_2p_perc_homeTeam_player_oppTeamStats_aggr['2pp'],c='r',marker='>',
             markersize=6,linestyle='')
    for x0, y0, path in zip(df_2p_perc_homeTeam_player_ownTeamStats_aggr['2pp'], 
                            df_2p_perc_homeTeam_player_oppTeamStats_aggr['2pp']
                            , pathsBasketball):
        ab = AnnotationBbox(getImage(path), (x0, y0), frameon=False)
        ax.add_artist(ab)
    
    ax.fill([0.5,1,1,0.5,0.5],[0,0,0.5,0.5,0],facecolor='lightsalmon',edgecolor='orangered',alpha=0.2,linewidth=3)
    ax.fill([0,0.5,0.5,0,0],[0.5,0.5,1,1,0.5],facecolor='lightsalmon',edgecolor='orangered',alpha=0.2,linewidth=3)
  
    
    for i in range(0,int(len(df_2p_perc_homeTeam_player_ownTeamStats_aggr))):
        if (df_2p_perc_homeTeam_player_ownTeamStats_aggr['2pp'][i] != 0 or
            df_2p_perc_homeTeam_player_oppTeamStats_aggr['2pp'][i] != 0):
            plt.text(df_2p_perc_homeTeam_player_ownTeamStats_aggr['2pp'][i],
                 df_2p_perc_homeTeam_player_oppTeamStats_aggr['2pp'][i],
                 dfHomeTeam[2][orig_idx_homeTeam_srt[i]],
                 fontsize=10,fontname='Arial',zorder=100)
    
    ax.set_xlabel('Team 2P%',**axis_font)
    ax.set_ylabel('Opposing team 2P%',**axis_font)
    ax.set_title('Team 2P% per player',**axis_font)
    
    im = plt.imread(get_sample_data(os.path.join(cwd,'team_logos',team_list_logos[idx_logo_homeTeam])))
    newax = fig.add_axes(pos_logo, anchor='E', zorder=3)
    newax.imshow(im)
    newax.axis('off')
    
    ax.grid(True)
    plt.show()
    plt.savefig(os.path.join(cwd,'2p_perPlayer_'+string_team+'.png'),dpi=500,bbox_inches='tight', 
                   transparent=True,
                   pad_inches=0.1)

    ######################
    ### FG% per lineup ###
    ######################
    df_fg_perc_homeTeam_lineup_ownTeamStats_aggr        = df_homeTeam_lineups_ownTeamStats_aggr[['2pm','2pa','3pm','3pa']]
    df_fg_perc_homeTeam_lineup_ownTeamStats_aggr['fgp'] = ((df_fg_perc_homeTeam_lineup_ownTeamStats_aggr['2pm']+df_fg_perc_homeTeam_lineup_ownTeamStats_aggr['3pm'])
                                              /(df_fg_perc_homeTeam_lineup_ownTeamStats_aggr['2pa']+df_fg_perc_homeTeam_lineup_ownTeamStats_aggr['3pa']))
    df_fg_perc_homeTeam_lineup_ownTeamStats_aggr['fgp'].fillna(0, inplace=True)
    df_fg_perc_homeTeam_lineup_ownTeamStats_aggr['fgp'].replace(np.inf,4,inplace=True)
    
    df_fg_perc_homeTeam_lineup_oppTeamStats_aggr        = df_homeTeam_lineups_oppTeamStats_aggr[['2pm','2pa','3pm','3pa']]
    df_fg_perc_homeTeam_lineup_oppTeamStats_aggr['fgp'] = ((df_fg_perc_homeTeam_lineup_oppTeamStats_aggr['2pm']+df_fg_perc_homeTeam_lineup_oppTeamStats_aggr['3pm'])
                                              /(df_fg_perc_homeTeam_lineup_oppTeamStats_aggr['2pa']+df_fg_perc_homeTeam_lineup_oppTeamStats_aggr['3pa']))
    df_fg_perc_homeTeam_lineup_oppTeamStats_aggr['fgp'].fillna(0, inplace=True)
    df_fg_perc_homeTeam_lineup_oppTeamStats_aggr['fgp'].replace(np.inf,4,inplace=True)
    
    fig,ax = plt.subplots()
    plt.plot(df_fg_perc_homeTeam_lineup_ownTeamStats_aggr['fgp'],
             df_fg_perc_homeTeam_lineup_oppTeamStats_aggr['fgp'],c='r',marker='>',
             markersize=6,linestyle='')
    for x0, y0, path in zip(df_fg_perc_homeTeam_lineup_ownTeamStats_aggr['fgp'], 
                            df_fg_perc_homeTeam_lineup_oppTeamStats_aggr['fgp']
                            , pathsBasketball):
        ab = AnnotationBbox(getImage(path), (x0, y0), frameon=False)
        ax.add_artist(ab)
    
    ax.fill([0.5,1,1,0.5,0.5],[0,0,0.5,0.5,0],facecolor='lightsalmon',edgecolor='orangered',alpha=0.2,linewidth=3)
    ax.fill([0,0.5,0.5,0,0],[0.5,0.5,1,1,0.5],facecolor='lightsalmon',edgecolor='orangered',alpha=0.2,linewidth=3)
  
    
    for i in range(0,int(len(df_fg_perc_homeTeam_lineup_ownTeamStats_aggr))):
        if (df_fg_perc_homeTeam_lineup_ownTeamStats_aggr['fgp'][i] != 0 or
            df_fg_perc_homeTeam_lineup_oppTeamStats_aggr['fgp'][i] != 0):
            plt.text(offset_lb + (offset_ub-offset_lb)*random.random() + df_fg_perc_homeTeam_lineup_ownTeamStats_aggr['fgp'][i],
                     offset_lb + (offset_ub-offset_lb)*random.random() +df_fg_perc_homeTeam_lineup_oppTeamStats_aggr['fgp'][i],str(i+1),
                     fontsize=15,zorder=100)

    ax.set_xlabel('Team FG%',**axis_font)
    ax.set_ylabel('Opposing team FG%',**axis_font)
    ax.set_title('Team FG% per lineup',**axis_font)
    ax.grid(True)
    
    im = plt.imread(get_sample_data(os.path.join(cwd,'team_logos',team_list_logos[idx_logo_homeTeam])))
    newax = fig.add_axes(pos_logo, anchor='E', zorder=3)
    newax.imshow(im)
    newax.axis('off')
    
    plt.show()
    plt.savefig(os.path.join(cwd,'fgp_perLineup_'+string_team+'.png'),dpi=500,bbox_inches='tight', 
                   transparent=True,
                   pad_inches=0.1)    

    
    
    ######################
    ### FG% per player ###
    ######################
    df_fg_perc_homeTeam_player_ownTeamStats_aggr        = df_homeTeam_startingPlusBench_ownTeamStats_aggr[['2pm','2pa','3pm','3pa']]
    df_fg_perc_homeTeam_player_ownTeamStats_aggr['fgp'] = ((df_fg_perc_homeTeam_player_ownTeamStats_aggr['2pm']+df_fg_perc_homeTeam_player_ownTeamStats_aggr['3pm'])
                                              /(df_fg_perc_homeTeam_player_ownTeamStats_aggr['2pa']+df_fg_perc_homeTeam_player_ownTeamStats_aggr['3pa']))
    df_fg_perc_homeTeam_player_ownTeamStats_aggr['fgp'].fillna(0, inplace=True)
    df_fg_perc_homeTeam_player_ownTeamStats_aggr['fgp'].replace(np.inf,4,inplace=True)
    
    df_fg_perc_homeTeam_player_oppTeamStats_aggr        = df_homeTeam_startingPlusBench_oppTeamStats_aggr[['2pm','2pa','3pm','3pa']]
    df_fg_perc_homeTeam_player_oppTeamStats_aggr['fgp'] = ((df_fg_perc_homeTeam_player_oppTeamStats_aggr['2pm']+df_fg_perc_homeTeam_player_oppTeamStats_aggr['3pm'])
                                              /(df_fg_perc_homeTeam_player_oppTeamStats_aggr['2pa']+df_fg_perc_homeTeam_player_oppTeamStats_aggr['3pa']))
    df_fg_perc_homeTeam_lineup_oppTeamStats_aggr['fgp'].fillna(0, inplace=True)
    df_fg_perc_homeTeam_player_oppTeamStats_aggr['fgp'].replace(np.inf,4,inplace=True)
    
    fig,ax = plt.subplots()
    plt.plot(df_fg_perc_homeTeam_player_ownTeamStats_aggr['fgp'],
             df_fg_perc_homeTeam_player_oppTeamStats_aggr['fgp'],c='r',marker='>',
             markersize=6,linestyle='')
    for x0, y0, path in zip(df_fg_perc_homeTeam_player_ownTeamStats_aggr['fgp'], 
                            df_fg_perc_homeTeam_player_oppTeamStats_aggr['fgp']
                            , pathsBasketball):
        ab = AnnotationBbox(getImage(path), (x0, y0), frameon=False)
        ax.add_artist(ab)
    
    ax.fill([0.5,1,1,0.5,0.5],[0,0,0.5,0.5,0],facecolor='lightsalmon',edgecolor='orangered',alpha=0.2,linewidth=3)
    ax.fill([0,0.5,0.5,0,0],[0.5,0.5,1,1,0.5],facecolor='lightsalmon',edgecolor='orangered',alpha=0.2,linewidth=3)
  
    
    for i in range(0,int(len(df_fg_perc_homeTeam_player_ownTeamStats_aggr))):
        if (df_fg_perc_homeTeam_player_ownTeamStats_aggr['fgp'][i] != 0 or
            df_fg_perc_homeTeam_player_oppTeamStats_aggr['fgp'][i] != 0):
            plt.text(df_fg_perc_homeTeam_player_ownTeamStats_aggr['fgp'][i],
                 df_fg_perc_homeTeam_player_oppTeamStats_aggr['fgp'][i],
                 dfHomeTeam[2][orig_idx_homeTeam_srt[i]],
                 fontsize=10,fontname='Arial',zorder=100)
    
    ax.set_xlabel('Team FG%',**axis_font)
    ax.set_ylabel('Opposing team FG%',**axis_font)
    ax.set_title('Team FG% per player',**axis_font)
    ax.grid(True)
    
    im = plt.imread(get_sample_data(os.path.join(cwd,'team_logos',team_list_logos[idx_logo_homeTeam])))
    newax = fig.add_axes(pos_logo, anchor='E', zorder=3)
    newax.imshow(im)
    newax.axis('off')
    
    plt.show()
    plt.savefig(os.path.join(cwd,'fgp_perPlayer_'+string_team+'.png'),dpi=500,
                   transparent=True)

    #####################################################
    ### Offensive and defensive efficiency per lineup ###
    #####################################################
    homeTeam_offDef_efficiency_perLineup         = []
    for i in range(0,int(len(df_homeTeam_lineups_ownTeamStats_aggr))):
        points_homeTeam = (df_homeTeam_lineups_ownTeamStats_aggr['1pm'][i]+
                       2.0*df_homeTeam_lineups_ownTeamStats_aggr['2pm'][i]+
                       3.0*df_homeTeam_lineups_ownTeamStats_aggr['3pm'][i])
        points_oppTeam = (df_homeTeam_lineups_oppTeamStats_aggr['1pm'][i]+
                       2.0*df_homeTeam_lineups_oppTeamStats_aggr['2pm'][i]+
                       3.0*df_homeTeam_lineups_oppTeamStats_aggr['3pm'][i])
        possessions = (df_homeTeam_lineups_ownTeamStats_aggr['2pa'][i]+
                       df_homeTeam_lineups_ownTeamStats_aggr['3pa'][i]-
                       df_homeTeam_lineups_ownTeamStats_aggr['oreb'][i]+
                       df_homeTeam_lineups_ownTeamStats_aggr['to'][i]+
                       df_homeTeam_lineups_ownTeamStats_aggr['1pa'][i])
        possessions_oppTeam = (df_homeTeam_lineups_oppTeamStats_aggr['2pa'][i]+
                       df_homeTeam_lineups_oppTeamStats_aggr['3pa'][i]-
                       df_homeTeam_lineups_oppTeamStats_aggr['oreb'][i]+
                       df_homeTeam_lineups_oppTeamStats_aggr['to'][i]+
                       df_homeTeam_lineups_oppTeamStats_aggr['1pa'][i])
        
        if possessions > 0:
            this_lineup_offEff = points_homeTeam/possessions*100.0
        else:
            this_lineup_offEff = 0
        if possessions_oppTeam > 0:
            this_lineup_defEff = points_oppTeam/possessions_oppTeam*100.0
        else:
            this_lineup_defEff = 0
        
        homeTeam_offDef_efficiency_perLineup.append([df_homeTeam_lineups_ownTeamStats_aggr['Lineup'][i],
                                       this_lineup_offEff,this_lineup_defEff])
            
    df_homeTeam_offDef_efficiency_perLineup = pd.DataFrame(np.array(homeTeam_offDef_efficiency_perLineup))
    df_homeTeam_offDef_efficiency_perLineup.columns = ['Lineup','offEff','defEff']
    df_homeTeam_offDef_efficiency_perLineup['offEff'].fillna(0, inplace=True)
    df_homeTeam_offDef_efficiency_perLineup['defEff'].fillna(0, inplace=True)
    df_homeTeam_offDef_efficiency_perLineup[['offEff','defEff']]=(
            df_homeTeam_offDef_efficiency_perLineup[['offEff','defEff']].apply(pd.to_numeric,errors='coerce'))
    
    df_homeTeam_offDef_efficiency_perLineup        = pd.DataFrame(np.array(homeTeam_offDef_efficiency_perLineup))
    df_homeTeam_offDef_efficiency_perLineup.columns = ['Player','offEff','defEff']
    df_homeTeam_offDef_efficiency_perLineup['offEff'].fillna(0, inplace=True)
    df_homeTeam_offDef_efficiency_perLineup['defEff'].fillna(0, inplace=True)
    df_homeTeam_offDef_efficiency_perLineup[['offEff','defEff']]=(
            df_homeTeam_offDef_efficiency_perLineup[['offEff','defEff']].apply(pd.to_numeric,errors='coerce'))
    
    pathsBasketball = []
    for i in range(0,int(len(df_homeTeam_offDef_efficiency_perLineup))):
        pathsBasketball.append('basketball.png')
    
    fig,ax = plt.subplots()
    plt.plot(df_homeTeam_offDef_efficiency_perLineup['offEff'],
             df_homeTeam_offDef_efficiency_perLineup['defEff'],c='r',marker='d',
             markersize=6,linestyle='')
    
    for x0, y0, path in zip(df_homeTeam_offDef_efficiency_perLineup['offEff'], 
                            df_homeTeam_offDef_efficiency_perLineup['defEff']
                            , pathsBasketball):
        ab = AnnotationBbox(getImage(path), (x0, y0), frameon=False)
        ax.add_artist(ab)
    
    offset_lb = -5
    offset_ub = 5
    
    for i in range(0,int(len(df_homeTeam_offDef_efficiency_perLineup))):
        if (df_homeTeam_offDef_efficiency_perLineup['offEff'][i] != 0 or
            df_homeTeam_offDef_efficiency_perLineup['defEff'][i] != 0):
            plt.text(offset_lb + (offset_ub-offset_lb)*random.random() + df_homeTeam_offDef_efficiency_perLineup['offEff'][i],
                     offset_lb + (offset_ub-offset_lb)*random.random() +df_homeTeam_offDef_efficiency_perLineup['defEff'][i],str(i+1),
                     fontsize=15,zorder=100)
    
    
    if np.max(df_homeTeam_offDef_efficiency_perLineup['offEff'])>100 and np.min(df_homeTeam_offDef_efficiency_perLineup['defEff'])<100:
        ax.fill([100,np.max(df_homeTeam_offDef_efficiency_perLineup['offEff']),np.max(df_homeTeam_offDef_efficiency_perLineup['offEff']),100,100],
                 [np.min(df_homeTeam_offDef_efficiency_perLineup['defEff']),np.min(df_homeTeam_offDef_efficiency_perLineup['defEff']),
                 100,100,np.min(df_homeTeam_offDef_efficiency_perLineup['defEff'])],facecolor='lightsalmon',edgecolor='orangered',alpha=0.2,linewidth=3)

    ax.set_xlabel('Team Offensive Efficiency',**axis_font)
    ax.set_ylabel('Team Defensive Efficiency',**axis_font)
    ax.set_title('Team Offensive/Defensive Efficiency',**axis_font)
    
    
    im = plt.imread(get_sample_data(os.path.join(cwd,'team_logos',team_list_logos[idx_logo_homeTeam])))
    newax = fig.add_axes(pos_logo, anchor='E', zorder=3)
    newax.imshow(im)
    newax.axis('off')
    
    ax.grid(True)
    plt.show()
    plt.savefig(os.path.join(cwd,'offDef_eff_perLineup'+string_team+'.png'),dpi=500,bbox_inches='tight', 
                   transparent=True,
                   pad_inches=0.1)
    
    #####################################################
    ### Offensive and defensive efficiency per player ###
    #####################################################
    homeTeam_offDef_efficiency_perPlayer = []
    for i in range(0,int(len(df_homeTeam_startingPlusBench_ownTeamStats_aggr))):
        points_homeTeam = (df_homeTeam_startingPlusBench_ownTeamStats_aggr['1pm'][i]+
                       2.0*df_homeTeam_startingPlusBench_ownTeamStats_aggr['2pm'][i]+
                       3.0*df_homeTeam_startingPlusBench_ownTeamStats_aggr['3pm'][i])
        points_oppTeam = (df_homeTeam_startingPlusBench_oppTeamStats_aggr['1pm'][i]+
                       2.0*df_homeTeam_startingPlusBench_oppTeamStats_aggr['2pm'][i]+
                       3.0*df_homeTeam_startingPlusBench_oppTeamStats_aggr['3pm'][i])
        possessions = (df_homeTeam_startingPlusBench_ownTeamStats_aggr['2pa'][i]+
                       df_homeTeam_startingPlusBench_ownTeamStats_aggr['3pa'][i]-
                       df_homeTeam_startingPlusBench_ownTeamStats_aggr['oreb'][i]+
                       df_homeTeam_startingPlusBench_ownTeamStats_aggr['to'][i]+
                       0.4*df_homeTeam_startingPlusBench_ownTeamStats_aggr['1pa'][i])
        possessions_oppTeam = (df_homeTeam_startingPlusBench_oppTeamStats_aggr['2pa'][i]+
                       df_homeTeam_startingPlusBench_oppTeamStats_aggr['3pa'][i]-
                       df_homeTeam_startingPlusBench_oppTeamStats_aggr['oreb'][i]+
                       df_homeTeam_startingPlusBench_oppTeamStats_aggr['to'][i]+
                       0.4*df_homeTeam_startingPlusBench_oppTeamStats_aggr['1pa'][i])
        if possessions > 0:
            this_player_offEff = points_homeTeam/possessions*100.0
        else:
            this_player_offEff = 0
        if possessions_oppTeam > 0:
            this_player_defEff = points_oppTeam/possessions_oppTeam*100.0
        else:
            this_player_defEff = 0
        
        homeTeam_offDef_efficiency_perPlayer.append([df_homeTeam_startingPlusBench_ownTeamStats_aggr['Player'][i],
                                       this_player_offEff,this_player_defEff])
    
    
    df_homeTeam_offDef_efficiency_perPlayer         = pd.DataFrame(np.array(homeTeam_offDef_efficiency_perPlayer))
    df_homeTeam_offDef_efficiency_perPlayer.columns = ['Player','offEff','defEff']
    df_homeTeam_offDef_efficiency_perPlayer['offEff'].fillna(0, inplace=True)
    df_homeTeam_offDef_efficiency_perPlayer['defEff'].fillna(0, inplace=True)
    df_homeTeam_offDef_efficiency_perPlayer[['offEff','defEff']]=(
            df_homeTeam_offDef_efficiency_perPlayer[['offEff','defEff']].apply(pd.to_numeric,errors='coerce'))
    
    pathsBasketball = []
    for i in range(0,int(len(df_homeTeam_offDef_efficiency_perPlayer))):
        pathsBasketball.append('basketball.png')
    
    fig,ax = plt.subplots()
    plt.plot(df_homeTeam_offDef_efficiency_perPlayer['offEff'],
             df_homeTeam_offDef_efficiency_perPlayer['defEff'],c='r',marker='d',
             markersize=6,linestyle='')
    
    for x0, y0, path in zip(df_homeTeam_offDef_efficiency_perPlayer['offEff'], 
                            df_homeTeam_offDef_efficiency_perPlayer['defEff']
                            , pathsBasketball):
        ab = AnnotationBbox(getImage(path), (x0, y0), frameon=False)
        ax.add_artist(ab)
    
    for i in range(0,int(len(df_homeTeam_offDef_efficiency_perPlayer))):
        if (df_homeTeam_offDef_efficiency_perPlayer['offEff'][i] != 0 or
            df_homeTeam_offDef_efficiency_perPlayer['defEff'][i] != 0):
            plt.text(df_homeTeam_offDef_efficiency_perPlayer['offEff'][i],
                 df_homeTeam_offDef_efficiency_perPlayer['defEff'][i],
                 dfHomeTeam[2][orig_idx_homeTeam_srt[i]],
                 fontsize=10,fontname='Arial',zorder=100)
    
    if np.max(df_homeTeam_offDef_efficiency_perPlayer['offEff'])>100 and np.min(df_homeTeam_offDef_efficiency_perPlayer['defEff'])<100:
        ax.fill([100,np.max(df_homeTeam_offDef_efficiency_perPlayer['offEff']),np.max(df_homeTeam_offDef_efficiency_perPlayer['offEff']),100,100],
                 [np.min(df_homeTeam_offDef_efficiency_perPlayer['defEff']),np.min(df_homeTeam_offDef_efficiency_perPlayer['defEff']),
                 100,100,np.min(df_homeTeam_offDef_efficiency_perPlayer['defEff'])],facecolor='lightsalmon',edgecolor='orangered',alpha=0.2,linewidth=3)
    
    
    ax.set_xlabel('Team Offensive Efficiency',**axis_font)
    ax.set_ylabel('Team Defensive Efficiency',**axis_font)
    ax.set_title('Team Offensive/Defensive Efficiency',**axis_font)
    
    im = plt.imread(get_sample_data(os.path.join(cwd,'team_logos',team_list_logos[idx_logo_homeTeam])))
    newax = fig.add_axes(pos_logo, anchor='E', zorder=3)
    newax.imshow(im)
    newax.axis('off')
    
    ax.grid(True)
    plt.show()
    plt.savefig(os.path.join(cwd,'offDef_eff_perPlayer'+string_team+'.png'),dpi=500,bbox_inches='tight', 
                   transparent=True,
                   pad_inches=0.1)
    
    
    return (df_2p_perc_homeTeam_lineups_ownTeamStats_aggr,
            df_2p_perc_homeTeam_lineups_oppTeamStats_aggr,
            df_2p_perc_homeTeam_player_ownTeamStats_aggr,
            df_2p_perc_homeTeam_player_oppTeamStats_aggr,
            df_fg_perc_homeTeam_lineup_ownTeamStats_aggr,
            df_fg_perc_homeTeam_lineup_oppTeamStats_aggr,
            df_fg_perc_homeTeam_player_ownTeamStats_aggr,
            df_fg_perc_homeTeam_player_oppTeamStats_aggr,
            df_homeTeam_offDef_efficiency_perLineup,
            df_homeTeam_offDef_efficiency_perPlayer)
            
    
        

