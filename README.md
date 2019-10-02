# pyHoops
pyHoops: a Python package to web-parse basketball games' play-by-play data and compute advanced statistics

![LogoMakr_2zgNYE](https://user-images.githubusercontent.com/55788224/65873275-f52afe80-e382-11e9-81aa-f28caf32f5c9.png)

## About:

Using pyHoops, a play-by-play report of a basketball game (see Figure below. Source: Lega Basket Serie A website)

![Screen Shot 2019-10-02 at 9 51 30 AM (2)](https://user-images.githubusercontent.com/55788224/66027310-e5362a80-e4fa-11e9-8acc-6d75b5c3e131.png)

can be web-parsed, and basketball statistics per lineup and per player can be easily computed. In the Figure below, it is depicted the offensive efficiency vs. the defensice efficiency (per player) of the Italian basketball team Germani Basket Brescia for the game against A|X Armani Exchange Milano, whose play-by-play report is available [here](http://web.legabasket.it/game/1672517/a_x_armani_exchange_milano-germani_basket_brescia-65:73/pbp). 

![offDef_eff_perPlayergermanibasketbrescia](https://user-images.githubusercontent.com/55788224/66026681-a5227800-e4f9-11e9-8fcd-d69c58f6c2ab.png)

The output is a sequence of dataframes and Figures reporting the contribution of a specific lineup or player on the flow of the game, in terms of field goal percentage, offensive/defensive efficiency, etc, both of the own team and of the opposing team. This is a set of statistics which is generally not available (at least in European basketball leagues), but which provides more valuable information on the impact of lineups and players on the game. As example, a player might contribute positively on his/her team offense (high offensive efficiency), but also negatively affect his/her team defense (high defensive efficiency).

With pyHoops, statistics for a single game can be easily stored as spreadsheets, with the overarching goal of collecting statistics foe every game of the season and build more extensive team-specific datasets to better understand the impact of lineups and players on the performance of the team.

## Installation:

## Dependencies:

pyHoops requires the following python packages: <code>bs4</code>, <code>numpy</code>, 


## Example:



##  License:

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

## Contributing:

We welcome all feedback

