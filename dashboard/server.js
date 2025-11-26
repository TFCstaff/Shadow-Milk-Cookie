const express = require("express");
const session = require("express-session");
const path = require("path");
const sqlite3 = require("sqlite3").verbose();
const passport = require("passport");
const DiscordStrategy = require("passport-discord").Strategy;
const fetch = require("node-fetch"); // Make sure to `npm install node-fetch`

// Load Discord bot credentials
const config = {
    clientID: process.env.CLIENT_ID,
    clientSecret: process.env.CLIENT_SECRET,
    callbackURL: process.env.CALLBACK_URL
};

// Vercel proxy URL
const PROXY_URL = "https://shadow-milk-cookie.vercel.app/api/discord-proxy";

// ---- DATABASE ----
const dbPath = path.join(__dirname, "applications.sqlite");
const db = new sqlite3.Database(dbPath, (err) => {
    if (err) console.error("Failed to open database:", err);
    else console.log("Database opened at", dbPath);
});

// Create tables if not exist
db.run(`CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT,
    name TEXT,
    questions TEXT
)`);

db.run(`CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT,
    user_id TEXT,
    answers TEXT,
    status TEXT DEFAULT 'pending',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)`);

db.run(`CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id TEXT PRIMARY KEY,
    auto_dm INTEGER DEFAULT 0,
    default_template INTEGER
)`);

// ---- EXPRESS APP ----
const app = express();
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// Views
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));

// ---- SESSION + PASSPORT ----
passport.serializeUser((user, done) => done(null, user));
passport.deserializeUser((user, done) => done(null, user));

passport.use(new DiscordStrategy({
    clientID: config.clientID,
    clientSecret: config.clientSecret,
    callbackURL: config.callbackURL,
    scope: ["identify", "guilds"]
}, async (accessToken, refreshToken, profile, done) => {
    try {
        const response = await fetch(PROXY_URL, {
            headers: { Authorization: `Bearer ${accessToken}` }
        });
        const userProfile = await response.json();

        if (!userProfile || userProfile.error) {
            return done(new Error("Failed to fetch user through proxy"), null);
        }

        return done(null, userProfile);
    } catch (err) {
        return done(err, null);
    }
}));

app.use(session({
    secret: process.env.SESSION_SECRET || "dev-secret",
    resave: false,
    saveUninitialized: false,
    cookie: {
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax"
    }
}));
app.use(passport.initialize());
app.use(passport.session());

// ---- AUTH MIDDLEWARE ----
function auth(req, res, next) {
    if (req.isAuthenticated()) return next();
    res.redirect("/login");
}

// ---- ROUTES ----
app.get("/", (req, res) => res.render("index", { user: req.user }));

// Discord OAuth
app.get("/login", passport.authenticate("discord"));
app.get("/callback", passport.authenticate("discord", { failureRedirect: "/" }), (req, res) => {
    res.redirect("/dashboard");
});
app.get("/logout", (req, res) => { req.logout(() => res.redirect("/")); });

// Dashboard
app.get("/dashboard", auth, (req, res) => {
    db.all("SELECT * FROM templates WHERE guild_id=?", [req.user.id], (err, rows) => {
        res.render("dashboard", { user: req.user, templates: rows });
    });
});

// Create template
app.post("/dashboard/template/create", auth, (req, res) => {
    const { name, questions } = req.body;
    const parsedQuestions = JSON.stringify(questions.split("\n"));
    db.run("INSERT INTO templates (guild_id, name, questions) VALUES (?, ?, ?)", [req.user.id, name, parsedQuestions], () => {
        res.redirect("/dashboard");
    });
});

// Apply page
app.get("/apply/:guild_id/:template_id", auth, (req, res) => {
    const { guild_id, template_id } = req.params;
    db.get("SELECT * FROM templates WHERE id=? AND guild_id=?", [template_id, guild_id], (err, template) => {
        if (!template) return res.send("Application not found");
        res.render("apply", { template, user: req.user });
    });
});

// Submit application
app.post("/apply/:guild_id/:template_id", (req, res) => {
    const { guild_id } = req.params;
    const answers = JSON.stringify(req.body);
    const user_id = req.body.user_id;
    db.run("INSERT INTO submissions (guild_id, user_id, answers) VALUES (?, ?, ?)", [guild_id, user_id, answers], () => res.send("Application submitted!"));
});

// Review submissions
app.get("/review/:guild_id", auth, (req, res) => {
    const { guild_id } = req.params;
    db.all("SELECT * FROM submissions WHERE guild_id=?", [guild_id], (err, rows) => {
        res.render("review", { submissions: rows });
    });
});

// Dashboard settings
app.get("/dashboard/settings", auth, (req, res) => {
    const guild_id = req.user.id;
    db.get("SELECT * FROM guild_settings WHERE guild_id=?", [guild_id], (err, settings) => {
        if (!settings) settings = { auto_dm: 0, default_template: null };
        db.all("SELECT * FROM templates WHERE guild_id=?", [guild_id], (err, templates) => {
            res.render("settings", { settings, templates });
        });
    });
});

// Update settings
app.post("/dashboard/settings", auth, (req, res) => {
    const guild_id = req.user.id;
    const auto_dm = req.body.auto_dm ? 1 : 0;
    const default_template = req.body.default_template || null;
    db.run("INSERT OR REPLACE INTO guild_settings (guild_id, auto_dm, default_template) VALUES (?, ?, ?)",
        [guild_id, auto_dm, default_template], () => {
            res.redirect("/dashboard/settings");
        });
});

// ---- START SERVER ----
const PORT = process.env.PORT || 3000;
if (process.env.NODE_ENV !== "production") {
    app.listen(PORT, () => console.log(`Shadow Milk Dashboard running on port ${PORT}`));
}

module.exports = app;
