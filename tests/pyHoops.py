#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 13 15:45:18 2019

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
from copy import deepcopy

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


def web_parse_playbyplay(thisUrl): 

    p    = requests.get(thisUrl)
    
    if p.status_code < 400:
        soup   = BeautifulSoup(p.text,'html.parser')
    
        home_actions = []        
        for div in soup.findAll('div',attrs={'class':'action-comment home'}):
            home_actions.append(div.text.lower())
            
        home_score = []        
        for div in soup.findAll('div',attrs={'class':'scores home'}):
            home_score.append(div.text)
            
        away_actions = []        
        for div in soup.findAll('div',attrs={'class':'action-comment visitor'}):
            away_actions.append(div.text.lower())
            
        away_score = []        
        for div in soup.findAll('div',attrs={'class':'scores visitor'}):
            away_score.append(div.text)
            
        time_of_game = []
        for span in soup.findAll('span',attrs={'class':'time orange'}):
            time_of_game.append(span.text)
            
        quarter_of_game = []
        for span in soup.findAll('span',attrs={'class':'quarter'}):
            quarter_of_game.append(span.text.lower())
            
        pbp_matrix = []
        for i in range(0,int(len(home_actions))):
            this_row = [home_actions[i],home_score[i],time_of_game[i],quarter_of_game[i],
                        away_score[i],away_actions[i]]
            pbp_matrix.append(this_row)
            
        df_pbp = pd.DataFrame(np.array(pbp_matrix),columns=['Home_action',
                              'Home_score','time_of_game','quarter_of_game',
                              'Away_score','Away_action',])
            
        for i in range(0,int(len(df_pbp))):
            for j in range(0,int(len(df_pbp.loc[i]))):
                s                  = df_pbp.loc[i][j]
                s_mod              = ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))
                s_mod_noAp         = s_mod.replace('\'','')
                s_mod_noTrailWhite = s_mod_noAp.replace('\n','')
                s_mod_noSpace      = s_mod_noTrailWhite.replace(' ','')
                df_pbp.loc[i][j]   = s_mod_noSpace
        
        df_pbp.to_excel('play_by_play.xlsx',sheet_name='Sheet_name_1')
        
    else:
        
        df_pbp = []
        print('Play by play not loaded correctly!')    
        
    return df_pbp

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
        
    else:
        dfHomeTeam = []
        dfAwayTeam = []
        print('Boxscores not loaded correctly!')  
        
    return dfHomeTeam, dfAwayTeam


