import requests
import schedule
import time
import datetime
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from loginInfo import get_email, get_password

port = 465  # For SSL

context = ssl.create_default_context()
email = get_email()
password = get_password()
receiver_email = "mats.fridberg@gmail.com"

previously_found_watches = []

class link_data:
    def __init__(self, title, link, exists):
        self.title = title
        self.link = link
        self.exists = exists

#Scrape klocksnack to find result we are searching for
def init_scrape(lf):
    url = "https://klocksnack.se/forums/handla-säljes-bytes.11/" 
    response = requests.get(url)

    if response.status_code != 200:
        print("Could not connect to klocksnack.se")
        exit(0)

    soup = BeautifulSoup(response.text, "html.parser")

    soup = soup.find('ol', {"class": "discussionListItems"})

    #SORT OUT 'a' TAGS WITHIN THE 'li' tag
    titles = []
    links = []
    for li in soup.findAll('li'):
        for a in li.findAll('a',{"class": "PreviewTooltip"},  href=True):
            links.append(a['href'])
            titles.append(a)


    #PUT TITLES IN AN ARRAY
    only_text = []
    for c in titles:
        only_text.append(c.text)

    #PUT CORRESPONDING LINKS IN AN ARRAY
    only_links = []
    for l in links:
        only_links.append(l)
 
    
    #CREATE AN ARRAY OF OUR title/link OBJECT
    link_data_arr = []
    for l in range(len(only_text)):
        link_data_arr.append(link_data(only_text[l], str( "klocksnack.se/" + only_links[l]), False))
    

    result = []
    #CHECK IF THE STRING WE ARE LOOKING FOR IS IN THE TITLE
    for t in link_data_arr:
        if lf in t.title:
            result.append(t)

    #RETURN RESULT
    return result
    
def send_mail():

    a_tags_message = ""

    for i in range(len(previously_found_watches)):
        if previously_found_watches[i].exists is False:
            a_tags_message += "<br><a href=" + '"' + str(previously_found_watches[i].link) + '">' + str(previously_found_watches[i].title) + "</a><br>" 

    #Generate message
    if a_tags_message != "":
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Watch found"
        msg['From'] = email
        msg['To'] = receiver_email

        # Create the body of the message (a plain-text and an HTML version).
        text = ""
        html = """\
        <head>
            <style type="text/css" media="screen">
            
            a{
                font-weight: bold;
                color: RoyalBlue;
                text-decoration: underline;
            }

            </style>

        </head>
        <html>
            <head></head>
            <body>
                <p>Tjenixen!<br>
                    <br>
                    Klockan du letat efter finns nu till försäljning!<br>
                    """+ a_tags_message + """
                </p>
            </body>
        </html>
        """
        # Record the MIME types of both parts - text/plain and text/html.
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')

        msg.attach(part1)
        msg.attach(part2)

        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(email, password)

            #SEND EMAIL         
            server.sendmail(email, receiver_email, msg.as_string())
            print("Email sent")

    #SET THE SENT WATCHES TO TRUE
    for i in range(len(previously_found_watches)):
        previously_found_watches[i].exists = True

    return


def main_program(user_input):
    
    scrape_result = init_scrape(user_input)

    for pfw in previously_found_watches:
        for sr in scrape_result:
            if sr.title == pfw.title:
                sr.exists = True

    for i in range(len(scrape_result)):
            if scrape_result[i].exists is False:
                previously_found_watches.append(scrape_result[i])
                

    if previously_found_watches:
        for i in range(len(previously_found_watches)):
            print(str(previously_found_watches[i].title) + " : " + str(previously_found_watches[i].exists))

    print("Latest search was made: " + str(datetime.datetime.now()) + "\n")

    if previously_found_watches:
        #Here we want to generate email if new result is found
        send_mail()
        print("Return to main for now, waiting \n")
    else:
        print("Nothing was found, returning to main, waiting! \n")

    return

def main():

    lf = input("Type name of watch you are looking for!: ")

    main_program(lf)

    def job():
        main_program(lf)

    schedule.every(10).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)   

    exit(0)

if __name__ == "__main__":
    main()



