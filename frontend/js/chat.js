/* ═══════════════════════════════════════════════════════════
   Resume RAG Chatbot — Frontend Logic
   ═══════════════════════════════════════════════════════════ */

// ── Configuration ──────────────────────────────────────────
// Change this to your deployed backend URL in production
const API_BASE_URL = "http://localhost:8000";

// ── DOM Elements ───────────────────────────────────────────
const chatMessages   = document.getElementById("chat-messages");
const chatInput      = document.getElementById("chat-input");
const btnSend        = document.getElementById("btn-send");
const btnInfo        = document.getElementById("btn-info");
const modalOverlay   = document.getElementById("modal-overlay");
const modalClose     = document.getElementById("modal-close");
const suggestionsBar = document.getElementById("suggestions-bar");
const statusText     = document.getElementById("status-text");
const statsContainer = document.getElementById("stats-container");
const statQueries    = document.getElementById("stat-queries");
const statTime       = document.getElementById("stat-time");

// ── State ──────────────────────────────────────────────────
let isLoading = false;

// ── Default suggestions (fallback if API fails) ────────────
const DEFAULT_SUGGESTIONS = [
    "What is Pangochain?",
    "What are his main technical skills?",
    "Describe his ML research work.",
    "What work experience does he have?",
];


// ═══════════════════════════════════════════════════════════
// Initialization
// ═══════════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
    renderWelcome();
    loadSuggestions();
    checkHealth();
    loadStats();
    setupEventListeners();
});


function setupEventListeners() {
    // Send on button click
    btnSend.addEventListener("click", handleSend);

    // Enter to send, Shift+Enter for newline
    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    // Auto-resize textarea
    chatInput.addEventListener("input", () => {
        chatInput.style.height = "auto";
        chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + "px";
        btnSend.disabled = !chatInput.value.trim();
    });

    // Info modal
    btnInfo.addEventListener("click", () => {
        modalOverlay.hidden = false;
    });

    modalClose.addEventListener("click", () => {
        modalOverlay.hidden = true;
    });

    modalOverlay.addEventListener("click", (e) => {
        if (e.target === modalOverlay) {
            modalOverlay.hidden = true;
        }
    });

    // Close modal on Escape
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && !modalOverlay.hidden) {
            modalOverlay.hidden = true;
        }
    });
}


// ═══════════════════════════════════════════════════════════
// Welcome & Suggestions
// ═══════════════════════════════════════════════════════════

function renderWelcome() {
    const welcome = document.createElement("div");
    welcome.className = "welcome-container";
    welcome.innerHTML = `
        <div class="welcome-icon">💬</div>
        <h2>Hi there! I'm a Resume Chatbot</h2>
        <p>
            Ask me anything about skills, projects, experience, or education.
            I'll answer using only real documents — no hallucinations, guaranteed.
        </p>
    `;
    chatMessages.appendChild(welcome);
}


async function loadSuggestions() {
    let suggestions = DEFAULT_SUGGESTIONS;

    try {
        const res = await fetch(`${API_BASE_URL}/api/suggestions`);
        if (res.ok) {
            const data = await res.json();
            if (data.suggestions && data.suggestions.length > 0) {
                suggestions = data.suggestions;
            }
        }
    } catch {
        // Use defaults silently
    }

    renderSuggestions(suggestions);
}


function renderSuggestions(suggestions) {
    suggestionsBar.innerHTML = "";
    suggestions.forEach((text) => {
        const chip = document.createElement("button");
        chip.className = "suggestion-chip";
        chip.textContent = text;
        chip.addEventListener("click", () => {
            chatInput.value = text;
            chatInput.dispatchEvent(new Event("input"));
            handleSend();
        });
        suggestionsBar.appendChild(chip);
    });
}

async function loadStats() {
    try {
        const res = await fetch(`${API_BASE_URL}/api/stats`);
        if (res.ok) {
            const data = await res.json();
            if (data.total_questions > 0) {
                statsContainer.hidden = false;
                statQueries.textContent = data.total_questions;
                statTime.textContent = `${data.avg_response_time_ms}ms`;
            }
        }
    } catch (e) {
        console.error("Failed to load stats", e);
    }
}


// ═══════════════════════════════════════════════════════════
// Health Check
// ═══════════════════════════════════════════════════════════

async function checkHealth() {
    try {
        const res = await fetch(`${API_BASE_URL}/api/health`);
        if (res.ok) {
            const data = await res.json();
            if (data.index_loaded) {
                setStatus("online", `Ready · ${data.chunk_count} knowledge chunks`);
            } else {
                setStatus("offline", "Index not loaded");
            }
        } else {
            setStatus("offline", "Backend unavailable");
        }
    } catch {
        setStatus("offline", "Connecting...");
    }
}


function setStatus(state, text) {
    statusText.innerHTML = `
        <span class="status-dot ${state}"></span>
        ${text}
    `;
}


// ═══════════════════════════════════════════════════════════
// Message Handling
// ═══════════════════════════════════════════════════════════

