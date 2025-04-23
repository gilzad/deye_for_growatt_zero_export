# Introduction
This code reads out the power consumption from a Deye 12k inverter and dynamically limits the power of a Growatt MIN inverter to comply with a zero-export policy.

## Background
The Deye SUN-12K-SG04LP3-EU already has an integrated energy meter. In my use case the Deye inverter uses its own current transformers (CTs) to monitor the power on grid connection. Instead of adding another energy meter to enable the zero-export control of my second Growatt MIN 4600TL-XH inverter, I prefer to retrieve the data from the Deye's integrated energy meter and feed the Growatt inverter with it.

In my environment this code successfully runs on a raspberry pi (really, any Rpi with two USB connections can handle this). The raspi is connected with two USB-to-RS485 adapters to each of the inverters.

## How to use
* Make sure your physical serial connections work.
  - For the Deye inverter I use the first two pins of its "Modbus" RJ45 port.
    * I checked the connection with `modpoll -b 9600 -p none -m rtu -t 4:hex   -a 1 -r 1 -c 100 /dev/ttyS0` (see the source below)
  - For the Growatt inverter I use its "Sys COM Port" pins `5` and `6`.
    * And you have to enable a "Export Limit" with a "Smart Meter" and set the power limit "000.0%" in its "Advanced Settings".
* Place the three Python files into one folder.
* Ensure you've got the `pymodbus` library installed.
* Ensure the paths for the serial connections correspond to the respective inverter. Change the hardcoded paths if needed.
* In that folder, run `python3 main.py`.

# Motivation
I tried to keep the project as simple as possible. That means:
* Use a spare Raspberry Pi that I have at hand.
* Avoid any aditional dependencies other than the pymodbus library for the Modbus client.
* Don't do anything else, just use the Deye's integrated smart meter and control the Growatt.
* Keep the code transparent, so I can quickly grasp what's happening.
* I only have so much time for now. But for greater goals there are many awesome projects out there and I might use them.

## Important Notes
* The serial connections are hardcoded in `main.py`. In its current state the code expects the Deye inverter at `/dev/ttyUSB0` and the Growatt inverter at `/dev/ttyUSB1`. Change that for your environment accordingly.
* If you use the library `pymodbus` **2.x**, uncomment and comment the corresponding lines in `poll_deye.py`. I wrote notes where which line suits which `pymodbus` library.
* I experienced that my Growatt inverter does not really react to the value from the total system power (register 52) the expected way. Instead of adjusting its power to the value, it takes any positive value around `+35` to increase its power. A negative value around `-35` makes it reduce its power and a value in between (I chose `20`) keeps the currently generated power level.
  - This means I cannot set a target power immediately but have to let the inverter move towards it.
* The code for the Growatt inverter is hardcoded to be a modbus server with the device address `2`, because that's how the inverter expects an SDM630 smart meter to communicate with it.
* The code for the Deye inverter is hardcoded with the client address `1`. You can change it easily by adjusting the second parameter for `read_holding_registers` accordingly.

## Acknowledgments
Without all the knowledge on the forums and on Github I'd be pretty lost. The most important ones that I can still remember are:
* https://github.com/EmbedME/growatt_simulate_sdm630/tree/main
  - This project has covered a great deal of a working communication with a valid CRC, completely without `pymodbus`.
  - For my MIN 4600TL-XH I had to remove the condition against register `52` (my inverter needs _some_ response before it queries `52`). But it helped me get going and find the values that control my Growatt inverter.
  - Really, the code in `simulate_sdm630.py` is basically the original from EmbedME wrapped in a class so I can use it as a separate instance.
* https://github.com/hankipanky/esphome-fake-eastron-SDM630/tree/master
  - From here I could assemble a dictionary for all possible queries.
    * However, my Growatt MIN 4600TL-XH only queries a few registers and I could return 0 for all except for register `52`, actually. But I have to respond _something_ to the other queries, else my inverter will not ask for `52` either.
  - This developer has put great effort in hardware and software. The github page has some thorough and helpful explanations, too.
* https://powerforum.co.za/topic/11513-connecting-a-raspberry-pi-3b-to-deye-inverter/#findComment-141248
  - This post utilizes `modpoll` to verify a working connection and describes what the response means.
  - It helped me have a simple way to check if my modbus connection was working at all.