def get_homeTeam_stats_perPlayer(df_pbp,dfHomeTeam,minutes_in_quarter,cwd):
                                                

    # Get info for home team (all players: starting five and bench)
    homeTeam_allPlayers_jerseyNumber   = []
    homeTeam_allPlayers_names          = []
    homeTeam_allPlayers_allNames       = []
    homeTeam_allPlayers_info           = []
    homeTeam_startingFive_jerseyNumber = []
    homeTeam_startingFive_names        = []
    homeTeam_startingFive_info         = []
    homeTeam_bench_jerseyNumber        = []
    homeTeam_bench_names               = []
    homeTeam_bench_info                = []
    

    orig_idx_starting_five_homeTeam = []
    orig_idx_bench_homeTeam         = []
    for i in range(0,int(len(dfHomeTeam))):
        # Row is associated with a jersey number
        if dfHomeTeam.loc[i][1]:
            
            # Clean the full name of the player by getting rid of special
            # characters, spaces, etc
            # We use this approach to have more uniformity in the text and avoid
            # potential mismatches caused by weird/special characters such as accents
            s             = dfHomeTeam.loc[i][2]
            ccc           = ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))
            ccc           = ccc.replace(u'\xa0', u' ')
            ccc           = ccc.replace('\'','')
            s_mod_noSpace = ccc.replace(' ','')
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
                
            if dfHomeTeam.loc[i][0] == '*':
                homeTeam_startingFive_jerseyNumber.append(str(dfHomeTeam.loc[i][1]))
                homeTeam_startingFive_names.append(s_mod_noSpace)
                homeTeam_startingFive_info.append([s_mod_noSpace,all_combinations])
                orig_idx_starting_five_homeTeam.append(i)
            else:
                homeTeam_bench_jerseyNumber.append(str(dfHomeTeam.loc[i][1]))
                homeTeam_bench_names.append(s_mod_noSpace)
                homeTeam_bench_info.append([s_mod_noSpace,all_combinations])
                orig_idx_bench_homeTeam.append(i)
                
            homeTeam_allPlayers_jerseyNumber.append(str(dfHomeTeam.loc[i][1]))
            homeTeam_allPlayers_names.append(s_mod_noSpace)
            homeTeam_allPlayers_info.append([s_mod_noSpace,all_combinations])
            homeTeam_allPlayers_allNames.append(all_combinations)
    

    
    # Check when the starting five of the home team is on/off the court
    in_out_startingFive_homeTeam = []
    for i in range(0,int(len(homeTeam_startingFive_jerseyNumber))):
        all_names                = deepcopy(homeTeam_allPlayers_allNames)
        this_player_jerseyNumber = homeTeam_startingFive_jerseyNumber[i]
        this_player_idx          = homeTeam_allPlayers_jerseyNumber.index(this_player_jerseyNumber)
        all_names.pop(this_player_idx)
        flat_list_all_names = [item for sublist in all_names for item in sublist]
        thisPlayerOnOff = [['t1','10:00',0,'in']]
        for j in range(0,int(len(df_pbp['Home_action']))):
            if any(k in df_pbp['Home_action'][j] for k in homeTeam_startingFive_info[i][1]) and any(k in df_pbp['Home_action'][j] for k in flat_list_all_names):
                if np.mod(int(len(thisPlayerOnOff)),2) == 0:
                    in_or_out = 'in'
                    thisPlayerOnOff.append([df_pbp['quarter_of_game'][j],df_pbp['time_of_game'][j],j,in_or_out])
                else:
                    in_or_out = 'out'
                    thisPlayerOnOff.append([df_pbp['quarter_of_game'][j],df_pbp['time_of_game'][j],j+1,in_or_out])
        in_out_startingFive_homeTeam.append(thisPlayerOnOff)
        
    # Compute overall time on court for starting five of home team
    timeOnCourt_startingFive_homeTeam = []
    for i in range(0,int(len(homeTeam_startingFive_jerseyNumber))):
        this_player_in_out = in_out_startingFive_homeTeam[i]
        this_timeOnCourt   = 0
        # Player ends game on the bench because the sequence is In-Out-In-Out- ...  -In-Out (even number overall)
        if np.mod(int(len(this_player_in_out)),2) == 0:
            for j in range(0,int(len(in_out_startingFive_homeTeam[i])/2)):
                in_quarter  = int(in_out_startingFive_homeTeam[i][2*j][0][1])
                out_quarter = int(in_out_startingFive_homeTeam[i][2*j+1][0][1])
                in_time     = (in_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(in_out_startingFive_homeTeam[i][2*j][1][0:2])*60+
                                                                   int(in_out_startingFive_homeTeam[i][2*j][1][3:5])))
                out_time    = (out_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(in_out_startingFive_homeTeam[i][2*j+1][1][0:2])*60+
                                                                   int(in_out_startingFive_homeTeam[i][2*j+1][1][3:5]))) 
                this_timeOnCourt += out_time - in_time
        # Player ends game on the floor because the sequence is In-Out-In-Out- ...  -In-Out-In (odd number overall)
        else:
            for j in range(0,int((len(in_out_startingFive_homeTeam[i])-1)/2)):
                in_quarter  = int(in_out_startingFive_homeTeam[i][2*j][0][1])
                out_quarter = int(in_out_startingFive_homeTeam[i][2*j+1][0][1])
                in_time     = (in_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(in_out_startingFive_homeTeam[i][2*j][1][0:2])*60+
                                                                   int(in_out_startingFive_homeTeam[i][2*j][1][3:5])))
                out_time    = (out_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(in_out_startingFive_homeTeam[i][2*j+1][1][0:2])*60+
                                                                   int(in_out_startingFive_homeTeam[i][2*j+1][1][3:5]))) 
                this_timeOnCourt += out_time - in_time
            in_quarter        = int(in_out_startingFive_homeTeam[i][-1][0][1])
            out_quarter       = 4
            in_time           = (in_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(in_out_startingFive_homeTeam[i][-1][1][0:2])*60+int(in_out_startingFive_homeTeam[i][-1][1][3:5])))
            out_time          = (out_quarter-1)*minutes_in_quarter*60 + minutes_in_quarter*60
            this_timeOnCourt += out_time - in_time
            
        
                
        timeOnCourt_startingFive_homeTeam.append(this_timeOnCourt)
    
    
    # Check when the bench of the home team is on/off the court
    in_out_bench_homeTeam = []
    for i in range(0,int(len(homeTeam_bench_jerseyNumber))):
        all_names                = deepcopy(homeTeam_allPlayers_allNames)
        this_player_jerseyNumber = homeTeam_bench_jerseyNumber[i]
        this_player_idx          = homeTeam_allPlayers_jerseyNumber.index(this_player_jerseyNumber)
        all_names.pop(this_player_idx)
        flat_list_all_names = [item for sublist in all_names for item in sublist]
        thisPlayerOnOff = []
        for j in range(0,int(len(df_pbp['Home_action']))):
            if any(k in df_pbp['Home_action'][j] for k in homeTeam_bench_info[i][1]) and any(k in df_pbp['Home_action'][j] for k in flat_list_all_names):
                if np.mod(int(len(thisPlayerOnOff)),2) == 0:
                    in_or_out = 'in'
                    thisPlayerOnOff.append([df_pbp['quarter_of_game'][j],df_pbp['time_of_game'][j],j,in_or_out])
                else:
                    in_or_out = 'out'
                    thisPlayerOnOff.append([df_pbp['quarter_of_game'][j],df_pbp['time_of_game'][j],j+1,in_or_out])
        in_out_bench_homeTeam.append(thisPlayerOnOff)
    
    # Compute overall time on court for bench of home team
    timeOnCourt_bench_homeTeam = []
    for i in range(0,int(len(homeTeam_bench_jerseyNumber))):
        this_player_in_out = in_out_bench_homeTeam[i]
        this_timeOnCourt   = 0
        # Player ends game on the bench (same idea as explained above)
        if np.mod(int(len(this_player_in_out)),2) == 0:
            for j in range(0,int(len(in_out_bench_homeTeam[i])/2)):
                in_quarter  = int(in_out_bench_homeTeam[i][2*j][0][1])
                out_quarter = int(in_out_bench_homeTeam[i][2*j+1][0][1])
                in_time     = (in_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(in_out_bench_homeTeam[i][2*j][1][0:2])*60+
                                                                   int(in_out_bench_homeTeam[i][2*j][1][3:5])))
                out_time    = (out_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(in_out_bench_homeTeam[i][2*j+1][1][0:2])*60+
                                                                   int(in_out_bench_homeTeam[i][2*j+1][1][3:5]))) 
                this_timeOnCourt += out_time - in_time
        else:
            for j in range(0,int((len(in_out_bench_homeTeam[i])-1)/2)):
                in_quarter  = int(in_out_bench_homeTeam[i][2*j][0][1])
                out_quarter = int(in_out_bench_homeTeam[i][2*j+1][0][1])
                in_time     = (in_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(in_out_bench_homeTeam[i][2*j][1][0:2])*60+
                                                                   int(in_out_bench_homeTeam[i][2*j][1][3:5])))
                out_time    = (out_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(in_out_bench_homeTeam[i][2*j+1][1][0:2])*60+
                                                                   int(in_out_bench_homeTeam[i][2*j+1][1][3:5]))) 
                this_timeOnCourt += out_time - in_time
            in_quarter        = int(in_out_bench_homeTeam[i][-1][0][1])
            out_quarter       = 4
            in_time           = (in_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(in_out_bench_homeTeam[i][-1][1][0:2])*60+int(in_out_bench_homeTeam[i][-1][1][3:5])))
            out_time          = (out_quarter-1)*minutes_in_quarter*60 + minutes_in_quarter*60
            this_timeOnCourt += out_time - in_time
            
        timeOnCourt_bench_homeTeam.append(this_timeOnCourt)
        
    

        
    # For each player of the starting five, isolate all actions when he was
    # on the court
    starters_homeTeam_allPlays = []   
    for i in range(0,int(len(homeTeam_startingFive_jerseyNumber))):
        this_starter_homeTeam_allPlays = []
        if np.mod(int(len(in_out_startingFive_homeTeam[i])),2) == 0:
            for j in range(0,int(len(in_out_startingFive_homeTeam[i])/2)):
                this_starter_homeTeam_allPlays.append(list(df_pbp['Home_action'][in_out_startingFive_homeTeam[i][2*j][2]:in_out_startingFive_homeTeam[i][2*j+1][2]]))
        else:
            for j in range(0,int((len(in_out_startingFive_homeTeam[i])-1)/2)):
                this_starter_homeTeam_allPlays.append(list(df_pbp['Home_action'][in_out_startingFive_homeTeam[i][2*j][2]:in_out_startingFive_homeTeam[i][2*j+1][2]]))
            this_starter_homeTeam_allPlays.append(list(df_pbp['Home_action'][in_out_startingFive_homeTeam[i][-1][2]:len(df_pbp['Home_action'])]))    
        this_starter_homeTeam_allPlays = [item for sublist in this_starter_homeTeam_allPlays for item in sublist]
        starters_homeTeam_allPlays.append(this_starter_homeTeam_allPlays)
    
    starters_homeTeam_allPlays_awayTeam = []   
    for i in range(0,int(len(homeTeam_startingFive_jerseyNumber))):
        this_starter_homeTeam_allPlays_awayTeam = []
        if np.mod(int(len(in_out_startingFive_homeTeam[i])),2) == 0:
            for j in range(0,int(len(in_out_startingFive_homeTeam[i])/2)):
                this_starter_homeTeam_allPlays_awayTeam.append(list(df_pbp['Away_action'][in_out_startingFive_homeTeam[i][2*j][2]:in_out_startingFive_homeTeam[i][2*j+1][2]]))
        else:
            for j in range(0,int((len(in_out_startingFive_homeTeam[i])-1)/2)):
                this_starter_homeTeam_allPlays_awayTeam.append(list(df_pbp['Away_action'][in_out_startingFive_homeTeam[i][2*j][2]:in_out_startingFive_homeTeam[i][2*j+1][2]]))
            this_starter_homeTeam_allPlays_awayTeam.append(list(df_pbp['Away_action'][in_out_startingFive_homeTeam[i][-1][2]:len(df_pbp['Away_action'])]))    
        this_starter_homeTeam_allPlays_awayTeam = [item for sublist in this_starter_homeTeam_allPlays_awayTeam for item in sublist]
        starters_homeTeam_allPlays_awayTeam.append(this_starter_homeTeam_allPlays_awayTeam)
            
    
    # Same for bench players
    bench_homeTeam_allPlays = []   
    for i in range(0,int(len(homeTeam_bench_jerseyNumber))):
        this_benchPlayer_homeTeam_allPlays = []
        if np.mod(int(len(in_out_bench_homeTeam[i])),2) == 0:
            for j in range(0,int(len(in_out_bench_homeTeam[i])/2)):
                this_benchPlayer_homeTeam_allPlays.append(list(df_pbp['Home_action'][in_out_bench_homeTeam[i][2*j][2]:in_out_bench_homeTeam[i][2*j+1][2]]))
        else:
            for j in range(0,int((len(in_out_bench_homeTeam[i])-1)/2)):
                this_benchPlayer_homeTeam_allPlays.append(list(df_pbp['Home_action'][in_out_bench_homeTeam[i][2*j][2]:in_out_bench_homeTeam[i][2*j+1][2]]))
            this_benchPlayer_homeTeam_allPlays.append(list(df_pbp['Home_action'][in_out_bench_homeTeam[i][-1][2]:len(df_pbp['Home_action'])]))    
        this_benchPlayer_homeTeam_allPlays = [item for sublist in this_benchPlayer_homeTeam_allPlays for item in sublist]
        bench_homeTeam_allPlays.append(this_benchPlayer_homeTeam_allPlays)
    
    bench_homeTeam_allPlays_awayTeam = []   
    for i in range(0,int(len(homeTeam_bench_jerseyNumber))):
        this_benchPlayer_homeTeam_allPlays_awayTeam = []
        if np.mod(int(len(in_out_bench_homeTeam[i])),2) == 0:
            for j in range(0,int(len(in_out_bench_homeTeam[i])/2)):
                this_benchPlayer_homeTeam_allPlays_awayTeam.append(list(df_pbp['Away_action'][in_out_bench_homeTeam[i][2*j][2]:in_out_bench_homeTeam[i][2*j+1][2]]))
        else:
            for j in range(0,int((len(in_out_bench_homeTeam[i])-1)/2)):
                this_benchPlayer_homeTeam_allPlays_awayTeam.append(list(df_pbp['Away_action'][in_out_bench_homeTeam[i][2*j][2]:in_out_bench_homeTeam[i][2*j+1][2]]))
            this_benchPlayer_homeTeam_allPlays_awayTeam.append(list(df_pbp['Away_action'][in_out_bench_homeTeam[i][-1][2]:len(df_pbp['Away_action'])]))    
        this_benchPlayer_homeTeam_allPlays_awayTeam = [item for sublist in this_benchPlayer_homeTeam_allPlays_awayTeam for item in sublist]
        bench_homeTeam_allPlays_awayTeam.append(this_benchPlayer_homeTeam_allPlays_awayTeam)
    

    
    ###################################################
    # Stats for the home team starting five (own stats)
    ###################################################
    # Note: the way information is retrieved is specific for the Italian League,
    # as there is no easy way to automatize the process, since every different 
    # play-by-play might have a different language and different notation.
    # If pyHoops should be used for other leagues, this part of the code 
    # (and all the equivalent parts below) should be changed accordingly
    all_stats_homeTeam_startingFive         = []
    for i in range(0,int(len(homeTeam_startingFive_jerseyNumber))):
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
        
        for k in range(0,int(len(starters_homeTeam_allPlays[i]))):
            
            # If a row contains the keywords "free throw" and "missed", then it is a missed free throw   
            if ('tirolibero' in starters_homeTeam_allPlays[i][k]  and 'sbagliato' in  starters_homeTeam_allPlays[i][k]):
                _1p_attempted += 1
            # If a row contains the keyword "free throw", but not "missed", then it is a made free throw
            if ('tirolibero' in starters_homeTeam_allPlays[i][k] and 'sbagliato' not in  starters_homeTeam_allPlays[i][k]):
                _1p_attempted += 1
                _1p_made      += 1
            # Same concept for a 2pt shot, but there are multiple keywords both for the type of shot
            # (fade-away, jumper, catch-and-shoot) and missed shot (missed or blocked)
            if ( ('tiroinsospensioneda2pt' in starters_homeTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in starters_homeTeam_allPlays[i][k] or 'layupda2pt' in starters_homeTeam_allPlays[i][k]
                  or  'tiroda2ptinallontanamento' in starters_homeTeam_allPlays[i][k] or 'giroetiroda2pt' in starters_homeTeam_allPlays[i][k] or 'tiroda2ptinpenetrazione' in starters_homeTeam_allPlays[i][k]) and 
                  ('sbagliato' in  starters_homeTeam_allPlays[i][k] or 'stoppato' in  starters_homeTeam_allPlays[i][k])):
                _2p_attempted += 1
            if  ( ('tiroinsospensioneda2pt' in starters_homeTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in starters_homeTeam_allPlays[i][k] or 'layupda2pt' in starters_homeTeam_allPlays[i][k]
                 or  'tiroda2ptinallontanamento' in starters_homeTeam_allPlays[i][k] or 'giroetiroda2pt' in starters_homeTeam_allPlays[i][k] or 'tiroda2ptinpenetrazione' in starters_homeTeam_allPlays[i][k]) and 
                  ('sbagliato' not in  starters_homeTeam_allPlays[i][k] and 'stoppato' not in  starters_homeTeam_allPlays[i][k])):
                _2p_attempted += 1
                _2p_made      += 1
            # A dunk or alleyoop results in a dunk (note: not all alleyoops actually result in a dunk, so there might be a slight
            # inconsistency on the number of overall dunks, but not on the overall 2pt made/attempted)
            if ('schiacciata' in starters_homeTeam_allPlays[i][k]) or ('alleyoop' in starters_homeTeam_allPlays[i][k]):
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            # Same concept as free throw and 2pt shot, but for a 3pt shot
            if ( ('tiroda3ptinsospensione' in starters_homeTeam_allPlays[i][k] and ('sbagliato' in  starters_homeTeam_allPlays[i][k] or 'stoppato' in  starters_homeTeam_allPlays[i][k]))):
                _3p_attempted += 1
            if ( ('tiroda3ptinsospensione' in starters_homeTeam_allPlays[i][k] and ('sbagliato' not in  starters_homeTeam_allPlays[i][k] and 'stoppato' not in  starters_homeTeam_allPlays[i][k]))):
                _3p_attempted += 1
                _3p_made += 1
            # Defensive rebound
            if 'rimbalzodifensivo' in starters_homeTeam_allPlays[i][k]:
                def_rebound += 1
            # Offensive rebound
            if 'rimbalzooffensivo' in starters_homeTeam_allPlays[i][k]:
                off_rebound += 1
            # Assist
            if 'assist' in starters_homeTeam_allPlays[i][k]:
                assist += 1
            # Steal
            if 'pallarecuperata' in starters_homeTeam_allPlays[i][k]:
                steal += 1
            # Turnover
            if 'pallapersa' in starters_homeTeam_allPlays[i][k]:
                turnover += 1
            # Block
            if 'stoppata' in starters_homeTeam_allPlays[i][k]:
                block_made += 1 
            # Block against
            if 'stoppato' in starters_homeTeam_allPlays[i][k]:
                block_received += 1 
            # Foul received
            if 'fallosubito' in starters_homeTeam_allPlays[i][k]:
                foul_received += 1
            # Foul made
            if ('fallo' in starters_homeTeam_allPlays[i][k] and 
               'fallosubito' not in starters_homeTeam_allPlays[i][k]):
                foul_made += 1
        all_stats_homeTeam_startingFive.append([homeTeam_startingFive_names[i],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received,timeOnCourt_startingFive_homeTeam[i]/60.0])
    
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
    
    ##########################################################
    ## Stats for the home team starting five (away team stats)
    ##########################################################
    ## Note: the way information is retrieved is specific for the Italian League,
    ## as there is no easy way to automatize the process, since every different 
    ## play-by-play might have a different language and different notation.
    ## If pyHoops should be used for other leagues, this part of the code 
    ## (and all the equivalent parts below) should be changed accordingly
    all_stats_homeTeam_startingFive_awayTeam = []
    for i in range(0,int(len(homeTeam_startingFive_jerseyNumber))):
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
        
        # For info on the different IFs, refer to code above
        for k in range(0,int(len(starters_homeTeam_allPlays_awayTeam[i]))):
            
                
            if ('tirolibero' in starters_homeTeam_allPlays_awayTeam[i][k]  and 'sbagliato' in  starters_homeTeam_allPlays_awayTeam[i][k]):
                _1p_attempted += 1
            if ('tirolibero' in starters_homeTeam_allPlays_awayTeam[i][k] and 'sbagliato' not in  starters_homeTeam_allPlays_awayTeam[i][k]):
                _1p_attempted += 1
                _1p_made      += 1
            if ( ('tiroinsospensioneda2pt' in starters_homeTeam_allPlays_awayTeam[i][k] or 'tiroda2ptinsospensione' in starters_homeTeam_allPlays_awayTeam[i][k] or 'layupda2pt' in starters_homeTeam_allPlays_awayTeam[i][k]
                  or  'tiroda2ptinallontanamento' in starters_homeTeam_allPlays_awayTeam[i][k] or 'giroetiroda2pt' in starters_homeTeam_allPlays_awayTeam[i][k] or 'tiroda2ptinpenetrazione' in starters_homeTeam_allPlays_awayTeam[i][k]) and 
                  ('sbagliato' in  starters_homeTeam_allPlays_awayTeam[i][k] or 'stoppato' in  starters_homeTeam_allPlays_awayTeam[i][k])):
                _2p_attempted += 1
            if  ( ('tiroinsospensioneda2pt' in starters_homeTeam_allPlays_awayTeam[i][k] or 'tiroda2ptinsospensione' in starters_homeTeam_allPlays_awayTeam[i][k] or 'layupda2pt' in starters_homeTeam_allPlays_awayTeam[i][k]
                 or  'tiroda2ptinallontanamento' in starters_homeTeam_allPlays_awayTeam[i][k] or 'giroetiroda2pt' in starters_homeTeam_allPlays_awayTeam[i][k] or 'tiroda2ptinpenetrazione' in starters_homeTeam_allPlays_awayTeam[i][k]) and 
                  ('sbagliato' not in  starters_homeTeam_allPlays_awayTeam[i][k] and 'stoppato' not in  starters_homeTeam_allPlays_awayTeam[i][k])):
                _2p_attempted += 1
                _2p_made      += 1
            if ('schiacciata' in starters_homeTeam_allPlays_awayTeam[i][k]) or ('alleyoop' in starters_homeTeam_allPlays_awayTeam[i][k]):
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            if ( ('tiroda3ptinsospensione' in starters_homeTeam_allPlays_awayTeam[i][k] and ('sbagliato' in  starters_homeTeam_allPlays_awayTeam[i][k] or 'stoppato' in  starters_homeTeam_allPlays_awayTeam[i][k]))):
                _3p_attempted += 1
            if ( ('tiroda3ptinsospensione' in starters_homeTeam_allPlays_awayTeam[i][k] and ('sbagliato' not in  starters_homeTeam_allPlays_awayTeam[i][k] and 'stoppato' not in  starters_homeTeam_allPlays_awayTeam[i][k]))):
                _3p_attempted += 1
                _3p_made += 1
            if 'rimbalzodifensivo' in starters_homeTeam_allPlays_awayTeam[i][k]:
                def_rebound += 1
            if 'rimbalzooffensivo' in starters_homeTeam_allPlays_awayTeam[i][k]:
                off_rebound += 1
            if 'assist' in starters_homeTeam_allPlays_awayTeam[i][k]:
                assist += 1
            if 'pallarecuperata' in starters_homeTeam_allPlays_awayTeam[i][k]:
                steal += 1
            if 'pallapersa' in starters_homeTeam_allPlays_awayTeam[i][k]:
                turnover += 1
            if 'stoppata' in starters_homeTeam_allPlays_awayTeam[i][k]:
                block_made += 1 
            if 'stoppato' in starters_homeTeam_allPlays_awayTeam[i][k]:
                block_received += 1 
            if 'fallosubito' in starters_homeTeam_allPlays_awayTeam[i][k]:
                foul_received += 1
            if ('fallo' in starters_homeTeam_allPlays_awayTeam[i][k] and 
               'fallosubito' not in starters_homeTeam_allPlays_awayTeam[i][k]):
                foul_made += 1
        all_stats_homeTeam_startingFive_awayTeam.append([homeTeam_startingFive_names[i],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received,timeOnCourt_startingFive_homeTeam[i]/60.0])
    
    # Save data to dataframe and to spreadsheet
    df_homeTeam_startingFive_awayTeamStats = pd.DataFrame(np.array(all_stats_homeTeam_startingFive_awayTeam))
    df_homeTeam_startingFive_awayTeamStats.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_homeTeam_startingFive_awayTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_homeTeam_startingFive_awayTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_homeTeam_startingFive_awayTeamStats.to_excel(os.path.join(cwd,'homeTeam_awayTeamStats_StartingFive.xlsx'),
          sheet_name='Sheet_name_1')
    
    # Determine for each player how many baskets were assisted. To do so, we
    # need to verify if, after a made 2pt or 3pt, in the next row of the dataset
    # an assist was recorded. Again, this is specific for this type of play by
    # play structure. For a different play by play, the assist could be recorded
    # before the shot, and hence the above row should be inspected
    assistedBaskets_homeTeam_startingFive         = []
    for i in range(0,int(len(homeTeam_startingFive_jerseyNumber))):
        _2p_made                  = 0
        _2p_attempted             = 0
        dunk                      = 0
        _3p_made                  = 0
        _3p_attempted             = 0
        assisted_basket           = 0
    
        # For info on the different IFs, refer to code above
        for k in range(0,int(len(starters_homeTeam_allPlays[i])-1)):
            if ( ('tiroinsospensioneda2pt' in starters_homeTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in starters_homeTeam_allPlays[i][k] or 'layupda2pt' in starters_homeTeam_allPlays[i][k]
                  or  'tiroda2ptinallontanamento' in starters_homeTeam_allPlays[i][k] or 'giroetiroda2pt' in starters_homeTeam_allPlays[i][k] or 'tiroda2ptinpenetrazione' in starters_homeTeam_allPlays[i][k]) and 
                  ('sbagliato' in  starters_homeTeam_allPlays[i][k] or 'stoppato' in  starters_homeTeam_allPlays[i][k]) and
                  homeTeam_startingFive_names[i] in starters_homeTeam_allPlays[i][k]):
                _2p_attempted += 1
            if  ( ('tiroinsospensioneda2pt' in starters_homeTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in starters_homeTeam_allPlays[i][k] or 'layupda2pt' in starters_homeTeam_allPlays[i][k]
                 or  'tiroda2ptinallontanamento' in starters_homeTeam_allPlays[i][k]) and 
                  ('sbagliato' not in  starters_homeTeam_allPlays[i][k] and 'stoppato' not in  starters_homeTeam_allPlays[i][k]) and
                  homeTeam_startingFive_names[i] in starters_homeTeam_allPlays[i][k]):
                _2p_attempted += 1
                _2p_made      += 1
            if  ( ('tiroinsospensioneda2pt' in starters_homeTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in starters_homeTeam_allPlays[i][k] or 'layupda2pt' in starters_homeTeam_allPlays[i][k]
                 or  'tiroda2ptinallontanamento' in starters_homeTeam_allPlays[i][k]) and  
                  ('sbagliato' not in  starters_homeTeam_allPlays[i][k] and 'stoppato' not in  starters_homeTeam_allPlays[i][k]) and ('assist' in starters_homeTeam_allPlays[i][k+1]) and
                  homeTeam_startingFive_names[i] in starters_homeTeam_allPlays[i][k]):
                assisted_basket += 1
            if ('schiacciata' in starters_homeTeam_allPlays[i][k]) and (homeTeam_startingFive_names[i] in starters_homeTeam_allPlays[i][k] and
                  homeTeam_startingFive_names[i] in starters_homeTeam_allPlays[i][k]) or ('alleyoop' in starters_homeTeam_allPlays[i][k]) and (homeTeam_startingFive_names[i] in starters_homeTeam_allPlays[i][k]):
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            if (('schiacciata' in starters_homeTeam_allPlays[i][k]) and ('assist' in starters_homeTeam_allPlays[i][k+1]) and (homeTeam_startingFive_names[i] in starters_homeTeam_allPlays[i][k]) or
               (('alleyoop' in starters_homeTeam_allPlays[i][k]) and ('assist' in starters_homeTeam_allPlays[i][k+1]) and (homeTeam_startingFive_names[i] in starters_homeTeam_allPlays[i][k]))):
                assisted_basket += 1
            if ( ('tiroda3ptinsospensione' in starters_homeTeam_allPlays[i][k] and ('sbagliato' in  starters_homeTeam_allPlays[i][k] or 'stoppato' in  starters_homeTeam_allPlays[i][k])) and
                  homeTeam_startingFive_names[i] in starters_homeTeam_allPlays[i][k]):
                _3p_attempted += 1
            if ( ('tiroda3ptinsospensione' in starters_homeTeam_allPlays[i][k] and ('sbagliato' not in  starters_homeTeam_allPlays[i][k] and 'stoppato' not in  starters_homeTeam_allPlays[i][k])) and
                  homeTeam_startingFive_names[i] in starters_homeTeam_allPlays[i][k]):
                _3p_attempted += 1
                _3p_made += 1
            if ( ('tiroda3ptinsospensione' in starters_homeTeam_allPlays[i][k] and ('sbagliato' in  starters_homeTeam_allPlays[i][k] and 'stoppato' in  starters_homeTeam_allPlays[i][k])) and
                  homeTeam_startingFive_names[i] in starters_homeTeam_allPlays[i][k] and 'assist' in starters_homeTeam_allPlays[i][k+1]):
                assisted_basket += 1
    
        assistedBaskets_homeTeam_startingFive.append([homeTeam_startingFive_names[i],_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,assisted_basket])
    
    # Save data to dataframe and to spreadsheet
    df_homeTeam_startingFive_assistedBaskets = pd.DataFrame(np.array(assistedBaskets_homeTeam_startingFive))
    df_homeTeam_startingFive_assistedBaskets.columns = ['Player','2pm','2pa','dunk','3pm','3pa','assisted_baskets']
    df_homeTeam_startingFive_assistedBaskets[['2pm','2pa','dunk','3pm','3pa','assisted_baskets']] = (df_homeTeam_startingFive_assistedBaskets[['2pm','2pa','dunk','3pm','3pa','assisted_baskets']].apply(pd.to_numeric))
    df_homeTeam_startingFive_assistedBaskets.to_excel(os.path.join(cwd,'homeTeam_StartingFive_assistedBaskets.xlsx'),
          sheet_name='Sheet_name_1')
    

    
    ###########################################
    # Stats for the home team bench (own stats)
    ###########################################
    # Note: the way information is retrieved is specific for the Italian League,
    # as there is no easy way to automatize the process, since every different 
    # play-by-play might have a different language and different notation.
    # If pyHoops should be used for other leagues, this part of the code 
    # (and all the equivalent parts below) should be changed accordingly
    all_stats_homeTeam_bench         = []
    for i in range(0,int(len(homeTeam_bench_jerseyNumber))):
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
        
        # For info on the different IFs, refer to code above
        for k in range(0,int(len(bench_homeTeam_allPlays[i]))):
            
                
            if ('tirolibero' in bench_homeTeam_allPlays[i][k]  and 'sbagliato' in  bench_homeTeam_allPlays[i][k]):
                _1p_attempted += 1
            if ('tirolibero' in bench_homeTeam_allPlays[i][k] and 'sbagliato' not in  bench_homeTeam_allPlays[i][k]):
                _1p_attempted += 1
                _1p_made      += 1
            if ( ('tiroinsospensioneda2pt' in bench_homeTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in bench_homeTeam_allPlays[i][k] or 'layupda2pt' in bench_homeTeam_allPlays[i][k]
                  or  'tiroda2ptinallontanamento' in bench_homeTeam_allPlays[i][k] or 'giroetiroda2pt' in bench_homeTeam_allPlays[i][k] or 'tiroda2ptinpenetrazione' in bench_homeTeam_allPlays[i][k]) and 
                  ('sbagliato' in  bench_homeTeam_allPlays[i][k] or 'stoppato' in  bench_homeTeam_allPlays[i][k])):
                _2p_attempted += 1
            if  ( ('tiroinsospensioneda2pt' in bench_homeTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in bench_homeTeam_allPlays[i][k] or 'layupda2pt' in bench_homeTeam_allPlays[i][k]
                 or  'tiroda2ptinallontanamento' in bench_homeTeam_allPlays[i][k]  or 'giroetiroda2pt' in bench_homeTeam_allPlays[i][k] or 'tiroda2ptinpenetrazione' in bench_homeTeam_allPlays[i][k]) and 
                  ('sbagliato' not in  bench_homeTeam_allPlays[i][k] and 'stoppato' not in  bench_homeTeam_allPlays[i][k])):
                _2p_attempted += 1
                _2p_made      += 1
            if ('schiacciata' in bench_homeTeam_allPlays[i][k]) or ('alleyoop' in bench_homeTeam_allPlays[i][k]):
                _2p_attempted += 1
                _2p_made      += 1 
                dunk          += 1
            if ( ('tiroda3ptinsospensione' in bench_homeTeam_allPlays[i][k] and ('sbagliato' in  bench_homeTeam_allPlays[i][k] or 'stoppato' in  bench_homeTeam_allPlays[i][k]))):
                _3p_attempted += 1
            if ( ('tiroda3ptinsospensione' in bench_homeTeam_allPlays[i][k] and ('sbagliato' not in  bench_homeTeam_allPlays[i][k] and 'stoppato' not in  bench_homeTeam_allPlays[i][k]))):
                _3p_attempted += 1
                _3p_made += 1
            if 'rimbalzodifensivo' in bench_homeTeam_allPlays[i][k]:
                def_rebound += 1
            if 'rimbalzooffensivo' in bench_homeTeam_allPlays[i][k]:
                off_rebound += 1
            if 'assist' in bench_homeTeam_allPlays[i][k]:
                assist += 1
            if 'pallarecuperata' in bench_homeTeam_allPlays[i][k]:
                steal += 1
            if 'pallapersa' in bench_homeTeam_allPlays[i][k]:
                turnover += 1
            if 'stoppata' in bench_homeTeam_allPlays[i][k]:
                block_made += 1 
            if 'stoppato' in bench_homeTeam_allPlays[i][k]:
                block_received += 1 
            if 'fallosubito' in bench_homeTeam_allPlays[i][k]:
                foul_received += 1
            if ('fallo' in bench_homeTeam_allPlays[i][k] and 
               'fallosubito' not in bench_homeTeam_allPlays[i][k]):
                foul_made += 1
        all_stats_homeTeam_bench.append([homeTeam_bench_names[i],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received,timeOnCourt_bench_homeTeam[i]/60.0])
    
    # Save data to dataframe and to spreadsheet
    df_homeTeam_bench_homeTeamStats = pd.DataFrame(np.array(all_stats_homeTeam_bench))
    df_homeTeam_bench_homeTeamStats.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_homeTeam_bench_homeTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_homeTeam_bench_homeTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_homeTeam_bench_homeTeamStats.to_excel(os.path.join(cwd,'homeTeam_homeTeamStats_bench.xlsx'),
          sheet_name='Sheet_name_1')
    

    ##########################################################
    ## Stats for the home team bench (away team stats)
    ##########################################################
    ## Note: the way information is retrieved is specific for the Italian League,
    ## as there is no easy way to automatize the process, since every different 
    ## play-by-play might have a different language and different notation.
    ## If pyHoops should be used for other leagues, this part of the code 
    ## (and all the equivalent parts below) should be changed accordingly
    all_stats_homeTeam_bench_awayTeam = []
    for i in range(0,int(len(homeTeam_bench_jerseyNumber))):
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
        
        # For info on the different IFs, refer to code above
        for k in range(0,int(len(bench_homeTeam_allPlays_awayTeam[i]))):
            
                
            if ('tirolibero' in bench_homeTeam_allPlays_awayTeam[i][k]  and 'sbagliato' in  bench_homeTeam_allPlays_awayTeam[i][k]):
                _1p_attempted += 1
            if ('tirolibero' in bench_homeTeam_allPlays_awayTeam[i][k] and 'sbagliato' not in  bench_homeTeam_allPlays_awayTeam[i][k]):
                _1p_attempted += 1
                _1p_made      += 1
            if ( ('tiroinsospensioneda2pt' in bench_homeTeam_allPlays_awayTeam[i][k] or 'tiroda2ptinsospensione' in bench_homeTeam_allPlays_awayTeam[i][k] or 'layupda2pt' in bench_homeTeam_allPlays_awayTeam[i][k]
                  or  'tiroda2ptinallontanamento' in bench_homeTeam_allPlays_awayTeam[i][k] or 'giroetiroda2pt' in bench_homeTeam_allPlays_awayTeam[i][k] or 'tiroda2ptinpenetrazione' in bench_homeTeam_allPlays_awayTeam[i][k]) and 
                  ('sbagliato' in  bench_homeTeam_allPlays_awayTeam[i][k] or 'stoppato' in  bench_homeTeam_allPlays_awayTeam[i][k])):
                _2p_attempted += 1
            if  ( ('tiroinsospensioneda2pt' in bench_homeTeam_allPlays_awayTeam[i][k] or 'tiroda2ptinsospensione' in bench_homeTeam_allPlays_awayTeam[i][k] or 'layupda2pt' in bench_homeTeam_allPlays_awayTeam[i][k]
                 or  'tiroda2ptinallontanamento' in bench_homeTeam_allPlays_awayTeam[i][k] or 'giroetiroda2pt' in bench_homeTeam_allPlays_awayTeam[i][k] or 'tiroda2ptinpenetrazione' in bench_homeTeam_allPlays_awayTeam[i][k]) and 
                  ('sbagliato' not in  bench_homeTeam_allPlays_awayTeam[i][k] and 'stoppato' not in  bench_homeTeam_allPlays_awayTeam[i][k])):
                _2p_attempted += 1
                _2p_made      += 1
            if ('schiacciata' in bench_homeTeam_allPlays_awayTeam[i][k]) or ('alleyoop' in bench_homeTeam_allPlays_awayTeam[i][k]):
                _2p_attempted += 1
                _2p_made      += 1 
                dunk          += 1
            if ( ('tiroda3ptinsospensione' in bench_homeTeam_allPlays_awayTeam[i][k] and ('sbagliato' in  bench_homeTeam_allPlays_awayTeam[i][k] or 'stoppato' in  bench_homeTeam_allPlays_awayTeam[i][k]))):
                _3p_attempted += 1
            if ( ('tiroda3ptinsospensione' in bench_homeTeam_allPlays_awayTeam[i][k] and ('sbagliato' not in  bench_homeTeam_allPlays_awayTeam[i][k] and 'stoppato' not in  bench_homeTeam_allPlays_awayTeam[i][k]))):
                _3p_attempted += 1
                _3p_made += 1
            if 'rimbalzodifensivo' in bench_homeTeam_allPlays_awayTeam[i][k]:
                def_rebound += 1
            if 'rimbalzooffensivo' in bench_homeTeam_allPlays_awayTeam[i][k]:
                off_rebound += 1
            if 'assist' in bench_homeTeam_allPlays_awayTeam[i][k]:
                assist += 1
            if 'pallarecuperata' in bench_homeTeam_allPlays_awayTeam[i][k]:
                steal += 1
            if 'pallapersa' in bench_homeTeam_allPlays_awayTeam[i][k]:
                turnover += 1
            if 'stoppata' in bench_homeTeam_allPlays_awayTeam[i][k]:
                block_made += 1 
            if 'stoppato' in bench_homeTeam_allPlays_awayTeam[i][k]:
                block_received += 1 
            if 'fallosubito' in bench_homeTeam_allPlays_awayTeam[i][k]:
                foul_received += 1
            if ('fallo' in bench_homeTeam_allPlays_awayTeam[i][k] and 
               'fallosubito' not in bench_homeTeam_allPlays_awayTeam[i][k]):
                foul_made += 1
        all_stats_homeTeam_bench_awayTeam.append([homeTeam_bench_names[i],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received,timeOnCourt_bench_homeTeam[i]/60.0])
    
    # Save data to dataframe and to spreadsheet
    df_homeTeam_bench_awayTeamStats = pd.DataFrame(np.array(all_stats_homeTeam_bench_awayTeam))
    df_homeTeam_bench_awayTeamStats.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_homeTeam_bench_awayTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_homeTeam_bench_awayTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_homeTeam_bench_awayTeamStats.to_excel(os.path.join(cwd,'homeTeam_awayTeamStats_bench.xlsx'),
          sheet_name='Sheet_name_1')
    

    
    # Determine for each player how many baskets were assisted
    assistedBaskets_homeTeam_bench         = []
    for i in range(0,int(len(homeTeam_bench_jerseyNumber))):
        _2p_made                  = 0
        _2p_attempted             = 0
        dunk                      = 0
        _3p_made                  = 0
        _3p_attempted             = 0
        assisted_basket           = 0
    
        # For info on the different IFs, refer to code above
        for k in range(0,int(len(bench_homeTeam_allPlays[i])-1)):
            if ( ('tiroinsospensioneda2pt' in bench_homeTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in bench_homeTeam_allPlays[i][k] or 'layupda2pt' in bench_homeTeam_allPlays[i][k]
                  or  'tiroda2ptinallontanamento' in bench_homeTeam_allPlays[i][k] or 'giroetiroda2pt' in bench_homeTeam_allPlays[i][k] or 'tiroda2ptinpenetrazione' in bench_homeTeam_allPlays[i][k]) and 
                  ('sbagliato' in  bench_homeTeam_allPlays[i][k] or 'stoppato' in  bench_homeTeam_allPlays[i][k]) and
                  homeTeam_bench_names[i] in bench_homeTeam_allPlays[i][k]):
                _2p_attempted += 1
            if  ( ('tiroinsospensioneda2pt' in bench_homeTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in bench_homeTeam_allPlays[i][k] or 'layupda2pt' in bench_homeTeam_allPlays[i][k]
                 or  'tiroda2ptinallontanamento' in bench_homeTeam_allPlays[i][k] or 'giroetiroda2pt' in bench_homeTeam_allPlays[i][k] or 'tiroda2ptinpenetrazione' in bench_homeTeam_allPlays[i][k]) and 
                  ('sbagliato' not in  bench_homeTeam_allPlays[i][k] and 'stoppato' not in  bench_homeTeam_allPlays[i][k]) and
                  homeTeam_bench_names[i] in bench_homeTeam_allPlays[i][k]):
                _2p_attempted += 1
                _2p_made      += 1
            if  ( ('tiroinsospensioneda2pt' in bench_homeTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in bench_homeTeam_allPlays[i][k] or 'layupda2pt' in bench_homeTeam_allPlays[i][k]
                 or  'tiroda2ptinallontanamento' in bench_homeTeam_allPlays[i][k] or 'giroetiroda2pt' in bench_homeTeam_allPlays[i][k] or 'tiroda2ptinpenetrazione' in bench_homeTeam_allPlays[i][k]) and  
                  ('sbagliato' not in  bench_homeTeam_allPlays[i][k] and 'stoppato' not in  bench_homeTeam_allPlays[i][k]) and ('assist' in bench_homeTeam_allPlays[i][k+1]) and
                  homeTeam_bench_names[i] in bench_homeTeam_allPlays[i][k]):
                assisted_basket += 1
            if ('schiacciata' in bench_homeTeam_allPlays[i][k]) and (homeTeam_bench_names[i] in bench_homeTeam_allPlays[i][k]) or ('alleyoop' in bench_homeTeam_allPlays[i][k]) and (homeTeam_bench_names[i] in bench_homeTeam_allPlays[i][k]):
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            if (('schiacciata' in bench_homeTeam_allPlays[i][k]) and ('assist' in bench_homeTeam_allPlays[i][k+1]) and (homeTeam_bench_names[i] in bench_homeTeam_allPlays[i][k]) or
               (('alleyoop' in bench_homeTeam_allPlays[i][k]) and ('assist' in bench_homeTeam_allPlays[i][k+1]) and (homeTeam_bench_names[i] in bench_homeTeam_allPlays[i][k]))):
                assisted_basket += 1
            if ( ('tiroda3ptinsospensione' in bench_homeTeam_allPlays[i][k] and ('sbagliato' in  bench_homeTeam_allPlays[i][k] or 'stoppato' in  bench_homeTeam_allPlays[i][k])) and
                  homeTeam_bench_names[i] in bench_homeTeam_allPlays[i][k]):
                _3p_attempted += 1
            if ( ('tiroda3ptinsospensione' in bench_homeTeam_allPlays[i][k] and ('sbagliato' not in  bench_homeTeam_allPlays[i][k] and 'stoppato' not in  bench_homeTeam_allPlays[i][k])) and
                  homeTeam_bench_names[i] in bench_homeTeam_allPlays[i][k]):
                _3p_attempted += 1
                _3p_made += 1
            if ( ('tiroda3ptinsospensione' in bench_homeTeam_allPlays[i][k] and ('sbagliato' in  bench_homeTeam_allPlays[i][k] and 'stoppato' in  bench_homeTeam_allPlays[i][k])) and
                  homeTeam_bench_names[i] in bench_homeTeam_allPlays[i][k] and 'assist' in bench_homeTeam_allPlays[i][k+1]):
                assisted_basket += 1
    
        assistedBaskets_homeTeam_bench.append([homeTeam_bench_names[i],_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,assisted_basket])
    
    # Save data to dataframe and to spreadsheet
    df_homeTeam_bench_assistedBaskets = pd.DataFrame(np.array(assistedBaskets_homeTeam_bench))
    df_homeTeam_bench_assistedBaskets.columns = ['Player','2pm','2pa','dunk','3pm','3pa','assisted_baskets']
    df_homeTeam_bench_assistedBaskets[['2pm','2pa','dunk','3pm','3pa','assisted_baskets']] = (df_homeTeam_bench_assistedBaskets[['2pm','2pa','dunk','3pm','3pa','assisted_baskets']].apply(pd.to_numeric))
    df_homeTeam_bench_assistedBaskets.to_excel(os.path.join(cwd,'homeTeam_Bench_assistedBaskets.xlsx'),
          sheet_name='Sheet_name_1')
    
    # Merge starting five and bench info for homeTeam
    df_homeTeam_startingPlusBench_homeTeamStats = pd.concat([df_homeTeam_startingFive_homeTeamStats,
                                                        df_homeTeam_bench_homeTeamStats], ignore_index=True)
    df_homeTeam_startingPlusBench_awayTeamStats = pd.concat([df_homeTeam_startingFive_awayTeamStats,
                                                        df_homeTeam_bench_awayTeamStats], ignore_index=True)
    df_homeTeam_startingPlusBench_assistedBaskets = pd.concat([df_homeTeam_startingFive_assistedBaskets,
                                                        df_homeTeam_bench_assistedBaskets], ignore_index=True)  
                
    return (df_homeTeam_startingPlusBench_homeTeamStats,
           df_homeTeam_startingPlusBench_awayTeamStats,
           df_homeTeam_startingPlusBench_assistedBaskets,
           homeTeam_startingFive_names,homeTeam_startingFive_info,
           homeTeam_bench_names,homeTeam_bench_info,
           orig_idx_starting_five_homeTeam,orig_idx_bench_homeTeam)

