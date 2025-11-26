const { exec } = require("child_process");

// Install Python dependencies automatically
exec("python3 -m pip install -r python-bot/requirements.txt", (err, out) => {
    if (err) console.error("Failed to install Python dependencies:", err);
    else console.log("Python dependencies installed");

    // Start Python bot in background
    const pythonBot = exec("python3 python-bot/bot.py");

    pythonBot.stdout.on("data", (data) => console.log(`[Python Bot]: ${data}`));
    pythonBot.stderr.on("data", (data) => console.error(`[Python Bot ERROR]: ${data}`));

    pythonBot.on("close", (code) => console.log(`Python bot exited with code ${code}`));
});

// Start Node.js dashboard
require("./dashboard/server.js");
