<h1 align="center">
  <img src="https://raw.githubusercontent.com/Dxv-404/ink-education/main/static/assets/pixel-heart.png" width="40px"/>
  <br>INK: The Pixel-Perfect Learning Operating System<br>
  <img src="https://raw.githubusercontent.com/Dxv-404/ink-education/main/static/assets/pixel-heart.png" width="40px"/>
</h1>

<p align="center">
  <i>A retro-inspired academic toolkit reimagined for the modern student. Blending gamified productivity with pixel-art aesthetics and community learning — all in one vibrant ecosystem.</i>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/Dxv-404/ink-education/main/static/assets/ink-header-banner.gif" width="100%" alt="INK Banner"/>
</p>

<p align="center">
  <a href="https://github.com/Dxv-404/INK">
    <img alt="Stars" src="https://img.shields.io/github/stars/Dxv-404/INK?style=flat-square&color=7b3eab" />
  </a>
  <a href="https://github.com/Dxv-404/ink-education/issues">
    <img alt="Issues" src="https://img.shields.io/github/issues/Dxv-404/INK?style=flat-square&color=ff5722" />
  </a>
  <a href="https://github.com/Dxv-404/ink-education/blob/main/LICENSE">
    <img alt="License" src="https://img.shields.io/github/license/Dxv-404/INK?style=flat-square&color=4caf50" />
  </a>
</p>

---

## <img src="https://raw.githubusercontent.com/Dxv-404/ink-education/main/static/assets/pixel-book.png" width="40"/>&nbsp;What is INK?

**INK** is a full-stack web platform crafted for students who want to combine aesthetics with function. It’s not just a dashboard or a marketplace — it’s an **academic OS** where learning becomes interactive, productive, and personal.

### ✨ Key Features
- **Modular Dashboard:** Drag-and-drop widgets that reflect your learning style.
- **Knowledge Bounties:** Ask, answer, and earn INK coins.
- **Academic Marketplace:** Buy and sell notes, templates, services, or study guides.
- **Q&A Forum:** Nexus-inspired threaded discussions with space aesthetics.
- **Study Spot Finder:** Discover on-campus study-friendly zones on an interactive map.
- **Gamified Productivity:** Pomodoro timer, XP system, daily streaks, and more.
- **Voxel Avatars:** Customize your pixel presence.

### 🔒 Authentication System
- Firebase integration for Email + Google login.
- **6-digit email verification** via Gmail SMTP for added security.
- Auto session recovery via `uid` URL param or cookie.

### 🔮 Coming in v2.0
- AI-enhanced bounty helper and note summarizer
- Real-time chat using WebSockets
- Dashboard calendar + timetable widget
- AI-verified marketplace listings

---

## <img src="https://raw.githubusercontent.com/Dxv-404/ink-education/main/static/assets/pixel-map.png" width="40"/> Screenshots

| Dashboard | Bounty Board | Marketplace | Study Spot Finder |
|----------|--------------|-------------|-------------------|
| ![](https://raw.githubusercontent.com/Dxv-404/ink-education/main/static/assets/screens/dashboard.png) | ![](https://raw.githubusercontent.com/Dxv-404/ink-education/main/static/assets/screens/bounty.gif) | ![](https://raw.githubusercontent.com/Dxv-404/ink-education/main/static/assets/screens/marketplace.png) | ![](https://raw.githubusercontent.com/Dxv-404/ink-education/main/static/assets/screens/studyspot.gif) |

---

## <img src="https://raw.githubusercontent.com/Dxv-404/ink-education/main/static/assets/pixel-wrench.png" width="40"/> Tech Stack

| Layer    | Technology |
|----------|-------------|
| Frontend | HTML, CSS, JavaScript, Leaflet.js, Custom pixel assets |
| Backend  | Flask (Python) |
| Database | MongoDB |
| Auth     | Firebase Auth, Flask Sessions |
| APIs     | GitHub OAuth, Spotify |
| Assets   | Pixel & voxel sprites, custom UI icons |

---

## <img src="https://raw.githubusercontent.com/Dxv-404/ink-education/main/static/assets/pixel-doc.png" width="40"/> Installation and Setup

```bash
# 1. Clone the game 
git clone https://github.com/Dxv-404/INK.git
cd INK

# 2. Install the modules 
pip install -r requirements.txt

# 3. Configure Firebase 
# Add your serviceAccountKey.json and update Firebase settings in app.py

# 4. Launch the platform 
python app.py

# 5. Visit
http://localhost:5000
