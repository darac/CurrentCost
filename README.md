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

Configuration
-------------

The munin plugin is a multigraph plugin, so you'll need Munin version 1.4.0 or newer. You will also need the following perl modules (use CPAN or your OS's package manager):

* XML::Simple
* Device::SerialPort
* YAML
* Time::Local

Install the plugin by symlinking it into your `/etc/munin/plugins` directory.

Next, add the following to your Plugin configuration file (the easiest way is to create a new file `/etc/munin/plugin-conf.d/currentcost`):

    [currentcost]
    env.device          /dev/ttyUSB0
    env.baud            2400
    env.tick            6
    env.currency        £
    env.rate1           13.9
    env.rate1qty        900
    env.rate2           8.2
    env.nightrate       0
    env.nighthours      23:30-06:30
    env.standingcharge  0.0
    env.metertype       CC128

The configuration can be broken down into the following sections

### Device

* env.device

   Specfies the device node where the CurrentCost monitor can be found. You may find it useful to use a udev rule to symlink this somewhere permanent.

* env.baud

  Specifies the baud rate to use. CurrentCost devices may speak at 2400, 9600 or 57600 baud, depending on their age.

* env.tick

  How long, in seconds, to consider data valid for. CurrentCost monitors typically put out data every 6 or 10 seconds. If Munin does a data run less than "env.tick" seconds after a config run, there's no need to wait for more data.

* env.metertype

  The model of the meter. Currently "CC02" and "CC128" are supported.

### COSTS

* env.currency

  The currency symbol to use on the cost graph. CurrentCost typically uses "£" or "€", but you may find "$" more to your taste.

* env.rate1

  The primary rate in hundredths of a "env.currency" per kWh. (i.e.  pence/cents per kWh)

* env.rate1qty

  How many kWh per month are charged at "env.rate1". Some tariffs charge one rate for the first so many units and then another rate for the remainder. If you are charged a flat rate per unit, set this to 0.

* env.rate2

  The secondary rate in hundredths of a "env.currency" per kWh. (i.e.  pence/cents per kWh)

* env.nightrate

  The night rate in hundredths of a "env.currency" per kWh. Some tariffs (such as Economy 7) charge differently during the night and typically require a meter capable of reading two rates. If you do not have such a tariff, set this to 0.

* env.nighthours

  The time period for which "env.nightrate" applies. This should be of the form "hh:mm-hh:mm" and should span midnight.


Tweeter
=======

This script reads the RRDs provided by Munin (so you need to be running the munin script above) and summarises the output into daily tweets of the form:

    Whole House Energy for 18/06/2012: 12.81kWh (Maximum: 2596W @ 17:45, Minimum: 429W @ 11:20) #CurrentCost

Configuration
-------------

You should start by calling:

    python EnergyTweeter.py --mode=setup --host=foobar.example.org

where `foobar.example.org` is the munin host to which the CurrentCost is attached. *Note*: you want to run `EnergyTweeter.py` on the Munin Master host, but that, of course, doesn't have to be the host running the munin plugin.

You should be walked through authorising the plugin with twitter.

Next, run:

    python EnergyTweeter.py --mode=getenergy

to see the data being read. You can run:

    python EnergyTweeter.py --mode=tweetenergy

to put out your first tweet, but you will most likely find it useful to add

    python EnergyTweeter.py --mode=cron

to a cron job.
