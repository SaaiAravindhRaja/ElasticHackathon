# Page Design Document

## Visual Styling
- **Primary Brand Color**: Electric Blue (#1f6fff)
- **Alert Color**: Red (#e45757)
- **Success Color**: Green
- **Typography**: Sans-serif, bold headings, small-caps helper labels, light gray timestamps.
- **Layout**: Clean, multi-column layouts using cards and panels.

## 1. Product 1: Sales-Optimized Support Chatbot (Customer-Facing)
- **Layout**: Three-column (Nav - Chat - Context).
- **Left Sidebar**: Navigation (Home, Chat History, Help Center, Settings), "Speak to an Agent" CTA.
- **Center Pane**: Chat interface.
  - Bot Header: "ElasticCX Support Bot", "AI Active", "Fast Response".
  - User Prompt: Solid blue bubble.
  - Bot Response: White card with bullets, "ELASTICCX INTELLIGENT RAG" label, Citations ([Source: ...]).
  - Revenue Optimization Card: Light blue info box, upsell prompt, "Talk to an Agent" button.
  - Composer: Input field, attachment/voice icons.
- **Right Sidebar**: Account Context.
  - Monthly API Volume card with progress bar.
  - Current Plan card with "Upgrade" button.
  - Relevant Docs list.

## 2. Product 2: Customer Pitching Assistant (Sales/Agent-Facing)
- **Layout**: Two-column split (Left 60% Transcript, Right 40% Assist).
- **Title Bar**: Brand, Live Call status, Time, Controls.
- **Left Panel**: Whisper Live Transcription.
  - Speaker bubbles with avatars and timestamps.
  - Agent bubbles (blue).
  - "AI Suggested Next Question" chips at the bottom.
  - Sentiment meter and Talk Ratio bar.
- **Right Panel**: Assist Cards.
  - **Red Alert Card**: "COMPETITOR ALERT", "Known Weakness", "KILLER QUESTION TO DROP".
  - **Objection Module**: "ACTIVE OBJECTION", Counter-points, Talking points.
  - **Feature CTA**: "Reporting Pro Feature" card.

## 3. Product 3: Customer Support Prompting Agent (Agent-Facing)
- **Layout**: Two-column responsive grid (Left Transcript, Right Guidance).
- **Top Header**: Brand, Tabs (Active Call, Queue, History), Status.
- **Left Column**:
  - Call Control Card (Caller info, Timer, Controls).
  - Live Transcription panel with real-time analysis strip ("AI is identifying customer intent").
- **Right Column**: Smart Suggestions.
  - Confidence bar.
  - Recommended Solution card with script.
  - Step-by-Step Action Plan card (numbered list).
  - Referenced Internal Documents card.
  - Footer input ("Ask AI for further clarification") and "Resolve Case" button.

## 4. Product 4: Recommendations Dashboard (Internal/Product-Facing)
- **Layout**: Dashboard grid.
- **Header**: Brand, Tabs (Executive View, etc.), Search, Date filter, Export button.
- **KPI Cards**: Churn Vulnerability Gap, Feature Mention Volume, At-Risk Revenue.
- **Middle Panels**:
  - "Lost Revenue Insights" (Left): Cards with amount lost and quotes.
  - "Top Requested Features" (Right): Ranked list with progress bars.
- **Bottom Panel**: "Market Intelligence: Competitor Vulnerabilities".
  - Table with Competitor, Vulnerability, Evidence Level (stars), Strategic Action, Source.
