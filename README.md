# pyHoops
pyHoops: a Python package to web-parse basketball games' play-by-play data and compute advanced statistics (logo created with [LogoMakr](https://logomakr.com/)).

![LogoMakr_2zgNYE](https://user-images.githubusercontent.com/55788224/65873275-f52afe80-e382-11e9-81aa-f28caf32f5c9.png)

## About:

Using pyHoops, a play-by-play report of a basketball game (see Figure below. Source: Lega Basket Serie A website)

<img width="1211" alt="Screen Shot 2019-11-13 at 10 36 50 PM" src="https://user-images.githubusercontent.com/55788224/68807047-6559bf00-0667-11ea-8aa6-eba2a21a8dbc.png">

can be web-parsed, and basketball statistics per lineup and per player can be easily computed. In the Figure below, it is depicted the offensive efficiency vs. the defensive efficiency (per player) of the Italian basketball team Virtus Roma for the game against Acqua S. Bernardo Cantu', whose play-by-play report is available [here](http://web.legabasket.it/game/1672568/acqua_s__bernardo_cant__-virtus_roma_74:76). 

![offDef_eff_perPlayerroma](https://user-images.githubusercontent.com/55788224/68843407-58b98300-06c8-11ea-9395-dad3aee2a38f.png)

The output is a sequence of dataframes and Figures reporting the contribution of a specific lineup or player on the flow of the game, in terms of field goal percentage, offensive/defensive efficiency, etc, both of the own team and of the opposing team. This is a set of statistics which is generally not available (at least in European basketball leagues), but which provides more valuable information on the impact of lineups and players on the game. As example, a player might contribute positively on his/her team offense (high offensive efficiency), but also negatively affect his/her team defense (high defensive efficiency).

With pyHoops, statistics for a single game can be easily stored as spreadsheets, with the overarching goal of collecting statistics for every game of the season and build more extensive team-specific datasets to better understand the impact of lineups and players on the performance of the team.

## Installation:

The most updated version of pyHoops is directly accessible via the folder <code>tests</code> in this repository. The package <code>pyHoops.py</code> would need to be saved in the same folder as the main code calling it (see Section "Example"). pyHoops will be soon added to PyPi, so that an automatic installation via pip is also possible.

## Dependencies:
pyHoops has been tested on 
- <code>python 2.7.14</code>
- <code>python 3.7.1</code>

As a general note, we recommend to use a python 3.X release, since python 2.7 will soon become deprecated.
pyHoops requires the following python packages: <code>bs4</code>, <code>itertools</code>, <code>matplotlib</code>, <code>numpy</code>, <code>os</code>, <code>pandas</code>, <code>random</code>, <code>re</code>, <code>requests</code>, <code>sys</code>, <code>unicodedata</code>.

## Example
In the folder <copy>tests</copy>, the file <copy>pyHoops_tests.py</copy> can be used to run several tests. The  file directly calls the package <copy>pyHoops.py</copy>, which must be saved in the same folder (we suggest to directly download the folder <code>tests</code> as provided and run tests using the <copy>pyHoops_tests.py</copy> file). To change test, simply comment the two lines defining the play-by-play and boxscore webpages of the current game, and uncomment the lines of the game you are interested in analyzing.

##  License:

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

Copyright <2019, Alessandro Bombelli>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


## Contributing:

We welcome all feedback that might help improve the package.

