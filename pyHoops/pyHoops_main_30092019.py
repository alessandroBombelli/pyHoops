#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 30 12:02:52 2019

@author: alessandro
"""

import os
import sys
import pyHoops

sys.path.append('C:/Python27/Lib/site-packages')
sys.path.append('/Library/TeX/texbin/xelatex')
sys.path.append('/anaconda/bin/python')
sys.path.append('/anaconda/lib/python2.7/site-packages')

#######################
### INPUTS:
#######################

# PAth to current folder
cwd             = os.getcwd()

# List of teams and associated logos. An additional logo is added, to be associated
# with teams that do not have a logo in the folder
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

# To run each test, uncomment the two urls:
# 1) thisUrl        : url to play-by-play webpage of the game
# 2) thisUrlBoxscore: url to boxscore webpage of the game
# and run the code
# IN the original version of this file, the game between
# A|X Armani Exchange Milano and Germani Basket Brescia (TEST 3) is processed


##################################################################
### LBA Lega Basket Serie A: single game from 2018-2019 season ###
##################################################################

## TEST 1: Cantu - Avellino (2018-2019 season)
#thisUrl         = 'http://web.legabasket.it/game/1672352/acqua_s_bernardo_cant__-sidigas_avellino_83:73/pbp'
#thisUrlBoxscore = 'http://web.legabasket.it/game/1672352/acqua_s_bernardo_cant__-sidigas_avellino_83:73'

##########################################################################
### LBA Lega Basket Serie A: second week (all games), 2019-2020 season ###
##########################################################################

## TEST 2: Reggio Emilia - Trentino (2019-2020 season)
#thisUrl         = 'http://web.legabasket.it/game/1672520/grissin_bon_reggio_emilia-dolomiti_energia_trentino_76:84/pbp'
#thisUrlBoxscore = 'http://web.legabasket.it/game/1672520/grissin_bon_reggio_emilia-dolomiti_energia_trentino_76:84'

# TEST 3: Armani Milano - Brescia (2019-2020 season)
thisUrl         = 'http://web.legabasket.it/game/1672517/a_x_armani_exchange_milano-germani_basket_brescia-65:73/pbp'
thisUrlBoxscore = 'http://web.legabasket.it/game/1672517/a_x_armani_exchange_milano-germani_basket_brescia-65:73'

## TEST 4: Virtus Roma - Brindisi (2019-2020 season)
#thisUrl         = 'http://web.legabasket.it/game/1672523/virtus_roma-happy_casa_brindisi_63:87/pbp'
#thisUrlBoxscore ='http://web.legabasket.it/game/1672523/virtus_roma-happy_casa_brindisi_63:87'

## TEST 5: Sassari - Pesaro (2019-2020 season)
#thisUrl         = 'http://web.legabasket.it/game/1672516/banco_di_sardegna_sassari-carpegna_prosciutto_basket_pesaro-99:79/pbp'
#thisUrlBoxscore = 'http://web.legabasket.it/game/1672516/banco_di_sardegna_sassari-carpegna_prosciutto_basket_pesaro-99:79'

## TEST 6: Pistoia - Virtus Bologna (2019-2020 season)
#thisUrl         = 'http://web.legabasket.it/game/1672521/oriora_pistoia-segafredo_virtus_bologna-78:88/pbp'
#thisUrlBoxscore = 'http://web.legabasket.it/game/1672521/oriora_pistoia-segafredo_virtus_bologna-78:88'

## TEST 7: Fortitudo Bologna - Venezia (2019-2020 season)
#thisUrl         = 'http://web.legabasket.it/game/1672522/pompea_fortitudo_bologna-umana_reyer_venezia-89:82/pbp'
#thisUrlBoxscore = 'http://web.legabasket.it/game/1672522/pompea_fortitudo_bologna-umana_reyer_venezia-89:82'

## TEST 8: Cremona - Treviso (2019-2020 season)
#thisUrl         = 'http://web.legabasket.it/game/1672518/vanoli_basket_cremona-d___longhi_treviso-89:87/pbp'
#thisUrlBoxscore = 'http://web.legabasket.it/game/1672518/vanoli_basket_cremona-d___longhi_treviso-89:87'

## TEST 9: Trieste - Varese (2019-2020 season)
#thisUrl         = 'http://web.legabasket.it/game/1672519/pallacanestro_trieste-openjobmetis_varese-62:92/pbp'
#thisUrlBoxscore = 'http://web.legabasket.it/game/1672519/pallacanestro_trieste-openjobmetis_varese-62:92'




####################
####################
### MAIN: 
####################
####################

############################################### 
# Extracting all play-by-play info from webpage
###############################################      
df = pyHoops.web_parse_playbyplay(thisUrl)

###################################################### 
# Extracting boxscores (home + away team) from webpage
######################################################      
dfHomeTeam,dfAwayTeam = pyHoops.web_parse_boxscores(thisUrlBoxscore)

#############################################################
# Determining idx of logo picture for home team and away team
#############################################################
string_homeTeam = df.loc[0][0]
string_awayTeam = df.loc[0][2]
idx_logo_homeTeam,idx_logo_awayTeam = pyHoops.determine_team_logo(string_homeTeam,string_awayTeam,team_list)

################################################################
### Determining indices in the df dataframe where minutes change
### (to keep track of on-court time)
################################################################
idxMinutes,all_minutes_found = pyHoops.find_indices_minutes(df)

#################################################################
### For the home team, determine statistics for the starting five
### and bench (own team and opposing team)
#################################################################
(df_homeTeam_startingFive_homeTeamStats,
 df_homeTeam_startingFive_oppTeamStats,
 df_homeTeam_bench_homeTeamStats,
 df_homeTeam_bench_oppTeamStats,
 df_homeTeam_startingPlusBench_ownTeamStats_aggr,
 df_homeTeam_startingPlusBench_oppTeamStats_aggr,
 starting_five_homeTeam,
 bench_homeTeam,
 orig_idx_starting_five_homeTeam,
 orig_idx_bench_homeTeam,
 all_possible_names_starting_five_homeTeam) = pyHoops.get_homeTeam_stats_perPlayer(df,
                                                dfHomeTeam,idxMinutes,all_minutes_found,cwd)

#################################################################
### For the away team, determine statistics for the starting five
### and bench (own team and opposing team)
#################################################################
(df_awayTeam_startingFive_ownTeamStats,
 df_awayTeam_startingFive_oppTeamStats,
 df_awayTeam_bench_ownTeamStats,
 df_awayTeam_bench_oppTeamStats,
 df_awayTeam_startingPlusBench_ownTeamStats_aggr,
 df_awayTeam_startingPlusBench_oppTeamStats_aggr,
 starting_five_awayTeam,
 bench_awayTeam,
 orig_idx_starting_five_awayTeam,
 orig_idx_bench_awayTeam,
 all_possible_names_starting_five_awayTeam)  = pyHoops.get_awayTeam_stats_perPlayer(df,
                                                dfAwayTeam,idxMinutes,all_minutes_found,cwd)

###########################################
### For the home team, determine statistics
### for the different lineups
###########################################
(df_homeTeam_lineups_ownTeamStats,
 df_homeTeam_lineups_oppTeamStats,
 df_homeTeam_lineups_ownTeamStats_aggr,
 df_homeTeam_lineups_oppTeamStats_aggr) = pyHoops.get_homeTeam_stats_perLineup(df,dfHomeTeam,
                                                     starting_five_homeTeam,bench_homeTeam,idxMinutes,all_minutes_found,cwd)

###########################################
### For the away team, determine statistics
### for the different lineups
###########################################
(df_awayTeam_lineups_ownTeamStats,
 df_awayTeam_lineups_oppTeamStats,
 df_awayTeam_lineups_ownTeamStats_aggr,
 df_awayTeam_lineups_oppTeamStats_aggr) = pyHoops.get_awayTeam_stats_perLineup(df,dfAwayTeam,
                                                     starting_five_awayTeam,bench_awayTeam,idxMinutes,all_minutes_found,cwd)


# Defining plotting parameters for the post-processing phase
pos_logo   = [0.0, 0.7, 0.3, 0.3]
axis_font  = {'fontname':'Arial', 'size':'14'}

#################################################
### Additional dataframes and plots for home team
#################################################

(df_2p_perc_homeTeam_lineups_ownTeamStats_aggr,
df_2p_perc_homeTeam_lineups_oppTeamStats_aggr,
df_2p_perc_homeTeam_player_ownTeamStats_aggr,
df_2p_perc_homeTeam_player_oppTeamStats_aggr,
df_fg_perc_homeTeam_lineup_ownTeamStats_aggr,
df_fg_perc_homeTeam_lineup_oppTeamStats_aggr,
df_fg_perc_homeTeam_player_ownTeamStats_aggr,
df_fg_perc_homeTeam_player_oppTeamStats_aggr,
df_homeTeam_offDef_efficiency_perLineup,
df_homeTeam_offDef_efficiency_perPlayer) = pyHoops.plot_team_statistics(df_homeTeam_lineups_ownTeamStats_aggr,
                             df_homeTeam_lineups_oppTeamStats_aggr,
                             df_homeTeam_startingPlusBench_ownTeamStats_aggr,
                             df_homeTeam_startingPlusBench_oppTeamStats_aggr,
                             cwd,
                             team_list_logos,idx_logo_homeTeam,dfHomeTeam,
                             starting_five_homeTeam,
                             bench_homeTeam,
                             orig_idx_starting_five_homeTeam,
                             orig_idx_bench_homeTeam,string_homeTeam,pos_logo,axis_font)

#################################################
### Additional dataframes and plots for away team
#################################################
(df_2p_perc_awayTeam_lineups_ownTeamStats_aggr,
df_2p_perc_awayTeam_lineups_oppTeamStats_aggr,
df_2p_perc_awayTeam_player_ownTeamStats_aggr,
df_2p_perc_awayTeam_player_oppTeamStats_aggr,
df_fg_perc_awayTeam_lineup_ownTeamStats_aggr,
df_fg_perc_awayTeam_lineup_oppTeamStats_aggr,
df_fg_perc_awayTeam_player_ownTeamStats_aggr,
df_fg_perc_awayTeam_player_oppTeamStats_aggr,
df_awayTeam_offDef_efficiency_perLineup,
df_awayTeam_offDef_efficiency_perPlayer) = pyHoops.plot_team_statistics(df_awayTeam_lineups_ownTeamStats_aggr,
                             df_awayTeam_lineups_oppTeamStats_aggr,
                             df_awayTeam_startingPlusBench_ownTeamStats_aggr,
                             df_awayTeam_startingPlusBench_oppTeamStats_aggr,
                             cwd,
                             team_list_logos,idx_logo_awayTeam,dfAwayTeam,
                             starting_five_awayTeam,
                             bench_awayTeam,
                             orig_idx_starting_five_awayTeam,
                             orig_idx_bench_awayTeam,string_awayTeam,pos_logo,axis_font)


