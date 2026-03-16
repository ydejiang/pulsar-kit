#!/usr/local/bin/python
import os
import sys
import datetime
import requests
from termcolor import colored
from bs4 import BeautifulSoup

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
import html
from email.mime.base import MIMEBase
from email import encoders

# This code was adapted from (Dr. Liu):
# Filarkey: Filtering latest arXiv papers by keywords and topics: https://github.com/pulsar-xliu/filter_arxiv_by_keywords.

# Define website to be read 
link = "https://arxiv.org/list/astro-ph/new"
# link = "https://arxiv.org/list/gr-qc/new"

# Set report path
base_path = '/home/yindejiang/arXiv'
topic = link.split('/')[-2]
report_path = os.path.join(base_path, topic) 
print("\n\tFilarkey: Filtering latest arXiv papers by keywords and topics")
print(f"\n\tDefault report repository:", colored(f"{report_path}", "blue"))

# Define keywords. 
# Use all_keywords for filtering. Report major_keyword only.
major_keyword  = ["pulsar", "neutron star", "black hole", "magnetar", "fast radio burst", "gravitational wave", "radio telescope", "scintillation", "single pulse"]
major_keywords = ["Pulsar", "Neutron Star", "Black Hole", "Magnetar", "Fast Radio Burst", "Gravitational Wave", "Radio Telescope", "Scintillation", "Single Pulse",
                  "pulsars", "neutron stars", "black holes", "magnetars", "fast radio bursts", "gravitational waves", "radio telescopes",
                  "Pulsars", "Neutron Stars", "Black Holes", "Magnetars", "Fast Radio Bursts", "Gravitational Waves", "Radio Telescopes"]
minor_keywords = ["X-ray binary", "globular cluster", "open cluster", 
                  "X-ray Binary", "Globular Cluster", "Open Cluster"]
short_keywords = ["MeerKAT", "SKA", "LMXB", "NS", "BH", "GW", "FRB"]
all_keywords = major_keyword + major_keywords + minor_keywords + short_keywords

def filter_papers(link, report_path, topic):
    """Access the website and extract paper information."""
    print(f"\tAccessing", colored(f"{link}", 'blue'))
    page = requests.get(link)
    soup = BeautifulSoup(page.content, 'html.parser')

    # get the date of latest release, check up to date.
    date_str = get_posting_date(soup)
    file_name = set_filename(report_path, topic, date_str)

    # Extract information 
    titles = soup.find_all('div', {'class' : 'list-title mathjax'})
    abstracts = soup.find_all('p', {'class' : 'mathjax'})
    authors = soup.find_all('div', {'class' : 'list-authors'})
    subjects = soup.find_all('div', {'class' : 'list-subjects'})
    refs = soup.find_all('a', {'title' : 'Abstract'})

    lines_titles = [title.get_text() for title in titles]
    lines_abstracts = [abstract.get_text() for abstract in abstracts]
    lines_authors = [author.get_text() for author in authors]
    lines_subjects = [subject.get_text() for subject in subjects]
    lines_refs = [ref.get_text() for ref in refs]

    lines_comments = get_comments(soup)

    print(f"\tData extracted")
    return date_str, file_name, lines_titles, lines_abstracts, lines_authors, lines_subjects, lines_refs, lines_comments

def get_posting_date(page_content):
    """Extract the posting date from the page."""
    date_element = page_content.find('h3', string=lambda t: t and "Showing new listings for" in t)
    date_str = date_element.get_text(strip=True).replace('Showing new listings for ', '')
    return date_str 

def set_filename(report_path, topic, date_str):
    """Create a filename to save the filtered papers."""
    date_obj = datetime.datetime.strptime(date_str, '%A, %d %B %Y')
    formatted_date = date_obj.strftime('%Y-%m-%d-') + date_obj.strftime('%a')
    os.makedirs(f"{report_path}", exist_ok=True)
    filename = os.path.join(report_path, f"{topic}_new_{formatted_date}.html")
    if os.path.exists(filename):
        print(colored(f"\n\tWarning: Reports up to date. Latest release at {formatted_date}", "yellow"))
        print('\tHave a nice day!\n')
        sys.exit()
    else:
        print(f"\n\tNew papers found")
        print("\tSaving reports to", colored(f"{filename.split('/')[-1]}\n", "magenta"))
        return filename

