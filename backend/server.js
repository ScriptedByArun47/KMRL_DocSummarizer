

const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
const bodyParser = require("body-parser");

const app = express();
app.use(cors());
app.use(bodyParser.json());

// ==========================
// MongoDB Connection
// ==========================
mongoose.connect("mongodb+srv://akisback049:kRQPOcjqInE2t5fT@cluster0.9quv2g9.mongodb.net/", {
    useNewUrlParser: true,
    useUnifiedTopology: true
}).then(() => console.log("✅ MongoDB Connected"))
  .catch(err => console.error("❌ MongoDB Error:", err));

// ==========================
// Schemas
// ==========================
const UserSchema = new mongoose.Schema({
    username: { type: String, required: true, unique: true },
    password: { type: String, required: true }, // For production use bcrypt
    role: { type: String, enum: ["admin", "hr", "employee"], required: true }
});

const DocumentSchema = new mongoose.Schema({
    title: String,
    url: String,
    summary: String,
    uploadedBy: String, // username
    uploadedAt: { type: Date, default: Date.now }
});

const User = mongoose.model("User", UserSchema);
const Document = mongoose.model("Document", DocumentSchema);

// ==========================
// Auth Routes
// ==========================
app.post("/api/register", async (req, res) => {
    try {
        const { username, password, role } = req.body;
        const user = new User({ username, password, role });
        await user.save();
        res.json({ message: "User registered successfully" });
    } catch (err) {
        res.status(400).json({ error: err.message });
    }
});

app.post("/api/login", async (req, res) => {
    const { username, password } = req.body;
    const user = await User.findOne({ username, password });
    if (!user) {
        return res.status(401).json({ error: "Invalid credentials" });
    }
    res.json({ message: "Login successful", user });
});

// ==========================
// Document Routes
// ==========================
app.post("/api/documents", async (req, res) => {
    try {
        const { title, url, summary, uploadedBy } = req.body;
        const doc = new Document({ title, url, summary, uploadedBy });
        await doc.save();
        res.json({ message: "Document saved successfully", doc });
    } catch (err) {
        res.status(400).json({ error: err.message });
    }
});

app.get("/api/documents", async (req, res) => {
    const docs = await Document.find().sort({ uploadedAt: -1 });
    res.json(docs);
});

app.get("/api/documents/:id", async (req, res) => {
    const doc = await Document.findById(req.params.id);
    if (!doc) return res.status(404).json({ error: "Document not found" });
    res.json(doc);
});

// ==========================
// Start Server
// ==========================
app.listen(9000, () => console.log("🚀 Server running on http://localhost:9000"));
