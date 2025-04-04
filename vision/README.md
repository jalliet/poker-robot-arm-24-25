# Poker Vision Tracking System

## Overview

This project is designed to track poker chips, detect folds, and monitor hand movements using computer vision. The system leverages multiple threads to handle different tasks concurrently, ensuring efficient and real-time processing.

## Key Features

1. **Birds-Eye Camera Feed**: Captures a top-down view of the poker table and shares the frame for fold detection.
2. **Chip Detection**: Uses a YOLO model to detect and count poker chips on demand.
3. **Fold Detection**: Analyzes the birds-eye frame to detect fold events using DBSCAN clustering - in other terms it is looking for the edges on the back of the cards.
4. **Hand Tracking**: Tracks hand movements using an inference pipeline and a virtual camera.
5. **Event Aggregation**: Collects and processes events from various threads and will include logic to infer what moves have occured based on visual events.
6. **Interactive Region Setup**: Allows user to reconfigure player, pot and card areas of the video feed to calibrate for different setups.

## Unique Approaches

- **Concurrent Camera Access**: The system uses a virtual camera to mirror the physical camera feed, as well as a producer-consumer thread for the shared frames, allowing multiple threads to access the same video stream without conflicts.
- **Thread-Safe Shared Data**: Utilizes locks and events to ensure safe and synchronized access to shared data across threads.
- **On-Demand Chip Detection**: Chip detection is triggered by user input, "C" or 'c" in this case, optimizing resource usage and processing time.

## Components

### Birds-Eye Camera Thread

Captures frames from the physical camera and sends them to a virtual camera. The frames are also shared for fold detection.

### Chip Detection Thread

Triggered on demand to capture a frame from the chip camera and detect poker chips using a YOLO model.

### Fold Detection Thread

Processes the shared birds-eye frame to detect fold events using DBSCAN clustering. Player areas are configured via a JSON file.

### Hand Tracking Thread

Uses an inference pipeline to detect hands in the virtual camera feed and sends detection events to the event queue.

### Key Listener Thread

Listens for user input to trigger chip detection or stop the application.

### Event Aggregator Thread

Aggregates and processes events from various threads.

### Setup Areas Script

Provides a graphical interface to configure player areas and other regions. The configuration is saved to a JSON file.

## Setup and Usage

1. **Install Dependencies**: Ensure you have all required Python packages installed.
2. **Configure Regions**: Run `setup_areas.py` to configure player areas and other regions.
3. **Run the Main Script**: Execute `main.py` to start all threads and begin tracking.

## Configuration

The configuration file (`config.json`) contains the coordinates and dimensions of player areas and other regions. This file is used by the fold detection thread to identify areas of interest.

Will contain other setup data such as total chip value etc.

## Running the System

To start the system, run the `main.py` script. The system will initialize all threads and begin processing. Use the console input to trigger chip detection or stop the application.

```bash
python vision/main.py
```

## Conclusion

This poker vision tracking system provides a robust and efficient solution for monitoring poker games using computer vision. Its unique approaches to concurrent camera access and thread-safe data sharing ensure reliable and real-time performance.