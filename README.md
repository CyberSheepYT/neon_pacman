🟡 NEON PAC-MAN

    A complete, arcade-faithful Pac-Man built in one single Python file —neon glow maze, real ghost AI, chiptune synth audio, particles, CRT scanlines,and an animated attract screen. No image files. No sound files. No assets. Just Python.

📸 Preview

(drop a screenshot or GIF here — the neon maze looks best mid-game with a power pellet active!)
✨ Features
🎮 Faithful Arcade Gameplay

    The classic 28×31 maze, fully playable with wrap-around side tunnels
    Scatter / Chase waves — ghosts periodically give up the hunt and retreat totheir corners, just like the 1980 original
    Ghost house with staggered ghost releases, door, and respawn logic
    Frightened mode: power pellets turn ghosts blue (then flashing white as thetimer runs out) — eat them for combo points
    Eyes mode: eaten ghosts fly home as eyeballs and respawn
    Fruit bonuses appear at 70 and 170 pellets, worth more on higher levels
    Extra life at 10,000 points
    Level speed ramp — every level gets faster and power pellets last shorter

👻 Real Ghost Personalities

Each ghost uses its authentic arcade targeting logic:
Ghost	Color	Personality
Blinky	🔴 Red	Relentlessly chases your exact tile. Gets meaner as pellets run out.
Pinky	🩷 Pink	Ambusher — targets 4 tiles ahead of where you're heading.
Inky	🔵 Cyan	Flanker — uses a vector through Blinky to cut off your escape.
Clyde	🟠 Orange	Confused — chases you from afar, flees to his corner up close.
🌆 The "God Look"

    Procedurally generated neon maze outlines with bloom glow
    A new wall color palette every level (blue → teal → ember → violet → lime)
    Glowing Pac-Man and ghosts, particle bursts on every pickup
    Floating score popups, ghost-eat freeze-frame
    CRT scanline overlay for that cabinet feel
    Fully animated attract screen with a chase intermission loop
    Maze flash celebration on level clear

🔊 Synthesized Chiptune Audio (optional)

Every sound is generated in code with numpy — zero audio files:

    Intro jingle, waka-waka, power-pellet surge, ghost-eat pop
    Background siren that switches to panic-mode during fright
    Sweeping death sound, level-clear fanfare, extra-life chime

No numpy? The game still runs perfectly — just silently.
🚀 Installation

Requires Python 3.8+

# 1. install pygamepip install pygame# 2. (optional) enable all sound effectspip install numpy# 3. run it!python neon_pacman.py

That's it. One file, no other dependencies, no assets folder.
🕹️ Controls
Key
	
Action
↑ ↓ ← → / WASD	Move
ENTER / SPACE	Start game
P	Pause
M	Mute / unmute
ESC	Quit (saves high score)
 
 
🏆 Scoring
Item
	
Points
Pellet	10
Power pellet	50
Ghosts (in one fright)	200 → 400 → 800 → 1600
Fruit (levels 1–5)	100 / 300 / 500 / 700 / 1000
Extra life	at 10,000 pts
 
 
🖥️ Display & Auto-Fit

The window targets ~1000px tall (756×980 on a standard desktop) and — smart part —
measures your monitor first and shrinks itself to fit smaller screens and laptops.
It runs comfortably on anything from a potato laptop to a 4K display.

Want to force a size? Open the file and edit the cap in set_window_size():

TILE = int(max(15, min(27, fit)))   # ↑ raise 27 for bigger, lower 15 for smaller



🛠️ Customization Cheat-Sheet

Everything fun is a constant near the top of the file:
Want to change...
	
Edit this
Ghost / player speed	PAC_SPEED, GHOST_SPEED (tiles per sec)
Frightened duration	in power_up() — 7.5 - (level - 1) * 0.75
Scatter/chase wave timing	SCATTER_PLAN list (seconds)
Maze colors	PALETTES list
Ghost release delays	GHOST_DEFS last value per ghost
Starting lives	new_game() — self.lives = 3
Difficulty ramp	pace = min(1.28, 1 + 0.045 * (level - 1))
The maze itself	the MAZE text map (# wall, . pellet, o power pellet)
 
 

Yes — you can redraw the maze just by editing ASCII art. The renderer rebuilds
all walls, glow, and pellets from the text automatically.
💾 High Score

Your high score is saved to neon_pac_highscore.txt next to the game file and
persists between runs. Beat it. Defend it. 🏆
🧠 Under the Hood (for the curious)

     Grid-locked movement engine — actors travel on exact tile rails; direction
    decisions are guaranteed to fire precisely on tile centers, so cornering and
    AI turns are pixel-perfect at any speed
     Authentic ghost AI — min-distance targeting with no-reverse rule, per-ghost
    target tiles, mode-timer waves, and forced reversals on mode switches
     Procedural wall rendering — the neon outline is computed from wall/free
    adjacency, so any valid ASCII maze renders beautifully with zero art assets
     Runtime chiptune synth — square/sine/saw oscillators with pitch sweeps,
    vibrato, and envelopes rendered to numpy buffers at load time

📂 Project Structure

📦 neon-pacman
 ┣ 📄 neon_pacman.py        ← the entire game
 ┣ 📄 README.md             ← you are here
 ┗ 📄 neon_pac_highscore.txt ← created automatically on first game

🐛 Troubleshooting
Problem
	
Fix
No sound	pip install numpy — audio needs it
Window too big for screen	It auto-fits — but you can lower the cap in set_window_size()
ModuleNotFoundError: pygame	pip install pygame
High score reset	The .txt file was moved/deleted — it lives next to the script
 
 
📄 License

MIT — do whatever you want. Fork it, mod it, ship it, put it on your résumé.

Built with ❤️, 🐍, and an unreasonable number of neon glow layers.

Now go eat some ghosts. 🟡👻