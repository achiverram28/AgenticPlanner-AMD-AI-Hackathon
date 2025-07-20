Automate meeting scheduling using AI agent that understands natural email requests, evaluates real calendars, resolves conflicts, and adapts instantly, no micromanagement.


Test Cases:

## Test Case 1 : ( USERTWO & USERTHREE are available )

<img width="887" height="215" alt="05BBE32F-0E8C-47EC-82F1-0DA52A37524B" src="https://github.com/user-attachments/assets/3bf140a3-4ee3-4c87-80df-d7699aa28bfd" />

## Test Case 2 : ( USERTWO is available but USERTHREE is busy )

![071B7FA0-990F-4E67-8FF3-2F185B395897_1_105_c](https://github.com/user-attachments/assets/05c81787-3e61-424c-a350-3e7e1eaa019a)

## Test Case 3 : ( Both USERTWO & USERTHREE are busy )

![38674382-8AD4-49BC-BA24-CEEAB327F172_1_105_c](https://github.com/user-attachments/assets/27933fa2-bcf7-4108-b929-ae322a9de61f)

## Test Case 3 : ( USERTWO is busy but USERTHREE is available )

![85C6AA46-4535-48AA-8C16-47365238C934_1_105_c](https://github.com/user-attachments/assets/df00809b-6983-43bf-94f2-6311e87bbfe4)

# Agentic Meeting Scheduler

A fully autonomous, AI-powered meeting scheduling system that understands natural language requests, coordinates availability across Google Calendars, resolves conflicts, and adapts dynamically—all with a fast, modern large language model (LLM) at its core.

## Features

### 1. Robust Natural Language Understanding
- **Backed by deepseek-llm-7b-chat**, deployed using vLLM (OpenAI-compatible, MI300 GPU).
- Parses a wide range of free-text requests, extracting date, time, and duration with context awareness.
- Handles ambiguous or partial instructions and recovers gracefully using fallbacks.

### 2. Autonomous Coordination & Adaptability
- Schedules meetings without any human micromanagement—just send a request and receive a result.
- Detects scheduling conflicts across all invited calendars, sender included.
- Automatically searches for and proposes the next available time slot if conflicts arise.

### 3. Multi-User Calendar Integration
- **Google Calendar API** support for real event data.
- Batch fetches all meetings/events for every participant, optimizing network use.
- Merges busy times and analyzes overlapping slots for precise availability checks.

### 4. Fast, Scalable, Efficient
- Designed for sub-10-second latency end-to-end, suitable for both individual and group scheduling.
- Leverages Python’s concurrency tools for batch calendar fetching and parallel slot evaluation.
- Modular components allow for scaling to larger teams or organizations.

### 5. Adaptive Conflict Resolution
- Suggests optimal alternative slots immediately when conflicts occur.
- Reschedules dynamically in response to last-minute changes or new priorities.

### 6. Production-Quality Design
- Fully time zone-aware using pytz (IST by default).
- Structured, extensible output in machine-readable JSON.
- Detailed logging for auditability and debugging.
- Fallbacks to robust rule-based logic if LLM or calendar fails.

## System Overview

| Component                  | Technology/Library           | Description                                              |
|----------------------------|------------------------------|----------------------------------------------------------|
| Natural Language Parsing   | deepseek-llm-7b-chat, vLLM   | Instantly parses scheduling requests from free text       |
| Calendar Coordination      | Google Calendar API          | Fetches batch events, checks multi-person conflicts      |
| Timezone Handling          | pytz                         | All times in IST, supports cross-region scheduling       |
| Parallelism & Batching     | concurrent.futures           | Concurrent event fetching and slot checking; fast search |
| Output                     | JSON                         | Clear, structured schedule response + audit metadata     |

## How It Works

1. **Request Submission**
   - User sends a natural language scheduling request (e.g., “Book a meeting Thursday at 3pm for 30 minutes.”).

2. **LLM Parsing**
   - The tool queries the local deepseek-llm-7b-chat via vLLM, which extracts date, time, and duration as JSON.
   - If LLM parsing fails, fallback heuristics extract best-guess details.

3. **Calendar Fetching (Batch & Concurrent)**
   - Fetches all events for every participant from Google Calendar.
   - Operations are batched and run in parallel for low latency.

4. **Conflict Detection**
   - Merges, sorts, and analyzes all busy slots for every attendee.
   - Reports any conflicts at the requested meeting time.

5. **Dynamic Scheduling**
   - If original time is free, confirms the booking.
   - If busy, automatically searches forward in 15-minute increments for the next available slot.

6. **Response & Logging**
   - Returns a detailed JSON output including scheduled meeting details, conflicts, and reasoning.
   - Logs every scheduling decision for transparency and troubleshooting.

## Example JSON Output

```json
{
  "ScheduledTime": "2025-07-23T10:00:00+05:30",
  "EventEnd": "2025-07-23T10:30:00+05:30",
  "Status": "No Conflict",
  "ConflictedUsers": [],
  "Attendees": [
    {"email": "userone.amd@gmail.com", "events": [ ... ]},
    {"email": "usertwo.amd@gmail.com", "events": [ ... ]}
  ],
  "Subject": "Agentic AI Project Status Update",
  "Duration_mins": "30",
  "Location": "IISc Bangalore",
  "MetaData": {
    "LLM_Tone": "neutral",
    "Priority": 2,
    "LLM_Reason": "Request is straightforward and not urgent."
  }
}
```

## Requirements & Technologies

- **Python 3.8+**
- **deepseek-llm-7b-chat** via **vLLM** (openai-compatible, MI300 GPU recommended)
- **Google Calendar API** (OAuth tokens per user)
- **pytz, dateparser, dateutil, concurrent.futures**
- **openai Python SDK**


## Demo Workflow

1. **Input:**  
   Free text: “Let’s meet Wednesday at 10am to review the roadmap.”

2. **System Actions:**  
   - LLM parses the request.
   - Batches/fetches all calendars.
   - Checks for conflicts.
   - Suggests time or auto-reschedules as needed.

3. **Output:**  
   JSON summary including all key meeting metadata, attendees, times, and explanatory meta.

## Key Advantages

- **Completely autonomous—no manual slot picking required.**
- **Flexible and accurate—handles complex, ambiguous human requests.**
- **Low-latency, scalable to large teams and busy calendars.**
- **Transparent and auditable logs for all scheduling activity.**
- **Easy to integrate, open, and extensible for future AI upgrades or policy customizations.**


**Ready to automate your meeting scheduling with true AI? Deploy, connect your calendar, and let agentic intelligence handle your calendar chaos!**

