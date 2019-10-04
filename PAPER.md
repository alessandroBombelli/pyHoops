---
title: 'pyHoops: A Python package for advanced basketball data analytics'
tags:
  - Python
  - basketball
  - web-parsing
  - data analysis
authors:
  - name: Alessandro Bombelli
    orcid: 0000-0001-7889-9552
    affiliation: Air Transport & Operations, Faculty of Aerospace Engineering, Delft University of Technology
date: 04 October 2019
bibliography: pyHoops_references.bib
---

# Summary

Advanced data analytics has received contrasting opinions within the sport community. One of the greatest American Football of all times, Bill Belichick, stated that he uses analytics "less than zero" when preparing games [@belichick2019]. On the other end, the movie "Money Ball" stressed the necessity of advanced data analytics in baseball, i.e., sabermetric, to improve team's performances. Restricting the field of view to basketball, there exist, especially in the United States, a strong interest towards data science to enhance players' performances. Europe, on the other hand, is still a step behind in this sense. While statistics on individual performances of players are generally available after games in the form of box scores, such statistics are generally miopic. In fact, being individual statistics, they cannot fully grasp the impact of a player on his/her team while on the court and, equally importantly, the impact on the opposing team.

Basketball games in most European leagues and in Euroleague (the most important European basketball competition) are paired with a play-by-play report that maps every action (field goal made or attemped, foul, assist, substitution) of the game. Goal of ``pyHoops`` is to process such play-by-play reports to extrapolate performance indices that map the impact of players or lineups on the own and opposing team. As example, a player might be a prolific scorer, hence positively affecting his/her own offense, but a below-average defender, and thus negatively affect the team.

``pyHoops`` is based on two major blocks: (1) web-parsing to translate play-by-play html tables into <code>pandas</code> databases, and (2) computation of statistics and performance indices. The web-parsing block easily stores play-by-play reports by automatically aceessing the associated webpage. Since webpages (and html tables) vary according to the specific league, the web-parsing block is league-specific and should be modified according to underlying html structure of the webpages of interest. As a last resort, play-by-play reports and boxscores can be directly copied from the webpage, saved as spreadsheets and loaded as databases to skip the web-parsing block. The secondo block uses play-by-play information to aggregate statistics for every distinct player and lineup, both for the own team and the opposing team.

Having now team-aggregated and not player-specific information, ``pyHoops`` can easily compute and compare, as example, the field goal percentage of the home team when a particular player was on the court, versus the field goal percentage of the away team when the same player was on the court. While each call of ``pyHoops`` focuses on a single game, season-wide statistics can be computed by running ``pyHoops`` everytime a new game occurs and storing new information in a <code>pandas</code> database, with the overarching goal of creating season-specific databases.

We hope ``pyHoops`` can foster a better understanding and interest in advanced team-oriented basktetball statistics within the European basketball movement. Although some works already exist in the academic literature addressing advanced basketball analytics for European basketball [@travassos:2013;metulini:2018], we believe this work to be the first one (i) to focus on aggregated team-oriented statistics rather than individual-oriented statistics, and (ii) to provide an open-source package to be used be team data analysts of basketball enthusiasts to perform such analyses.      


# Acknowledgements

The contribution of Luca Cappelletti in the development phase of the package is warmly acknowledged.

# References