def get_awayTeam_stats_perPlayer(df_pbp,dfAwayTeam,minutes_in_quarter,cwd):
    # Get info for away team (all players: starting five and bench)
    awayTeam_allPlayers_jerseyNumber   = []
    awayTeam_allPlayers_names          = []
    awayTeam_allPlayers_allNames       = []
    awayTeam_allPlayers_info           = []
    awayTeam_startingFive_jerseyNumber = []
    awayTeam_startingFive_names        = []
    awayTeam_startingFive_info         = []
    awayTeam_bench_jerseyNumber        = []
    awayTeam_bench_names               = []
    awayTeam_bench_info                = []
    
    orig_idx_starting_five_awayTeam = []
    orig_idx_bench_awayTeam         = []
    for i in range(0,int(len(dfAwayTeam))):
        # Row is associated with a jersey number
        if dfAwayTeam.loc[i][1]:
            
            # Clean the full name of the player by getting rid of special
            # characters, spaces, etc
            s             = dfAwayTeam.loc[i][2]
            ccc           = ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))
            ccc           = ccc.replace(u'\xa0', u' ')
            ccc           = ccc.replace('\'','')
            s_mod_noSpace = ccc.replace(' ','')
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
                
            if dfAwayTeam.loc[i][0] == '*':
                awayTeam_startingFive_jerseyNumber.append(str(dfAwayTeam.loc[i][1]))
                awayTeam_startingFive_names.append(s_mod_noSpace)
                awayTeam_startingFive_info.append([s_mod_noSpace,all_combinations])
                orig_idx_starting_five_awayTeam.append(i)
            else:
                awayTeam_bench_jerseyNumber.append(str(dfAwayTeam.loc[i][1]))
                awayTeam_bench_names.append(s_mod_noSpace)
                awayTeam_bench_info.append([s_mod_noSpace,all_combinations])
                orig_idx_bench_awayTeam.append(i)
                
            awayTeam_allPlayers_jerseyNumber.append(str(dfAwayTeam.loc[i][1]))
            awayTeam_allPlayers_names.append(s_mod_noSpace)
            awayTeam_allPlayers_info.append([s_mod_noSpace,all_combinations])
            awayTeam_allPlayers_allNames.append(all_combinations)
    

    
    # Check when the starting five of the home team is on/off the court
    in_out_startingFive_awayTeam = []
    for i in range(0,int(len(awayTeam_startingFive_jerseyNumber))):
        all_names                = deepcopy(awayTeam_allPlayers_allNames)
        this_player_jerseyNumber = awayTeam_startingFive_jerseyNumber[i]
        this_player_idx          = awayTeam_allPlayers_jerseyNumber.index(this_player_jerseyNumber)
        all_names.pop(this_player_idx)
        flat_list_all_names = [item for sublist in all_names for item in sublist]
        thisPlayerOnOff = [['t1','10:00',0,'in']]
        for j in range(0,int(len(df_pbp['Away_action']))):
            if any(k in df_pbp['Away_action'][j] for k in awayTeam_startingFive_info[i][1]) and any(k in df_pbp['Away_action'][j] for k in flat_list_all_names):
                if np.mod(int(len(thisPlayerOnOff)),2) == 0:
                    in_or_out = 'in'
                    thisPlayerOnOff.append([df_pbp['quarter_of_game'][j],df_pbp['time_of_game'][j],j,in_or_out])
                else:
                    in_or_out = 'out'
                    thisPlayerOnOff.append([df_pbp['quarter_of_game'][j],df_pbp['time_of_game'][j],j+1,in_or_out])
        in_out_startingFive_awayTeam.append(thisPlayerOnOff)
        
    # Compute overall time on court for starting five of away team
    timeOnCourt_startingFive_awayTeam = []
    for i in range(0,int(len(awayTeam_startingFive_jerseyNumber))):
        this_player_in_out = in_out_startingFive_awayTeam[i]
        this_timeOnCourt   = 0
        # Player ends game on the bench
        if np.mod(int(len(this_player_in_out)),2) == 0:
            for j in range(0,int(len(in_out_startingFive_awayTeam[i])/2)):
                in_quarter  = int(in_out_startingFive_awayTeam[i][2*j][0][1])
                out_quarter = int(in_out_startingFive_awayTeam[i][2*j+1][0][1])
                in_time     = (in_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(in_out_startingFive_awayTeam[i][2*j][1][0:2])*60+
                                                                   int(in_out_startingFive_awayTeam[i][2*j][1][3:5])))
                out_time    = (out_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(in_out_startingFive_awayTeam[i][2*j+1][1][0:2])*60+
                                                                   int(in_out_startingFive_awayTeam[i][2*j+1][1][3:5]))) 
                this_timeOnCourt += out_time - in_time
        else:
            for j in range(0,int((len(in_out_startingFive_awayTeam[i])-1)/2)):
                in_quarter  = int(in_out_startingFive_awayTeam[i][2*j][0][1])
                out_quarter = int(in_out_startingFive_awayTeam[i][2*j+1][0][1])
                in_time     = (in_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(in_out_startingFive_awayTeam[i][2*j][1][0:2])*60+
                                                                   int(in_out_startingFive_awayTeam[i][2*j][1][3:5])))
                out_time    = (out_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(in_out_startingFive_awayTeam[i][2*j+1][1][0:2])*60+
                                                                   int(in_out_startingFive_awayTeam[i][2*j+1][1][3:5]))) 
                this_timeOnCourt += out_time - in_time
            in_quarter        = int(in_out_startingFive_awayTeam[i][-1][0][1])
            out_quarter       = 4
            in_time           = (in_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(in_out_startingFive_awayTeam[i][-1][1][0:2])*60+int(in_out_startingFive_awayTeam[i][-1][1][3:5])))
            out_time          = (out_quarter-1)*minutes_in_quarter*60 + minutes_in_quarter*60
            this_timeOnCourt += out_time - in_time
            
        
                
        timeOnCourt_startingFive_awayTeam.append(this_timeOnCourt)
    
    
    # Check when the bench of the away team is on/off the court
    in_out_bench_awayTeam = []
    for i in range(0,int(len(awayTeam_bench_jerseyNumber))):
        all_names                = deepcopy(awayTeam_allPlayers_allNames)
        this_player_jerseyNumber = awayTeam_bench_jerseyNumber[i]
        this_player_idx          = awayTeam_allPlayers_jerseyNumber.index(this_player_jerseyNumber)
        all_names.pop(this_player_idx)
        flat_list_all_names = [item for sublist in all_names for item in sublist]
        thisPlayerOnOff = []
        for j in range(0,int(len(df_pbp['Away_action']))):
            if any(k in df_pbp['Away_action'][j] for k in awayTeam_bench_info[i][1]) and any(k in df_pbp['Away_action'][j] for k in flat_list_all_names):
                if np.mod(int(len(thisPlayerOnOff)),2) == 0:
                    in_or_out = 'in'
                    thisPlayerOnOff.append([df_pbp['quarter_of_game'][j],df_pbp['time_of_game'][j],j,in_or_out])
                else:
                    in_or_out = 'out'
                    thisPlayerOnOff.append([df_pbp['quarter_of_game'][j],df_pbp['time_of_game'][j],j+1,in_or_out])
        in_out_bench_awayTeam.append(thisPlayerOnOff)
    
    # Compute overall time on court for bench of away team
    timeOnCourt_bench_awayTeam = []
    for i in range(0,int(len(awayTeam_bench_jerseyNumber))):
        this_player_in_out = in_out_bench_awayTeam[i]
        this_timeOnCourt   = 0
        # Player ends game on the bench
        if np.mod(int(len(this_player_in_out)),2) == 0:
            for j in range(0,int(len(in_out_bench_awayTeam[i])/2)):
                in_quarter  = int(in_out_bench_awayTeam[i][2*j][0][1])
                out_quarter = int(in_out_bench_awayTeam[i][2*j+1][0][1])
                in_time     = (in_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(in_out_bench_awayTeam[i][2*j][1][0:2])*60+
                                                                   int(in_out_bench_awayTeam[i][2*j][1][3:5])))
                out_time    = (out_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(in_out_bench_awayTeam[i][2*j+1][1][0:2])*60+
                                                                   int(in_out_bench_awayTeam[i][2*j+1][1][3:5]))) 
                this_timeOnCourt += out_time - in_time
        else:
            for j in range(0,int((len(in_out_bench_awayTeam[i])-1)/2)):
                in_quarter  = int(in_out_bench_awayTeam[i][2*j][0][1])
                out_quarter = int(in_out_bench_awayTeam[i][2*j+1][0][1])
                in_time     = (in_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(in_out_bench_awayTeam[i][2*j][1][0:2])*60+
                                                                   int(in_out_bench_awayTeam[i][2*j][1][3:5])))
                out_time    = (out_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(in_out_bench_awayTeam[i][2*j+1][1][0:2])*60+
                                                                   int(in_out_bench_awayTeam[i][2*j+1][1][3:5]))) 
                this_timeOnCourt += out_time - in_time
            in_quarter        = int(in_out_bench_awayTeam[i][-1][0][1])
            out_quarter       = 4
            in_time           = (in_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(in_out_bench_awayTeam[i][-1][1][0:2])*60+int(in_out_bench_awayTeam[i][-1][1][3:5])))
            out_time          = (out_quarter-1)*minutes_in_quarter*60 + minutes_in_quarter*60
            this_timeOnCourt += out_time - in_time
            
        timeOnCourt_bench_awayTeam.append(this_timeOnCourt)
    
    # For each player of the starting five, isolate all actions when he was
    # on the court
    starters_awayTeam_allPlays = []   
    for i in range(0,int(len(awayTeam_startingFive_jerseyNumber))):
        this_starter_awayTeam_allPlays = []
        if np.mod(int(len(in_out_startingFive_awayTeam[i])),2) == 0:
            for j in range(0,int(len(in_out_startingFive_awayTeam[i])/2)):
                this_starter_awayTeam_allPlays.append(list(df_pbp['Away_action'][in_out_startingFive_awayTeam[i][2*j][2]:in_out_startingFive_awayTeam[i][2*j+1][2]]))
        else:
            for j in range(0,int((len(in_out_startingFive_awayTeam[i])-1)/2)):
                this_starter_awayTeam_allPlays.append(list(df_pbp['Away_action'][in_out_startingFive_awayTeam[i][2*j][2]:in_out_startingFive_awayTeam[i][2*j+1][2]]))
            this_starter_awayTeam_allPlays.append(list(df_pbp['Away_action'][in_out_startingFive_awayTeam[i][-1][2]:len(df_pbp['Away_action'])]))    
        this_starter_awayTeam_allPlays = [item for sublist in this_starter_awayTeam_allPlays for item in sublist]
        starters_awayTeam_allPlays.append(this_starter_awayTeam_allPlays)
    
    starters_awayTeam_allPlays_homeTeam = []   
    for i in range(0,int(len(awayTeam_startingFive_jerseyNumber))):
        this_starter_awayTeam_allPlays_homeTeam = []
        if np.mod(int(len(in_out_startingFive_awayTeam[i])),2) == 0:
            for j in range(0,int(len(in_out_startingFive_awayTeam[i])/2)):
                this_starter_awayTeam_allPlays_homeTeam.append(list(df_pbp['Home_action'][in_out_startingFive_awayTeam[i][2*j][2]:in_out_startingFive_awayTeam[i][2*j+1][2]]))
        else:
            for j in range(0,int((len(in_out_startingFive_awayTeam[i])-1)/2)):
                this_starter_awayTeam_allPlays_homeTeam.append(list(df_pbp['Home_action'][in_out_startingFive_awayTeam[i][2*j][2]:in_out_startingFive_awayTeam[i][2*j+1][2]]))
            this_starter_awayTeam_allPlays_homeTeam.append(list(df_pbp['Home_action'][in_out_startingFive_awayTeam[i][-1][2]:len(df_pbp['Home_action'])]))    
        this_starter_awayTeam_allPlays_homeTeam = [item for sublist in this_starter_awayTeam_allPlays_homeTeam for item in sublist]
        starters_awayTeam_allPlays_homeTeam.append(this_starter_awayTeam_allPlays_homeTeam)
            
    
    # Same for bench players
    bench_awayTeam_allPlays = []   
    for i in range(0,int(len(awayTeam_bench_jerseyNumber))):
        this_benchPlayer_awayTeam_allPlays = []
        if np.mod(int(len(in_out_bench_awayTeam[i])),2) == 0:
            for j in range(0,int(len(in_out_bench_awayTeam[i])/2)):
                this_benchPlayer_awayTeam_allPlays.append(list(df_pbp['Away_action'][in_out_bench_awayTeam[i][2*j][2]:in_out_bench_awayTeam[i][2*j+1][2]]))
        else:
            for j in range(0,int((len(in_out_bench_awayTeam[i])-1)/2)):
                this_benchPlayer_awayTeam_allPlays.append(list(df_pbp['Away_action'][in_out_bench_awayTeam[i][2*j][2]:in_out_bench_awayTeam[i][2*j+1][2]]))
            this_benchPlayer_awayTeam_allPlays.append(list(df_pbp['Away_action'][in_out_bench_awayTeam[i][-1][2]:len(df_pbp['Away_action'])]))    
        this_benchPlayer_awayTeam_allPlays = [item for sublist in this_benchPlayer_awayTeam_allPlays for item in sublist]
        bench_awayTeam_allPlays.append(this_benchPlayer_awayTeam_allPlays)
    
    bench_awayTeam_allPlays_homeTeam = []   
    for i in range(0,int(len(awayTeam_bench_jerseyNumber))):
        this_benchPlayer_awayTeam_allPlays_homeTeam = []
        if np.mod(int(len(in_out_bench_awayTeam[i])),2) == 0:
            for j in range(0,int(len(in_out_bench_awayTeam[i])/2)):
                this_benchPlayer_awayTeam_allPlays_homeTeam.append(list(df_pbp['Home_action'][in_out_bench_awayTeam[i][2*j][2]:in_out_bench_awayTeam[i][2*j+1][2]]))
        else:
            for j in range(0,int((len(in_out_bench_awayTeam[i])-1)/2)):
                this_benchPlayer_awayTeam_allPlays_homeTeam.append(list(df_pbp['Home_action'][in_out_bench_awayTeam[i][2*j][2]:in_out_bench_awayTeam[i][2*j+1][2]]))
            this_benchPlayer_awayTeam_allPlays_homeTeam.append(list(df_pbp['Home_action'][in_out_bench_awayTeam[i][-1][2]:len(df_pbp['Home_action'])]))    
        this_benchPlayer_awayTeam_allPlays_homeTeam = [item for sublist in this_benchPlayer_awayTeam_allPlays_homeTeam for item in sublist]
        bench_awayTeam_allPlays_homeTeam.append(this_benchPlayer_awayTeam_allPlays_homeTeam)
    

    
    ###################################################
    # Stats for the away team starting five (own stats)
    ###################################################
    # Note: the way information is retrieved is specific for the Italian League,
    # as there is no easy way to automatize the process, since every different 
    # play-by-play might have a different language and different notation.
    # If pyHoops should be used for other leagues, this part of the code 
    # (and all the equivalent parts below) should be changed accordingly
    all_stats_awayTeam_startingFive         = []
    for i in range(0,int(len(awayTeam_startingFive_jerseyNumber))):
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
        
        # For info on the different IFs, refer to code above
        for k in range(0,int(len(starters_awayTeam_allPlays[i]))):
            
                
            if ('tirolibero' in starters_awayTeam_allPlays[i][k]  and 'sbagliato' in  starters_awayTeam_allPlays[i][k]):
                _1p_attempted += 1
            if ('tirolibero' in starters_awayTeam_allPlays[i][k] and 'sbagliato' not in  starters_awayTeam_allPlays[i][k]):
                _1p_attempted += 1
                _1p_made      += 1
            if ( ('tiroinsospensioneda2pt' in starters_awayTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in starters_awayTeam_allPlays[i][k] or 'layupda2pt' in starters_awayTeam_allPlays[i][k]
                  or  'tiroda2ptinallontanamento' in starters_awayTeam_allPlays[i][k] or 'giroetiroda2pt' in starters_awayTeam_allPlays[i][k] or 'tiroda2ptinpenetrazione' in starters_awayTeam_allPlays[i][k]) and 
                  ('sbagliato' in  starters_awayTeam_allPlays[i][k] or 'stoppato' in  starters_awayTeam_allPlays[i][k])):
                _2p_attempted += 1
            if  ( ('tiroinsospensioneda2pt' in starters_awayTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in starters_awayTeam_allPlays[i][k] or 'layupda2pt' in starters_awayTeam_allPlays[i][k]
                 or  'tiroda2ptinallontanamento' in starters_awayTeam_allPlays[i][k] or 'giroetiroda2pt' in starters_awayTeam_allPlays[i][k] or 'tiroda2ptinpenetrazione' in starters_awayTeam_allPlays[i][k]) and 
                  ('sbagliato' not in  starters_awayTeam_allPlays[i][k] and 'stoppato' not in  starters_awayTeam_allPlays[i][k])):
                _2p_attempted += 1
                _2p_made      += 1
            if ('schiacciata' in starters_awayTeam_allPlays[i][k]) or ('alleyoop' in starters_awayTeam_allPlays[i][k]):
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            if ( ('tiroda3ptinsospensione' in starters_awayTeam_allPlays[i][k] and ('sbagliato' in  starters_awayTeam_allPlays[i][k] or 'stoppato' in  starters_awayTeam_allPlays[i][k]))):
                _3p_attempted += 1
            if ( ('tiroda3ptinsospensione' in starters_awayTeam_allPlays[i][k] and ('sbagliato' not in  starters_awayTeam_allPlays[i][k] and 'stoppato' not in  starters_awayTeam_allPlays[i][k]))):
                _3p_attempted += 1
                _3p_made += 1
            if 'rimbalzodifensivo' in starters_awayTeam_allPlays[i][k]:
                def_rebound += 1
            if 'rimbalzooffensivo' in starters_awayTeam_allPlays[i][k]:
                off_rebound += 1
            if 'assist' in starters_awayTeam_allPlays[i][k]:
                assist += 1
            if 'pallarecuperata' in starters_awayTeam_allPlays[i][k]:
                steal += 1
            if 'pallapersa' in starters_awayTeam_allPlays[i][k]:
                turnover += 1
            if 'stoppata' in starters_awayTeam_allPlays[i][k]:
                block_made += 1 
            if 'stoppato' in starters_awayTeam_allPlays[i][k]:
                block_received += 1 
            if 'fallosubito' in starters_awayTeam_allPlays[i][k]:
                foul_received += 1
            if ('fallo' in starters_awayTeam_allPlays[i][k] and 
               'fallosubito' not in starters_awayTeam_allPlays[i][k]):
                foul_made += 1
        all_stats_awayTeam_startingFive.append([awayTeam_startingFive_names[i],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received,timeOnCourt_startingFive_awayTeam[i]/60.0])
    
    # Save data to dataframe and to spreadsheet
    df_awayTeam_startingFive_awayTeamStats = pd.DataFrame(np.array(all_stats_awayTeam_startingFive))
    df_awayTeam_startingFive_awayTeamStats.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_awayTeam_startingFive_awayTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_awayTeam_startingFive_awayTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_awayTeam_startingFive_awayTeamStats.to_excel(os.path.join(cwd,'awayTeam_awayTeamStats_StartingFive.xlsx'),
          sheet_name='Sheet_name_1')
    

    
    ##########################################################
    ## Stats for the away team starting five (home team stats)
    ##########################################################
    ## Note: the way information is retrieved is specific for the Italian League,
    ## as there is no easy way to automatize the process, since every different 
    ## play-by-play might have a different language and different notation.
    ## If pyHoops should be used for other leagues, this part of the code 
    ## (and all the equivalent parts below) should be changed accordingly
    all_stats_awayTeam_startingFive_homeTeam = []
    for i in range(0,int(len(awayTeam_startingFive_jerseyNumber))):
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
        
        # For info on the different IFs, refer to code above
        for k in range(0,int(len(starters_awayTeam_allPlays_homeTeam[i]))):
            
                
            if ('tirolibero' in starters_awayTeam_allPlays_homeTeam[i][k]  and 'sbagliato' in  starters_awayTeam_allPlays_homeTeam[i][k]):
                _1p_attempted += 1
            if ('tirolibero' in starters_awayTeam_allPlays_homeTeam[i][k] and 'sbagliato' not in  starters_awayTeam_allPlays_homeTeam[i][k]):
                _1p_attempted += 1
                _1p_made      += 1
            if ( ('tiroinsospensioneda2pt' in starters_awayTeam_allPlays_homeTeam[i][k] or 'tiroda2ptinsospensione' in starters_awayTeam_allPlays_homeTeam[i][k] or 'layupda2pt' in starters_awayTeam_allPlays_homeTeam[i][k]
                  or  'tiroda2ptinallontanamento' in starters_awayTeam_allPlays_homeTeam[i][k] or 'giroetiroda2pt' in starters_awayTeam_allPlays_homeTeam[i][k] or 'tiroda2ptinpenetrazione' in starters_awayTeam_allPlays_homeTeam[i][k]) and 
                  ('sbagliato' in  starters_awayTeam_allPlays_homeTeam[i][k] or 'stoppato' in  starters_awayTeam_allPlays_homeTeam[i][k])):
                _2p_attempted += 1
            if  ( ('tiroinsospensioneda2pt' in starters_awayTeam_allPlays_homeTeam[i][k] or 'tiroda2ptinsospensione' in starters_awayTeam_allPlays_homeTeam[i][k] or 'layupda2pt' in starters_awayTeam_allPlays_homeTeam[i][k]
                 or  'tiroda2ptinallontanamento' in starters_awayTeam_allPlays_homeTeam[i][k] or 'giroetiroda2pt' in starters_awayTeam_allPlays_homeTeam[i][k] or 'tiroda2ptinpenetrazione' in starters_awayTeam_allPlays_homeTeam[i][k]) and 
                  ('sbagliato' not in  starters_awayTeam_allPlays_homeTeam[i][k] and 'stoppato' not in  starters_awayTeam_allPlays_homeTeam[i][k])):
                _2p_attempted += 1
                _2p_made      += 1
            if ('schiacciata' in starters_awayTeam_allPlays_homeTeam[i][k]) or ('alleyoop' in starters_awayTeam_allPlays_homeTeam[i][k]):
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            if ( ('tiroda3ptinsospensione' in starters_awayTeam_allPlays_homeTeam[i][k] and ('sbagliato' in  starters_awayTeam_allPlays_homeTeam[i][k] or 'stoppato' in  starters_awayTeam_allPlays_homeTeam[i][k]))):
                _3p_attempted += 1
            if ( ('tiroda3ptinsospensione' in starters_awayTeam_allPlays_homeTeam[i][k] and ('sbagliato' not in  starters_awayTeam_allPlays_homeTeam[i][k] and 'stoppato' not in  starters_awayTeam_allPlays_homeTeam[i][k]))):
                _3p_attempted += 1
                _3p_made += 1
            if 'rimbalzodifensivo' in starters_awayTeam_allPlays_homeTeam[i][k]:
                def_rebound += 1
            if 'rimbalzooffensivo' in starters_awayTeam_allPlays_homeTeam[i][k]:
                off_rebound += 1
            if 'assist' in starters_awayTeam_allPlays_homeTeam[i][k]:
                assist += 1
            if 'pallarecuperata' in starters_awayTeam_allPlays_homeTeam[i][k]:
                steal += 1
            if 'pallapersa' in starters_awayTeam_allPlays_homeTeam[i][k]:
                turnover += 1
            if 'stoppata' in starters_awayTeam_allPlays_homeTeam[i][k]:
                block_made += 1 
            if 'stoppato' in starters_awayTeam_allPlays_homeTeam[i][k]:
                block_received += 1 
            if 'fallosubito' in starters_awayTeam_allPlays_homeTeam[i][k]:
                foul_received += 1
            if ('fallo' in starters_awayTeam_allPlays_homeTeam[i][k] and 
               'fallosubito' not in starters_awayTeam_allPlays_homeTeam[i][k]):
                foul_made += 1
        all_stats_awayTeam_startingFive_homeTeam.append([awayTeam_startingFive_names[i],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received,timeOnCourt_startingFive_awayTeam[i]/60.0])
    
    # Save data to dataframe and to spreadsheet
    df_awayTeam_startingFive_homeTeamStats = pd.DataFrame(np.array(all_stats_awayTeam_startingFive_homeTeam))
    df_awayTeam_startingFive_homeTeamStats.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_awayTeam_startingFive_homeTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_awayTeam_startingFive_homeTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_awayTeam_startingFive_homeTeamStats.to_excel(os.path.join(cwd,'awayTeam_homeTeamStats_StartingFive.xlsx'),
          sheet_name='Sheet_name_1')
    

    
    # Determine for each player how many baskets were assisted
    assistedBaskets_awayTeam_startingFive         = []
    for i in range(0,int(len(awayTeam_startingFive_jerseyNumber))):
        _2p_made                  = 0
        _2p_attempted             = 0
        dunk                      = 0
        _3p_made                  = 0
        _3p_attempted             = 0
        assisted_basket           = 0
    
        # For info on the different IFs, refer to code above
        for k in range(0,int(len(starters_awayTeam_allPlays[i])-1)):
            if ( ('tiroinsospensioneda2pt' in starters_awayTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in starters_awayTeam_allPlays[i][k] or 'layupda2pt' in starters_awayTeam_allPlays[i][k]
                  or  'tiroda2ptinallontanamento' in starters_awayTeam_allPlays[i][k] or 'giroetiroda2pt' in starters_awayTeam_allPlays[i][k] or 'tiroda2ptinpenetrazione' in starters_awayTeam_allPlays[i][k]) and 
                  ('sbagliato' in  starters_awayTeam_allPlays[i][k] or 'stoppato' in  starters_awayTeam_allPlays[i][k]) and
                  (any(ext in starters_awayTeam_allPlays[i][k] for ext in awayTeam_startingFive_info[i][1]))  ):
                _2p_attempted += 1
            if  ( ('tiroinsospensioneda2pt' in starters_awayTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in starters_awayTeam_allPlays[i][k] or 'layupda2pt' in starters_awayTeam_allPlays[i][k]
                 or  'tiroda2ptinallontanamento' in starters_awayTeam_allPlays[i][k] or 'giroetiroda2pt' in starters_awayTeam_allPlays[i][k] or 'tiroda2ptinpenetrazione' in starters_awayTeam_allPlays[i][k]) and 
                  ('sbagliato' not in  starters_awayTeam_allPlays[i][k] and 'stoppato' not in  starters_awayTeam_allPlays[i][k]) and
                  (any(ext in starters_awayTeam_allPlays[i][k] for ext in awayTeam_startingFive_info[i][1]))  ):
                _2p_attempted += 1
                _2p_made      += 1
            if  ( ('tiroinsospensioneda2pt' in starters_awayTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in starters_awayTeam_allPlays[i][k] or 'layupda2pt' in starters_awayTeam_allPlays[i][k]
                 or  'tiroda2ptinallontanamento' in starters_awayTeam_allPlays[i][k] or 'giroetiroda2pt' in starters_awayTeam_allPlays[i][k] or 'tiroda2ptinpenetrazione' in starters_awayTeam_allPlays[i][k]) and  
                  ('sbagliato' not in  starters_awayTeam_allPlays[i][k] and 'stoppato' not in  starters_awayTeam_allPlays[i][k]) and ('assist' in starters_awayTeam_allPlays[i][k+1]) and
                  (any(ext in starters_awayTeam_allPlays[i][k] for ext in awayTeam_startingFive_info[i][1]))  ):
                assisted_basket += 1
            
            if (('schiacciata' in starters_awayTeam_allPlays[i][k] and any(ext in starters_awayTeam_allPlays[i][k] for ext in awayTeam_startingFive_info[i][1])) or
               ('alleyoop' in starters_awayTeam_allPlays[i][k] and any(ext in starters_awayTeam_allPlays[i][k] for ext in awayTeam_startingFive_info[i][1]))) :
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            if ('schiacciata' in starters_awayTeam_allPlays[i][k] and 'assist' in starters_awayTeam_allPlays[i][k+1] and any(ext in starters_awayTeam_allPlays[i][k] for ext in awayTeam_startingFive_info[i][1]) 
            or 'alleyoop'    in starters_awayTeam_allPlays[i][k] and 'assist' in starters_awayTeam_allPlays[i][k+1] and any(ext in starters_awayTeam_allPlays[i][k] for ext in awayTeam_startingFive_info[i][1])  ):
                assisted_basket += 1
            
            if ( ('tiroda3ptinsospensione' in starters_awayTeam_allPlays[i][k] and ('sbagliato' in  starters_awayTeam_allPlays[i][k] or 'stoppato' in  starters_awayTeam_allPlays[i][k])) and
                  (any(ext in starters_awayTeam_allPlays[i][k] for ext in awayTeam_startingFive_info[i][1]))  ):
                _3p_attempted += 1
            if ( ('tiroda3ptinsospensione' in starters_awayTeam_allPlays[i][k] and ('sbagliato' not in  starters_awayTeam_allPlays[i][k] and 'stoppato' not in  starters_awayTeam_allPlays[i][k])) and
                  (any(ext in starters_awayTeam_allPlays[i][k] for ext in awayTeam_startingFive_info[i][1])) ):
                _3p_attempted += 1
                _3p_made += 1
            if ( ('tiroda3ptinsospensione' in starters_awayTeam_allPlays[i][k] and ('sbagliato' not in  starters_awayTeam_allPlays[i][k] and 'stoppato' not in  starters_awayTeam_allPlays[i][k])) and
                  (any(ext in starters_awayTeam_allPlays[i][k] for ext in awayTeam_startingFive_info[i][1]))   and 'assist' in starters_awayTeam_allPlays[i][k+1]):
                assisted_basket += 1
    
        assistedBaskets_awayTeam_startingFive.append([awayTeam_startingFive_names[i],_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,assisted_basket])
    
    # Save data to dataframe and to spreadsheet
    df_awayTeam_startingFive_assistedBaskets = pd.DataFrame(np.array(assistedBaskets_awayTeam_startingFive))
    df_awayTeam_startingFive_assistedBaskets.columns = ['Player','2pm','2pa','dunk','3pm','3pa','assisted_baskets']
    df_awayTeam_startingFive_assistedBaskets[['2pm','2pa','dunk','3pm','3pa','assisted_baskets']] = (df_awayTeam_startingFive_assistedBaskets[['2pm','2pa','dunk','3pm','3pa','assisted_baskets']].apply(pd.to_numeric))
    df_awayTeam_startingFive_assistedBaskets.to_excel(os.path.join(cwd,'homeTeam_StartingFive_assistedBaskets.xlsx'),
          sheet_name='Sheet_name_1')
    

    
    ###########################################
    # Stats for the away team bench (own stats)
    ###########################################
    # Note: the way information is retrieved is specific for the Italian League,
    # as there is no easy way to automatize the process, since every different 
    # play-by-play might have a different language and different notation.
    # If pyHoops should be used for other leagues, this part of the code 
    # (and all the equivalent parts below) should be changed accordingly
    all_stats_awayTeam_bench         = []
    for i in range(0,int(len(awayTeam_bench_jerseyNumber))):
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
        
        # For info on the different IFs, refer to code above
        for k in range(0,int(len(bench_awayTeam_allPlays[i]))):
            
                
            if ('tirolibero' in bench_awayTeam_allPlays[i][k]  and 'sbagliato' in  bench_awayTeam_allPlays[i][k]):
                _1p_attempted += 1
            if ('tirolibero' in bench_awayTeam_allPlays[i][k] and 'sbagliato' not in  bench_awayTeam_allPlays[i][k]):
                _1p_attempted += 1
                _1p_made      += 1
            if ( ('tiroinsospensioneda2pt' in bench_awayTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in bench_awayTeam_allPlays[i][k] or 'layupda2pt' in bench_awayTeam_allPlays[i][k]
                  or  'tiroda2ptinallontanamento' in bench_awayTeam_allPlays[i][k] or 'giroetiroda2pt' in bench_awayTeam_allPlays[i][k] or 'tiroda2ptinpenetrazione' in bench_awayTeam_allPlays[i][k]) and 
                  ('sbagliato' in  bench_awayTeam_allPlays[i][k] or 'stoppato' in  bench_awayTeam_allPlays[i][k])):
                _2p_attempted += 1
            if  ( ('tiroinsospensioneda2pt' in bench_awayTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in bench_awayTeam_allPlays[i][k] or 'layupda2pt' in bench_awayTeam_allPlays[i][k]
                 or  'tiroda2ptinallontanamento' in bench_awayTeam_allPlays[i][k] or 'giroetiroda2pt' in bench_awayTeam_allPlays[i][k] or 'tiroda2ptinpenetrazione' in bench_awayTeam_allPlays[i][k]) and 
                  ('sbagliato' not in  bench_awayTeam_allPlays[i][k] and 'stoppato' not in  bench_awayTeam_allPlays[i][k])):
                _2p_attempted += 1
                _2p_made      += 1
            if ('schiacciata' in bench_awayTeam_allPlays[i][k]) or ('alleyoop' in bench_awayTeam_allPlays[i][k]):
                _2p_attempted += 1
                _2p_made      += 1 
                dunk          += 1
            if ( ('tiroda3ptinsospensione' in bench_awayTeam_allPlays[i][k] and ('sbagliato' in  bench_awayTeam_allPlays[i][k] or 'stoppato' in  bench_awayTeam_allPlays[i][k]))):
                _3p_attempted += 1
            if ( ('tiroda3ptinsospensione' in bench_awayTeam_allPlays[i][k] and ('sbagliato' not in  bench_awayTeam_allPlays[i][k] and 'stoppato' not in  bench_awayTeam_allPlays[i][k]))):
                _3p_attempted += 1
                _3p_made += 1
            if 'rimbalzodifensivo' in bench_awayTeam_allPlays[i][k]:
                def_rebound += 1
            if 'rimbalzooffensivo' in bench_awayTeam_allPlays[i][k]:
                off_rebound += 1
            if 'assist' in bench_awayTeam_allPlays[i][k]:
                assist += 1
            if 'pallarecuperata' in bench_awayTeam_allPlays[i][k]:
                steal += 1
            if 'pallapersa' in bench_awayTeam_allPlays[i][k]:
                turnover += 1
            if 'stoppata' in bench_awayTeam_allPlays[i][k]:
                block_made += 1 
            if 'stoppato' in bench_awayTeam_allPlays[i][k]:
                block_received += 1 
            if 'fallosubito' in bench_awayTeam_allPlays[i][k]:
                foul_received += 1
            if ('fallo' in bench_awayTeam_allPlays[i][k] and 
               'fallosubito' not in bench_awayTeam_allPlays[i][k]):
                foul_made += 1
        all_stats_awayTeam_bench.append([awayTeam_bench_names[i],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received,timeOnCourt_bench_awayTeam[i]/60.0])
    
    # Save data to dataframe and to spreadsheet
    df_awayTeam_bench_awayTeamStats = pd.DataFrame(np.array(all_stats_awayTeam_bench))
    df_awayTeam_bench_awayTeamStats.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_awayTeam_bench_awayTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_awayTeam_bench_awayTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_awayTeam_bench_awayTeamStats.to_excel(os.path.join(cwd,'awayTeam_awayTeamStats_bench.xlsx'),
          sheet_name='Sheet_name_1')
    

    ##########################################################
    ## Stats for the away team bench (home team stats)
    ##########################################################
    ## Note: the way information is retrieved is specific for the Italian League,
    ## as there is no easy way to automatize the process, since every different 
    ## play-by-play might have a different language and different notation.
    ## If pyHoops should be used for other leagues, this part of the code 
    ## (and all the equivalent parts below) should be changed accordingly
    all_stats_awayTeam_bench_homeTeam = []
    for i in range(0,int(len(awayTeam_bench_jerseyNumber))):
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
        
        # For info on the different IFs, refer to code above
        for k in range(0,int(len(bench_awayTeam_allPlays_homeTeam[i]))):
            
                
            if ('tirolibero' in bench_awayTeam_allPlays_homeTeam[i][k]  and 'sbagliato' in  bench_awayTeam_allPlays_homeTeam[i][k]):
                _1p_attempted += 1
            if ('tirolibero' in bench_awayTeam_allPlays_homeTeam[i][k] and 'sbagliato' not in  bench_awayTeam_allPlays_homeTeam[i][k]):
                _1p_attempted += 1
                _1p_made      += 1
            if ( ('tiroinsospensioneda2pt' in bench_awayTeam_allPlays_homeTeam[i][k] or 'tiroda2ptinsospensione' in bench_awayTeam_allPlays_homeTeam[i][k] or 'layupda2pt' in bench_awayTeam_allPlays_homeTeam[i][k]
                  or  'tiroda2ptinallontanamento' in bench_awayTeam_allPlays_homeTeam[i][k] or 'giroetiroda2pt' in bench_awayTeam_allPlays_homeTeam[i][k] or 'tiroda2ptinpenetrazione' in bench_awayTeam_allPlays_homeTeam[i][k]) and 
                  ('sbagliato' in  bench_awayTeam_allPlays_homeTeam[i][k] or 'stoppato' in  bench_awayTeam_allPlays_homeTeam[i][k])):
                _2p_attempted += 1
            if  ( ('tiroinsospensioneda2pt' in bench_awayTeam_allPlays_homeTeam[i][k] or 'tiroda2ptinsospensione' in bench_awayTeam_allPlays_homeTeam[i][k] or 'layupda2pt' in bench_awayTeam_allPlays_homeTeam[i][k]
                 or  'tiroda2ptinallontanamento' in bench_awayTeam_allPlays_homeTeam[i][k] or 'giroetiroda2pt' in bench_awayTeam_allPlays_homeTeam[i][k] or 'tiroda2ptinpenetrazione' in bench_awayTeam_allPlays_homeTeam[i][k]) and 
                  ('sbagliato' not in  bench_awayTeam_allPlays_homeTeam[i][k] and 'stoppato' not in  bench_awayTeam_allPlays_homeTeam[i][k])):
                _2p_attempted += 1
                _2p_made      += 1
            if ('schiacciata' in bench_awayTeam_allPlays_homeTeam[i][k]) or ('alleyoop' in bench_awayTeam_allPlays_homeTeam[i][k]):
                _2p_attempted += 1
                _2p_made      += 1 
                dunk          += 1
            if ( ('tiroda3ptinsospensione' in bench_awayTeam_allPlays_homeTeam[i][k] and ('sbagliato' in  bench_awayTeam_allPlays_homeTeam[i][k] or 'stoppato' in  bench_awayTeam_allPlays_homeTeam[i][k]))):
                _3p_attempted += 1
            if ( ('tiroda3ptinsospensione' in bench_awayTeam_allPlays_homeTeam[i][k] and ('sbagliato' not in  bench_awayTeam_allPlays_homeTeam[i][k] and 'stoppato' not in  bench_awayTeam_allPlays_homeTeam[i][k]))):
                _3p_attempted += 1
                _3p_made += 1
            if 'rimbalzodifensivo' in bench_awayTeam_allPlays_homeTeam[i][k]:
                def_rebound += 1
            if 'rimbalzooffensivo' in bench_awayTeam_allPlays_homeTeam[i][k]:
                off_rebound += 1
            if 'assist' in bench_awayTeam_allPlays_homeTeam[i][k]:
                assist += 1
            if 'pallarecuperata' in bench_awayTeam_allPlays_homeTeam[i][k]:
                steal += 1
            if 'pallapersa' in bench_awayTeam_allPlays_homeTeam[i][k]:
                turnover += 1
            if 'stoppata' in bench_awayTeam_allPlays_homeTeam[i][k]:
                block_made += 1 
            if 'stoppato' in bench_awayTeam_allPlays_homeTeam[i][k]:
                block_received += 1 
            if 'fallosubito' in bench_awayTeam_allPlays_homeTeam[i][k]:
                foul_received += 1
            if ('fallo' in bench_awayTeam_allPlays_homeTeam[i][k] and 
               'fallosubito' not in bench_awayTeam_allPlays_homeTeam[i][k]):
                foul_made += 1
        all_stats_awayTeam_bench_homeTeam.append([awayTeam_bench_names[i],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received,timeOnCourt_bench_awayTeam[i]/60.0])
    
    # Save data to dataframe and to spreadsheet
    df_awayTeam_bench_homeTeamStats = pd.DataFrame(np.array(all_stats_awayTeam_bench_homeTeam))
    df_awayTeam_bench_homeTeamStats.columns = ['Player','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_awayTeam_bench_homeTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_awayTeam_bench_homeTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_awayTeam_bench_homeTeamStats.to_excel(os.path.join(cwd,'awayTeam_homeTeamStats_bench.xlsx'),
          sheet_name='Sheet_name_1')
    

    
    # Determine for each player how many baskets were assisted
    assistedBaskets_awayTeam_bench         = []
    for i in range(0,int(len(awayTeam_bench_jerseyNumber))):
        _2p_made                  = 0
        _2p_attempted             = 0
        dunk                      = 0
        _3p_made                  = 0
        _3p_attempted             = 0
        assisted_basket           = 0
    
        # For info on the different IFs, refer to code above
        for k in range(0,int(len(bench_awayTeam_allPlays[i])-1)):
            if ( ('tiroinsospensioneda2pt' in bench_awayTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in bench_awayTeam_allPlays[i][k] or 'layupda2pt' in bench_awayTeam_allPlays[i][k]
                  or  'tiroda2ptinallontanamento' in bench_awayTeam_allPlays[i][k] or 'giroetiroda2pt' in bench_awayTeam_allPlays[i][k] or 'tiroda2ptinpenetrazione' in bench_awayTeam_allPlays[i][k]) and 
                  ('sbagliato' in  bench_awayTeam_allPlays[i][k] or 'stoppato' in  bench_awayTeam_allPlays[i][k]) and
                  (any(ext in bench_awayTeam_allPlays[i][k] for ext in awayTeam_bench_info[i][1])) ):
                _2p_attempted += 1
            if  ( ('tiroinsospensioneda2pt' in bench_awayTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in bench_awayTeam_allPlays[i][k] or 'layupda2pt' in bench_awayTeam_allPlays[i][k]
                 or  'tiroda2ptinallontanamento' in bench_awayTeam_allPlays[i][k] or 'giroetiroda2pt' in bench_awayTeam_allPlays[i][k] or 'tiroda2ptinpenetrazione' in bench_awayTeam_allPlays[i][k]) and 
                  ('sbagliato' not in  bench_awayTeam_allPlays[i][k] and 'stoppato' not in  bench_awayTeam_allPlays[i][k]) and
                  (any(ext in bench_awayTeam_allPlays[i][k] for ext in awayTeam_bench_info[i][1])) ):
                _2p_attempted += 1
                _2p_made      += 1
            if  ( ('tiroinsospensioneda2pt' in bench_awayTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in bench_awayTeam_allPlays[i][k] or 'layupda2pt' in bench_awayTeam_allPlays[i][k]
                 or  'tiroda2ptinallontanamento' in bench_awayTeam_allPlays[i][k] or 'giroetiroda2pt' in bench_awayTeam_allPlays[i][k] or 'tiroda2ptinpenetrazione' in bench_awayTeam_allPlays[i][k]) and  
                  ('sbagliato' not in  bench_awayTeam_allPlays[i][k] and 'stoppato' not in  bench_awayTeam_allPlays[i][k]) and ('assist' in bench_awayTeam_allPlays[i][k+1]) and
                  (any(ext in bench_awayTeam_allPlays[i][k] for ext in awayTeam_bench_info[i][1])) ):
                assisted_basket += 1
            if ('schiacciata' in bench_awayTeam_allPlays[i][k]) and (awayTeam_bench_names[i] in bench_awayTeam_allPlays[i][k] and
                  awayTeam_bench_names[i] in bench_awayTeam_allPlays[i][k]) or ('alleyoop' in bench_awayTeam_allPlays[i][k]) and ((any(ext in bench_awayTeam_allPlays[i][k] for ext in awayTeam_bench_info[i][1]))):
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            if ( ('schiacciata' in bench_awayTeam_allPlays[i][k]) and ('assist' in bench_awayTeam_allPlays[i][k+1]) and (awayTeam_bench_names[i] in bench_awayTeam_allPlays[i][k])  or
                 ('alleyoop' in bench_awayTeam_allPlays[i][k])    and ('assist' in bench_awayTeam_allPlays[i][k+1]) and (any(ext in bench_awayTeam_allPlays[i][k] for ext in awayTeam_bench_info[i][1])) ):
                assisted_basket += 1
            if ( 'tiroda3ptinsospensione' in bench_awayTeam_allPlays[i][k] and ('sbagliato' in  bench_awayTeam_allPlays[i][k] or 'stoppato' in  bench_awayTeam_allPlays[i][k]) and
                  (any(ext in bench_awayTeam_allPlays[i][k] for ext in awayTeam_bench_info[i][1])) ):
                _3p_attempted += 1
            if ( 'tiroda3ptinsospensione' in bench_awayTeam_allPlays[i][k] and ('sbagliato' not in  bench_awayTeam_allPlays[i][k] and 'stoppato' not in  bench_awayTeam_allPlays[i][k]) and
                  (any(ext in bench_awayTeam_allPlays[i][k] for ext in awayTeam_bench_info[i][1])) ):
                _3p_attempted += 1
                _3p_made += 1
            if ( ('tiroda3ptinsospensione' in bench_awayTeam_allPlays[i][k] and ('sbagliato' not in  bench_awayTeam_allPlays[i][k] and 'stoppato' not in  bench_awayTeam_allPlays[i][k])) and
                  (any(ext in bench_awayTeam_allPlays[i][k] for ext in awayTeam_bench_info[i][1])) and 'assist' in bench_awayTeam_allPlays[i][k+1]):
                assisted_basket += 1
    
        assistedBaskets_awayTeam_bench.append([awayTeam_bench_names[i],_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,assisted_basket])
    
    # Save data to dataframe and to spreadsheet
    df_awayTeam_bench_assistedBaskets = pd.DataFrame(np.array(assistedBaskets_awayTeam_bench))
    df_awayTeam_bench_assistedBaskets.columns = ['Player','2pm','2pa','dunk','3pm','3pa','assisted_baskets']
    df_awayTeam_bench_assistedBaskets[['2pm','2pa','dunk','3pm','3pa','assisted_baskets']] = (df_awayTeam_bench_assistedBaskets[['2pm','2pa','dunk','3pm','3pa','assisted_baskets']].apply(pd.to_numeric))
    df_awayTeam_bench_assistedBaskets.to_excel(os.path.join(cwd,'awayTeam_Bench_assistedBaskets.xlsx'),
          sheet_name='Sheet_name_1')
    
    # Merge starting five and bench info for away team
    df_awayTeam_startingPlusBench_awayTeamStats = pd.concat([df_awayTeam_startingFive_awayTeamStats,
                                                        df_awayTeam_bench_awayTeamStats], ignore_index=True)
    df_awayTeam_startingPlusBench_homeTeamStats = pd.concat([df_awayTeam_startingFive_homeTeamStats,
                                                        df_awayTeam_bench_homeTeamStats], ignore_index=True)
    df_awayTeam_startingPlusBench_assistedBaskets = pd.concat([df_awayTeam_startingFive_assistedBaskets,
                                                        df_awayTeam_bench_assistedBaskets], ignore_index=True)
                
    return (df_awayTeam_startingPlusBench_awayTeamStats,
           df_awayTeam_startingPlusBench_homeTeamStats,
           df_awayTeam_startingPlusBench_assistedBaskets,
           awayTeam_startingFive_names,awayTeam_startingFive_info,
           awayTeam_bench_names,awayTeam_bench_info,
           orig_idx_starting_five_awayTeam,orig_idx_bench_awayTeam)
    
