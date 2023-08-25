# Raspberry PI controller for a drying room/rack

## Requirements
- `sudo apt install libgpiod2`
## Setup

- `sudo cp configs/etc/systemd/system/rpimonitor.service /etc/systemd/system/`
- `sudo systemctl daemon-reload`
- `sudo systemctl enable rpimonitor.service`
- `sudo systemctl start rpimonitor.service`
- `sudo systemctl status rpimonitor.service`
- `sudo journalctl -u rpimonitor.service`
Aim:
- Contrinuosly monitor status
- Create an on-off cycle over a few hours for fans and heater
- Live camera view

## Components
- Relays to control heating and ventilation
- Temperature and humidity sensors

## Module
- [x] Gather sensors data
- [x] Send sensors data to ThingsBoard
- [x] Schedule of relays
- [x] Camera control
- [ ] Relays control
- [ ] Temperature control

## Resources
- Monitor with [Prometheus](https://opensource.com/article/21/7/home-temperature-raspberry-pi-prometheus)


Format for schedule:
```json
{
  "start_time": "None or datetime",
  "schedule": [
    {
      "duration": "minutes",
      "relays": [
        {
          "id": "id",
          "status": "0/1"
        }
      ]
    }
  ]
}
```
