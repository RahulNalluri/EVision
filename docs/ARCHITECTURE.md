# EVision Architecture

EVision is designed as a software-first in-car AI copilot. The prototype uses simulated signals, but the same structure can later connect to real EV APIs or vehicle telemetry streams.

## System Flow

1. **Live EV signals**
   - Battery percentage
   - Speed
   - Acceleration
   - Braking pattern
   - Driving mode
   - AC usage

2. **Environment context**
   - Traffic condition
   - Weather
   - Road type
   - Route distance
   - Destination range requirement

3. **Data processing layer**
   - Normalizes signals
   - Creates driving behavior features
   - Detects inefficient patterns

4. **Kaggle-trained prediction engine**
   - Predicts trip energy from driving, battery, road, traffic, and weather features
   - Predicts current range
   - Predicts optimized range
   - Checks whether the destination is reachable

5. **Battery Utilization Engine**
   - Calculates Battery Utilization Index
   - Estimates energy wastage percentage
   - Builds energy consumption breakdown

6. **Generative AI Copilot**
   - Converts analytics into plain-language suggestions
   - Explains why battery is draining
   - Gives speed, AC, driving, and charging advice
   - Grounds driver answers with retrieved knowledge-base chunks

7. **Car screen interface**
   - Shows glanceable driving guidance
   - Displays range, battery, score, tips, and trip report
   - Keeps chat/voice optional rather than making it the main UI

## Prototype Notes

The energy model is trained on 5,000 records from Kaggle's CC0 EV Energy Consumption Dataset. Its learned estimate is blended with guard-railed analytics so braking, AC load, range safety, and recommendation reasons remain explainable. The car-screen controls simulate signals that would arrive automatically through real vehicle and context APIs.

The editable Eraser source is `docs/eraser/architecture.eraserdiagram`.