def get_homeTeam_stats_perLineup(df_pbp,dfHomeTeam,homeTeam_startingFive_names,
                                 homeTeam_startingFive_info,homeTeam_bench_names,
                                 homeTeam_bench_info,minutes_in_quarter,
                                 cwd): 
    all_lineups    = []
    all_lineups.append([homeTeam_startingFive_names,0])
    current_lineup = deepcopy(homeTeam_startingFive_names)
    current_lineup_allNames = []
    for i in range(0,int(len(homeTeam_startingFive_names))):
        current_lineup_allNames.append(homeTeam_startingFive_info[i][1])
    current_bench  = deepcopy(homeTeam_bench_names)
    current_bench_allNames = []
    for i in range(0,int(len(homeTeam_bench_names))):
        current_bench_allNames.append(homeTeam_bench_info[i][1])
    
    # Cycle through the play by play for the home team, and look for all rows
    # where two players  (one from current lineup, one from current bench) 
    # are mentioned together. In such a case, the first player
    # is the player exiting the game, the second player is the player entering the game
    for i in range(0,int(len(df_pbp['Home_action']))):
        player_out_flag = 0
        for cont_1 in range(0,int(len(current_lineup))):
            if (any(ext in df_pbp['Home_action'][i] for ext in current_lineup_allNames[cont_1])):
                player_out          = current_lineup[cont_1]
                player_out_allNames = current_lineup_allNames[cont_1]
                player_out_flag = 1
                break
        player_in_flag = 0
        for cont_2 in range(0,int(len(current_bench))):
            if (any(ext in df_pbp['Home_action'][i] for ext in current_bench_allNames[cont_2])):
                player_in          = current_bench[cont_2]
                player_in_allNames = current_bench_allNames[cont_2]
                player_in_flag = 1
                break
        # If both a current lineup player and a bench player are found, there is
        # a change in the lineup
        if player_out_flag*player_in_flag == 1:
            temp_current_lineup          = []
            temp_current_lineup_allNames = []
            for j in range(0,int(len(homeTeam_startingFive_names))):
                if j != cont_1:
                    temp_current_lineup.append(current_lineup[j])
                    temp_current_lineup_allNames.append(current_lineup_allNames[j])
            temp_current_lineup.append(player_in)
            temp_current_lineup_allNames.append(player_in_allNames)
            temp_current_bench          = []
            temp_current_bench_allNames = []
            for j in range(0,int(len(homeTeam_bench_names))):
                if j != cont_2:
                    temp_current_bench.append(current_bench[j])
                    temp_current_bench_allNames.append(current_bench_allNames[j])
            temp_current_bench.append(player_out)
            temp_current_bench_allNames.append(player_out_allNames) 
            
            current_lineup = deepcopy(temp_current_lineup)
            current_lineup_allNames = deepcopy(temp_current_lineup_allNames)
            current_bench = deepcopy(temp_current_bench)
            current_bench_allNames = deepcopy(temp_current_bench_allNames)
            
            all_lineups.append([current_lineup,i])
    
    # Compute time of pay for each lineup
    time_of_play_lineup = []        
    for i in range(0,int(len(all_lineups))):
        if i != int(len(all_lineups)-1):
            
            if i == 0:
            
                first_index  = 0
                second_index = all_lineups[i+1][1]
                
                in_quarter  = 1
                out_quarter = int(df_pbp['quarter_of_game'][second_index][1])
                in_time     = (in_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(df_pbp['time_of_game'][first_index][0:2])*60+
                                                                   int(df_pbp['time_of_game'][first_index][3:5])))
                out_time    = (out_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(df_pbp['time_of_game'][second_index][0:2])*60+
                                                                   int(df_pbp['time_of_game'][second_index][3:5]))) 
                this_timeOnCourt = out_time - in_time
                
            else:
                
                first_index  = all_lineups[i][1]
                second_index = all_lineups[i+1][1]
                
                in_quarter  = int(df_pbp['quarter_of_game'][first_index][1])
                out_quarter = int(df_pbp['quarter_of_game'][second_index][1])
                in_time     = (in_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(df_pbp['time_of_game'][first_index][0:2])*60+
                                                                   int(df_pbp['time_of_game'][first_index][3:5])))
                out_time    = (out_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(df_pbp['time_of_game'][second_index][0:2])*60+
                                                                   int(df_pbp['time_of_game'][second_index][3:5]))) 
                this_timeOnCourt = out_time - in_time
                
        else:
            
            first_index  = all_lineups[i][1]
            second_index = int(len(df_pbp['Home_action'])-1)
            
            in_quarter  = int(df_pbp['quarter_of_game'][first_index][1])
            out_quarter = 4
            in_time     = (in_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(df_pbp['time_of_game'][first_index][0:2])*60+
                                                               int(df_pbp['time_of_game'][first_index][3:5])))
            out_time    = (out_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(df_pbp['time_of_game'][second_index][0:2])*60+
                                                               int(df_pbp['time_of_game'][second_index][3:5]))) 
            this_timeOnCourt = out_time - in_time
            
        time_of_play_lineup.append(this_timeOnCourt)
    
    # Sometimes, if multiple lineup changes happen simultaneously, they are recorded in consecutive lines
    # of the play by play. In such a case, the "intermediate" lineups would dispaly a time of
    # play of 0 seconds, and hence should be discarded. In other words, we want to make sure
    # that if multiple changes occur, only the lineup accounting for all the simultaneous
    # changes will be added    
    all_lineups_homeTeam_filtered = []
    for i in range(0,int(len(all_lineups))):
        if time_of_play_lineup[i] > 0:
            all_lineups_homeTeam_filtered.append([all_lineups[i][0],time_of_play_lineup[i],all_lineups[i][1]])
    
    time_overall = 0
    for i in range(0,int(len(all_lineups_homeTeam_filtered))):
        time_overall += all_lineups_homeTeam_filtered[i][1]
           
    lineups_homeTeam_allPlays = []   
    for i in range(0,int(len(all_lineups_homeTeam_filtered))):
        if i != int(len(all_lineups_homeTeam_filtered)-1):
            lineups_homeTeam_allPlays.append(list(df_pbp['Home_action'][all_lineups_homeTeam_filtered[i][2]:all_lineups_homeTeam_filtered[i+1][2]]))
        else:
            lineups_homeTeam_allPlays.append(list(df_pbp['Home_action'][all_lineups_homeTeam_filtered[i][2]:int(len(df_pbp['Home_action']))]))
    
    lineups_homeTeam_allPlays_awayTeam = []   
    for i in range(0,int(len(all_lineups_homeTeam_filtered))):
        if i != int(len(all_lineups_homeTeam_filtered)-1):
            lineups_homeTeam_allPlays_awayTeam.append(list(df_pbp['Away_action'][all_lineups_homeTeam_filtered[i][2]:all_lineups_homeTeam_filtered[i+1][2]]))
        else:
            lineups_homeTeam_allPlays_awayTeam.append(list(df_pbp['Away_action'][all_lineups_homeTeam_filtered[i][2]:int(len(df_pbp['Away_action']))]))
    
    
    for i in range(0,int(len(all_lineups_homeTeam_filtered))):
        for j in range(0,int(len(all_lineups_homeTeam_filtered[i][0]))):
            all_lineups_homeTeam_filtered[i][0][j] = str(all_lineups_homeTeam_filtered[i][0][j])
        
    homeTeam_lineups_sorted     = []
    for i in range(0,int(len(all_lineups_homeTeam_filtered))):
        this_lineup        = all_lineups_homeTeam_filtered[i][0]
        this_lineup_sorted = sorted(this_lineup)
        homeTeam_lineups_sorted.append(this_lineup_sorted)
    
    # Some lineups might appear multiple times during the game (e.g., the
    # starting five). Here, we store all the indices of repeated lineups as 
    # they appear thoughout the game. As an example, if a specific lineup
    # is associated with indices 0 (starting lineup then), 5, 10, 13, it means
    # it appeared on the floor as the first, sixth, eleventh, and fourteenth
    # distinct lineup
    idx_unique_lineups_homeTeam = []
    for i in range(0,int(len(homeTeam_lineups_sorted))):
        this_lineup_idx = []
        for j in range(0,int(len(homeTeam_lineups_sorted))):
            if homeTeam_lineups_sorted[j] == homeTeam_lineups_sorted[i]:
                this_lineup_idx.append(j)
        idx_unique_lineups_homeTeam.append(this_lineup_idx)
    
    if max(len(l) for l in idx_unique_lineups_homeTeam) > 1:
        idx_unique_lineups_homeTeam  = list(np.unique(np.array(idx_unique_lineups_homeTeam)))
    
    all_stats_homeTeam_lineups_homeTeam = []
    for i in range(0,int(len(lineups_homeTeam_allPlays))):
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
        
        for k in range(0,int(len(lineups_homeTeam_allPlays[i]))):
            
                
            if ('tirolibero' in lineups_homeTeam_allPlays[i][k]  and 'sbagliato' in  lineups_homeTeam_allPlays[i][k]):
                _1p_attempted += 1
            if ('tirolibero' in lineups_homeTeam_allPlays[i][k] and 'sbagliato' not in  lineups_homeTeam_allPlays[i][k]):
                _1p_attempted += 1
                _1p_made      += 1
            if ( ('tiroinsospensioneda2pt' in lineups_homeTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in lineups_homeTeam_allPlays[i][k] or 'layupda2pt' in lineups_homeTeam_allPlays[i][k]
                  or  'tiroda2ptinallontanamento' in lineups_homeTeam_allPlays[i][k] or 'giroetiroda2pt' in lineups_homeTeam_allPlays[i][k] or 'tiroda2ptinpenetrazione' in lineups_homeTeam_allPlays[i][k]) and 
                  ('sbagliato' in  lineups_homeTeam_allPlays[i][k] or 'stoppato' in  lineups_homeTeam_allPlays[i][k])):
                _2p_attempted += 1
            if  ( ('tiroinsospensioneda2pt' in lineups_homeTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in lineups_homeTeam_allPlays[i][k] or 'layupda2pt' in lineups_homeTeam_allPlays[i][k]
                 or  'tiroda2ptinallontanamento' in lineups_homeTeam_allPlays[i][k] or 'giroetiroda2pt' in lineups_homeTeam_allPlays[i][k] or 'tiroda2ptinpenetrazione' in lineups_homeTeam_allPlays[i][k]) and 
                  ('sbagliato' not in  lineups_homeTeam_allPlays[i][k] and 'stoppato' not in  lineups_homeTeam_allPlays[i][k])):
                _2p_attempted += 1
                _2p_made      += 1
            if ('schiacciata' in lineups_homeTeam_allPlays[i][k]) or ('alleyoop' in lineups_homeTeam_allPlays[i][k]):
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            if ( ('tiroda3ptinsospensione' in lineups_homeTeam_allPlays[i][k] and ('sbagliato' in  lineups_homeTeam_allPlays[i][k] or 'stoppato' in  lineups_homeTeam_allPlays[i][k]))):
                _3p_attempted += 1
            if ( ('tiroda3ptinsospensione' in lineups_homeTeam_allPlays[i][k] and ('sbagliato' not in  lineups_homeTeam_allPlays[i][k] and 'stoppato' not in  lineups_homeTeam_allPlays[i][k]))):
                _3p_attempted += 1
                _3p_made += 1
            if 'rimbalzodifensivo' in lineups_homeTeam_allPlays[i][k]:
                def_rebound += 1
            if 'rimbalzooffensivo' in lineups_homeTeam_allPlays[i][k]:
                off_rebound += 1
            if 'assist' in lineups_homeTeam_allPlays[i][k]:
                assist += 1
            if 'pallarecuperata' in lineups_homeTeam_allPlays[i][k]:
                steal += 1
            if 'pallapersa' in lineups_homeTeam_allPlays[i][k]:
                turnover += 1
            if 'stoppata' in lineups_homeTeam_allPlays[i][k]:
                block_made += 1 
            if 'stoppato' in lineups_homeTeam_allPlays[i][k]:
                block_received += 1 
            if 'fallosubito' in lineups_homeTeam_allPlays[i][k]:
                foul_received += 1
            if ('fallo' in lineups_homeTeam_allPlays[i][k] and 
               'fallosubito' not in lineups_homeTeam_allPlays[i][k]):
                foul_made += 1
        all_stats_homeTeam_lineups_homeTeam.append([homeTeam_lineups_sorted[i],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received,all_lineups_homeTeam_filtered[i][1]/60.0])
    
    # Save data to dataframe and to spreadsheet
    df_homeTeam_lineups_homeTeamStats = pd.DataFrame(np.array(all_stats_homeTeam_lineups_homeTeam))
    df_homeTeam_lineups_homeTeamStats.columns = ['Lineup','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_homeTeam_lineups_homeTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_homeTeam_lineups_homeTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_homeTeam_lineups_homeTeamStats.to_excel(os.path.join(cwd,'homeTeam_homeTeamStats_lineups.xlsx'),
          sheet_name='Sheet_name_1')    
    
    # Merge rows that refer to the same lineup
    all_stats_homeTeam_lineups_homeTeam_merged = []
    for i in range(0,int(len(idx_unique_lineups_homeTeam))):
        idx_this_lineup   = idx_unique_lineups_homeTeam[i]
        stats_this_lineup = np.zeros([1,len(df_homeTeam_lineups_homeTeamStats.loc[0][1:])])
        for j in range(0,int(len(idx_this_lineup))):
            stats_this_lineup = stats_this_lineup + np.array(df_homeTeam_lineups_homeTeamStats.loc[idx_this_lineup[j]][1:])
        stats_this_lineup = list(stats_this_lineup[0])
        stats_this_lineup = [df_homeTeam_lineups_homeTeamStats.loc[idx_this_lineup[0]][0]]+stats_this_lineup
        all_stats_homeTeam_lineups_homeTeam_merged.append(stats_this_lineup)
    
    df_homeTeam_lineups_homeTeamStats_merged = pd.DataFrame(np.array(all_stats_homeTeam_lineups_homeTeam_merged))
    df_homeTeam_lineups_homeTeamStats_merged.columns = ['Lineup','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_homeTeam_lineups_homeTeamStats_merged[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_homeTeam_lineups_homeTeamStats_merged[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_homeTeam_lineups_homeTeamStats_merged.to_excel(os.path.join(cwd,'homeTeam_homeTeamStats_lineups_merged.xlsx'),
          sheet_name='Sheet_name_1') 
    all_stats_homeTeam_lineups_awayTeam = []
    for i in range(0,int(len(lineups_homeTeam_allPlays_awayTeam))):
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
        
        for k in range(0,int(len(lineups_homeTeam_allPlays_awayTeam[i]))):
            
                
            if ('tirolibero' in lineups_homeTeam_allPlays_awayTeam[i][k]  and 'sbagliato' in  lineups_homeTeam_allPlays_awayTeam[i][k]):
                _1p_attempted += 1
            if ('tirolibero' in lineups_homeTeam_allPlays_awayTeam[i][k] and 'sbagliato' not in  lineups_homeTeam_allPlays_awayTeam[i][k]):
                _1p_attempted += 1
                _1p_made      += 1
            if ( ('tiroinsospensioneda2pt' in lineups_homeTeam_allPlays_awayTeam[i][k] or 'tiroda2ptinsospensione' in lineups_homeTeam_allPlays_awayTeam[i][k] or 'layupda2pt' in lineups_homeTeam_allPlays_awayTeam[i][k]
                  or  'tiroda2ptinallontanamento' in lineups_homeTeam_allPlays_awayTeam[i][k] or 'giroetiroda2pt' in lineups_homeTeam_allPlays_awayTeam[i][k] or 'tiroda2ptinpenetrazione' in lineups_homeTeam_allPlays_awayTeam[i][k]) and 
                  ('sbagliato' in  lineups_homeTeam_allPlays_awayTeam[i][k] or 'stoppato' in  lineups_homeTeam_allPlays_awayTeam[i][k])):
                _2p_attempted += 1
            if  ( ('tiroinsospensioneda2pt' in lineups_homeTeam_allPlays_awayTeam[i][k] or 'tiroda2ptinsospensione' in lineups_homeTeam_allPlays_awayTeam[i][k] or 'layupda2pt' in lineups_homeTeam_allPlays_awayTeam[i][k]
                 or  'tiroda2ptinallontanamento' in lineups_homeTeam_allPlays_awayTeam[i][k] or 'giroetiroda2pt' in lineups_homeTeam_allPlays_awayTeam[i][k] or 'tiroda2ptinpenetrazione' in lineups_homeTeam_allPlays_awayTeam[i][k]) and 
                  ('sbagliato' not in  lineups_homeTeam_allPlays_awayTeam[i][k] and 'stoppato' not in  lineups_homeTeam_allPlays_awayTeam[i][k])):
                _2p_attempted += 1
                _2p_made      += 1
            if ('schiacciata' in lineups_homeTeam_allPlays_awayTeam[i][k]) or ('alleyoop' in lineups_homeTeam_allPlays_awayTeam[i][k]):
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            if ( ('tiroda3ptinsospensione' in lineups_homeTeam_allPlays_awayTeam[i][k] and ('sbagliato' in  lineups_homeTeam_allPlays_awayTeam[i][k] or 'stoppato' in  lineups_homeTeam_allPlays_awayTeam[i][k]))):
                _3p_attempted += 1
            if ( ('tiroda3ptinsospensione' in lineups_homeTeam_allPlays_awayTeam[i][k] and ('sbagliato' not in  lineups_homeTeam_allPlays_awayTeam[i][k] and 'stoppato' not in  lineups_homeTeam_allPlays_awayTeam[i][k]))):
                _3p_attempted += 1
                _3p_made += 1
            if 'rimbalzodifensivo' in lineups_homeTeam_allPlays_awayTeam[i][k]:
                def_rebound += 1
            if 'rimbalzooffensivo' in lineups_homeTeam_allPlays_awayTeam[i][k]:
                off_rebound += 1
            if 'assist' in lineups_homeTeam_allPlays_awayTeam[i][k]:
                assist += 1
            if 'pallarecuperata' in lineups_homeTeam_allPlays_awayTeam[i][k]:
                steal += 1
            if 'pallapersa' in lineups_homeTeam_allPlays_awayTeam[i][k]:
                turnover += 1
            if 'stoppata' in lineups_homeTeam_allPlays_awayTeam[i][k]:
                block_made += 1 
            if 'stoppato' in lineups_homeTeam_allPlays_awayTeam[i][k]:
                block_received += 1 
            if 'fallosubito' in lineups_homeTeam_allPlays_awayTeam[i][k]:
                foul_received += 1
            if ('fallo' in lineups_homeTeam_allPlays_awayTeam[i][k] and 
               'fallosubito' not in lineups_homeTeam_allPlays_awayTeam[i][k]):
                foul_made += 1
        all_stats_homeTeam_lineups_awayTeam.append([homeTeam_lineups_sorted[i],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received,all_lineups_homeTeam_filtered[i][1]/60.0])
    
    # Save data to dataframe and to spreadsheet
    df_homeTeam_lineups_awayTeamStats = pd.DataFrame(np.array(all_stats_homeTeam_lineups_awayTeam))
    df_homeTeam_lineups_awayTeamStats.columns = ['Lineup','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_homeTeam_lineups_awayTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_homeTeam_lineups_awayTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_homeTeam_lineups_awayTeamStats.to_excel(os.path.join(cwd,'homeTeam_awayTeamStats_lineups.xlsx'),
          sheet_name='Sheet_name_1')    
    
    # Merge rows that refer to the same lineup
    all_stats_homeTeam_lineups_awayTeam_merged = []
    for i in range(0,int(len(idx_unique_lineups_homeTeam))):
        idx_this_lineup   = idx_unique_lineups_homeTeam[i]
        stats_this_lineup = np.zeros([1,len(df_homeTeam_lineups_awayTeamStats.loc[0][1:])])
        for j in range(0,int(len(idx_this_lineup))):
            stats_this_lineup = stats_this_lineup + np.array(df_homeTeam_lineups_awayTeamStats.loc[idx_this_lineup[j]][1:])
        stats_this_lineup = list(stats_this_lineup[0])
        stats_this_lineup = [df_homeTeam_lineups_awayTeamStats.loc[idx_this_lineup[0]][0]]+stats_this_lineup
        all_stats_homeTeam_lineups_awayTeam_merged.append(stats_this_lineup)
    
    df_homeTeam_lineups_awayTeamStats_merged = pd.DataFrame(np.array(all_stats_homeTeam_lineups_awayTeam_merged))
    df_homeTeam_lineups_awayTeamStats_merged.columns = ['Lineup','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_homeTeam_lineups_awayTeamStats_merged[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_homeTeam_lineups_awayTeamStats_merged[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_homeTeam_lineups_awayTeamStats_merged.to_excel(os.path.join(cwd,'homeTeam_awayTeamStats_lineups_merged.xlsx'),
          sheet_name='Sheet_name_1')
    
    return df_homeTeam_lineups_homeTeamStats_merged,df_homeTeam_lineups_awayTeamStats_merged

