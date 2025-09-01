# AGENTS

The project includes several chess agents (bots). Each bot analyses the board and returns a move along with a confidence score.

- **RandomBot** – chooses a random legal move adjusted by a simple evaluation.
- **AggressiveBot** – seeks moves that maximise material gain.
- **FortifyBot** – favours moves that improve defence and pawn structure.
- **EndgameBot** – applies heuristics tailored for endgame positions.
- **DynamicBot** – meta-agent that combines suggestions from multiple sub-bots.
- **CriticalBot** – targets opponent pieces deemed highly threatening.
- **TrapBot** – tries to set tactical traps for the opponent.
- **KingValueBot** – evaluates positions based on king safety and piece values.
- **NeuralBot** – scores moves using a neural network evaluation.
- **UtilityBot** – provides basic evaluation utilities used by other bots.