async function handleSend() {
    const question = chatInput.value.trim();
    if (!question || isLoading) return;

    // Clear welcome on first message
    const welcome = chatMessages.querySelector(".welcome-container");
    if (welcome) welcome.remove();

    // Hide suggestions after first question
    suggestionsBar.classList.add("hidden");

    // Add user message
    addMessage("user", question);

    // Reset input
    chatInput.value = "";
    chatInput.style.height = "auto";
    btnSend.disabled = true;

    // Show typing indicator
    isLoading = true;
    const typingEl = showTypingIndicator();

    try {
        const res = await fetch(`${API_BASE_URL}/api/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question }),
        });

        // Remove typing indicator
        typingEl.remove();
        isLoading = false;

        if (res.ok) {
            const data = await res.json();
            addBotMessage(data);
            loadStats();
        } else if (res.status === 429) {
            addMessage("error", "⏳ Too many requests. Please wait a moment and try again.");
        } else {
            const errorText = await res.text();
            console.error("API error:", res.status, errorText);
            addMessage("error", "Something went wrong. Please try again.");
        }
    } catch (err) {
        typingEl.remove();
        isLoading = false;
        console.error("Network error:", err);
        addMessage(
            "error",
            "🔌 Can't reach the chatbot server. It might be warming up — free-tier servers sleep when idle. Try again in 30 seconds."
        );
    }
}


// ═══════════════════════════════════════════════════════════
// Rendering
// ═══════════════════════════════════════════════════════════

function addMessage(type, text) {
    const wrapper = document.createElement("div");
    wrapper.className = `message ${type}`;

    const avatarIcon = type === "user" ? "👤" : type === "error" ? "⚠️" : "🤖";

    wrapper.innerHTML = `
        <div class="message-avatar">${avatarIcon}</div>
        <div class="message-content">${escapeHtml(text)}</div>
    `;

    chatMessages.appendChild(wrapper);
    scrollToBottom();
}


function addBotMessage(data) {
    const wrapper = document.createElement("div");
    wrapper.className = "message bot";

    // Parse basic markdown in the answer
    const formattedAnswer = renderMarkdown(data.answer);

    // Build sources HTML
    let sourcesHtml = "";
    if (data.sources && data.sources.length > 0) {
        const tags = data.sources.map((s) => {
            const label = s.heading || s.source_file.replace(".md", "");
            const score = (s.score * 100).toFixed(0);
            return `<span class="source-tag" title="${escapeHtml(s.text)}">${escapeHtml(label)} <span class="source-score">${score}%</span></span>`;
        }).join("");

        sourcesHtml = `
            <div class="message-sources">
                <div class="sources-label">Sources</div>
                ${tags}
            </div>
        `;
    }

    // Response time
    let timeHtml = "";
    if (data.response_time_ms) {
        const timeStr = data.response_time_ms < 1000
            ? `${data.response_time_ms}ms`
            : `${(data.response_time_ms / 1000).toFixed(1)}s`;
        timeHtml = `
            <div class="response-time">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                </svg>
                ${timeStr}
            </div>
        `;
    }

    wrapper.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div>
            <div class="message-content">
                ${formattedAnswer}
                ${sourcesHtml}
            </div>
            ${timeHtml}
        </div>
    `;

    chatMessages.appendChild(wrapper);
    
    // Apply syntax highlighting to code blocks
    if (typeof hljs !== 'undefined') {
        wrapper.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }
    
    scrollToBottom();
}


function showTypingIndicator() {
    const typing = document.createElement("div");
    typing.className = "typing-indicator";
    typing.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="typing-dots">
            <span></span><span></span><span></span>
        </div>
    `;
    chatMessages.appendChild(typing);
    scrollToBottom();
    return typing;
}


function scrollToBottom() {
    requestAnimationFrame(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
}


// ═══════════════════════════════════════════════════════════
// Markdown & Sanitization
// ═══════════════════════════════════════════════════════════

function renderMarkdown(text) {
    if (!text) return "";
    
    // Use marked.js if available
    if (typeof marked !== 'undefined') {
        return marked.parse(text, { breaks: true });
    }
    
    // Fallback to basic rendering if marked fails to load
    let html = escapeHtml(text);
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/(?<!\*)\*([^*]+?)\*(?!\*)/g, "<em>$1</em>");
    html = html.replace(/`([^`]+?)`/g, "<code>$1</code>");
    html = html.replace(/^- (.+)$/gm, "<li>$1</li>");
    html = html.replace(/(<li>.*<\/li>\n?)+/gs, "<ul>$&</ul>");
    html = html.replace(/\n\n/g, "</p><p>");
    html = html.replace(/\n/g, "<br>");
    html = `<p>${html}</p>`;
    html = html.replace(/<p>\s*<\/p>/g, "");
    html = html.replace(/<p>(<ul>)/g, "$1");
    html = html.replace(/(<\/ul>)<\/p>/g, "$1");
    return html;
}


function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}