def get_comments(page_content):
    """Extract comments from the page. Use 'No comments' if not found."""
    papers = page_content.find_all('a', {'name': lambda x: x and x.startswith('item')})
    lines_comments = []

    for i in range(len(papers)):
        current_anchor = papers[i]
        next_anchor = papers[i+1] if i+1 < len(papers) else None
        
        # Find all elements between current_anchor and next_anchor
        elements_between = []
        elem = current_anchor.find_next()
        while elem and elem != next_anchor:
            elements_between.append(elem)
            elem = elem.find_next()
        
        # Check for list-comments within this section
        comments_tag = None
        for elem in elements_between:
            if elem.name == 'div' and 'class' in elem.attrs and 'list-comments' in elem.attrs['class']:
                comments_tag = elem
                break
        
        if comments_tag:
            comments = comments_tag.text.strip().replace('Comments: ', '')
        else:
            comments = 'Comments:\n No comments'
        lines_comments.append(comments)   

    return lines_comments


def write_html(all_keywords, major_keyword, date, filename,
               lines_titles, lines_abstracts, lines_authors,
               lines_subjects, lines_refs, lines_comments):
    """Filter the papers by keywords and save as an HTML file."""

    count_match = 1
    for i in range(len(lines_abstracts)):
        if any(word in lines_abstracts[i] for word in all_keywords):
            count_match += 1

    with open(filename, 'w', encoding='utf-8') as f:
        f.write("<!DOCTYPE html>\n")
        f.write("<html><head>\n")
        f.write("<meta charset='utf-8'>\n")
        f.write("<meta name='viewport' content='width=device-width, initial-scale=1.0'>\n")
        f.write("<title>Filarkey: New arXiv papers</title>\n")

        f.write("<script>MathJax = {tex: {inlineMath: [['$', '$'],['$$', '$$']]}}</script>\n")
        f.write('<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>\n')

        f.write("""
<style>
body {
    font-family: 'Lucida Grande', Helvetica, Arial, Verdana, sans-serif;
    font-size: 16px;
    line-height: 1.45;
    color: #222;
    background: #ffffff;
    max-width: 1400px;
    margin: 20px auto;
    padding: 0 24px;
}

h3 {
    margin-bottom: 8px;
    font-size: 1.35em;
    font-weight: 600;
}

p.page-meta {
    margin-top: 4px;
    margin-bottom: 8px;
}

.highlight {
    color: chocolate;
    font-weight: 600;
}

a {
    color: #1a5fb4;
    text-decoration: none;
}

a:visited {
    color: #1a5fb4;
}

a:hover {
    text-decoration: underline;
}

.paper-block {
    margin-bottom: 18px;
}

.paper-meta {
    margin-bottom: 2px;
    font-size: 1em;
}

.paper-title {
    padding-left: 28px;
    display: block;
    word-wrap: break-word;
    font-size: 1.2em;
    font-weight: 700;
    color: #222;
    margin-top: 3px;
    margin-bottom: 2px;
}

.paper-authors {
    padding-left: 28px;
    display: block;
    word-wrap: break-word;
    color: #1a5fb4;
    margin-top: 2px;
    margin-bottom: 2px;
}

.paper-comments {
    padding-left: 28px;
    display: block;
    word-wrap: break-word;
    font-size: 0.95em;
    color: #444;
    margin-top: 1px;
    margin-bottom: 2px;
}

.subject-tag {
    display: inline-block;
    margin-left: 6px;
    padding: 2px 8px;
    font-size: 0.78em;
    font-weight: 600;
    color: #ffffff;
    background-color: #6f8fc7;
    border-radius: 5px;
    vertical-align: middle;
    line-height: 1.3;
}

.abstract-box {
    padding-left: 28px;
    margin-top: 0;
    margin-bottom: 8px;
    max-width: 1300px;
    font-size: 0.98em;
    color: #222;
    line-height: 1.4;
}

.abstract-label {
#    font-weight: bold;
    color: #4b5cc4;
}

.abstract-details {
    display: inline;
}

.abstract-summary {
    display: inline;
    color: #4b5cc4;
    cursor: pointer;
    white-space: nowrap;
    margin-left: 4px;
    list-style: none;
}

.abstract-summary::-webkit-details-marker {
    display: none;
}

.more-text {
    display: inline;
    color: #4b5cc4;
}

.less-text {
    display: none;
    color: #4b5cc4;
}

.abstract-details[open] .more-text {
    display: none;
}

.abstract-details[open] .less-text {
    display: inline;
}

.footer-note {
    margin-top: 24px;
    color: #444;
}
</style>
""")

        f.write("</head><body>\n")

        f.write(f"<h3>Selected new papers on arXiv, {html.escape(str(date))}</h3>\n")
        f.write(f"<p class='page-meta'>Using keywords: <span class='highlight'>{html.escape(', '.join(major_keyword))}</span></p>\n")
        f.write(f"<p class='page-meta'>Retrieved <span class='highlight'>{count_match-1}</span> out of {len(lines_abstracts)} papers.</p>\n")

        count_paper = 1

        for i in range(len(lines_abstracts)):
            if any(word in lines_abstracts[i] for word in all_keywords):
                title = lines_titles[i]
                author = lines_authors[i]
                abstract = lines_abstracts[i]
                comments = lines_comments[i]
                subject = lines_subjects[i]
                ref = lines_refs[i].replace('arXiv:', 'abs/')

                title_clean = title.split('Title:')[-1].strip()
                html_url = 'https://arxiv.org/' + ref.strip()
                pdf_url = html_url.replace('/abs/', '/pdf/')

                title_clean = html.escape(title_clean)
                author = html.escape(author.replace("\n", " ").strip())
                abstract = html.escape(abstract.replace("\n", " ").strip())
                comments = html.escape(comments.replace("\n", " ").strip())
                subject = html.escape(subject)

                subjects_list = subject.split(';')
                first_subject = subjects_list[0].split(':')[-1].strip() if subjects_list else ''

                subject_name = ""
                subject_code = ""
                match = re.search(r'(.+?)\s*\(([^)]+)\)', first_subject)
                if match:
                    subject_name = match.group(1).strip()
                    subject_code = match.group(2).strip()

                preview = abstract[:0]

                f.write("<div class='paper-block'>\n")

                f.write(
                    f"<div class='paper-meta'>"
                    f"[{count_paper}] "
                    f"<a href='{html.escape(html_url)}'>arXiv:{html.escape(ref.split('/')[-1])}</a> "
                    f"[<a href='{html.escape(html_url)}'>html</a>, "
                    f"<a href='{html.escape(pdf_url)}'>pdf</a>]"
                )

                if subject_code:
                    f.write(
                        f" <span class='subject-tag' title='{html.escape(subject_name)}'>"
                        f"{html.escape(subject_code)}</span>"
                    )

                f.write("</div>\n")

                f.write(f"<span class='paper-title'>{title_clean}</span>\n")
                f.write(f"<span class='paper-authors'>{author}</span>\n")

                if comments.strip():
                    f.write(f"<span class='paper-comments'>{comments}</span>\n")

                f.write("<div class='abstract-box'>")
                f.write("<span class='abstract-label'>Abstract:</span> ")
                f.write(f"{preview}... ")

                f.write(
                    f"<details class='abstract-details'>"
                    f"<summary class='abstract-summary'>"
                    f"<span class='more-text'>▽ More</span>"
                    f"<span class='less-text'>△ Less</span>"
                    f"</summary>"
                    f"{abstract}"
                    f"</details>"
                )

                f.write("</div>\n")
                f.write("</div>\n")

                count_paper += 1

        f.write("<p class='footer-note'>End of selected papers.</p>\n")
        f.write("</body></html>\n")

    print(f"\tRetrieved {count_match-1} out of {len(lines_abstracts)} papers.")
    print("\n\tHave a nice day!\n")


