# DIO test program

This directory contains files to test robot DIO pin wiring.

It requires a test plug with the schematic in
`docs/wiring_diagrams/dio-test-plug.qet`.  That plug contains two
circuits:

- A red LED across +24V and ground pins to test power
- A blue LED across DOUT and DIN pins to test input and output
  - The diode prevents false test pass if DOUT and DIN are reversed

LEDs are both wired with current-limiting resistors; this is not
required for the blue LED, but protects against miswired circuits.

## Installation

For the QC team, make this start automatically on the desktop in a
terminal (and disable the robot launcher):

```
mkdir ~/.local/share/applications
cp -a install_scripts/dio_test ~
cp install_scripts/dio_test/dio_test-launcher.desktop ~/.local/share/applications
ln -s ../../.local/share/applications/dio_test-launcher.desktop \
    /home/pathpilot/.config/autostart/dio_test-launcher.desktop
rm -f /home/pathpilot/.config/autostart/robot-launcher.desktop
```

## Test procedure

Setup:
- Run the DIO test program `dio_test.sh` on the controller PC
- Install test plug on DIO0

DIO test:
- Confirm power and ground pins wired correctly
  - Red LED glows
- Confirm DIN and DOUT pins wired correctly
  - Blue LED blinks repeatedly
  - *OR* test program console output print "DIO (n) test success"
- Confirm DIO port wired in correct order from 0 to 15
  - DIO port number matches blinking light on IO module
  - *OR* DIO port number matches test program console output "DIO (n)
    test success"
- Install test plug on next DIO connector and repeat
