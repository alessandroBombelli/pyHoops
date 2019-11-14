#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 13 15:44:28 2019

@author: alessandro
"""

import os
import sys
import pickle
import numpy as np

sys.path.append('C:/Python27/Lib/site-packages')
sys.path.append('/Library/TeX/texbin/xelatex')
sys.path.append('/anaconda/bin/python')
sys.path.append('/anaconda/lib/python2.7/site-packages')
sys.path.append('anaconda/envs/py37/lib/python3.7/site-packages')

import pyHoops

#######################
#######################
### INPUTS:
#######################
#######################

# Number of minutes per quarter. It changes whether European basketball
# or NBA is considered
minutes_in_quarter = 10

# Path to current folder
cwd             = os.getcwd()

# List of teams and associated logos. An additional logo is added, to be associated
# with teams that do not have a logo in the folder (in this context, logos are
# specific for the Italian League)
team_list = ['brescia','brindisi','cantu','cremona','fortitudobologna',
'milano'	,'pesaro','pistoia','reggioemilia','roma','sassari','trentino',
'treviso','trieste','varese','venezia','virtusbologna']

team_list_logos = ['Brescia.png','Brindisi.png','Cantu.png','Cremona.png',
                   'Fortitudo_Bologna.png','Milano.png'	,'Pesaro.png',
                   'Pistoia.png','Reggio_Emilia.png','Roma.png','Sassari.png',
                   'Trentino.png','Treviso.png','Trieste.png','Varese.png',
                   'Venezia.png','Virtus_Bologna.png','LBA_logo.png']

#######################
#######################
### TESTS:
#######################
#######################
# Tor un each test, de-comment the four input lines and run the file

# TEST 1
thisUrl         = 'http://web.legabasket.it/game/1672570/germani_basket_brescia-openjobmetis_varese_91:74/pbp'
thisUrlBoxscore = 'http://web.legabasket.it/game/1672570/germani_basket_brescia-openjobmetis_varese_91:74'
string_homeTeam = 'brescia'
string_awayTeam = 'varese'

## TEST 2
#thisUrl         = 'http://web.legabasket.it/game/1672568/acqua_s__bernardo_cant__-virtus_roma_74:76/pbp'
#thisUrlBoxscore = 'http://web.legabasket.it/game/1672568/acqua_s__bernardo_cant__-virtus_roma_74:76'
#string_homeTeam = 'cantu'
#string_awayTeam = 'roma'

## TEST 3
#thisUrl         = 'http://web.legabasket.it/game/1672567/pallacanestro_trieste-happy_casa_brindisi_72:80/pbp'
#thisUrlBoxscore = 'http://web.legabasket.it/game/1672567/pallacanestro_trieste-happy_casa_brindisi_72:80'
#string_homeTeam = 'trieste'
#string_awayTeam = 'brindisi'

## TEST 4
#thisUrl         = 'http://web.legabasket.it/game/1672569/segafredo_virtus_bologna-d___longhi_treviso_84:79/pbp'
#thisUrlBoxscore = 'http://web.legabasket.it/game/1672569/segafredo_virtus_bologna-d___longhi_treviso_84:79'
#string_homeTeam = 'virtusbologna'
#string_awayTeam = 'treviso'

## TEST 5
#thisUrl         = 'http://web.legabasket.it/game/1672565/a_x_armani_exchange_milano-oriora_pistoia_83:63/pbp'
#thisUrlBoxscore = 'http://web.legabasket.it/game/1672565/a_x_armani_exchange_milano-oriora_pistoia_83:63'
#string_homeTeam = 'milano'
#string_awayTeam = 'pistoia'

# webparsing = 1 means the web-parsing routine is active. Otehrwise, the three
# datasets (full play-by-play matrix, boxscores for home team and away team)
# are loaded as pickle data   
webparsing = 1

####################
####################
### MAIN: 
####################
####################


if webparsing == 1:

    ###############################################
    # Extracting all play-by-play info from webpage
    ###############################################      
    df = pyHoops.web_parse_playbyplay(thisUrl) 
    
    ###################################################### 
    # Extracting boxscores (home + away team) from webpage
    ######################################################      
    dfHomeTeam,dfAwayTeam = pyHoops.web_parse_boxscores(thisUrlBoxscore)

# webparsing = 0 means the play-by-play and boxscores are loaded
# offline as pickle data. If using this option, make sure to change the test 
# name (e.g., _test1.pickle, _test2.pickle etc) to be consistent with the
# test you actually want to run    
else:
    
    with open(os.path.join(cwd,'play_by_play_test1.pickle'), 'rb') as handle:
        df         = pickle.load(handle)
    with open(os.path.join(cwd,'homeTeam_boxscore_test1.pickle'), 'rb') as handle:
        dfHomeTeam = pickle.load(handle)
    with open(os.path.join(cwd,'awayTeam_boxscore_test1.pickle'), 'rb') as handle:
        dfAwayTeam = pickle.load(handle)
        
#############################################################
# Determining idx of logo picture for home team and away team
#############################################################
idx_logo_homeTeam,idx_logo_awayTeam = pyHoops.determine_team_logo(string_homeTeam,string_awayTeam,team_list)

#################################################################
### For the home team, determine statistics for the starting five
### and bench (own team and opposing team)
#################################################################
(df_homeTeam_startingPlusBench_homeTeamStats,
 df_homeTeam_startingPlusBench_awayTeamStats,
 df_homeTeam_startingPlusBench_assistedBaskets,
 homeTeam_startingFive_names,homeTeam_startingFive_info,
 homeTeam_bench_names,homeTeam_bench_info,
 orig_idx_starting_five_homeTeam,orig_idx_bench_homeTeam) = pyHoops.get_homeTeam_stats_perPlayer(df,dfHomeTeam,minutes_in_quarter,cwd)

#################################################################
### For the away team, determine statistics for the starting five
### and bench (own team and opposing team)
#################################################################
(df_awayTeam_startingPlusBench_awayTeamStats,
 df_awayTeam_startingPlusBench_homeTeamStats,
 df_awayTeam_startingPlusBench_assistedBaskets,
 awayTeam_startingFive_names,awayTeam_startingFive_info,
 awayTeam_bench_names,awayTeam_bench_info,
 orig_idx_starting_five_awayTeam,orig_idx_bench_awayTeam) = pyHoops.get_awayTeam_stats_perPlayer(df,dfAwayTeam,minutes_in_quarter,cwd)

#####################################################################
### For the home team, determine statistics for the different lineups
#####################################################################
(df_homeTeam_lineups_homeTeamStats_merged,
 df_homeTeam_lineups_awayTeamStats_merged)  = pyHoops.get_homeTeam_stats_perLineup(df,dfHomeTeam,homeTeam_startingFive_names,
                                              homeTeam_startingFive_info,homeTeam_bench_names,
                                              homeTeam_bench_info,minutes_in_quarter,cwd)

#####################################################################
### For the away team, determine statistics for the different lineups
#####################################################################
(df_awayTeam_lineups_homeTeamStats_merged,
df_awayTeam_lineups_awayTeamStats_merged)  = pyHoops.get_awayTeam_stats_perLineup(df,dfAwayTeam,awayTeam_startingFive_names,
                                              awayTeam_startingFive_info,awayTeam_bench_names,
                                              awayTeam_bench_info,minutes_in_quarter,cwd)
        
###################
### Plotting graphs
###################
idx_logo_homeTeam,idx_logo_awayTeam = pyHoops.determine_team_logo(string_homeTeam,string_awayTeam,team_list)

# Position (normalized) of the logo of the team in the figure
pos_logo               = [0.0, 0.7, 0.3, 0.3]
axis_font              = {'fontname':'Arial', 'size':'14'}
# Players or lineups with a playing time less than minimum_minutes_played
# will not be displayed to avoid outliers caused by a too short playing time
# Note: if pyHoops is run for multiple games (e.g., all the games of a
# basketball season), this effect will be mitigated since data are summed
# and all players/lineups should get sufficient playing time to have relevant
# statistics 
minimum_minutes_played = 2.5

(df_2p_perc_homeTeam_lineups_homeTeamStats_aggr,
            df_2p_perc_homeTeam_lineups_awayTeamStats_aggr,
            df_2p_perc_homeTeam_player_homeTeamStats_aggr,
            df_2p_perc_homeTeam_player_awayTeamStats_aggr,
            df_fg_perc_homeTeam_lineup_homeTeamStats_aggr,
            df_fg_perc_homeTeam_lineup_awayTeamStats_aggr,
            df_fg_perc_homeTeam_player_homeTeamStats_aggr,
            df_fg_perc_homeTeam_player_awayTeamStats_aggr,
            df_homeTeam_offDef_efficiency_perLineup,
            df_homeTeam_offDef_efficiency_perPlayer) = pyHoops.plot_team_statistics(df_homeTeam_lineups_homeTeamStats_merged,
                         df_homeTeam_lineups_awayTeamStats_merged,
                         df_homeTeam_startingPlusBench_homeTeamStats,
                         df_homeTeam_startingPlusBench_awayTeamStats,
                         cwd,
                         team_list_logos,idx_logo_homeTeam,dfHomeTeam,
                         homeTeam_startingFive_names,
                         homeTeam_bench_names,
                         orig_idx_starting_five_homeTeam,
                         orig_idx_bench_homeTeam,string_homeTeam,pos_logo,axis_font,
                         minimum_minutes_played)

(df_2p_perc_awayTeam_lineups_awayTeamStats_aggr,
            df_2p_perc_awayTeam_lineups_homeTeamStats_aggr,
            df_2p_perc_awayTeam_player_awayTeamStats_aggr,
            df_2p_perc_awayTeam_player_homeTeamStats_aggr,
            df_fg_perc_awayTeam_lineup_awayTeamStats_aggr,
            df_fg_perc_awayTeam_lineup_homeTeamStats_aggr,
            df_fg_perc_awayTeam_player_awayTeamStats_aggr,
            df_fg_perc_awayTeam_player_homeTeamStats_aggr,
            df_awayTeam_offDef_efficiency_perLineup,
            df_awayTeam_offDef_efficiency_perPlayer) = pyHoops.plot_team_statistics(df_awayTeam_lineups_awayTeamStats_merged,
                         df_awayTeam_lineups_homeTeamStats_merged,
                         df_awayTeam_startingPlusBench_awayTeamStats,
                         df_awayTeam_startingPlusBench_homeTeamStats,
                         cwd,
                         team_list_logos,idx_logo_awayTeam,dfAwayTeam,
                         awayTeam_startingFive_names,
                         awayTeam_bench_names,
                         orig_idx_starting_five_awayTeam,
                         orig_idx_bench_awayTeam,string_awayTeam,pos_logo,axis_font,
                         minimum_minutes_played)

#%%

#####################################################
### Displaying some extracts of the created datasets
#####################################################

# The play-by-play structure has 6 columns that contain, respectively, 
# (i) action of home team, (ii) score of home team, (iii) time of game (in
# current quarter), (iv) quarter of game, (v) score of away team,
# (vi) action of away team. Note that, apart from a few exceptions, if
# column (i) is non empty (i.e., there is an info regarding the home team),
# the associated column (vi) will be empty, and viceversa.
#
# Plotting a few samples
print(df.loc[0])
print('')
print(df.loc[int(np.round(0.2*len(df)))])
print('')
print(df.loc[int(np.round(0.4*len(df)))])
print('')
print(df.loc[int(np.round(0.6*len(df)))])
print('')

# Boxscores for home team and away team 
print(dfHomeTeam)
print('')
print(dfAwayTeam)
print('')

# Cumulative boxscores per player and per lineup, i.e., summary of 
# what the whole own team and the whole opposing team did on the floor
# while a specific player or lineup were on the floor

# Boxscore of home team performance when a specific player of the home
# team was on the floor
print(df_homeTeam_startingPlusBench_homeTeamStats)
print('')
# Boxscore of away team performance when a specific player of the home
# team was on the floor
print(df_homeTeam_startingPlusBench_awayTeamStats)
print('')
# Boxscore of home team performance when a specific lineup of the home
# team was on the floor (note: the summation of numbers in the last
# column 'min' should sum up to the total number of minutes in the
# game, since different lineups do not overlap and cover the whole time-span)
print(df_homeTeam_lineups_homeTeamStats_merged)
print('')
# Boxscore of away team performance when a specific lineup of the home
# team was on the floor note: the summation of numbers in the last
# column 'min' should sum up to the total number of minutes in the
# game, since different lineups do not overlap and cover the whole time-span)
print(df_homeTeam_lineups_awayTeamStats_merged)
print('')
# Offensive/defensive efficiency of home team per player
print(df_homeTeam_offDef_efficiency_perPlayer)
print('')
# Offensive/defensive efficiency of home team per lineup
print(df_homeTeam_offDef_efficiency_perLineup)
print('')