def get_awayTeam_stats_perLineup(df_pbp,dfAwayTeam,awayTeam_startingFive_names,
                                 awayTeam_startingFive_info,awayTeam_bench_names,
                                 awayTeam_bench_info,minutes_in_quarter,
                                 cwd): 
    all_lineups    = []
    all_lineups.append([awayTeam_startingFive_names,0])
    current_lineup = deepcopy(awayTeam_startingFive_names)
    current_lineup_allNames = []
    for i in range(0,int(len(awayTeam_startingFive_names))):
        current_lineup_allNames.append(awayTeam_startingFive_info[i][1])
    current_bench  = deepcopy(awayTeam_bench_names)
    current_bench_allNames = []
    for i in range(0,int(len(awayTeam_bench_names))):
        current_bench_allNames.append(awayTeam_bench_info[i][1])
    
    for i in range(0,int(len(df_pbp['Away_action']))):
        player_out_flag = 0
        for cont_1 in range(0,int(len(current_lineup))):
            if (any(ext in df_pbp['Away_action'][i] for ext in current_lineup_allNames[cont_1])):
                player_out          = current_lineup[cont_1]
                player_out_allNames = current_lineup_allNames[cont_1]
                player_out_flag = 1
                break
        player_in_flag = 0
        for cont_2 in range(0,int(len(current_bench))):
            if (any(ext in df_pbp['Away_action'][i] for ext in current_bench_allNames[cont_2])):
                player_in          = current_bench[cont_2]
                player_in_allNames = current_bench_allNames[cont_2]
                player_in_flag = 1
                break
        if player_out_flag*player_in_flag == 1:
            temp_current_lineup          = []
            temp_current_lineup_allNames = []
            for j in range(0,int(len(awayTeam_startingFive_names))):
                if j != cont_1:
                    temp_current_lineup.append(current_lineup[j])
                    temp_current_lineup_allNames.append(current_lineup_allNames[j])
            temp_current_lineup.append(player_in)
            temp_current_lineup_allNames.append(player_in_allNames)
            temp_current_bench          = []
            temp_current_bench_allNames = []
            for j in range(0,int(len(awayTeam_bench_names))):
                if j != cont_2:
                    temp_current_bench.append(current_bench[j])
                    temp_current_bench_allNames.append(current_bench_allNames[j])
            temp_current_bench.append(player_out)
            temp_current_bench_allNames.append(player_out_allNames) 
            
            current_lineup = deepcopy(temp_current_lineup)
            current_lineup_allNames = deepcopy(temp_current_lineup_allNames)
            current_bench = deepcopy(temp_current_bench)
            current_bench_allNames = deepcopy(temp_current_bench_allNames)
            
            all_lineups.append([current_lineup,i])
    
    time_of_play_lineup = []        
    for i in range(0,int(len(all_lineups))):
        if i != int(len(all_lineups)-1):
            
            if i == 0:
            
                first_index  = 0
                second_index = all_lineups[i+1][1]
                
                in_quarter  = 1
                out_quarter = int(df_pbp['quarter_of_game'][second_index][1])
                in_time     = (in_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(df_pbp['time_of_game'][first_index][0:2])*60+
                                                                   int(df_pbp['time_of_game'][first_index][3:5])))
                out_time    = (out_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(df_pbp['time_of_game'][second_index][0:2])*60+
                                                                   int(df_pbp['time_of_game'][second_index][3:5]))) 
                this_timeOnCourt = out_time - in_time
                
            else:
                
                first_index  = all_lineups[i][1]
                second_index = all_lineups[i+1][1]
                
                in_quarter  = int(df_pbp['quarter_of_game'][first_index][1])
                out_quarter = int(df_pbp['quarter_of_game'][second_index][1])
                in_time     = (in_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(df_pbp['time_of_game'][first_index][0:2])*60+
                                                                   int(df_pbp['time_of_game'][first_index][3:5])))
                out_time    = (out_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(df_pbp['time_of_game'][second_index][0:2])*60+
                                                                   int(df_pbp['time_of_game'][second_index][3:5]))) 
                this_timeOnCourt = out_time - in_time
                
        else:
            
            first_index  = all_lineups[i][1]
            second_index = int(len(df_pbp['Away_action'])-1)
            
            in_quarter  = int(df_pbp['quarter_of_game'][first_index][1])
            out_quarter = 4
            in_time     = (in_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(df_pbp['time_of_game'][first_index][0:2])*60+
                                                               int(df_pbp['time_of_game'][first_index][3:5])))
            out_time    = (out_quarter-1)*minutes_in_quarter*60 + (minutes_in_quarter*60-(int(df_pbp['time_of_game'][second_index][0:2])*60+
                                                               int(df_pbp['time_of_game'][second_index][3:5]))) 
            this_timeOnCourt = out_time - in_time
            
        time_of_play_lineup.append(this_timeOnCourt)
        
    all_lineups_awayTeam_filtered = []
    for i in range(0,int(len(all_lineups))):
        if time_of_play_lineup[i] > 0:
            all_lineups_awayTeam_filtered.append([all_lineups[i][0],time_of_play_lineup[i],all_lineups[i][1]])
    
    time_overall = 0
    for i in range(0,int(len(all_lineups_awayTeam_filtered))):
        time_overall += all_lineups_awayTeam_filtered[i][1]
           
    lineups_awayTeam_allPlays = []   
    for i in range(0,int(len(all_lineups_awayTeam_filtered))):
        if i != int(len(all_lineups_awayTeam_filtered)-1):
            lineups_awayTeam_allPlays.append(list(df_pbp['Away_action'][all_lineups_awayTeam_filtered[i][2]:all_lineups_awayTeam_filtered[i+1][2]]))
        else:
            lineups_awayTeam_allPlays.append(list(df_pbp['Away_action'][all_lineups_awayTeam_filtered[i][2]:int(len(df_pbp['Away_action']))]))
    
    lineups_awayTeam_allPlays_homeTeam = []   
    for i in range(0,int(len(all_lineups_awayTeam_filtered))):
        if i != int(len(all_lineups_awayTeam_filtered)-1):
            lineups_awayTeam_allPlays_homeTeam.append(list(df_pbp['Home_action'][all_lineups_awayTeam_filtered[i][2]:all_lineups_awayTeam_filtered[i+1][2]]))
        else:
            lineups_awayTeam_allPlays_homeTeam.append(list(df_pbp['Home_action'][all_lineups_awayTeam_filtered[i][2]:int(len(df_pbp['Home_action']))]))
    
    
    for i in range(0,int(len(all_lineups_awayTeam_filtered))):
        for j in range(0,int(len(all_lineups_awayTeam_filtered[i][0]))):
            all_lineups_awayTeam_filtered[i][0][j] = str(all_lineups_awayTeam_filtered[i][0][j])
        
    awayTeam_lineups_sorted     = []
    for i in range(0,int(len(all_lineups_awayTeam_filtered))):
        this_lineup        = all_lineups_awayTeam_filtered[i][0]
        this_lineup_sorted = sorted(this_lineup)
        awayTeam_lineups_sorted.append(this_lineup_sorted)
    
    idx_unique_lineups_awayTeam = []
    for i in range(0,int(len(awayTeam_lineups_sorted))):
        this_lineup_idx = []
        for j in range(0,int(len(awayTeam_lineups_sorted))):
            if awayTeam_lineups_sorted[j] == awayTeam_lineups_sorted[i]:
                this_lineup_idx.append(j)
        idx_unique_lineups_awayTeam.append(this_lineup_idx)
    
    if max(len(l) for l in idx_unique_lineups_awayTeam) > 1:
        idx_unique_lineups_awayTeam  = list(np.unique(np.array(idx_unique_lineups_awayTeam)))
    
    
    all_stats_awayTeam_lineups_awayTeam = []
    for i in range(0,int(len(lineups_awayTeam_allPlays))):
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
        
        for k in range(0,int(len(lineups_awayTeam_allPlays[i]))):
            
                
            if ('tirolibero' in lineups_awayTeam_allPlays[i][k]  and 'sbagliato' in  lineups_awayTeam_allPlays[i][k]):
                _1p_attempted += 1
            if ('tirolibero' in lineups_awayTeam_allPlays[i][k] and 'sbagliato' not in  lineups_awayTeam_allPlays[i][k]):
                _1p_attempted += 1
                _1p_made      += 1
            if ( ('tiroinsospensioneda2pt' in lineups_awayTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in lineups_awayTeam_allPlays[i][k] or 'layupda2pt' in lineups_awayTeam_allPlays[i][k]
                  or  'tiroda2ptinallontanamento' in lineups_awayTeam_allPlays[i][k] or 'giroetiroda2pt' in lineups_awayTeam_allPlays[i][k] or 'tiroda2ptinpenetrazione' in lineups_awayTeam_allPlays[i][k]) and 
                  ('sbagliato' in  lineups_awayTeam_allPlays[i][k] or 'stoppato' in  lineups_awayTeam_allPlays[i][k])):
                _2p_attempted += 1
            if  ( ('tiroinsospensioneda2pt' in lineups_awayTeam_allPlays[i][k] or 'tiroda2ptinsospensione' in lineups_awayTeam_allPlays[i][k] or 'layupda2pt' in lineups_awayTeam_allPlays[i][k]
                 or  'tiroda2ptinallontanamento' in lineups_awayTeam_allPlays[i][k] or 'giroetiroda2pt' in lineups_awayTeam_allPlays[i][k] or 'tiroda2ptinpenetrazione' in lineups_awayTeam_allPlays[i][k]) and 
                  ('sbagliato' not in  lineups_awayTeam_allPlays[i][k] and 'stoppato' not in  lineups_awayTeam_allPlays[i][k])):
                _2p_attempted += 1
                _2p_made      += 1
            if ('schiacciata' in lineups_awayTeam_allPlays[i][k]) or ('alleyoop' in lineups_awayTeam_allPlays[i][k]):
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            if ( ('tiroda3ptinsospensione' in lineups_awayTeam_allPlays[i][k] and ('sbagliato' in  lineups_awayTeam_allPlays[i][k] or 'stoppato' in  lineups_awayTeam_allPlays[i][k]))):
                _3p_attempted += 1
            if ( ('tiroda3ptinsospensione' in lineups_awayTeam_allPlays[i][k] and ('sbagliato' not in  lineups_awayTeam_allPlays[i][k] and 'stoppato' not in  lineups_awayTeam_allPlays[i][k]))):
                _3p_attempted += 1
                _3p_made += 1
            if 'rimbalzodifensivo' in lineups_awayTeam_allPlays[i][k]:
                def_rebound += 1
            if 'rimbalzooffensivo' in lineups_awayTeam_allPlays[i][k]:
                off_rebound += 1
            if 'assist' in lineups_awayTeam_allPlays[i][k]:
                assist += 1
            if 'pallarecuperata' in lineups_awayTeam_allPlays[i][k]:
                steal += 1
            if 'pallapersa' in lineups_awayTeam_allPlays[i][k]:
                turnover += 1
            if 'stoppata' in lineups_awayTeam_allPlays[i][k]:
                block_made += 1 
            if 'stoppato' in lineups_awayTeam_allPlays[i][k]:
                block_received += 1 
            if 'fallosubito' in lineups_awayTeam_allPlays[i][k]:
                foul_received += 1
            if ('fallo' in lineups_awayTeam_allPlays[i][k] and 
               'fallosubito' not in lineups_awayTeam_allPlays[i][k]):
                foul_made += 1
        all_stats_awayTeam_lineups_awayTeam.append([awayTeam_lineups_sorted[i],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received,all_lineups_awayTeam_filtered[i][1]/60.0])
    
    # Save data to dataframe and to spreadsheet
    df_awayTeam_lineups_awayTeamStats = pd.DataFrame(np.array(all_stats_awayTeam_lineups_awayTeam))
    df_awayTeam_lineups_awayTeamStats.columns = ['Lineup','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_awayTeam_lineups_awayTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_awayTeam_lineups_awayTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_awayTeam_lineups_awayTeamStats.to_excel(os.path.join(cwd,'awayTeam_awayTeamStats_lineups.xlsx'),
          sheet_name='Sheet_name_1')    
    
    # Merge rows that refer to the same lineup
    all_stats_awayTeam_lineups_awayTeam_merged = []
    for i in range(0,int(len(idx_unique_lineups_awayTeam))):
        idx_this_lineup   = idx_unique_lineups_awayTeam[i]
        stats_this_lineup = np.zeros([1,len(df_awayTeam_lineups_awayTeamStats.loc[0][1:])])
        for j in range(0,int(len(idx_this_lineup))):
            stats_this_lineup = stats_this_lineup + np.array(df_awayTeam_lineups_awayTeamStats.loc[idx_this_lineup[j]][1:])
        stats_this_lineup = list(stats_this_lineup[0])
        stats_this_lineup = [df_awayTeam_lineups_awayTeamStats.loc[idx_this_lineup[0]][0]]+stats_this_lineup
        all_stats_awayTeam_lineups_awayTeam_merged.append(stats_this_lineup)
    
    df_awayTeam_lineups_awayTeamStats_merged = pd.DataFrame(np.array(all_stats_awayTeam_lineups_awayTeam_merged))
    df_awayTeam_lineups_awayTeamStats_merged.columns = ['Lineup','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_awayTeam_lineups_awayTeamStats_merged[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_awayTeam_lineups_awayTeamStats_merged[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_awayTeam_lineups_awayTeamStats_merged.to_excel(os.path.join(cwd,'awayTeam_awayTeamStats_lineups_merged.xlsx'),
          sheet_name='Sheet_name_1')         
    
    all_stats_awayTeam_lineups_homeTeam = []
    for i in range(0,int(len(lineups_awayTeam_allPlays_homeTeam))):
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
        
        for k in range(0,int(len(lineups_awayTeam_allPlays_homeTeam[i]))):
            
                
            if ('tirolibero' in lineups_awayTeam_allPlays_homeTeam[i][k]  and 'sbagliato' in  lineups_awayTeam_allPlays_homeTeam[i][k]):
                _1p_attempted += 1
            if ('tirolibero' in lineups_awayTeam_allPlays_homeTeam[i][k] and 'sbagliato' not in  lineups_awayTeam_allPlays_homeTeam[i][k]):
                _1p_attempted += 1
                _1p_made      += 1
            if ( ('tiroinsospensioneda2pt' in lineups_awayTeam_allPlays_homeTeam[i][k] or 'tiroda2ptinsospensione' in lineups_awayTeam_allPlays_homeTeam[i][k] or 'layupda2pt' in lineups_awayTeam_allPlays_homeTeam[i][k]
                  or  'tiroda2ptinallontanamento' in lineups_awayTeam_allPlays_homeTeam[i][k] or 'giroetiroda2pt' in lineups_awayTeam_allPlays_homeTeam[i][k] or 'tiroda2ptinpenetrazione' in lineups_awayTeam_allPlays_homeTeam[i][k]) and 
                  ('sbagliato' in  lineups_awayTeam_allPlays_homeTeam[i][k] or 'stoppato' in  lineups_awayTeam_allPlays_homeTeam[i][k])):
                _2p_attempted += 1
            if  ( ('tiroinsospensioneda2pt' in lineups_awayTeam_allPlays_homeTeam[i][k] or 'tiroda2ptinsospensione' in lineups_awayTeam_allPlays_homeTeam[i][k] or 'layupda2pt' in lineups_awayTeam_allPlays_homeTeam[i][k]
                 or  'tiroda2ptinallontanamento' in lineups_awayTeam_allPlays_homeTeam[i][k] or 'giroetiroda2pt' in lineups_awayTeam_allPlays_homeTeam[i][k] or 'tiroda2ptinpenetrazione' in lineups_awayTeam_allPlays_homeTeam[i][k]) and 
                  ('sbagliato' not in  lineups_awayTeam_allPlays_homeTeam[i][k] and 'stoppato' not in  lineups_awayTeam_allPlays_homeTeam[i][k])):
                _2p_attempted += 1
                _2p_made      += 1
            if ('schiacciata' in lineups_awayTeam_allPlays_homeTeam[i][k]) or ('alleyoop' in lineups_awayTeam_allPlays_homeTeam[i][k]):
                _2p_attempted += 1
                _2p_made      += 1
                dunk          += 1
            if ( ('tiroda3ptinsospensione' in lineups_awayTeam_allPlays_homeTeam[i][k] and ('sbagliato' in  lineups_awayTeam_allPlays_homeTeam[i][k] or 'stoppato' in  lineups_awayTeam_allPlays_homeTeam[i][k]))):
                _3p_attempted += 1
            if ( ('tiroda3ptinsospensione' in lineups_awayTeam_allPlays_homeTeam[i][k] and ('sbagliato' not in  lineups_awayTeam_allPlays_homeTeam[i][k] and 'stoppato' not in  lineups_awayTeam_allPlays_homeTeam[i][k]))):
                _3p_attempted += 1
                _3p_made += 1
            if 'rimbalzodifensivo' in lineups_awayTeam_allPlays_homeTeam[i][k]:
                def_rebound += 1
            if 'rimbalzooffensivo' in lineups_awayTeam_allPlays_homeTeam[i][k]:
                off_rebound += 1
            if 'assist' in lineups_awayTeam_allPlays_homeTeam[i][k]:
                assist += 1
            if 'pallarecuperata' in lineups_awayTeam_allPlays_homeTeam[i][k]:
                steal += 1
            if 'pallapersa' in lineups_awayTeam_allPlays_homeTeam[i][k]:
                turnover += 1
            if 'stoppata' in lineups_awayTeam_allPlays_homeTeam[i][k]:
                block_made += 1 
            if 'stoppato' in lineups_awayTeam_allPlays_homeTeam[i][k]:
                block_received += 1 
            if 'fallosubito' in lineups_awayTeam_allPlays_homeTeam[i][k]:
                foul_received += 1
            if ('fallo' in lineups_awayTeam_allPlays_homeTeam[i][k] and 
               'fallosubito' not in lineups_awayTeam_allPlays_homeTeam[i][k]):
                foul_made += 1
        all_stats_awayTeam_lineups_homeTeam.append([awayTeam_lineups_sorted[i],_1p_made,
          _1p_attempted,_2p_made,_2p_attempted,dunk,_3p_made,_3p_attempted,
          def_rebound,off_rebound,assist,steal,turnover,block_made,block_received,
           foul_made,foul_received,all_lineups_awayTeam_filtered[i][1]/60.0])
    
    # Save data to dataframe and to spreadsheet
    df_awayTeam_lineups_homeTeamStats = pd.DataFrame(np.array(all_stats_awayTeam_lineups_homeTeam))
    df_awayTeam_lineups_homeTeamStats.columns = ['Lineup','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_awayTeam_lineups_homeTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_awayTeam_lineups_homeTeamStats[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_awayTeam_lineups_homeTeamStats.to_excel(os.path.join(cwd,'awayTeam_homeTeamStats_lineups.xlsx'),
          sheet_name='Sheet_name_1')    
    
    # Merge rows that refer to the same lineup
    all_stats_awayTeam_lineups_homeTeam_merged = []
    for i in range(0,int(len(idx_unique_lineups_awayTeam))):
        idx_this_lineup   = idx_unique_lineups_awayTeam[i]
        stats_this_lineup = np.zeros([1,len(df_awayTeam_lineups_homeTeamStats.loc[0][1:])])
        for j in range(0,int(len(idx_this_lineup))):
            stats_this_lineup = stats_this_lineup + np.array(df_awayTeam_lineups_homeTeamStats.loc[idx_this_lineup[j]][1:])
        stats_this_lineup = list(stats_this_lineup[0])
        stats_this_lineup = [df_awayTeam_lineups_homeTeamStats.loc[idx_this_lineup[0]][0]]+stats_this_lineup
        all_stats_awayTeam_lineups_homeTeam_merged.append(stats_this_lineup)
    
    df_awayTeam_lineups_homeTeamStats_merged = pd.DataFrame(np.array(all_stats_awayTeam_lineups_homeTeam_merged))
    df_awayTeam_lineups_homeTeamStats_merged.columns = ['Lineup','1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']
    df_awayTeam_lineups_homeTeamStats_merged[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']] = (
                                            df_awayTeam_lineups_homeTeamStats_merged[['1pm','1pa','2pm','2pa','dunk','3pm','3pa',
                  'dreb','oreb','ass','st','to','blk','blkag','f','frec','min']].apply(pd.to_numeric))
    df_awayTeam_lineups_homeTeamStats_merged.to_excel(os.path.join(cwd,'awayTeam_homeTeamStats_lineups_merged.xlsx'),
          sheet_name='Sheet_name_1') 
    
    return df_awayTeam_lineups_homeTeamStats_merged,df_awayTeam_lineups_awayTeamStats_merged

