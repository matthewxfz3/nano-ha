# NanoHA Onboarding Flow

The agent guides the entire setup through conversation. No manual configuration needed.

## Full Onboarding Example

```
# After running: python setup.py

Agent: Hi! I'm your home agent. Let's set up your smart home.
       Let me check your system first...

       [checks Docker] Docker is running.
       [deploys HA] Starting Home Assistant...
       [waits for health check] Home Assistant is ready at http://localhost:8123.

       What smart home devices do you have?

User:  I have some smart lights and a presence sensor.

Agent: What brand are the lights?

User:  Philips Hue.

Agent: Hue lights connect through a Hue Bridge on your network.
       [calls discover_devices()] I found a Philips Hue bridge at 192.168.1.42.
       [calls start_config_flow("hue")] Press the button on top of your Hue bridge
       and tell me when you're done.

User:  Done.

Agent: [calls continue_config_flow(flow_id)]
       Connected! Found 4 lights:
       - Hue Color Lamp 1
       - Hue Color Lamp 2
       - Hue White Lamp 1
       - Hue Lightstrip

       What room are these in?

User:  The color lamps are in the living room. The white lamp is in the bedroom.
       The lightstrip is in the kitchen.

Agent: [calls create_area("Living Room")]
       [calls create_area("Bedroom")]
       [calls create_area("Kitchen")]
       [calls assign_device_to_area(...) x4]

       Done. I've organized them:
       - Living Room: 2 color lamps
       - Bedroom: 1 white lamp
       - Kitchen: 1 lightstrip

       Now, what kind of presence sensor do you have?

User:  Aqara FP300.

Agent: That's a Zigbee device. Do you have a Zigbee USB coordinator
       plugged into your computer?

User:  Yes, I have a SONOFF dongle.

Agent: [calls detect_hardware()] Found it on /dev/ttyUSB0.
       [deploys Zigbee2MQTT + Mosquitto]
       Starting Zigbee support...ready.

       [calls enable_zigbee_pairing(120)]
       Hold the reset button on your Aqara sensor for 5 seconds
       until the light starts flashing.

User:  OK, it's flashing.

Agent: [calls list_zigbee_devices()] Found it — Aqara Presence Sensor FP300.
       What room is this in?

User:  Living room.

Agent: [calls assign_device_to_area(...)]
       Done. The presence sensor is in the Living Room.

       Do you have a Home Assistant Voice PE for voice control?

User:  Yes.

Agent: [deploys Whisper + Piper]
       [calls configure_assist_pipeline()]
       Voice services are ready.

       Open the Home Assistant app on your phone. It should find the
       Voice PE via Bluetooth. Connect it to your WiFi network — make
       sure to use 2.4 GHz, not 5 GHz. Tell me when it's connected.

User:  Connected.

Agent: [verifies in HA] Your Voice PE is online.

       You're all set! From now on, say "Hey Nabu" to talk to me.
       Try it: "Turn on the living room lights."

User:  Hey Nabu, turn on the living room lights.

Agent: [calls call_service("light", "turn_on", area="living_room")]
       Done. The living room lights are on.
```

## Error Recovery Examples

### Device not found
```
Agent: [calls discover_devices()] I didn't find any new devices on your network.

       A few things to check:
       - Is the device powered on?
       - Is it on the same WiFi network as this computer?
       - For Zigbee devices, is the USB coordinator plugged in?

       Want me to try scanning again?
```

### Service won't start
```
Agent: [calls deploy_service("homeassistant")] Home Assistant is taking longer
       than expected to start.

       [calls check_service_health("homeassistant")] It looks like port 8123
       is already in use. Do you have another Home Assistant running?

       I can try a different port, or you can stop the other instance first.
```

### Voice PE won't connect
```
Agent: I don't see the Voice PE in Home Assistant yet. A few things to try:

       1. Make sure your phone's Bluetooth is on
       2. The Voice PE needs 2.4 GHz WiFi (not 5 GHz)
       3. Try unplugging the Voice PE for 10 seconds, then plug it back in

       Tell me when you want to try again.
```
