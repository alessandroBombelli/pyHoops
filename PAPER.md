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
date: 13 August 2017
bibliography: pyHoops_references.bib
---

# Summary

Advanced data analytics has received contrasting opinions within the sport community. One of the greatest American Football of all times, Bill Belichick, stated that he uses analytics "less than zero" when preparing games. On the other end, the movie "Money Ball" stressed the necessity of advanced data analytics in baseball, i.e., sabermetric, to improve team's performances. Restricting the field of view to basketball, there exist, especially in the United States, a strong interest towards data science to enhance players' performances. Europe, on the other hand, is still a step behind in this sense. While statistics on individual performances of players are generally available after games in the form of box scores, such statistics are geenrally miopic. In fact, being individual statistics, thaty cannot fully grasp the impact of a player on his/her team while on the court and, equally importantly, the impact on the opposing team.

Basketball games of most European leagues and of the Euroleague are provided with a play-by-play report that maps every action (field goal made or attemped, foul, assist, substitution) of the game. Goal of ``pyHoops`` is to process such play-by-play reports to extrapolate performance indices that map the impact of players or lineups on the own and opposing team. As example, a player might be a prolific scorer, hence positively affecting his/her onw offense, but a below-average defender, and thus affecting negatively the defensive effort.

``pyHoops`` is based on two major blocks: (1) web-parsing to translate play-by-play html tables into databases, and (2) computation of statistics and performance indices using the retrieved databases. The web-parsing block easily stores play-by-play reports using as inputs the urls to the play-by-play report and the boxscore. Since webpages (and html tables) vary according to the specific league, the web-parsing block is league-specific and should be modified given an inspection of the underlying html structure of the webpages of interest. As a last resort, play-by-play reports and boxscores can be directly copied from the webpage, saved as spreadsheets and loaded as databases to skip the web-parsing block. The secondo block uses play-by-play information to aggregate statistics for every distinct player and lineup, referring to the own team and the opposing team. To provide a more tangible example, ``pyHoops`` can translate a play-by-play report ![Example figure.](figure.png) 

Having now team-aggregated and not player-specific information, ``pyHoops`` can easily compute and compare, as example, the field goal percentage of the home team when a particular player was on the court, versus the field goal percentage of the away team when the same player was on the court. While each call of ``pyHoops`` focuses on a single game, season-wide statistics can be computed by running ``pyHoops`` everytime a new game occurs and storing new information in a <code>pandas</code> database, as example.

This full set of statistics could be used by coaches to predict the best matchups during a game and improve team's performances. We believe ``pyHoops`` could be a first step towards a better understanding and usage of advanced team-oriented basktetball statistics within the European basketball movement. Although some works already exist in the academic literature addressing advanced basketball analytics for European basketball, we believe this work to be the first one (i) to focus on aggregated team-oriented statistics rather than individual-oriented statistics, and (ii) to provide an open-source package to be used be team data analysts of basketball enthusiasts to perform such analyses.      



The forces on stars, galaxies, and dark matter under external gravitational
fields lead to the dynamical evolution of structures in the universe. The orbits
of these bodies are therefore key to understanding the formation, history, and
future state of galaxies. The field of "galactic dynamics," which aims to model
the gravitating components of galaxies to study their structure and evolution,
is now well-established, commonly taught, and frequently used in astronomy.
Aside from toy problems and demonstrations, the majority of problems require
efficient numerical tools, many of which require the same base code (e.g., for
performing numerical orbit integration).

``Gala`` is an Astropy-affiliated Python package for galactic dynamics. Python
enables wrapping low-level languages (e.g., C) for speed without losing
flexibility or ease-of-use in the user-interface. The API for ``Gala`` was
designed to provide a class-based and user-friendly interface to fast (C or
Cython-optimized) implementations of common operations such as gravitational
potential and force evaluation, orbit integration, dynamical transformations,
and chaos indicators for nonlinear dynamics. ``Gala`` also relies heavily on and
interfaces well with the implementations of physical units and astronomical
coordinate systems in the ``Astropy`` package [@astropy] (``astropy.units`` and
``astropy.coordinates``).

``Gala`` was designed to be used by both astronomical researchers and by
students in courses on gravitational dynamics or astronomy. It has already been
used in a number of scientific publications [@Pearson:2017] and has also been
used in graduate courses on Galactic dynamics to, e.g., provide interactive
visualizations of textbook material [@Binney:2008]. The combination of speed,
design, and support for Astropy functionality in ``Gala`` will enable exciting
scientific explorations of forthcoming data releases from the *Gaia* mission
[@gaia] by students and experts alike. The source code for ``Gala`` has been
archived to Zenodo with the linked DOI: [@zenodo]

# Acknowledgements

We acknowledge contributions from Brigitta Sipocz, Syrtis Major, and Semyeong
Oh, and support from Kathryn Johnston during the genesis of this project.

# References

https://bleacherreport.com/articles/2855622-patriots-bill-belichick-uses-analytics-less-than-zero-in-decision-making

