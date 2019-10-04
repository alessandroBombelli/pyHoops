```python
import sys
import os
# If running the code in the same folder as the package pyHoops.py, replace
# "from pyHoops import pyHoops" with "import pyHoops" 
from pyHoops import pyHoops
```


```python
# Path to current folder
cwd             = os.getcwd()

# List of teams and associated logos. An additional logo is added, to be associated
# with teams that do not have a logo in the folder
team_list = ['brescia','brindisi','cantu','cremona','fortitudobologna',
'milano','pesaro','pistoia','reggioemilia','roma','sassari','trentino',
'treviso','trieste','varese','venezia','virtusbologna']

team_list_logos = ['Brescia.png','Brindisi.png','Cantu.png','Cremona.png',
                   'Fortitudo_Bologna.png','Milano.png'	,'Pesaro.png',
                   'Pistoia.png','Reggio_Emilia.png','Roma.png','Sassari.png',
                   'Trentino.png','Treviso.png','Trieste.png','Varese.png',
                   'Venezia.png','Virtus_Bologna.png','LBA_logo.png'] 
```


```python
# TEST 3: Armani Milano - Brescia (2019-2020 season)
thisUrl         = 'http://web.legabasket.it/game/1672517/a_x_armani_exchange_milano-germani_basket_brescia-65:73/pbp'
thisUrlBoxscore = 'http://web.legabasket.it/game/1672517/a_x_armani_exchange_milano-germani_basket_brescia-65:73'
```


```python
############################################### 
# Extracting all play-by-play info from webpage
###############################################      
df,homeTeam,awayTeam = pyHoops.web_parse_playbyplay(thisUrl)

################# 
# Print game info
#################
pyHoops.print_game_analyzed(homeTeam,awayTeam)
```

    ###########################################################
    Game analyzed is: a|x armani exchange milano vs germani basket brescia
    ###########################################################



```python
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

```


```python
# Plotting some samples of the databases that we created

print(df_awayTeam_startingPlusBench_ownTeamStats_aggr.head())
print(df_awayTeam_lineups_ownTeamStats.head())
```

                  Player  1pm  1pa  2pm  2pa  dunk  3pm  3pa  dreb  oreb  ass  st  \
    0    abassabassawudu    4    4   11   22     1    5   11    14     5    9   2   
    1          caintyler    7    8   14   28     2    4   12    21     8   10   4   
    2          hortonken    8   10   17   29     2    5   14    24     7   13   5   
    3   lansdownedeandre    8   10   18   31     2    6   17    22     9   15   5   
    4  laquintanatommaso    9   10   10   15     1    0   10    11     2    4   5   
    
       to  blk  blkag   f  frec  min  
    0   8    0      0  14     7    0  
    1  13    2      0  13    13    0  
    2  10    3      0  13    15    0  
    3  10    2      0  18    14    0  
    4   5    3      0  11    10    0  
                                                  Lineup  1pm  1pa  2pm  2pa  \
    0  abassabassawuducaintylerhortonkenlansdownedean...    0    0    6    9   
    1  abassabassawuducaintylerhortonkenlansdownedean...    2    2    1    1   
    2  abassabassawuducaintylerhortonkenmossdavidvita...    0    0    0    0   
    3  abassabassawuducaintylerhortonkenmossdavidvita...    0    0    1    3   
    4  abassabassawuducaintylermossdavidsacchettibria...    0    0    0    1   
    
       dunk  3pm  3pa  dreb  oreb  ass  st  to  blk  blkag  f  frec  min  
    0     1    1    1     5     1    1   0   0    0      0  2     1    0  
    1     0    0    0     1     0    0   0   0    1      0  1     0    0  
    2     0    0    0     2     0    0   0   1    0      0  0     1    0  
    3     0    1    2     4     0    0   1   3    0      0  2     3    0  
    4     0    0    0     1     0    0   0   1    0      0  1     0    0  