def plot_team_statistics(df_homeTeam_lineups_ownTeamStats_aggr,
                         df_homeTeam_lineups_oppTeamStats_aggr,
                         df_homeTeam_startingPlusBench_ownTeamStats_aggr,
                         df_homeTeam_startingPlusBench_oppTeamStats_aggr,
                         cwd,
                         team_list_logos,idx_logo_homeTeam,dfHomeTeam,
                         starting_five_homeTeam,
                         bench_homeTeam,
                         orig_idx_starting_five_homeTeam,
                         orig_idx_bench_homeTeam,string_team,pos_logo,axis_font,
                         minimum_minutes_played):
    
    ######################
    ### 2P% per lineup ###
    ######################
    df_2p_perc_homeTeam_lineups_ownTeamStats_aggr        = deepcopy(df_homeTeam_lineups_ownTeamStats_aggr[['2pm','2pa']])
    df_2p_perc_homeTeam_lineups_ownTeamStats_aggr['2pp'] = df_2p_perc_homeTeam_lineups_ownTeamStats_aggr['2pm']/df_2p_perc_homeTeam_lineups_ownTeamStats_aggr['2pa']
    df_2p_perc_homeTeam_lineups_ownTeamStats_aggr['2pp'].fillna(0, inplace=True)
    
    df_2p_perc_homeTeam_lineups_oppTeamStats_aggr        = deepcopy(df_homeTeam_lineups_oppTeamStats_aggr[['2pm','2pa']])
    df_2p_perc_homeTeam_lineups_oppTeamStats_aggr['2pp'] = df_2p_perc_homeTeam_lineups_oppTeamStats_aggr['2pm']/df_2p_perc_homeTeam_lineups_oppTeamStats_aggr['2pa']
    df_2p_perc_homeTeam_lineups_oppTeamStats_aggr['2pp'].fillna(0, inplace=True)
    

    def getImage(path):
        return OffsetImage(plt.imread(path),zoom=0.01)
    
    fig,ax = plt.subplots()
    for i in range(0,int(len(df_2p_perc_homeTeam_lineups_ownTeamStats_aggr))):
        if df_homeTeam_lineups_ownTeamStats_aggr.loc[i]['min'] >= minimum_minutes_played:
            if (df_2p_perc_homeTeam_lineups_oppTeamStats_aggr['2pp'][i] != 0 or
                df_2p_perc_homeTeam_lineups_oppTeamStats_aggr['2pp'][i] != 0):
                plt.plot(df_2p_perc_homeTeam_lineups_ownTeamStats_aggr['2pp'][i],
                         df_2p_perc_homeTeam_lineups_oppTeamStats_aggr['2pp'][i],c='r',marker='>',
                         markersize=10,linestyle='')
                ab = AnnotationBbox(getImage(os.path.join(cwd,'basketball.png')), (df_2p_perc_homeTeam_lineups_ownTeamStats_aggr['2pp'][i], 
                                    df_2p_perc_homeTeam_lineups_oppTeamStats_aggr['2pp'][i]), frameon=False)
                ax.add_artist(ab)
    

    ax.fill([0.5,1,1,0.5,0.5],[0,0,0.5,0.5,0],facecolor='lightsalmon',edgecolor='orangered',alpha=0.2,linewidth=3)
    ax.fill([0,0.5,0.5,0,0],[0.5,0.5,1,1,0.5],facecolor='lightsalmon',edgecolor='orangered',alpha=0.2,linewidth=3)
  
    offset_lb = -0.05
    offset_ub = 0.05
    
    for i in range(0,int(len(df_2p_perc_homeTeam_lineups_ownTeamStats_aggr))):
        if df_homeTeam_lineups_ownTeamStats_aggr.loc[i]['min'] >= minimum_minutes_played:
            if (df_2p_perc_homeTeam_lineups_oppTeamStats_aggr['2pp'][i] != 0 or
                df_2p_perc_homeTeam_lineups_oppTeamStats_aggr['2pp'][i] != 0):
                plt.text(offset_lb + (offset_ub-offset_lb)*random.random() + df_2p_perc_homeTeam_lineups_ownTeamStats_aggr['2pp'][i],
                         offset_lb + (offset_ub-offset_lb)*random.random() +df_2p_perc_homeTeam_lineups_oppTeamStats_aggr['2pp'][i],str(i+1),
                         fontsize=15,zorder=100)

    ax.set_xlabel('Team 2P%',**axis_font)
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
    df_2p_perc_homeTeam_player_ownTeamStats_aggr        = deepcopy(df_homeTeam_startingPlusBench_ownTeamStats_aggr[['2pm','2pa']])
    df_2p_perc_homeTeam_player_ownTeamStats_aggr['2pp'] = (df_homeTeam_startingPlusBench_ownTeamStats_aggr['2pm']
                                              /df_homeTeam_startingPlusBench_ownTeamStats_aggr['2pa'])
    df_2p_perc_homeTeam_player_ownTeamStats_aggr['2pp'].fillna(0, inplace=True)
    
    df_2p_perc_homeTeam_player_oppTeamStats_aggr        = deepcopy(df_homeTeam_startingPlusBench_oppTeamStats_aggr[['2pm','2pa']])
    df_2p_perc_homeTeam_player_oppTeamStats_aggr['2pp'] = (df_homeTeam_startingPlusBench_oppTeamStats_aggr['2pm']
                                                      /df_homeTeam_startingPlusBench_oppTeamStats_aggr['2pa'])
    df_2p_perc_homeTeam_player_oppTeamStats_aggr['2pp'].fillna(0, inplace=True)
    
    #orig_idx_homeTeam      = orig_idx_starting_five_homeTeam+orig_idx_bench_homeTeam
    #names_homeTeam         = starting_five_homeTeam + bench_homeTeam 
    
    
    #idx_names_homeTeam_srt = names_homeTeam
    orig_idx_homeTeam_srt  = orig_idx_starting_five_homeTeam+orig_idx_bench_homeTeam
    
