import express from "express";
import fetch from "node-fetch";

const app = express();
app.use(express.json());

// Health check (important for Render)
app.get("/", (req, res) => {
    res.send("Telegram AI Bot server is running 🚀");
});

// AI chat endpoint
app.post("/chat", async (req, res) => {
    const userMessage = req.body.message;

    if (!userMessage) {
        return res.status(400).json({ error: "Message is required" });
    }

    try {
        const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${process.env.AI_API_KEY}`
            },
            body: JSON.stringify({
                model: "openai/gpt-3.5-turbo",
                messages: [{ role: "user", content: userMessage }]
            })
        });

        const data = await response.json();

        if (data.error) {
            return res.status(500).json({ error: data.error.message });
        }

        const aiText = data.choices[0].message.content;
        res.json({ reply: aiText });

    } catch (err) {
        res.status(500).json({ error: "Failed to contact AI service" });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log("Server running on port", PORT);
});
