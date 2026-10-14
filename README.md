# ⚡ LeadPulse AI — Smart B2B Lead Generation & Classification

An AI-powered web application built with **Streamlit**, **Geoapify Places API**, and **Google Gemini AI** that discovers local business leads across Pakistan by industry and location, then qualifies each prospect as **HOT** or **COLD** in seconds[cite: 2, 3].

---

## 🚀 Key Features

- **Location & Industry Discovery:** Fetch up to 30 targeted local businesses within a customizable radius (1–25 km) using the Geoapify Geocoding & Places APIs[cite: 2, 3].
- **High-Speed Single-Batch AI Qualification:** Analyzes all discovered businesses simultaneously in a single structured JSON call using Google Gemini (`gemini-3.8-flash`), reducing classification time to ~2 seconds.
- **Lead Quality Scoring (1–10):** Assigns each business a 1–10 quality score alongside a concise AI reasoning summary.
- **Interactive SaaS Dashboard:**
  - **KPI Summary Cards:** Instant breakdown of Total Leads, 🔥 HOT Prospects, ❄️ COLD Prospects, and Average Lead Score.
  - **Visual Lead Cards:** Clean 2-column card layout with status badges, phone numbers, websites, and AI insights[cite: 3].
  - **Interactive Data Table:** Sortable table with built-in visual progress bars for lead scores.
  - **Geographic Map View:** Interactive pin map displaying the exact coordinates of discovered leads.
- **One-Click CSV Export:** Filter leads by status or keyword and download clean CSV reports for outreach campaigns[cite: 3].

---

## 🛠️ Tech Stack

- **Frontend / UI:** Streamlit (Custom CSS Dark/Light Adaptive Theme)
- **AI / LLM:** Google Gemini API (`google-genai` SDK)[cite: 3, 4]
- **Geospatial Data:** Geoapify Geocoding & Places API[cite: 2, 3]
- **Data Processing:** Pandas, Requests, Python-Dotenv[cite: 3, 4]

---

## 🔄 System Workflow

```text
User Input (Industry + Location + Radius)
   ↓
Geoapify Geocoding API (Convert Location → Coordinates)
   ↓
Geoapify Places API (Fetch Local Business Leads)
   ↓
Google Gemini AI (Single-Batch Structured JSON Qualification & 1–10 Scoring)
   ↓
Interactive Streamlit Dashboard (Cards, Table, Map & CSV Export)