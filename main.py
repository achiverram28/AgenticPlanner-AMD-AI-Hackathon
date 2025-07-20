from openai import OpenAI
from datetime import datetime, timedelta, timezone, time
import json
import pytz
import re
from dateparser import parse as dp_parse
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dateutil import parser
import pytz

class AI_AGENT:
    def __init__(self):
        self.client = OpenAI(
            api_key="NULL",
            base_url="http://localhost:3000/v1",
            timeout=None,
            max_retries=0
        )
        self.model_path = "/home/user/Models/deepseek-ai/deepseek-llm-7b-chat"

    def get_next_weekday_date(self, base_date: datetime, target_weekday: int) -> datetime:
        days_ahead = (target_weekday - base_date.weekday() + 7) % 7
        if days_ahead == 0:
            days_ahead = 7
        return base_date + timedelta(days=days_ahead)

    def extract_time(self, text: str, ref: datetime) -> datetime.time:
        time_match = re.search(r'(\d{1,2}(:\d{2})?\s*(AM|PM|A\.M\.|P\.M\.)?)', text, re.IGNORECASE)
        if time_match:
            time_str = time_match.group(0)
            parsed_time = dp_parse(time_str, settings={
                "PREFER_DATES_FROM": "future",
                "RETURN_AS_TIMEZONE_AWARE": False
            })
            if parsed_time:
                return parsed_time.time()
        return datetime.min.time()

    def llm_analyze_email(self, subject, content):
        prompt = f"""
            You are an assistant that analyzes email tone, context, and urgency.
            
            Subject: {subject}
            Content: {content}
            
            Analyze this email and respond with:
            - tone: one of [urgent, neutral, casual]
            - reason: brief explanation
            - priority: integer (1 = high, 2 = medium, 3 = low)
            
            Respond in this JSON format:
            {{
              "tone": "...",
              "reason": "...",
              "priority": ...
            }}
            """

        response = self.client.chat.completions.create(
                model="/home/user/Models/deepseek-ai/deepseek-llm-7b-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=128,
                temperature=0.0
            )
        content = response.choices[0].message.content.strip()
        return json.loads(content)
        
        

    def parse_email(self, email_text: str, reference_date: str = None) -> dict:
        try:
            ref_dt = datetime.strptime(reference_date, "%d-%m-%YT%H:%M:%S")
            ref_dt = ref_dt.replace(tzinfo=pytz.utc)  # assuming input is UTC
        except ValueError:
            return {"DateTime": None}

        weekdays = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }

        weekday_found = None
        for wd in weekdays:
            if wd in email_text.lower():
                weekday_found = weekdays[wd]
                break

        if weekday_found is None:
            return {"DateTime": None}

        target_date = self.get_next_weekday_date(ref_dt, weekday_found)

        time_part = self.extract_time(email_text, ref_dt)

        ist = pytz.timezone("Asia/Kolkata")
        combined_dt = datetime.combine(target_date.date(), time_part)
        ist_dt = ist.localize(combined_dt)

        return {"DateTime": ist_dt.isoformat()}

def is_free(start_time, duration_minutes, busy_slots):
        end_time = start_time + timedelta(minutes=duration_minutes)
        for slot_start, slot_end in busy_slots:
            if not (end_time <= slot_start or start_time >= slot_end):
                return False
        return True
    
def retrieve_calendar_events(user, start, end):
    events_list = []
    token_path = "Keys/"+user.split("@")[0]+".token"
    user_creds = Credentials.from_authorized_user_file(token_path)
    calendar_service = build("calendar", "v3", credentials=user_creds)
    events_result = calendar_service.events().list(calendarId='primary', timeMin=start,timeMax=end,singleEvents=True,orderBy='startTime').execute()
    events = events_result.get('items')
    
    for event in events : 
        attendee_list = []
        try:
            for attendee in event["attendees"]: 
                attendee_list.append(attendee['email'])
        except: 
            attendee_list.append("SELF")
        start_time = event["start"]["dateTime"]
        end_time = event["end"]["dateTime"]
        events_list.append(
            {"StartTime" : start_time, 
             "EndTime": end_time, 
             "NumAttendees" :len(set(attendee_list)), 
             "Attendees" : list(set(attendee_list)),
             "Summary" : event["summary"]})
    return events_list

def merge_events(*event_lists):
    busy_intervals = []
    for events in event_lists:
        for ev in events:
            busy_intervals.append((parser.isoparse(ev["StartTime"]), parser.isoparse(ev["EndTime"])))
    # sort and merge overlaps
    busy_intervals.sort()
    merged = []
    for start, end in busy_intervals:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return merged

def find_next_available_slot(busy_slots, duration_minutes, day_start, day_end):
    slot_start = day_start
    while slot_start + timedelta(minutes=duration_minutes) <= day_end:
        if is_free(slot_start, duration_minutes, busy_slots):
            return slot_start
        slot_start += timedelta(minutes=30)  # 15 min granularity
    return None

def generate_reschedule_note(agent, user_email, summary, proposed_time):
    prompt = f"""
        The proposed time {proposed_time.strftime('%Y-%m-%d %H:%M')} conflicts with the event: '{summary}' for user {user_email}.
        Please generate a polite one-liner explaining why this meeting might be difficult to reschedule.
        Focus on the importance of the event based on the summary.
        """
    response = agent.client.chat.completions.create(
        model="/home/user/Models/deepseek-ai/deepseek-llm-7b-chat",
        messages=[
            {"role": "system", "content": "You are a polite assistant who helps schedule meetings."},
            {"role": "user", "content": prompt.strip()}
        ],
        temperature=0.7,
        max_tokens=80,
    )
    return response.choices[0].message.content.strip()    
    

