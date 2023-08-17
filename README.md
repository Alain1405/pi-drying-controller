# Raspberry PI controller for a drying room/rack

Aim:
- Contrinuosly monitor status
- Create an on-off cycle over a few hours for fans and heater
- Live camera view

## Components
- Relays to control heating and ventilation
- Temperature and humidity sensors

## Module
- Gather sensors data
- Send sensors data to prometheus
- Relays control
- Schedule of relays
- Camera control

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