'''
def send_email_html_report(
    html_file,
    date_str,
    smtp_server,
    smtp_port,
    sender_email,
    sender_password,
    receiver_email
):
    """
    Send the generated HTML report via QQ Mail SMTP server.
    The HTML is included both as email body and as an attachment.
    """

    # Read HTML content for email body
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Create email message
    msg = MIMEMultipart()
    msg['Subject'] = f"arXiv Physics-{topic} daily report ({date_str})"
    msg['From'] = sender_email

    if isinstance(receiver_email, list):
        msg['To'] = ", ".join(receiver_email)
    else:
        msg['To'] = receiver_email

    # 1) Attach HTML body
    html_part = MIMEText(html_content, 'html', 'utf-8')
    msg.attach(html_part)

    # 2) Attach local HTML file
    with open(html_file, 'rb') as f:
        attachment = MIMEBase('text', 'html')
        attachment.set_payload(f.read())

    encoders.encode_base64(attachment)
    attachment.add_header(
        'Content-Disposition',
        f'attachment; filename="{os.path.basename(html_file)}"'
    )
    msg.attach(attachment)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()

        print(colored("\tEmail notification sent successfully via QQ Mail.", "green"))

    except Exception as e:
        print(colored(f"\tEmail sending failed: {e}", "red"))

'''

