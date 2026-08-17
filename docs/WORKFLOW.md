# EVision Workflow

EVision does not ask the driver to manually enter values while driving. It observes available signals, predicts battery behavior, and surfaces useful guidance on the car screen.

## Real-Time Workflow

1. **Start trip**
   - EVision begins observing vehicle and route context.

2. **Read live signals**
   - Battery percentage, speed, acceleration, braking, drive mode, and AC load.

3. **Read route and environment**
   - Traffic, weather, road type, route distance, and destination buffer.

4. **Analyze behavior**
   - Detects aggressive acceleration, high speed, harsh braking, high cabin load, and inefficient driving mode.

5. **Predict battery usage**
   - Uses the trained Kaggle energy model and explainable analytics to estimate trip energy, current range, and optimized range.

6. **Calculate utilization**
   - Produces Battery Utilization Index, energy wastage percentage, and energy consumption breakdown.

7. **Generate guidance**
   - Suggests actions such as smoother acceleration, efficient speed range, better cabin temperature, Eco mode, or charging strategy.

8. **Show on car screen**
   - Displays short, timely, readable tips while driving.

9. **Trip summary**
   - Shows range saved, wastage reduced, and the next improvement area.

The editable Eraser source is `docs/eraser/workflow.eraserdiagram`.

## Example Guidance

- "Traffic is dense ahead. Hold 42-48 km/h and avoid sharp starts."
- "Set cabin to 24C to reduce AC load."
- "You can reach your destination without charging if you stay in Eco mode."
- "Fast charging is not needed for this route."
