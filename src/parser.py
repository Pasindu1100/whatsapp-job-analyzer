import re
import pandas as pd
from pathlib import Path

def parse_whatsapp_chat(file_path):
    print(f"Loading raw chat data from {file_path}...")
    # Supports both WhatsApp export styles:
    # 1) [MM/DD/YY, HH:MM:SS AM/PM] Sender: message
    # 2) M/D/YY, HH:MM AM/PM - Sender: message
    patterns = [
        r'^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}:\d{2}\s[AP]M)\]\s*(.*?):\s*(.*)$',
        r'^(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?\s*[AP]M)\s*-\s*(.*?):\s*(.*)$',
    ]
    parsed_data = []

    with open(file_path, 'r', encoding='utf-8') as file:
        current_date, current_time, current_sender = None, None, None
        current_message = []

        for line in file:
            line = line.strip()
            if not line:
                continue

            match = None
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    break

            if match:
                if current_sender is not None:
                    parsed_data.append(process_message(current_date, current_time, current_sender, current_message))
                current_date, current_time, current_sender, first_line_of_msg = match.groups()
                current_message = [first_line_of_msg]
            else:
                if current_sender is not None:
                    current_message.append(line)

        if current_sender is not None:
            parsed_data.append(process_message(current_date, current_time, current_sender, current_message))

    columns = ["source_group", "date", "time", "sender", "raw_text", "associated_media"]
    df = pd.DataFrame(parsed_data, columns=columns)
    if not df.empty:
        df = df.dropna(subset=['sender'])
    return df

def process_message(date, time, sender, message_lines):
    full_text = " \n ".join(message_lines)
    associated_media = None
    
    # Check for media tags and extract the filename
    if "<attached:" in full_text:
        media_match = re.search(r'<attached:\s([^>]+)>', full_text)
        if media_match:
            associated_media = media_match.group(1).strip()
            full_text = re.sub(r'<attached:\s[^>]+>', '', full_text).strip()
    
    return {
        "source_group": "UOB_Batch_Export",
        "date": date,
        "time": time,
        "sender": sender,
        "raw_text": full_text,
        "associated_media": associated_media
    }

if __name__ == "__main__":
    script_dir = Path(__file__).parent
    raw_chat_path = script_dir / "../data/raw/_chat.txt"
    output_path = script_dir / "../data/processed_jobs.json"
    raw_chat_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        jobs_df = parse_whatsapp_chat(raw_chat_path)
        
        # Filter: Keep messages with decent text length OR attached images
        jobs_df = jobs_df[(jobs_df['raw_text'].str.len() > 50) | (jobs_df['associated_media'].notna())]
        print(f"Successfully parsed {len(jobs_df)} potential job entries.")
        
        # FIXED: output_path is first (positional), orient and indent are named (keyword)
        jobs_df.to_json(output_path, orient="records", indent=4)
        print(f"Clean data saved to {output_path.resolve()}")
        
    except FileNotFoundError:
        print(f"Error: Could not find the file at: {raw_chat_path.resolve()}")