# Replication Package

This repository contains source code of PDTDroid, the transformation rules that we have summarized and the defined privacy specifications of five app subjects (per our cooperation agreement with ByteDance, we cannot disclose the real privacy specifications they provided).

## Directory Structure

    home
       |
       |--- code:                           The source code of PDTDroid
           |
           |--- start.py:                       The entry of PDTDroid, which accepts the tool parameters
           |--- fuzzing.py:                     The main module of our property-driven testing approach
           |
       |--- define:                            The defined privacy specifications of five app subjects
       |

## PDTDroid

PDTDroid is an automated GUI testing tool to support the application of our property-driven testing approach, which can effectively validate privacy-related functionalities.


### Download

```
git clone https://github.com/property-driven-privacy-testing/home.git
```

### Environment

If your system has the following support, you can directly run PDTDroid 
- Android SDK: API 26+
- Python 3.7
We use some python libraries, you can install them as prompted, for example:
```
pip install langid
```
Since the app we tested is too large to run on the emulator, you need to connect two real Android devices to the computer for testing, and get their serial numbers with the following command:
```
adb devices
```

### Run

#### Check Specifications
You can run our property-driven testing approach with the following command:
```
python code/start.py -app_path app/app_name.apk -choice guide -device_serial_1 x -device_serial_2 y -rule_name 1_
```

#### Generate LTL Formula 
You can convert the natural language specifications to LTL formulas with the following command:
```
python code/start.py -app_path app/app_name.apk -choice convert -device_serial_1 x -device_serial_2 y -rule_name 1_
```

#### Record Action
You can record the event trace of the proposition with the following command:
```
python code/start.py -app_path app/app_name.apk -choice "record p" -device_serial_1 x -device_serial_2 y -rule_name 1_
```

Here, 
* `-app_path` path of the app under test (AUT). 
* `-choice` The name of the function of PDTDroid.
* `-device_serial_1` The serial number of the device logged in to user A.
* `-device_serial_2` The serial number of the device logged in to user B.
* `-rule_name` prefix for file names that define specifications.


