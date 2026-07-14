# AI-powered-Dynamic-Multi-Robot-Warehouse-Navigation-System
AI-powered Dynamic Multi-Robot Warehouse Navigation using ROS 2 Jazzy, Nav2, Gazebo Harmonic, and Groq LLM with conversational memory for natural language robot control.
# 🤖 AI-Powered Dynamic Multi-Robot Warehouse Navigation

An intelligent **Dynamic Multi-Robot Warehouse Navigation System** built using **ROS 2 Jazzy**, **Nav2**, and **Gazebo Harmonic**, integrating **Groq LLM** for natural language robot control with **conversational memory**. The system enables multiple autonomous warehouse robots to understand human instructions, navigate safely in dynamic environments, and perform autonomous lot-to-lot transportation.

---

## 🚀 Features

- 🤖 Multi-Robot Warehouse Navigation
- 🧠 Natural Language Robot Commands using **Groq API**
- 💬 Conversational Memory for contextual command understanding
- 🧭 ROS 2 Jazzy Navigation Stack (Nav2)
- 📍 AMCL Localization
- 🗺️ Smac Planner (A*) for Global Path Planning
- 🚧 Dynamic Window Approach (DWB) for Local Planning & Obstacle Avoidance
- 🏭 Dynamic Warehouse Environment with Moving Obstacles
- 📡 Real-time LiDAR-based Obstacle Detection
- 🗺️ Geometry-Based Occupancy Map Generation (No SLAM Required)
- 🔄 Dynamic Goal Switching
- ✋ Stop / Resume Navigation Commands
- 🚗 Multi-Robot Architecture using ROS Namespaces
- 🎯 Context-aware Navigation with Sequential Command Support
- 📝 Natural Language Support
  - Abbreviations (R, G, B, Y, O)
  - Spelling Corrections
  - Previous Destination References
  - Sequential Navigation Commands

---

## 🏗️ System Architecture

```
                  Natural Language Command
                           │
                           ▼
                 Groq LLM + Chat Memory
                           │
                           ▼
              Natural Language Parser
                           │
                           ▼
                Target Lot Generation
                           │
                           ▼
                 ROS 2 Communication
                           │
                           ▼
               Nav2 Navigation Stack
       ┌────────────┬──────────────┬────────────┐
       │            │              │            │
       ▼            ▼              ▼            ▼
     AMCL      Smac Planner      DWB      Costmaps
 Localization    (Global)       (Local)   + LiDAR
                           │
                           ▼
                    Autonomous Robot
                           │
                           ▼
             Dynamic Warehouse Environment
```

---

## 📂 Project Structure

```
warehouse_bot/
│
├── launch/
├── config/
├── maps/
├── urdf/
├── worlds/
│
├── lot_navigator_node.py
├── lot_input_bot1.py
├── lot_input_bot2.py
├── lot_input_bot3.py
├── generate_map.py
├── dynamic_obstacles_mover.py
│
├── package.xml
├── setup.py
└── README.md
```

---

## 🛠️ Technologies Used

- ROS 2 Jazzy
- Gazebo Harmonic
- Nav2
- Python
- Groq API
- Llama 3.1
- AMCL
- Smac Planner (A*)
- Dynamic Window Approach (DWB)
- Occupancy Grid Maps
- LiDAR
- RViz2

---

## ⚙️ How It Works

1. The user gives a command in natural language.

   Example:

   ```
   Go to the green lot
   ```

2. The command is sent to the **Groq LLM**.

3. The LLM interprets the command using **conversation memory**.

4. The command is converted into a navigation goal.

5. The goal is published to the respective robot.

6. Nav2 performs

   - Localization
   - Global Path Planning
   - Local Planning
   - Dynamic Obstacle Avoidance

7. The robot autonomously reaches the destination.

---

## 🧠 Natural Language Examples

```
Go to Green
Take me to Blue
Return Home
Go back where you started
Go there
Go to G
Return to O
Go to Blue then Green then Red
Stop
```

The LLM also understands

- Typing mistakes
- Abbreviations
- Context-aware commands
- Previous destinations
- Sequential destinations

---

## 🏭 Dynamic Warehouse

The warehouse contains

- Moving obstacles
- Static shelves
- Warehouse lots
- Autonomous mobile robots

The occupancy map is generated directly from the warehouse geometry, while Nav2 continuously updates local costmaps using LiDAR data for real-time obstacle avoidance.

---

## 📍 Navigation Algorithms

| Component | Algorithm |
|-----------|-----------|
| Localization | AMCL |
| Global Planner | Smac Planner (A*) |
| Local Planner | Dynamic Window Approach (DWB) |
| Navigation | ROS 2 Nav2 |
| Mapping | Geometry-Based Occupancy Grid |
| Obstacle Detection | LiDAR + Local Costmaps |

---

## 📌 Key Highlights

- AI-powered warehouse navigation
- Dynamic warehouse simulation
- Conversational robot interaction
- Groq LLM integration
- Chat memory for contextual commands
- Autonomous multi-robot navigation
- Real-time obstacle avoidance
- Dynamic goal switching
- ROS 2 Jazzy & Nav2 implementation

---

## 📖 Future Improvements

- Voice Command Integration
- Fleet Management Dashboard
- Task Scheduling and Optimization
- Vision-based Object Detection
- Dynamic Task Allocation
- Warehouse Management System (WMS) Integration
- Cloud-based Robot Monitoring
- Multi-floor Warehouse Support

---

## 👨‍💻 Author

**Vidhessh Jayakumar**

Robotics & AI Engineer

---

## ⭐ If you found this project useful, consider giving it a Star!
