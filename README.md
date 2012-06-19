CurrentCost
===========

Munin Plugin to read CurrentCost meters, plus Tweeting script.

The project consists of two main files:

* currentcost
  The munin plugin

* EnergyTweeter.py
  The tweeting script

Munin
-----

The munin plugin works with [Munin](http://munin-monitoring.org/). When set up, the plugin reads data from your attached CurrentCost meter every five minutes (or however often Munin calls it). Munin will then produce three graphs based on the resulting data.

* CurrentCost Consumption

  ![CurrentCost Consumption Weekly Graph](https://github.com/darac/CurrentCost/raw/master/images/currentcost-week.png)

  This foo

* CurrentCost Cost

Tweeter
-------

Something about EnergyTweeter here.
