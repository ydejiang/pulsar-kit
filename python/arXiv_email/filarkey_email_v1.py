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

def write_html(all_keywords, major_keyword, date, filename, lines_titles, lines_abstracts, lines_authors, lines_subjects, lines_refs, lines_comments):
    """Filter the papers by keywords and save as an HTML file."""
    count_match = 1
    for i in range(len(lines_abstracts)):
        if any(word in lines_abstracts[i] for word in all_keywords):
            count_match += 1
    
    with open(filename, 'w') as f:
        # Write a header to render LaTeX equations
        f.write("<html><head>\n")
        f.write(f"<title>Filarkey: New arXiv papers</title>")
        f.write(f"<h3>Selected new papers on arXiv Physics-{topic}, {date}</h3>\n")
        f.write(f"<p>Using keywords: <span style='color: Chocolate;'>{', '.join(major_keyword)}</span></p>\n")
        f.write(f"<p>Retrived <span style='color: Chocolate;'>{count_match-1}</span> out of {len(lines_abstracts)} papers.</p>\n")
        f.write("<script>MathJax = {tex: {inlineMath: [['$', '$'],['$$', '$$']]}}</script>")
        f.write('<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>')

        # Add CSS for font family
        f.write("<style>body {font-family: font-family: 'Lucida Grande', helvetica, arial, verdana, sans-serif;}</style>\n")
        f.write("</head><body>\n")

        count_paper = 1
        for i in range(len(lines_abstracts)):
            if any(word in lines_abstracts[i] for word in all_keywords):
                title = lines_titles[i].encode('ascii', 'ignore').decode('ascii')
                author = lines_authors[i].encode('ascii', 'ignore').decode('ascii')
                abstract = lines_abstracts[i].encode('ascii', 'ignore').decode('ascii')
                comments = lines_comments[i].encode('ascii', 'ignore').decode('ascii')
                subject = lines_subjects[i].encode('ascii', 'ignore').decode('ascii')
                ref = lines_refs[i].encode('ascii', 'ignore').decode('ascii').replace('arXiv:', 'abs/')

                title_clean = title.split('Title:')[-1].strip()
                html_url = 'https://arxiv.org/' + ref.strip()
                pdf_url = html_url.replace('abs', 'pdf')
                
                subjects_list = subject.split(';')
                first_subject = subjects_list[0].split(':')[-1].strip() if subjects_list else ''
                other_subjects = '; '.join(subjects_list[1:]).strip() if len(subjects_list) > 1 else ''
                # Parse primary subject: name + code
                subject_name = ""
                subject_code = ""
                match = re.search(r'(.+?)\s*\(([^)]+)\)', first_subject)
                if match:
                    subject_name = match.group(1).strip()
                    subject_code = match.group(2).strip()
 
                # Write the information of the matched papers
                # f.write(f"[{count_paper}] <a href='{html_url}' style='text-decoration: none;'>arXiv:{ref.split('/')[-1]}</a> [<a href='{html_url}' style='text-decoration: none;'>html</a>, <a href='{pdf_url}' style='text-decoration: none;'>pdf</a>]<br>")
                f.write(
                    f"[{count_paper}] "
                    f"<a href='{html_url}' style='text-decoration: none;'>"
                    f"arXiv:{ref.split('/')[-1]}</a> "
                    f"[<a href='{html_url}' style='text-decoration: none;'>html</a>, "
                    f"<a href='{pdf_url}' style='text-decoration: none;'>pdf</a>] "
                 )
                if subject_code:
                    f.write(
                        f"""
                        <span style="
                        display: inline-block;
                        margin-left: 6px;
                        padding: 2px 6px;
                        font-size: 0.8em;
                        font-weight: 600;
                        color: white;
                        background-color: #5f86c6;
                        border-radius: 4px;
                        vertical-align: middle;
                        "
                        title="{subject_name}">
                        {subject_code}
                        </span>
                        """
                        )
                f.write("<br>\n")
                f.write(f"<strong style='padding-left: 40px; display: block; word-wrap: break-word; font-size: 1.25em;'>{title_clean}</strong>\n")
                f.write(f"<span style='padding-left: 40px; display: block; color: blue; word-wrap: break-word;'>{author}</span>\n")
                f.write(f"<span style='padding-left: 40px; display: block; word-wrap: break-word; font-size: 0.9em;'>{comments}</span>\n")
                
                # if first_subject:
                #    f.write(f"<span style='padding-left: 40px; display: block; word-wrap: break-word; font-size: 0.9em;'>Subjects: <strong>{first_subject}</strong>")
                #    if other_subjects:
                #        f.write(f"; {other_subjects}")
                #    f.write("</span>\n")

                # f.write(f"<p style='padding-left: 40px;'>{abstract}</p>\n")
                f.write(
                    f"""
                    <details style="padding-left: 40px;">
                    <summary style="cursor: pointer; font-size: 1.2em; color: purple;">
                    Abstract (click to expand)
                    </summary>
                    <p style="margin-top: 8px;">{abstract}</p>
                    </details>
                    <div style="margin-bottom: 5px;"></div>
                     """
                )
                count_paper += 1
        f.write("<p>End of selected papers.</p>\n")
        f.write(f"<br>\n")
        f.write("</body></html>\n") 
    print(f"\tRetrived {count_match-1} out of {len(lines_abstracts)} papers.")
    print("\n\tHave a nice day!\n")



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


'''
def main():
    report_info = filter_papers(link, report_path, topic)
    write_html(all_keywords, major_keyword, *report_info)
'''

def main():
    report_info = filter_papers(link, report_path, topic)
    write_html(all_keywords, major_keyword, *report_info)

    # QQ Mail SMTP configuration
    smtp_server = "smtp.qq.com"
    smtp_port   = 587
    sender_email = "atel_gcn@qq.com"
    sender_password = "fplkgcplcikecjec"   # QQ Mail authorization code
    receiver_emails = ["yin.dj@qq.com", "yfeng.dai@foxmail.com", "1938079121@qq.com", "2896663909@qq.com"]
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
