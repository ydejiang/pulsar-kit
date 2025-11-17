#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ATel and GCN Circular Email Aggregator

This script fetches recent ATel and GCN Circular emails from QQ mailbox,
parses their contents, and sends a consolidated report to the user's email.
"""

import imaplib
import email
import re
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import pytz
import argparse

# --------------------------
# Configuration Section
# --------------------------

# Timezone configuration (QQ mailbox uses Beijing time)
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# QQ Mail Server Configuration
IMAP_SERVER = "imap.qq.com"    # IMAP server address
IMAP_PORT = 993                # IMAP SSL port
SMTP_SERVER = "smtp.qq.com"    # SMTP server address
SMTP_PORT = 587                # SMTP submission port

# Default Email Account Configuration
DEFAULT_EMAIL = "20251117demo@qq.com"               # Default QQ email address
#DEFAULT_PASSWORD = "20251117demo"         # Default authorization code
DEFAULT_PASSWORD = "20251117demo" 
DEFAULT_TARGET_EMAIL = DEFAULT_EMAIL          # Default send to yourself

# IMAP Folder Names (from mail.list())
ATEL_FOLDER = "&UXZO1mWHTvZZOQ-/ATel"        # ATel mailbox folder
GCN_FOLDER = "&UXZO1mWHTvZZOQ-/GCN"          # GCN mailbox folder

# --------------------------
# Core Functions
# --------------------------

def get_current_utc_time():
    """
    Get current UTC time formatted in standard ATel style
    
    Returns:
        str: Formatted time string (e.g., '02 Sep 2025; 04:43 UT')
    """
    now = datetime.utcnow()
    return now.strftime("%d %b %Y; %H:%M UT")

def parse_atel_date(date_str):
    """
    Parse ATel date string into datetime object (Beijing time)
    
    Args:
        date_str: Date string in format "1 Sep 2025; 20:29 UT"
    
    Returns:
        datetime: Localized datetime object in Beijing timezone
    """
    try:
        # Split date and time parts
        date_part, time_part = date_str.split(";")
        
        # Extract day, month, year
        day, month, year = date_part.strip().split()
        
        # Extract hour and minute
        hour, minute = time_part.strip().split()[0].split(":")
        
        # Convert month name to number
        month_num = datetime.strptime(month, "%b").month
        
        # Create datetime object
        dt = datetime(int(year), month_num, int(day), int(hour), int(minute))
        dt = pytz.UTC.localize(dt) 
        return dt.astimezone(BEIJING_TZ)
    except Exception as e:
        print(f"Failed to parse ATel date: {date_str} - Using current time instead")
        return datetime.now(BEIJING_TZ)

def parse_gcn_date(date_str):
    """
    Parse GCN date string into datetime object (Beijing time)
    
    Args:
        date_str: Date string in format "25/09/02 19:46:44 GMT"
    
    Returns:
        datetime: Localized datetime object in Beijing timezone
    """
    try:
        date_str = date_str.strip()
        
        # Split date and time parts
        date_part, time_part = date_str.split()[:2]
        
        # Extract year, month, day (format: 25/09/02)
        yy, mm, dd = date_part.split("/")
        
        # Extract hour, minute, second
        hour, minute, second = time_part.split(":")
        
        # Create datetime object (note: GCN years are 2-digit)
        dt = datetime(int("20"+yy), int(mm), int(dd),
                     int(hour), int(minute), int(second))
        dt = pytz.UTC.localize(dt)
        #return BEIJING_TZ.localize(dt)
        return dt.astimezone(BEIJING_TZ)
    except Exception as e:
        print(f"Failed to parse GCN date: {date_str} - Using current time instead")
        return datetime.now(BEIJING_TZ)

def fetch_emails(folder, hours=24, email_account=None, email_password=None):
    """
    Fetch emails from specified folder within given time range
    
    Args:
        folder: IMAP folder name to search
        hours: Time range in hours to look back
        email_account: QQ email account (uses default if None)
        email_password: QQ email authorization code (uses default if None)
    
    Returns:
        list: List of email body texts or None if error occurs
    """
    # Use provided credentials or defaults
    email_account = email_account or DEFAULT_EMAIL
    email_password = email_password or DEFAULT_PASSWORD
    
    try:
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(email_account, email_password)

        # Select target folder
        status, _ = mail.select(folder)
        if status != "OK":
            print(f"Error: Cannot find folder {folder}")
            mail.logout()
            return None

        # Calculate time range cutoff
        cutoff_time = datetime.now(BEIJING_TZ) - timedelta(hours=hours)
        since_str = cutoff_time.strftime("%d-%b-%Y")  # IMAP date format
        
        # Search for emails since specified date
        status, data = mail.uid('SEARCH', None, f'(SINCE "{since_str}")')
        if status != "OK" or not data[0]:
            print(f"Warning: No emails found in last {hours} hours")
            mail.close()
            mail.logout()
            return None

        # Process found emails (newest first)
        email_uids = data[0].split()
        all_messages = []
        
        for uid in reversed(email_uids):
            status, msg_data = mail.uid('FETCH', uid, "(RFC822)")
            if status != "OK":
                continue
                
            msg = email.message_from_bytes(msg_data[0][1])
            
            # Extract and parse email date
            msg_date = None
            if 'Date' in msg:
                try:
                    msg_date = email.utils.parsedate_to_datetime(msg['Date'])
                    # Convert to Beijing time if no timezone specified
                    if msg_date.tzinfo is None:
                        msg_date = pytz.utc.localize(msg_date).astimezone(BEIJING_TZ)
                    else:
                        msg_date = msg_date.astimezone(BEIJING_TZ)
                except Exception as e:
                    print(f"Warning: Cannot parse email date: {msg['Date']}")

            # Only include emails within our time range
            if msg_date is None or msg_date >= cutoff_time:
                # Extract plain text body
                body_text = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body_text = part.get_payload(decode=True).decode(errors="ignore")
                            break
                else:
                    body_text = msg.get_payload(decode=True).decode(errors="ignore")
                
                all_messages.append(body_text)

        # Clean up connection
        mail.close()
        mail.logout()
        return all_messages

    except Exception as e:
        print(f"Error fetching emails: {str(e)}")
        return None

def parse_atel_content(raw_text_list):
    """
    Parse ATel email contents and extract key information
    
    Args:
        raw_text_list: List of raw email texts
    
    Returns:
        list: List of dictionaries containing parsed ATel information:
              - num: Circular number
              - title: Title text
              - posted_date: Original date string
              - posted_datetime: Parsed datetime object
              - url: Direct URL to circular
    """
    all_atels = []
    
    for raw_text in raw_text_list:
        # Match ATel header pattern using regex
        atels = re.findall(
            r"ATEL\s*#(\d+)\s*ATEL\s*#\d+\s*\nTitle:\s*(.*?)\nAuthor:.*?Posted:\s*(.*?)\n",
            raw_text, re.DOTALL
        )
        
        # Process each matched ATel
        for num, title, posted_date in atels:
            # Clean up title (remove extra whitespace)
            title = " ".join(title.split())
            
            all_atels.append({
                "num": num.strip(),
                "title": title,
                "posted_date": posted_date.strip(),
                "posted_datetime": parse_atel_date(posted_date),
                "url": f"https://www.astronomerstelegram.org/?read={num.strip()}"
            })

    # Sort by posting time (newest first)
    if all_atels:
        all_atels.sort(key=lambda x: x["posted_datetime"], reverse=True)
    return all_atels

def parse_gcn_content(raw_text_list):
    """
    Parse GCN Circular email contents and extract key information
    
    Args:
        raw_text_list: List of raw email texts
    
    Returns:
        list: List of dictionaries containing parsed GCN information:
              - num: Circular number
              - subject: Subject text
              - posted_date: Original date string
              - posted_datetime: Parsed datetime object
              - url: Direct URL to circular
    """
    all_gcns = []
    
    for raw_text in raw_text_list:
        # Match GCN header pattern using regex
        matches = re.finditer(
            r"NUMBER:\s*(\d+).*?"
            r"SUBJECT:\s*(.*?)\n"
            r"DATE:\s*(.*?GMT)\s*"
            r".*?"
            r"View this GCN Circular online at (https://gcn\.nasa\.gov/circulars/\d+)",
            raw_text,
            re.DOTALL
        )
        
        # Process each matched GCN
        for match in matches:
            num, subject, date_str, url = match.groups()
            all_gcns.append({
                "num": num.strip(),
                "subject": " ".join(subject.split()),  # Clean up subject
                "posted_date": date_str.strip(),
                "posted_datetime": parse_gcn_date(date_str),
                "url": url.strip()
            })

    # Sort by posting time (newest first)
    if all_gcns:
        all_gcns.sort(key=lambda x: x["posted_datetime"], reverse=True)
    return all_gcns

def format_number_range(numbers):
    """
    Format a list of numbers into a concise range string
    
    Args:
        numbers: List of number strings (e.g., ["41663", "41662", "41661"])
    
    Returns:
        str: Formatted range (e.g., "41663-41661" for multiple numbers)
             or single number (e.g., "41663" for one number)
    """
    if not numbers:
        return ""
    if len(numbers) == 1:
        return numbers[0]
    return f"{numbers[0]}-{numbers[-1]}"

def generate_combined_email(atels, gcns):
    """
    Generate combined email subject and content from parsed ATel/GCN data
    
    Args:
        atels: List of parsed ATel dictionaries
        gcns: List of parsed GCN dictionaries
    
    Returns:
        tuple: (subject, body_text) where:
               - subject: Email subject line
               - body_text: Full email content
    """
    # Process ATel information
    atel_numbers = [atel["num"] for atel in atels]
    atel_subject_part = f"ATel #{format_number_range(atel_numbers)}" if atel_numbers else ""
    
    # Format ATel entries for email body
    atel_content = []
    for atel in atels:
        atel_content.append(
            #f"#{atel['num']}. {atel['title']} ({atel['posted_date']}) [{atel['url']}]"
            f"#{atel['num']}. {atel['title']} [{atel['url']}]"
        )
    
    # Process GCN information
    gcn_numbers = [gcn["num"] for gcn in gcns]
    gcn_subject_part = f"GCN #{format_number_range(gcn_numbers)}" if gcn_numbers else ""
    
    # Format GCN entries for email body
    gcn_content = []
    for gcn in gcns:
        gcn_content.append(
            #f"#{gcn['num']}. {gcn['subject']} ({gcn['posted_date']}) [{gcn['url']}]"
            f"#{gcn['num']}. {gcn['subject']} [{gcn['url']}]"
        )
    
    # Generate subject line by combining ATel and GCN parts
    subject_parts = []
    if atel_subject_part:
        subject_parts.append(atel_subject_part)
    if gcn_subject_part:
        subject_parts.append(gcn_subject_part)
    subject = " & ".join(subject_parts) if subject_parts else "No new alerts"
    
    # Generate email header with current time
    current_time = get_current_utc_time()
    header = f"Astronomy Alerts Posted within the last 24 hours ({current_time}):\n\n"
    
    # Build email body sections
    body_parts = []
    
    # Add ATel section if exists
    if atel_content:
        body_parts.append("The Astronomer's Telegram:\n" + "\n".join(atel_content))
    
    # Add GCN section if exists
    if gcn_content:
        # Add separator line if both sections exist
        if atel_content:
            body_parts.append("")
        body_parts.append("GCN Circulars:\n" + "\n".join(gcn_content))
    
    # Combine all parts into final email body
    body_text = header + "\n".join(body_parts)
    return subject, body_text

def send_email(subject, content, email_account=None, email_password=None, target_emails=None):
    """
    Send email with given subject and content
    
    Args:
        subject: Email subject line
        content: Email body content
        email_account: QQ email account (uses default if None)
        email_password: QQ email authorization code (uses default if None)
        target_emails: List of target email addresses (uses sender if None)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Use provided credentials or defaults
    email_account = email_account or DEFAULT_EMAIL
    email_password = email_password or DEFAULT_PASSWORD
    target_emails = target_emails or [email_account]  # Default to sender if not specified
    
    try:
        # Create MIME email message
        msg = MIMEText(content, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = email_account
        msg["To"] = ", ".join(target_emails)  # Multiple recipients separated by comma

        # Connect to SMTP server and send
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(email_account, email_password)
        server.sendmail(email_account, target_emails, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def main(atel_hours=25, gcn_hours=25, email_account=None, email_password=None, target_emails=None):
    """
    Main function to execute the email aggregation process
    
    Args:
        atel_hours: Hours to look back for ATel emails (default: 25)
        gcn_hours: Hours to look back for GCN emails (default: 25)
        email_account: QQ email account (uses default if None)
        email_password: QQ email authorization code (uses default if None)
        target_emails: List of target email addresses (uses sender if None)
    
    Returns:
        bool: True if successful, False if any error occurred
    """
    print("\n" + "="*60)
    print(f"Starting ATel/GCN email aggregator (ATel: {atel_hours}h, GCN: {gcn_hours}h)")
    print("="*60 + "\n")
    
    # Use provided credentials or defaults
    email_account = email_account or DEFAULT_EMAIL
    email_password = email_password or DEFAULT_PASSWORD
    target_emails = target_emails or [email_account]
    
    print(f"Using email account: {email_account}")
    print(f"Sending to: {', '.join(target_emails)}")

    # Fetch and parse ATel emails
    print(f"\n[1/3] Fetching ATel emails (last {atel_hours} hours)...")
    atel_raw = fetch_emails(ATEL_FOLDER, atel_hours, email_account, email_password)
    atels = parse_atel_content(atel_raw) if atel_raw else []
    print(f"Found {len(atels)} ATel circulars")
    
    # Fetch and parse GCN emails
    print(f"\n[2/3] Fetching GCN emails (last {gcn_hours} hours)...")
    gcn_raw = fetch_emails(GCN_FOLDER, gcn_hours, email_account, email_password)
    gcns = parse_gcn_content(gcn_raw) if gcn_raw else []
    print(f"Found {len(gcns)} GCN circulars")
    
    # Check if we found any alerts
    if not atels and not gcns:
        print("\nWarning: No ATel or GCN emails found in specified time ranges")
        return False
    
    # Generate combined email
    print("\n[3/3] Generating combined email...")
    subject, content = generate_combined_email(atels, gcns)
    
    # Display preview before sending
    print("\n" + "="*60)
    print("Email Content Preview:")
    print("="*60)
    print(content)
    print("="*60 + "\n")
    
    # Send the email
    if send_email(subject, content, email_account, email_password, target_emails):
        print(f"Successfully sent email to {target_emails}: {subject}")
        print(f"Statistics: ATel {len(atels)} (last {atel_hours}h), GCN {len(gcns)} (last {gcn_hours}h)")
        return True
    else:
        return False

if __name__ == "__main__":
    # Set up command line argument parser
    parser = argparse.ArgumentParser(
        description="ATel and GCN Circular Email Aggregator - Fetches recent astronomy alerts and sends consolidated report",
        #formatter_class=argparse.ArgumentDefaultsHelpFormatter
        formatter_class=argparse.HelpFormatter 
    )
    
    # Time range parameters
    parser.add_argument(
        "--atel-hours",
        type=int,
        default=25,
        help="Hours to look back for ATel emails [default: %(default)s]"
    )
    parser.add_argument(
        "--gcn-hours",
        type=int,
        default=25,
        help="Hours to look back for GCN emails [default: %(default)s]"
    )
    
    # Email account parameters
    parser.add_argument(
        "--email",
        type=str,
        help=f"QQ email account for fetching emails [default: {DEFAULT_EMAIL}]"
    )
    parser.add_argument(
        "--password",
        type=str,
        help="QQ email authorization code [default: script default]"
    )
    parser.add_argument(
        "--target",
        type=str,
        help="Target email address(es), comma-separated for multiple [default: same as sender]"
    )
    
    # Parse command line arguments
    args = parser.parse_args()
    
    # Split target emails if multiple provided
    target_emails = [email.strip() for email in args.target.split(",")] if args.target else None
    
    # Execute main function with provided arguments
    if main(
        atel_hours=args.atel_hours,
        gcn_hours=args.gcn_hours,
        email_account=args.email,
        email_password=args.password,
        target_emails=target_emails
    ):
        exit(0)  # Success
    else:
        exit(1)  # Error
