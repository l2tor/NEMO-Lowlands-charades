This is the repository for the NEMO-Lowlands gameful gesture elicitation procedure.
A reference to the paper describing this study will appear here soon.

## Prerequisites ##
* Install Microsoft Visual C++ Redistributable for Visual Studio 2010 (64 bit): https://www.microsoft.com/en-us/download/details.aspx?id=14632
* Install Python 2.7
* Install Kinect SDK for Windows: https://www.microsoft.com/en-us/download/details.aspx?id=44561 (don't forget to reboot after)
* Install Microsoft Visual C++ 9.0 compiler for Python: http://aka.ms/vcpython27
* Install numpy
* Install nwalign
* Install matplotlib
* Install scipy
* Install easywebdav (for uploading files to a WebDAV server online)
* Install NAOqi Python SDK

Note: tested with the robot simulator from Choregraphe 2.1.4 (NAO V5), and the physical NAO V5 robot.

## To get things to work ##
* Build the Shared project
* Move the resulting .dll into the bin/Debug or bin/Release directory of the ControlPanel and KinectRecorder
* Place the files you can download [here](https://drive.google.com/open?id=13FMTFR3VtWSZRNBbyZVAFamF-9ybCEM-) into the bin/Release directory of the KinectRecorder
* Build the ControlPanel and KinectRecorder projects
* Change the IP address in web_client/web_client.js into the address of the computer that is running the main game
* Start the ControlPanel, change the IP address to your robot's IP address, and connect to it
* Open the web_client on the participant-facing tablet device
* Start the experiment from the ControlPanel
