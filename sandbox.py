# This imports the "json" module from the Python standard library
# https://docs.python.org/3/library/json.html
import json

# This is outside the scope of beginner Python and VRC, but this is for
# something called "type-hinting" that makes Python code easier to debug
from typing import Any, Callable, Dict

# This imports the Paho MQTT library that we will use to communicate to
# other running processes
# https://github.com/eclipse/paho.mqtt.python
import paho.mqtt.client as mqtt

# This creates a new class that will contain multiple functions
# which are known as "methods"
class Sandbox():
    v_ms = 1
    # The "__init__" method of any class is special in Python. It's what runs when
    # you create a class like `sandbox = Sandbox()`. In here, we usually put
    # first-time initialization and setup code. The "self" argument is a magic
    # argument that must be the first argument in any class method. This allows the code
    # inside the method to access class information.
    def __init__(self) -> None:
        # Create a string attribute to hold the hostname/ip address of the MQTT server
        # we're going to connect to (an attribute is just a variable in a class).
        # Because we're running this code within a Docker Compose network,
        # using the container name of "mqtt" will work.
        self.mqtt_host = "mqtt"
        # Create an integer attribute to hold the port number of the MQTT server
        # we're going to connect to. MQTT uses a default of port 1883, but we'll
        # add a zero, so as to not require administrator priviledges from the host
        # operating system by using a low port number.
        self.mqtt_port = 18830
        # Create an attribute to hold an instance of the Paho MQTT client class
        self.mqtt_client = mqtt.Client()

        # This part is a little bit more complicated. Here, we're assigning the
        # attributes of the Paho MQTT client `on_connect` and `on_message` to handles
        # of methods in our Sandbox class, which are defined below.
        # This isn't *running* those methods, but rather creating a reference to them.
        # Once we start running the Paho MQTT client, this tells the client to execute
        # these methods after it establishes the connection, and after every message
        # it recieves, respectfully.
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        # Create a string attribute to hold the commonly used prefix used in MQTT topics
        self.topic_prefix = "vrc"

        # Here, we're creating a dictionary of MQTT topic names to method handles
        # (as we discussed above). A dictionary is a data structure that allows use to
        # obtain values based on keys. Think of a dictionary of state names as keys
        # and their capitals as values. By using the state name as a key, you can easily
        # find the associated capital. However, this does not work in reverse. So here,
        # we're creating a dictionary of MQTT topics, and the methods we want to run
        # whenever a message arrives on that topic.
        self.topic_map: Dict[str, Callable[[dict], None]] = {
            # This is what is known as a "f-string". This allows you to easily inject
            # variables into a string without needing to combine lots of
            # strings together. Scroll down farther to see what `self.show_velocity` is.
            # https://realpython.com/python-f-strings/#f-strings-a-new-and-improved-way-to-format-strings-in-python
            #f"{self.topic_prefix}/velocity": self.show_velocity,
            #f"{self.topic_prefix}/#": self.aprilTagHeading,
            f"{self.topic_prefix}/apriltags/raw": self.show_AprilTag,
            #f"{self.topic_prefix}/apriltags/raw": self.show_aprilTags,
            }
            

    # Create a new method to effectively run everything.
    def run(self) -> None:
        # Connect the Paho MQTT client to the MQTT server with the given host and port
        # The 60 is a keep-alive timeout that defines how long in seconds
        # the connection should stay alive if connection is lost.
        self.mqtt_client.connect(host=self.mqtt_host, port=self.mqtt_port, keepalive=60)
        # This method of the Paho MQTT client tells it to start running in a loop
        # forever until it is stopped. This is a blocking function, so this line
        # will run forever until the entire program is stopped. That is why we've
        # setup the `on_message` callback you'll see below.
        self.mqtt_client.loop_forever()

    # As we described above, this method runs after the Paho MQTT client has connected
    # to the server. This is generally used to do any setup work after the connection
    # and subscribe to topics.
    def on_connect(self, client: mqtt.Client, userdata: Any, rc: int, properties: mqtt.Properties = None) -> None:
        # Print the result code to the console for debugging purposes.
        print(f"Connected with result code {str(rc)}")
        # After the MQTT client has connected to the server, this line has the client
        # connect to all topics that begin with our common prefix. The "#" character
        # acts as a wildcard. If you only wanted to subscribe to certain topics,
        # you would run this method multiple times with the exact topics you wanted
        # each time, such as:
        #client.subscribe(f"{self.topic_prefix}/velocity")
        # client.subscribe(f"{self.topic_prefix}/location")
        client.subscribe(f"{self.topic_prefix}/apriltags/raw")
        self.open_servo(1)
        self.close_servo(2)
        self.open_servo(3)
        
        

        # If you wanted to be more clever, you could also iterate through the topic map
        # in the `__init__` method, and subscribe to each topic in the keys.
        # For example:
        # for topic in self.topic_map.keys():
        #     client.subscribe(topic)

    # As we described above, this method runs after any message on a topic
    # that has been subscribed to has been recieved.
    def on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        # Print the topic name and the message payload to the console
        # for debugging purposes.

        #prints to the console what you subscribed to in this case april tag data
        print(f"{msg.topic}: f{str(msg.payload)}")

        # First, check if the topic of the message we've recieved is inside the topic
        # map we've created.
        if msg.topic in self.topic_map:
            # We can't send JSON (dictionary) data over MQTT, so we send it as an
            # encoded string. Here, we convert that encoded string back to
            # JSON information for convience.
            payload = json.loads(msg.payload)
            # Lookup the method for the topic, and execute it
            # (with the parentheses) and pass it the payload of the message.
            self.topic_map[msg.topic](payload)

        # By not creating an `else` statement here, we effectively discard
        # any message that wasn't from a topic in our topic map.

    # ================================================================================
    # Now the training wheels come off! Write your custom message handlers here.
    # Below is a very simple example to look at it. Ideally, you would want to
    # have a message handler do something more useful than just printing to
    # the console.
    def show_velocity(self, data: dict) -> None:
        vx = data["vX"]
        vy = data["vY"]
        vz = data["vZ"]
        self.v_ms = (vx, vy, vz) #meters per second
        print(self.v_ms)
        #print(f"Velocity information: {v_ms} m/s")
        # v_fts = tuple([v * 3.28084 for v in v_ms])
        # print(f"Velocity information: {v_fts} ft/s")

    def show_AprilTag(self, data: dict) -> None:
        id = data[0]["id"]
        posX = data[0]["pos"]["x"]
        posY = data[0]["pos"]["y"]
        posZ = data[0]["pos"]["z"]
        #print(self.heading)

        #Distance between each package is .075 m
        #Distance between the center of camera to center of servo 2 is .03 m
        # center = (-.06(x), .06(y))
        #GUI 2nd servo close = drop 
        if (id == 1 and posZ <= .65 and posX >= -.15 and posX <= -0.02 and posY >= -.076 and posY <= .05):#middle servo off set code
            self.close_servo(1)
            print(posX)
            print(posY)
            print(posZ)
        #GUI 3rd servo open = drop
        if (id == 2 and posZ <= .5):#and posX >= -1 and posX <= 0 and posY >= 0 and posY <= 1):#right servo off set code
            self.open_servo(2)

        #GUI 4th servo close = drop
        if (id == 3 and posZ <= .4):# and posX >= -.11 and posX <= .5 and posY >= -.02 and posY <= .08):#left servo off set code
            self.close_servo(3)

        if (id == 5):
            self.LEDcolor("Red")
        if (id == 6):
            self.LEDcolor("Green")
        if (id == 7):
            self.LEDcolor("Blue")
    
    # def aprilTagHeading(self, data: dict) -> None:
    #     self.heading = data[0]["heading"]
    #     print(self.heading)
    #     self.show_AprilTag()
        
        # Finally, we publish the payload to the topic, once again using f-strings to
        # re-use our common prefix.

    # def show_aprilTags(self, data: dict) -> None:
    #     id = data[0]["id"]
    #     pos = data[0]["pos"]
    #     posZ = data[0]["pos"]["z"]
    #     vx = data["vX"]
    #     vy = data["vY"]
    #     vz = data["vZ"]
    #     if (id == 4):
    #         print(f"AprilTag Number: {id}")
    #         print(f"Xvelocity: {vx}")
    #         print(f"Position Z: {posZ}")


    # ================================================================================
    # Here is an example on how to publish a message to an MQTT topic to
    # perform an action
    def open_servo(self, servoNumber: int) -> None:
        # First, we construct a dictionary payload per the documentation.
        data = {"servo": servoNumber, "action": "open"}
        # This creates it all in one line, however, you could also create it in multiple
        # lines as shown below.
        # data = {}
        # data["servo"] = 0
        # data["action"] = "open"

        # Now, we convert the dictionary to a JSON encoded string that we can publish.
        payload = json.dumps(data)

        # Finally, we publish the payload to the topic, once again using f-strings to
        # re-use our common prefix.
        self.mqtt_client.publish(topic=f"{self.topic_prefix}/pcc/set_servo_open_close", payload=payload)

    def close_servo(self, servoNumber: int) -> None:
        # First, we construct a dictionary payload per the documentation.
        data = {"servo": servoNumber, "action": "close"}
        # This creates it all in one line, however, you could also create it in multiple
        # lines as shown below.
        # data = {}
        # data["servo"] = 0
        # data["action"] = "open"

        # Now, we convert the dictionary to a JSON encoded string that we can publish.
        payload = json.dumps(data)

        # Finally, we publish the payload to the topic, once again using f-strings to
        # re-use our common prefix.
        self.mqtt_client.publish(topic=f"{self.topic_prefix}/pcc/set_servo_open_close", payload=payload)


    def LEDcolor(self, color: str) -> None:
        print(f"AprilTag Number: {id}")
        Red = {"wrgb": [255, 255, 0, 0]}
        Green =  {"wrgb": [255, 0, 255, 0]}
        Blue = {"wrgb": [255, 0, 0, 255]}
        if color == "Red":
            data = Red
        if color == "Green":
            data = Green
        if color == "Blue":
            data = Blue

        payload = json.dumps(data)
        self.mqtt_client.publish(topic=f"{self.topic_prefix}/pcc/set_base_color", payload=payload)

if __name__ == "__main__":
    box = Sandbox()
    box.run()
