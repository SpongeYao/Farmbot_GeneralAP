StepperControl
==========================
The Python code with a user interface is porvided with following functions:
1. 2-axis stepper-motor control
2. auto scanning function by setting start point, scanning interval and scanning amount
3. real-time image display 
4. image processing function(otsu method is provided here)

![GUI of gui_main.py](./gui_1.png)

> The communication between Arduino and computer is automatically built when the program is opened. If the connection is failed, it can be re-built again by clicking the 'Connect to Arduino' button in menubar


> The parameters on UI are saved automatically after the program is closed. 

```command line: 
python gui_main.py
```

### Arduino Code
Reference by Farmbot:
    https://github.com/FarmBot/farmbot-arduino-firmware 

### Command line for install Arudino and its related lib
```
sudo apt-get install arduino gcc-avr avr-libc avrdude python-configobj python-jinja2 python-serial
mkdir tmp
cd tmp
git clone https://github.com/miracle2k/python-glob2
cd python-glob2
wget https://bootstrap.pypa.io/ez_setup.py -O - | sudo python
sudo python setup.py install
git clone git://github.com/amperka/ino.git
cd ino
sudo make install
cd ~/tmp/
git clone  https://github.com/FarmBot/farmbot-arduino-firmware
cd farmbot-arduino-firmware
ino build
ino upload
```

### Python lib
Tkinter
opencv
python-serial


