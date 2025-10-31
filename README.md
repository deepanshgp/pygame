# Ninja Game 🎮

A feature-rich 2D platformer game built with Pygame featuring smooth movement mechanics, enemy AI, scoring system, and a built-in level editor.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.0+-green.svg)

## 🎯 Features

### 🎮 Core Gameplay
- **Smooth Character Movement** - Running, jumping, and advanced wall sliding mechanics
- **Dash Ability** - Quick dashes for evasion and attacking enemies
- **Combo System** - Chain kills for multiplier bonuses and higher scores
- **Multiple Enemy Types** - Regular shooters and aggressive dashing enemies
- **Level Progression** - Advance through increasingly challenging levels

### 🎨 Visual & Audio
- **Pixel Art Graphics** - Custom animated sprites and environments
- **Particle Effects** - Leaves, sparks, and dash trails
- **Screen Shake** - Impact feedback for combat
- **Smooth Transitions** - Circular level transitions and camera effects
- **Sound Effects** - Immersive audio for actions and environments

### 💾 Technical Features
- **SQLite Database** - Persistent high score tracking
- **Level Editor** - Built-in map creation tool
- **Save/Load System** - JSON-based level storage
- **Responsive Controls** - Multiple key binding support

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- Pip package manager

### Setup
1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/ninja-game.git
   cd ninja-game
   ```

2. **Install dependencies**
   ```bash
   pip install pygame
   ```

3. **Run the game**
   ```bash
   python game.py
   ```

## 🎯 How to Play

### Controls
| Action | Primary Key | Alternate Key |
|--------|-------------|---------------|
| Move Left | ← / A | A |
| Move Right | → / D | D |
| Jump | ↑ / W / Space | W / Space |
| Dash | X / K | K |
| Level Editor | N/A | Run `python editor.py` |

### Gameplay Tips
- **Wall Slide** - Press against walls to slow your descent
- **Dash Attack** - Use dash to defeat enemies (invulnerable during dash)
- **Combo System** - Defeat enemies quickly to build multiplier
- **Air Time** - Don't stay airborne too long or you'll take damage!

## 🛠 Level Editor

Create your own levels using the built-in editor:

```bash
python editor.py
```

### Editor Controls
- **WASD** - Move camera
- **Mouse Click** - Place tiles
- **Right Click** - Remove tiles
- **Mouse Wheel** - Change tile variant
- **Shift + Mouse Wheel** - Change tile type
- **G** - Toggle grid placement
- **T** - Auto-tile adjacent tiles
- **O** - Save map

## 🏗 Project Structure

```
ninja-game/
├── game.py              # Main game loop
├── editor.py            # Level editor
├── entities.py          # Player, enemies, physics
├── tilemap.py           # Tilemap rendering and collision
├── database.py          # High score database
├── utils.py             # Asset loading utilities
├── clouds.py            # Background cloud system
├── particle.py          # Particle effects
├── spark.py             # Spark effects
├── data/
│   ├── images/          # Sprites and textures
│   ├── maps/            # Level files (.json)
│   ├── sfx/             # Sound effects
│   └── high_scores.db   # Database file
```

## 👥 Development Team

### Deepansh Gupta
- Project architecture and physics engine
- Level editor implementation
- Database integration
- Game over screen and transitions

### Arnav Patil
- Player movement mechanics (dashing, wall jumping)
- Camera system and background rendering
- Audio system implementation
- Control scheme and optimization

### Tanvi Kumbhar
- Animation system and sprite work
- Enemy AI and behavior programming
- Visual effects (screen shake, particles)
- Combat and respawn mechanics

## 🎓 Course Concepts Applied

This project demonstrates practical application of software engineering principles:

- **Object-Oriented Programming** - Inheritance, encapsulation, polymorphism
- **Database Management** - SQLite integration for persistent data
- **Algorithm Design** - Spatial partitioning, collision detection
- **Software Architecture** - Modular design, separation of concerns
- **Version Control** - Collaborative development with Git
- **User Interface Design** - HUD, menus, and user feedback systems

**Enjoy playing!** ⚔️

*"The ninja's path is one of endless improvement."*