def handle_meeting_request(input_json):

    request_id = input_json["Request_id"]
    email_dt = input_json["Datetime"]
    location = input_json["Location"]
    sender = input_json["From"]
    subject = input_json["Subject"]
    content = input_json["EmailContent"]
    attendees = [att["email"] for att in input_json["Attendees"]]

    agent = AI_AGENT()
    email_context = agent.llm_analyze_email(subject, content)
    priority = email_context["priority"]
    tone = email_context["tone"]
    
    proposed_time = agent.parse_email(content, str(email_dt))["DateTime"]
    proposed_time = parser.isoparse(proposed_time)  # ensure datetime object

    match = re.search(r"(\d+)\s*minute", content.lower())
    duration_minutes = int(match.group(1)) if match else 60

    date_only = proposed_time.date()
    ist = pytz.timezone("Asia/Kolkata")
    day_start = ist.localize(datetime.combine(date_only, time(9, 0)))  
    day_end = ist.localize(datetime.combine(date_only, time(20, 0)))  

   
    user_event_map = {}
    all_events = []

    for email in [sender] + attendees:
        events = retrieve_calendar_events(email, day_start.isoformat(), day_end.isoformat())
        if proposed_time.time() == time(0, 0) and email == sender:
            print(f"Since exact time is not provided, defaulting to sender {sender} first free slot")
            busy_slots = merge_events(events)
            def is_free_for_sender(start_time):
                end_time = start_time + timedelta(minutes=duration_minutes)
                for slot_start, slot_end in busy_slots:
                    if not (end_time <= slot_start or start_time >= slot_end):
                        return False
                return True
            current = day_start
            while current + timedelta(minutes=duration_minutes) <= day_end:
                if is_free_for_sender(current):
                    proposed_time = current
                    break
                current += timedelta(minutes=30)
            print(proposed_time)

        user_event_map[email] = events
        all_events.append(events)

    # Step 4: Conflict check
    busy_slots = merge_events(*all_events)

    
    negotiation_note = ""
    
    if is_free(proposed_time, duration_minutes, busy_slots):
        final_start = proposed_time
    else:
        conflicted_users = []
        polite_notes = {}
        for email in attendees + [sender]:
            if email == sender:
                continue
            for event in user_event_map[email]:
                ev_start = parser.isoparse(event["StartTime"]).astimezone(ist)
                ev_end = parser.isoparse(event["EndTime"]).astimezone(ist)
                if ev_start <= proposed_time < ev_end:
                    conflicted_users.append(email)
                    note = generate_reschedule_note(agent, email, event.get("Summary", "No summary"), proposed_time)
                    polite_notes[email] = note
                    break
    
        negotiation_note = {
            "negotiation_required": True,
            "conflicted_users": list(set(conflicted_users)),
            "polite_notes": polite_notes,
            "note": f"The proposed time {proposed_time.strftime('%Y-%m-%d %H:%M')} has conflicts with some users."
        }
        final_start = find_next_available_slot(busy_slots, duration_minutes, day_start, day_end)

    if final_start is None:
        for offset in range(1, 8):
            future_date = date_only + timedelta(days=offset)
            day_start = ist.localize(datetime.combine(future_date, time(9, 0)))
            day_end = ist.localize(datetime.combine(future_date, time(20, 0)))
            # Update calendar fetch range
            all_events = []
            for email in [sender] + attendees:
                events = retrieve_calendar_events(email, day_start.isoformat(), day_end.isoformat())
                user_event_map[email] = events
                all_events.append(events)

            busy_slots = merge_events(*all_events)
            next_slot = find_next_available_slot(busy_slots, duration_minutes, day_start, day_end)
            if next_slot:
                final_start = next_slot
                break

    if final_start is None:
        return {
            "error": "No common slot found within the next 7 days for all attendees.",
            "Request_id": request_id
        }

    final_end = final_start + timedelta(minutes=duration_minutes)
   

    if priority == 1 and not is_free(proposed_time, duration_minutes, busy_slots):
        if isinstance(proposed_time, datetime):
            prop_time = proposed_time.time()
        else:
            prop_time = proposed_time
        final_start = proposed_time
        final_end = proposed_time + timedelta(minutes=duration_minutes)

        conflicted_users = []
        for email in attendees + [sender]:
            if email == sender:
                continue
            for event in user_event_map[email]:
                ev_start = parser.isoparse(event["StartTime"]).astimezone(ist)
                ev_end = parser.isoparse(event["EndTime"]).astimezone(ist)
                if ev_start <= ist.localize(datetime.combine(date_only, proposed_time.time())) < ev_end:
                    conflicted_users.append(email)
                    break
    
        negotiation_note = {
            "negotiation_required": True,
            "conflicted_users": list(set(conflicted_users)),
            "note": f"The proposed time {proposed_time} has conflicts. Please coordinate for the meet as this is of high priroty"
        }

    scheduled_event = {
        "StartTime": final_start.isoformat(),
        "EndTime": final_end.isoformat(),
        "NumAttendees": len([sender] + attendees),
        "Attendees": [sender] + attendees,
        "Summary": subject
    }

    enriched_attendees = []
    for email in [sender] + attendees:
        enriched_attendees.append({
            "email": email,
            "events": user_event_map[email] + [scheduled_event]
        })

    output = {
        "Request_id": request_id,
        "Datetime": input_json["Datetime"],
        "Location": location,
        "From": sender,
        "Attendees": enriched_attendees,
        "Subject": subject,
        "EmailContent": content,
        "EventStart": final_start.isoformat(),
        "EventEnd": final_end.isoformat(),
        "Duration_mins": str(duration_minutes),
        "MetaData": {
            "LLM_Tone": tone,
            "Priority": priority,
            "LLM_Reason": email_context["reason"],
            "Negotiation note": negotiation_note
        }
    }

    return output
    
