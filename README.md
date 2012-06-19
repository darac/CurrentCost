CurrentCost
===========

Munin Plugin to read CurrentCost meters, plus Tweeting script.

The project consists of two main files:

* currentcost
  The munin plugin

* EnergyTweeter.py
  The tweeting script

Munin
=====

The munin plugin works with [Munin](http://munin-monitoring.org/). When set up, the plugin reads data from your attached CurrentCost meter every five minutes (or however often Munin calls it). Munin will then produce three graphs based on the resulting data.

* CurrentCost Consumption

  ![CurrentCost Consumption Weekly Graph](https://github.com/darac/CurrentCost/raw/master/images/currentcost-week.png)

  This graph shows the "live" reading from the CurrentCost meter as well as a one-hour moving average.

* CurrentCost Estimated Cost

  ![CurrentCost Estimated Cost Weekly Graph](https://github.com/darac/CurrentCost/raw/master/images/currentcost_cost-week.png)

  This graph shows the estimated monthly bill.

* CurrentCost Total Usage

  ![CurrentCost Total Usage Weekly Graph](https://github.com/darac/CurrentCost/raw/master/images/currentcost_cumulative-week.png)

  This graph shows the cumulative usage over the period of the graph as well as a version that resets at midnight.

Tweeter
=======

This script reads the RRDs provided by Munin (so you need to be running the munin script above) and summarises the output into daily tweets of the form:

  Whole House Energy for 18/06/2012: 12.81kWh (Maximum: 2596W @ 17:45, Minimum: 429W @ 11:20) #CurrentCost


