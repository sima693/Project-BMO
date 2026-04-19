# 🤖 Project BMO (Be More)

> *"Who wants to play video games?!"*

Project BMO is an open-source attempt to bring everyone's favourite **video game system / friend / roommate** from *Adventure Time* to life. This project evolves from a desktop AI assistant with an animated face into a fully realised, mobile, autonomous robot.

---

## ✅ Phase 1 — The Digital Soul (Complete)

BMO now has a brain and a face! Launch the app and talk to BMO via your keyboard.

### Features in Phase 1
- **Dynamic animated face** — drawn procedurally in Pygame (teal body, D-pad, coloured buttons, speaker grille)
- **8 facial expressions** — neutral, happy, excited, thinking, sad, surprised, talking, sleeping
- **Smooth transitions** — all expressions lerp between states, no jarring snaps
- **Persistent blink** — random blink every 3–7 seconds, fast and natural
- **Sentiment analysis** — VADER maps BMO's response text to an expression automatically
- **Ollama-powered brain** — runs `llama3.2` locally, no internet required after setup
- **Streaming responses** — tokens appear live; mouth animates while BMO "speaks"
- **Conversation memory** — BMO remembers the last 10 exchanges

---

## 🚀 Setup

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.ai) installed and running

### 1 — Install Ollama & pull the model
```bash
# Install Ollama from https://ollama.ai
ollama pull llama3.2
ollama serve          # keep this running in a separate terminal
```

### 2 — Clone & install Python packages
```bash
git clone https://github.com/sima693/Project-BMO.git
cd Project-BMO
pip install -r requirements.txt
```

### 3 — Configure (optional)
```bash
cp .env.example .env
# Edit .env to change model, or switch to OpenAI backend
```

### 4 — Run BMO!
```bash
python -m bmo.app
```

---

## 🎮 Controls

| Key | Action |
|-----|--------|
| Type anything | Talk to BMO |
| `Enter` | Send message |
| `Backspace` | Delete character |
| `Ctrl + Backspace` | Delete last word |
| `Ctrl + C` | Clear conversation history |
| `Escape` | Quit |

---

## 🗺 Roadmap

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Core AI + Dynamic Face (Ollama + Pygame) | ✅ Complete |
| **Phase 2** | Voice: STT (Whisper) + TTS (Coqui/ElevenLabs) + OpenCV vision | 🔲 Planned |
| **Phase 3** | Hardware: Raspberry Pi 5 + 3.5" LCD + USB audio | 🔲 Planned |
| **Phase 4** | Robotics: micro-servo legs + arms + IMU gyroscope | 🔲 Planned |
| **Phase 5** | Polish: local-only AI (Ollama) + RetroPie + Home Assistant | 🔲 Planned |

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| Face UI | Pygame 2.x |
| AI Backend | Ollama (llama3.2) / OpenAI GPT-4o-mini |
| Sentiment | VADER (vaderSentiment) |
| Hardware target | Raspberry Pi 5 (Phase 3+) |
| Vision (Phase 2) | OpenCV / YOLOv11 |

---

## 📁 Project Structure

```
Project-BMO/
├── bmo/
│   ├── app.py          # Main loop, state machine, threading
│   ├── face.py         # Pygame body + face renderer (procedural drawing)
│   ├── expressions.py  # Expression parameters + lerp helper
│   ├── sentiment.py    # VADER sentiment → expression mapping
│   └── ai_engine.py    # Ollama/OpenAI backend + BMO system prompt
├── requirements.txt
├── .env.example
└── README.md
```

---

*Made with ❤️ by a friend of BMO*
