# PyMCL (PythonMineCraftLauncher)

*Currently working on a human-made readme*

A lightweight, vanilla-like Python launcher for Minecraft with Fabric & mod support — GUI only 🎛️🕹️

PyMCL launches any Minecraft client version, can install Fabric, auto-installs Java and required Minecraft dependencies, loads mods from a folder, and behaves like the vanilla launcher. It currently supports only offline-mode usernames (no Mojang / Microsoft authentication). 🚫🔑

---

Table of contents
- Features
- Requirements
- Quick start (GUI)
- Common workflows
- Configuration examples
- How it works (high-level)
- Troubleshooting
- Contributing
- License

Features ✨
- GUI-only: start and control everything from a simple desktop interface — no CLI required. 🖥️
- Auto-install Java: PyMCL will download and configure a compatible Java runtime when needed. ☕⬇️
- Auto-install Minecraft dependencies: version jars, libraries, and assets are downloaded on demand. 📦
- Fabric loader support: optional Fabric setup for supported versions. 🧩
- Mod support: drop mod JARs into a folder and enable them in the GUI. 📂
- Vanilla-like behavior: downloads required files, builds classpath and java args, and starts the game process similar to the vanilla launcher. 🎮
- Offline-mode usernames only: you provide the username locally — useful for single-player and local testing. 🔒

Requirements 🧾
- Python 3.8+ (3.10+ recommended)
- Internet connection for downloads
- Sufficient disk space for game versions and mods
- No preinstalled Java required — PyMCL will install a compatible Java runtime automatically (you can still override with JAVA_HOME if desired)

Quick start (GUI) 🚀
1. Clone the repo:
   ```bash
   git clone https://github.com/Earth1283/PyMCL.git
   cd PyMCL
   ```

2. (Optional) Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the GUI:
   ```bash
   python -m PyMCL
   ```
   - The app will open a desktop window where you can:
     - Select a Minecraft version
     - Enter an offline username
     - Toggle Fabric installation
     - Choose a mods folder
     - Set memory and JVM options
     - Click Launch to download needed files and start the game

4. First run behavior:
   - On first launch, PyMCL will automatically download a Java runtime if none suitable is found, then download the Minecraft version files (client jar, libraries, assets). Progress and logs are shown in the GUI. ⬇️⚙️

Common workflows 🔁

Launch a vanilla version
- Open PyMCL, pick the version, enter an offline username, click Launch. Simple. ✅

Launch with Fabric
- In the GUI, enable "Use Fabric" (or similar toggle). PyMCL will download and install Fabric for the selected version, adjust the classpath, and launch with Fabric. 🧩

Launch with mods
- Put mod JARs into a directory (e.g. ./mods).
- In the GUI, drag&drop your mods from your old mods folder, and PyMCL will take care of the rest. 📂

How PyMCL works (high-level) 🛠️
1. GUI collects user choices (version, username, fabric, mods, memory).
2. Checks local cache for Java and Minecraft assets.
3. If missing, downloads a compatible Java runtime and required Minecraft files.
4. If Fabric is enabled, downloads Fabric loader and mappings for the selected version.
5. Builds the JVM command (classpath, main class, game args) mirroring vanilla launcher behavior.
6. Starts the Java process and streams logs to the GUI console.

Important limitations ⚠️
- No online authentication: offline-mode usernames only. You cannot join online servers that require authenticated accounts (online-mode servers will reject offline names).
- Mod compatibility: PyMCL does not resolve complex dependency graphs between mods and loaders — ensure mods and Fabric are compatible with the chosen Minecraft version.
- Platform differences: PyMCL auto-installs Java, but permissions or firewall settings may require manual intervention on some OSes.

Troubleshooting 🔍
- "Java download failed":
  - Check your network/proxy settings. You can also point PyMCL to an existing JDK by setting JAVA_HOME before starting the app.
- Game crashes or mods cause errors:
  - Remove mods and add them back one-by-one to identify issues. Verify mod/Fabric/version compatibility.
- Missing libraries or assets:
  - Re-launch the same version; PyMCL will attempt to re-download missing files. Check the GUI logs for exact errors.

Security & privacy 🔒
- PyMCL downloads binaries (Java runtime and Minecraft files) from official distribution endpoints. Be mindful of where those downloads come from and verify network security when running on shared systems.

Contributing 🤝
Contributions welcome! Ways to help:
- Report bugs with steps to reproduce.
- Submit PRs for bug fixes, enhancements, or UI improvements.
- Improve docs or add screenshots and demos.
If planning larger changes, open an issue first to discuss the design.

License 📜
MIT

Contact 📨
Repository: https://github.com/Earth1283/PyMCL
Open issues/PRs for bug reports, feature requests, or help.

Thanks for trying PyMCL — a simple GUI launcher that handles Java, Minecraft dependencies, Fabric and mods for offline use. Enjoy! 🎮✨
