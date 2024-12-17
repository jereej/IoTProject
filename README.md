# IoTProject
This repository is created to store the python code for our group project. The files `bmp280.py`, `robust.py` and `simple.py` aren't created by us, we had some problems with importing the libraries onto the RaspberryPi Pico W that was provided to us, so we downloaded them manually onto the machine.

The imported libraries can be found from:
- [micropython/micropython-lib/micropython/](https://github.com/micropython/micropython-lib/tree/e4cf09527bce7569f5db742cf6ae9db68d50c6a9/micropython) (Official Micropython GitHub)
    - `umqtt.robust/umqtt/robust.py` => `robust.py`
        - Slight changes to how `simple.py` is imported due to us just importing the file in the same folder as our `picow_scripts.py` file.
    - `umqtt.simple/umqtt/simple.py` => `simple.py`
- [micropython.bmp280/bmp280.py](https://github.com/dafvid/micropython-bmp280/blob/master/bmp280.py) (Repository by Dafvid (David Stenwall))

>NOTE: Information in config.py file is redacted because it normally would contain sensitive information such as API tokens, passwords, etc.

The `picow_scripts.py` file contains all the code required to run the program. The file is created based on the exercises done during the course.