#    idx_names_homeTeam_srt = sorted(range(len(names_homeTeam)), key=lambda k: names_homeTeam[k], reverse=False)
#    orig_idx_homeTeam_srt  = []
#    for i in range(0,int(len(idx_names_homeTeam_srt))):
#        orig_idx_homeTeam_srt.append(orig_idx_homeTeam[idx_names_homeTeam_srt[i]])

    

    fig,ax = plt.subplots()
    for i in range(0,int(len(df_homeTeam_startingPlusBench_ownTeamStats_aggr))):
        if df_homeTeam_startingPlusBench_ownTeamStats_aggr.loc[i]['min'] >= minimum_minutes_played:
            plt.plot(df_2p_perc_homeTeam_player_ownTeamStats_aggr['2pp'][i],
                     df_2p_perc_homeTeam_player_oppTeamStats_aggr['2pp'][i],c='r',marker='>',
                     markersize=6,linestyle='')
            ab = AnnotationBbox(getImage(os.path.join(cwd,'basketball.png')), (df_2p_perc_homeTeam_player_ownTeamStats_aggr['2pp'][i], 
                                    df_2p_perc_homeTeam_player_oppTeamStats_aggr['2pp'][i]), frameon=False)
            ax.add_artist(ab)
    
    ax.fill([0.5,1,1,0.5,0.5],[0,0,0.5,0.5,0],facecolor='lightsalmon',edgecolor='orangered',alpha=0.2,linewidth=3)
    ax.fill([0,0.5,0.5,0,0],[0.5,0.5,1,1,0.5],facecolor='lightsalmon',edgecolor='orangered',alpha=0.2,linewidth=3)
  
    
    for i in range(0,int(len(df_homeTeam_startingPlusBench_ownTeamStats_aggr))):
        if df_homeTeam_startingPlusBench_ownTeamStats_aggr.loc[i]['min'] >= minimum_minutes_played:
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
    df_fg_perc_homeTeam_lineup_ownTeamStats_aggr        = deepcopy(df_homeTeam_lineups_ownTeamStats_aggr[['2pm','2pa','3pm','3pa']])
    df_fg_perc_homeTeam_lineup_ownTeamStats_aggr['fgp'] = ((df_fg_perc_homeTeam_lineup_ownTeamStats_aggr['2pm']+df_fg_perc_homeTeam_lineup_ownTeamStats_aggr['3pm'])
                                              /(df_fg_perc_homeTeam_lineup_ownTeamStats_aggr['2pa']+df_fg_perc_homeTeam_lineup_ownTeamStats_aggr['3pa']))
    df_fg_perc_homeTeam_lineup_ownTeamStats_aggr['fgp'].fillna(0, inplace=True)
    df_fg_perc_homeTeam_lineup_ownTeamStats_aggr['fgp'].replace(np.inf,4,inplace=True)
    
    df_fg_perc_homeTeam_lineup_oppTeamStats_aggr        = deepcopy(df_homeTeam_lineups_oppTeamStats_aggr[['2pm','2pa','3pm','3pa']])
    df_fg_perc_homeTeam_lineup_oppTeamStats_aggr['fgp'] = ((df_fg_perc_homeTeam_lineup_oppTeamStats_aggr['2pm']+df_fg_perc_homeTeam_lineup_oppTeamStats_aggr['3pm'])
                                              /(df_fg_perc_homeTeam_lineup_oppTeamStats_aggr['2pa']+df_fg_perc_homeTeam_lineup_oppTeamStats_aggr['3pa']))
    df_fg_perc_homeTeam_lineup_oppTeamStats_aggr['fgp'].fillna(0, inplace=True)
    df_fg_perc_homeTeam_lineup_oppTeamStats_aggr['fgp'].replace(np.inf,4,inplace=True)
    

    fig,ax = plt.subplots()
    for i in range(0,int(len(df_fg_perc_homeTeam_lineup_ownTeamStats_aggr))):
        if df_homeTeam_lineups_ownTeamStats_aggr.loc[i]['min'] >= minimum_minutes_played:
            plt.plot(df_fg_perc_homeTeam_lineup_ownTeamStats_aggr['fgp'][i],
                     df_fg_perc_homeTeam_lineup_oppTeamStats_aggr['fgp'][i],c='r',marker='>',
                     markersize=6,linestyle='')
            ab = AnnotationBbox(getImage(os.path.join(cwd,'basketball.png')), (df_fg_perc_homeTeam_lineup_ownTeamStats_aggr['fgp'][i], 
                                    df_fg_perc_homeTeam_lineup_oppTeamStats_aggr['fgp'][i]), frameon=False)
            ax.add_artist(ab)

    
    ax.fill([0.5,1,1,0.5,0.5],[0,0,0.5,0.5,0],facecolor='lightsalmon',edgecolor='orangered',alpha=0.2,linewidth=3)
    ax.fill([0,0.5,0.5,0,0],[0.5,0.5,1,1,0.5],facecolor='lightsalmon',edgecolor='orangered',alpha=0.2,linewidth=3)
  
    
    for i in range(0,int(len(df_fg_perc_homeTeam_lineup_ownTeamStats_aggr))):
        if df_homeTeam_lineups_ownTeamStats_aggr.loc[i]['min'] >= minimum_minutes_played:
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
    df_fg_perc_homeTeam_player_ownTeamStats_aggr        = deepcopy(df_homeTeam_startingPlusBench_ownTeamStats_aggr[['2pm','2pa','3pm','3pa']])
    df_fg_perc_homeTeam_player_ownTeamStats_aggr['fgp'] = ((df_fg_perc_homeTeam_player_ownTeamStats_aggr['2pm']+df_fg_perc_homeTeam_player_ownTeamStats_aggr['3pm'])
                                              /(df_fg_perc_homeTeam_player_ownTeamStats_aggr['2pa']+df_fg_perc_homeTeam_player_ownTeamStats_aggr['3pa']))
    df_fg_perc_homeTeam_player_ownTeamStats_aggr['fgp'].fillna(0, inplace=True)
    df_fg_perc_homeTeam_player_ownTeamStats_aggr['fgp'].replace(np.inf,4,inplace=True)
    
    df_fg_perc_homeTeam_player_oppTeamStats_aggr        = deepcopy(df_homeTeam_startingPlusBench_oppTeamStats_aggr[['2pm','2pa','3pm','3pa']])
    df_fg_perc_homeTeam_player_oppTeamStats_aggr['fgp'] = ((df_fg_perc_homeTeam_player_oppTeamStats_aggr['2pm']+df_fg_perc_homeTeam_player_oppTeamStats_aggr['3pm'])
                                              /(df_fg_perc_homeTeam_player_oppTeamStats_aggr['2pa']+df_fg_perc_homeTeam_player_oppTeamStats_aggr['3pa']))
    df_fg_perc_homeTeam_player_oppTeamStats_aggr['fgp'].fillna(0, inplace=True)
    df_fg_perc_homeTeam_player_oppTeamStats_aggr['fgp'].replace(np.inf,4,inplace=True)
    
    fig,ax = plt.subplots()
    for i in range(0,int(len(df_2p_perc_homeTeam_player_ownTeamStats_aggr))):
        if df_homeTeam_startingPlusBench_ownTeamStats_aggr.loc[i]['min'] >= minimum_minutes_played:
            plt.plot(df_fg_perc_homeTeam_player_ownTeamStats_aggr['fgp'][i],
                     df_fg_perc_homeTeam_player_oppTeamStats_aggr['fgp'][i],c='r',marker='>',
                     markersize=6,linestyle='')
            ab = AnnotationBbox(getImage(os.path.join(cwd,'basketball.png')), (df_fg_perc_homeTeam_player_ownTeamStats_aggr['fgp'][i], 
                                    df_fg_perc_homeTeam_player_oppTeamStats_aggr['fgp'][i]), frameon=False)
            ax.add_artist(ab)
    
    ax.fill([0.5,1,1,0.5,0.5],[0,0,0.5,0.5,0],facecolor='lightsalmon',edgecolor='orangered',alpha=0.2,linewidth=3)
    ax.fill([0,0.5,0.5,0,0],[0.5,0.5,1,1,0.5],facecolor='lightsalmon',edgecolor='orangered',alpha=0.2,linewidth=3)
  
    
    for i in range(0,int(len(df_fg_perc_homeTeam_player_ownTeamStats_aggr))):
        if df_homeTeam_startingPlusBench_ownTeamStats_aggr.loc[i]['min'] >= minimum_minutes_played:
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
                       0.4*df_homeTeam_lineups_ownTeamStats_aggr['1pa'][i])
        possessions_oppTeam = (df_homeTeam_lineups_oppTeamStats_aggr['2pa'][i]+
                       df_homeTeam_lineups_oppTeamStats_aggr['3pa'][i]-
                       df_homeTeam_lineups_oppTeamStats_aggr['oreb'][i]+
                       df_homeTeam_lineups_oppTeamStats_aggr['to'][i]+
                       0.4*df_homeTeam_lineups_oppTeamStats_aggr['1pa'][i])
        
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
    


    fig,ax = plt.subplots()
    for i in range(0,int(len(df_homeTeam_lineups_ownTeamStats_aggr))):
        if df_homeTeam_lineups_ownTeamStats_aggr.loc[i]['min'] >= minimum_minutes_played:
            plt.plot(df_homeTeam_offDef_efficiency_perLineup['offEff'][i],
                     df_homeTeam_offDef_efficiency_perLineup['defEff'][i],c='r',marker='d',
                     markersize=6,linestyle='')
            ab = AnnotationBbox(getImage(os.path.join(cwd,'basketball.png')), (df_homeTeam_offDef_efficiency_perLineup['offEff'][i], 
                                    df_homeTeam_offDef_efficiency_perLineup['defEff'][i]), frameon=False)
            ax.add_artist(ab)

    
    offset_lb = -5
    offset_ub = 5
    
    
    for i in range(0,int(len(df_homeTeam_lineups_ownTeamStats_aggr))):
        if df_homeTeam_lineups_ownTeamStats_aggr.loc[i]['min'] >= minimum_minutes_played:
            if (df_homeTeam_offDef_efficiency_perLineup['offEff'][i] != 0 or
                df_homeTeam_offDef_efficiency_perLineup['defEff'][i] != 0):
                plt.text(offset_lb + (offset_ub-offset_lb)*random.random() + df_homeTeam_offDef_efficiency_perLineup['offEff'][i],
                         offset_lb + (offset_ub-offset_lb)*random.random() +df_homeTeam_offDef_efficiency_perLineup['defEff'][i],str(i+1),
                         fontsize=15,zorder=100)
    
    if np.max(df_homeTeam_offDef_efficiency_perLineup['offEff'])>=100 and np.min(df_homeTeam_offDef_efficiency_perLineup['defEff'])<=100:
        ax.fill([100,np.max(df_homeTeam_offDef_efficiency_perLineup['offEff']),np.max(df_homeTeam_offDef_efficiency_perLineup['offEff']),100,100],
                 [np.min(df_homeTeam_offDef_efficiency_perLineup['defEff']),np.min(df_homeTeam_offDef_efficiency_perLineup['defEff']),
                 100,100,np.min(df_homeTeam_offDef_efficiency_perLineup['defEff'])],facecolor='lightsalmon',edgecolor='orangered',alpha=0.2,linewidth=3)

    ax.set_xlabel('Team Offensive Efficiency',**axis_font)
    ax.set_ylabel('team Defensive Efficiency',**axis_font)
    ax.set_title('Offensive/Defensive Efficiency per lineup',**axis_font)
    
    
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

    
    fig,ax = plt.subplots()
    for i in range(0,int(len(df_homeTeam_startingPlusBench_ownTeamStats_aggr))):
        if df_homeTeam_startingPlusBench_ownTeamStats_aggr.loc[i]['min'] >= minimum_minutes_played:
            plt.plot(df_homeTeam_offDef_efficiency_perPlayer['offEff'][i],
                     df_homeTeam_offDef_efficiency_perPlayer['defEff'][i],c='r',marker='d',
                     markersize=6,linestyle='')
    
            ab = AnnotationBbox(getImage(os.path.join(cwd,'basketball.png')), (df_homeTeam_offDef_efficiency_perPlayer['offEff'][i], 
                                    df_homeTeam_offDef_efficiency_perPlayer['defEff'][i]), frameon=False)
            ax.add_artist(ab)
    
    for i in range(0,int(len(df_homeTeam_startingPlusBench_ownTeamStats_aggr))):
        if df_homeTeam_startingPlusBench_ownTeamStats_aggr.loc[i]['min'] >= minimum_minutes_played:
            if (df_homeTeam_offDef_efficiency_perPlayer['offEff'][i] != 0 or
                df_homeTeam_offDef_efficiency_perPlayer['defEff'][i] != 0):
                plt.text(df_homeTeam_offDef_efficiency_perPlayer['offEff'][i],
                     df_homeTeam_offDef_efficiency_perPlayer['defEff'][i],
                     dfHomeTeam[2][orig_idx_homeTeam_srt[i]],
                     fontsize=10,fontname='Arial',zorder=100)
    
    if np.max(df_homeTeam_offDef_efficiency_perPlayer['offEff'])>=100 and np.min(df_homeTeam_offDef_efficiency_perPlayer['defEff'])<=100:
        ax.fill([100,np.max(df_homeTeam_offDef_efficiency_perPlayer['offEff']),np.max(df_homeTeam_offDef_efficiency_perPlayer['offEff']),100,100],
                 [np.min(df_homeTeam_offDef_efficiency_perPlayer['defEff']),np.min(df_homeTeam_offDef_efficiency_perPlayer['defEff']),
                 100,100,np.min(df_homeTeam_offDef_efficiency_perPlayer['defEff'])],facecolor='lightsalmon',edgecolor='orangered',alpha=0.2,linewidth=3)
    
    
    ax.set_xlabel('Team Offensive Efficiency',**axis_font)
    ax.set_ylabel('Team Defensive Efficiency',**axis_font)
    ax.set_title('Offensive/Defensive Efficiency per player',**axis_font)
    
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