def send_email_html_report(
    html_file,
    date_str,
    smtp_server,
    smtp_port,
    sender_email,
    sender_password,
    receiver_email
):
    """
    Send the generated HTML report via QQ Mail SMTP server.

    Parameters
    ----------
    html_file : str
        Path to the generated HTML report.
    date_str : str
        arXiv posting date string.
    smtp_server : str
        SMTP server address (e.g. smtp.qq.com).
    smtp_port : int
        SMTP server port (587 for QQ Mail).
    sender_email : str
        Sender email address.
    sender_password : str
        QQ Mail authorization code.
    receiver_email : str
        Receiver email address.
    """

    # Read HTML content
    with open(html_file, 'r') as f:
        html_content = f.read()

    # Create email message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"arXiv Physics-{topic} daily report ({date_str})"
    msg['From'] = sender_email
    # msg['To'] = receiver_email
    # Set email header "To"
    if isinstance(receiver_email, list):
        msg['To'] = ", ".join(receiver_email)
    else:
        msg['To'] = receiver_email

    # Attach HTML body
    html_part = MIMEText(html_content, 'html')
    msg.attach(html_part)

    try:
        # Connect to SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable TLS encryption
        server.login(sender_email, sender_password)

        # Send email
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()

        print(colored("\tEmail notification sent successfully via QQ Mail.", "green"))

    except Exception as e:
        print(colored(f"\tEmail sending failed: {e}", "red"))
                                                    

def main():
    report_info = filter_papers(link, report_path, topic)
    write_html(all_keywords, major_keyword, *report_info)

    # QQ Mail SMTP configuration
    smtp_server = "smtp.qq.com"
    smtp_port   = 587
    sender_email = "atel_gcn@qq.com"
    sender_password = "tfgwylabgimpcicg"   # QQ Mail authorization code
    receiver_emails = ["yin.dj@qq.com"]
    #receiver_emails = ["yin.dj@qq.com", "yfeng.dai@foxmail.com", "1938079121@qq.com", "2896663909@qq.com",
    #                   "13108997893@163.com"]
    # receiver_emails = ["atel_gcn@qq.com"]
    receiver_email = receiver_emails

    # Send email with HTML report
    date_str, filename, *_ = report_info
    send_email_html_report(
        filename,
        date_str,
        smtp_server,
        smtp_port,
        sender_email,
        sender_password,
        receiver_email
    )


if __name__ == '__main__':
    main()
