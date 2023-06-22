# Kinector
A Kinect motion capture add-on for Blender.

## Installation
Download the latest release, then use the `Install` button in Blender's add-ons menu to select the downloaded file. Use the checkbox to enable the add-on.

## Usage
Kinector transfers joint positions to named empties. Empties are suffixed with which body the joint belongs to. For example, the "SpineBase" joint for body "0" would be named "SpineBase0". Joints can be easily created by using `Add > Kinector Body` from the 3D viewport.

Kinector settings are controlled with the Kinector panel found under the `Misc` tab of the 3D viewport. This panel contains the following controls:

### Update Rate
The rate at which the Kinect is polled for a new frame. The Kinect has a frame rate of 30 frames per second, so values greater than 30 won't increase the frame rate, but may improve latency.

### Process/Observation noise
These parameters control the Kalman filter applied to joint positions. A high process noise and low observation noise will minimise filtering and allow fast movements to be captured. A lower process noise and higher observation noise will apply stronger filtering to reduce noise.

### Body Offset
Offsets which bodies are controlled by the Kinect. This can be used to quickly capture many performances.

### Insert Keyframes
When enabled, keyframes will be inserted when a new frame is received from the Kinect.

### Connect/Disconnect
Attempt to connect to or disconnect from the Kinect.

## Development
Ensure both [Kinect for Windows SDK 2.0](https://www.microsoft.com/en-us/download/details.aspx?id=44561) and [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/) are installed. [Visual Studio Code](https://code.visualstudio.com/) is recommended for development.

Clone this repository, then initialise submodules with `git submodule update --init`. Create a file called `settings.json` in the `.vscode` directory with the following contents:

	{
		"blender_path": "path/to/blender.exe",
		"cmake.environment": {
			"BLENDER_ADDONS_PATH": "path/to/blender/addons"
		}
	}

You can then run the build task with `Ctrl+Shift+B` to compile, copy to Blender's add-ons directory and launch Blender.