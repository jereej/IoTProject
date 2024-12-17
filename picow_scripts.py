import config
import network
import ssl
import time
from machine import Pin, I2C
from bmp280 import BMP280
from robust import MQTTClient


led_pin = Pin("LED", Pin.OUT)


def setup_i2c():
    # Sets up the I2C and BMP objects for data retrieval
    i2c = machine.I2C(id=0, sda=Pin(0), scl=Pin(1))
    timestamp = get_timestamp()
    # Printing out the found i2c devices due to problems with sensor
    print(f"{timestamp} [DEBUG] i2c scan: {i2c.scan()}")
    bmp = BMP280(i2c)
    if bmp and i2c:
        timestamp = get_timestamp()
        print(f"{timestamp} [DEBUG] bmp: {bmp}, i2c: {i2c}")
        return i2c, bmp


def test_bmp():
    # Used to simply test that I2C and BMP objects are created correctly
    # Created because of problems with sensor, problems were fixed by using a different sensor
    i2c, bmp = setup_i2c()
    if i2c and bmp:
        try:
            while True:
                timestamp = get_timestamp()
                print(f"{timestamp} [INFO] temp: {bmp.temperature}, pressure: {bmp.pressure}")
        except KeyboardInterrupt:
            timestamp = get_timestamp()
            print(f"{timestamp} [INFO] Session interrupted by user.")


def connect_to_wifi():
    # Creates the wlan object and connects to WiFi
    ssid = config.SSID
    pw = config.PW
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, pw)
    tries = 0
    while tries < 50:  # High maximum retry value due to problems in connecting to WiFi with a mobile phone hotspot
        if wlan.status() == 3:
            break
        tries += 1
        timestamp = get_timestamp()
        print(f"{timestamp} [INFO] Establishing WiFi connection, wlan status: {wlan.status()}")
        time.sleep(1)
    if wlan.status() != 3:
        timestamp = get_timestamp()
        raise RuntimeError(f"{timestamp} [ERROR] Failed to establish WiFi connection in {tries + 1} tries.")
    ip_address = wlan.ifconfig()
    timestamp = get_timestamp()
    print(f"{timestamp} [INFO] WiFi connection established successfully. IP address is: {ip_address[0]}")
    return wlan, ip_address[0]


def setup_mqtt():
    # Sets up the (umqtt.robust) MQTTClient
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.verify_mode = ssl.CERT_NONE
        client = MQTTClient(client_id=config.MQTT_CLIENT, server=config.MQTT_BROKER, port=config.MQTT_PORT,
                            user=config.MQTT_USERNAME, password=config.MQTT_PW, ssl=context, keepalive=7200)
        client.reconnect()  # Used in place of client.connect() due to problems with restarting the MQTTClient
        return client
    except OSError:
        timestamp = get_timestamp()
        print(f"{timestamp} [ERROR] OSError in setup_mqtt()")


def publish_with_mqtt(client, topic, value):
    client.publish(topic, value)
    timestamp = get_timestamp()
    print(f"{timestamp} [INFO] [MQTT] Published {value} to {topic} topic.")


def on_message(topic, msg):
    # Prints out the message received on a topic.
    # If received message is ON --> turns the led ON
    # If received message is OFF --> turns the led off
    timestamp = get_timestamp()
    print(f"{timestamp} [INFO] [MQTT] Received message: {msg} on topic: {topic}")
    if msg == b"ON":
        led_pin.on()
        timestamp = get_timestamp()
        print(f"{timestamp} [INFO] [Pico W] LED is ON")
    elif msg == b"OFF":
        led_pin.off()
        timestamp = get_timestamp()
        print(f"{timestamp} [INFO] [Pico W] LED is OFF")


def get_timestamp():
    # Timestamp formatted in dd/mm/yyyy h min s, single digit values are padded to keep print lengths uniform
    year, month, day, hour, minute, second, _, _ = time.localtime()
    return "[{:02d}/{:02d}/{} {:02d}h {:02d}min {:02d}s]".format(day, month, year, hour, minute, second)


def main():
    # NOTE: The function requires influxDB, node-red and grafana to be installed and running.
    #       Instructions on how to do that were deliberately left out.
    # Notes on how to start up applications if closed:
        # influxDB (mac --> influxd / windows --> cd <installation_path> --> .\influxd.exe)
        # open browser at localhost:8086 --> login creds: config.INFLUXDB_USER:config.INFLUXDB_PW
        # grafana (mac --> brew services start grafana / windows --> bin\grafana-server.exe)
        # open browser at localhost:3000 --> login creds: admin:admin
        # node-red --> give command node-red and open browser at localhost:1880
    
    # Main functionality of the program is done here. The function will try to establish a WiFi connection
    # After that it will try to set up the (umqtt.robust) MQTTClient
    # After that it will try to se up the i2c functionality
    # Finally, it will listen to messages in config.MQTT_CLIENT/control topic and send messages to
    # config.MQTT_CLIENT/temperature and config.MQTT_CLIENT/pressure topics.
    
    # Pressure is modified and rounded to represent hPa instead of Pa, temperature is displayed as is.
    wlan, _ = connect_to_wifi()
    client = setup_mqtt()
    try:
        time.sleep(3)
        _, bmp = setup_i2c()
        client.set_callback(on_message)
        client.subscribe(b"{}/control".format(config.MQTT_CLIENT))
        while True:
            publish_with_mqtt(client, f"{config.MQTT_CLIENT}/temp", str(bmp.temperature))
            publish_with_mqtt(client, f"{config.MQTT_CLIENT}/pressure", str(round((float(bmp.pressure) / 100), 2)))
            client.check_msg()
            time.sleep(5)
            # If the WiFi connection breaks at any point while running the program, tries to reconnect 5 times.
            # If reconnection is unsuccessful, will stop the program completely
            if wlan.status() != 3:
                timestamp = get_timestamp()
                print(f"{timestamp} [INFO] WiFi connection is broken. Sleeping 5s and trying to re-establish connection.")
                wlan.disconnect()  # Clear existing WiFi connections
                wlan = None        # Clear existing WiFi connections
                ip = None          # Clear existing WiFi connections
                time.sleep(5)
                tries = 0
                while tries < 5:
                    try:
                        tries += 1
                        wlan, ip = connect_to_wifi()  # Try to establish WiFi connection
                        if wlan and ip:
                            timestamp = get_timestamp()
                            print(f"{timestamp} [DEBUG] wlan: {wlan} ip: {ip}")
                            break
                    except RuntimeError:
                        if 5 - tries == 0:
                            break
                        timestamp = get_timestamp()
                        print(f"{timestamp} [INFO] Trying {5 - tries} more time(s) to re-establish WiFi connection")
                        
                if not ip:
                    # WiFi connection couldn't be re-established in 5 tries
                    timestamp = get_timestamp()
                    print(f"{timestamp} [INFO] Unable to re-establish WiFi connection. Stopping the program")
                    break
                time.sleep(2)
                client.reconnect()
    except KeyboardInterrupt:
        print("Program stopped")


if __name__ == '__main__':
    main()
