*This project has been created as part of the 42 curriculum by nbilyj.*

# 🚁 Fly-in — Drone Routing System

## 📌 Description

**Fly-in** is a pathfinding and simulation project where multiple drones must travel from a **start zone** to an **end zone** through a network of interconnected zones.

The objective is to **minimize the total number of simulation turns** while respecting a set of constraints:

* Zone capacities (`max_drones`)
* Connection capacities (`max_link_capacity`)
* Movement costs depending on zone types
* Collision avoidance between drones

This project combines:

* Graph algorithms (pathfinding)
* Scheduling and simulation
* Optimization strategies

---

## ⚙️ Features

* ✅ Custom **parser** for map files
* ✅ **Dijkstra-based pathfinding** with weighted costs
* ✅ **Multi-path routing** to distribute drones
* ✅ Turn-based **simulation engine**
* ✅ **Pygame visualizer** for real-time simulation
* ✅ Support for:

  * Restricted zones (multi-turn movement)
  * Priority zones (preferred paths)
  * Blocked zones (inaccessible)
  * Capacity constraints (zones + connections)

---

## 🚀 Instructions

### 1. Install dependencies

```bash
make install
```

or manually:

```bash
pip install pygame
```

---

### 2. Run simulation

```bash
make run MAP=maps/example.txt
```

or:

```bash
python3 main.py maps/example.txt
```

---

### 3. Controls (Visualizer)

* `SPACE` → next turn
* `A` → autoplay
* `Q` / `ESC` → quit

---

## 🧠 Algorithm Explenation

### Pathfinding

We use a modified **Dijkstra algorithm**:

* Each zone has a cost:

  * `normal` → 1
  * `restricted` → 2
  * `priority` → 1 (with bonus)
* Priority zones are slightly favored to guide the search

To improve throughput, we compute **multiple paths** using:

* Edge penalization (`avoid_edges`)
* Iterative Dijkstra runs

This allows distributing drones across different routes.

---

### Simulation Engine

The simulation runs in **discrete turns**.

Each drone can:

* Move to a connected zone
* Wait if blocked
* Enter a multi-turn movement (restricted zone)

Key rules:

* Zone capacity must not be exceeded
* Connection capacity must not be exceeded
* Drones move simultaneously
* Drones reaching the end are removed

---

### Optimization Choices

* **Multi-path distribution** to reduce congestion
* **Greedy scheduling** (drones closer to goal prioritized)
* **Priority bias** in pathfinding
* Lightweight simulation loop for performance

---

## 📊 Performance

The goal is to minimize the total number of turns.

Typical targets:

* Easy maps: < 10 turns
* Medium maps: 10–30 turns
* Hard maps: < 60 turns

Performance depends on:

* Path distribution quality
* Congestion handling
* Scheduling efficiency

---

## 🎮 Visual Representation

The project includes a **Pygame visualizer**:

* Zones displayed with colors
* Drone positions updated each turn
* Connection capacities shown
* UI panel with stats (turn count, progress)

This helps:

* Debug the simulation
* Understand congestion and bottlenecks
* Analyze algorithm behavior visually

---

## 🧪 Testing

Custom maps can be created to test:

* Edge cases (deadlocks, bottlenecks)
* High drone counts
* Complex graph structures

---

## 📚 Resources

* Dijkstra Algorithm:
  https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm

* Graph Theory Basics:
  https://en.wikipedia.org/wiki/Graph_(abstract_data_type)

* Pathfinding Strategies:
  https://www.redblobgames.com/pathfinding/a-star/introduction.html

---

## 🤖 AI Usage

AI was used for:

* Structuring the project architecture
* Debugging simulation edge cases
* Improving pathfinding strategies
* Writing documentation (README)

All generated content was reviewed, tested, and fully understood before integration.

---

## 🧱 Project Structure

```
.
├── main.py
├── parser.py
├── simulation.py
├── pathfinding.py
├── run_visual.py
├── maps/
└── Makefile
```

---

## 🏁 Conclusion

This project demonstrates how combining **graph algorithms** with **simulation and scheduling** can solve complex routing problems efficiently.

It highlights real-world challenges such as:

* Resource constraints
* Parallel movement
* Optimization under pressure

---
