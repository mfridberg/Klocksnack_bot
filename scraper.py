import time
import datetime
import requests
import schedule
import smtplib, ssl
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loginInfo import get_email, get_password, get_receiver_email

port = 465  # For SSL

context = ssl.create_default_context()

#Thinking what is best for performance. Using this or call functions every run
# email = get_email()
# password = get_password()
# receiver_email = get_receiver_email()

#Who does not love global variables?
watches_searching_for = ["yema", "halios", "aquaracer", "c60", "seiko"]
previously_found_watches = []

class link_data:
    def __init__(self, title, link, is_sent):
        self.title = title
        self.link = link
        self.is_sent = is_sent

#Scrape klocksnack to find result we are searching for
def init_scrape():
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
    #We are writing C code in python. 

    for t in link_data_arr:
        for lf in watches_searching_for:
            if lf in t.title.lower():
                result.append(t)

    #RETURN RESULT
    return result
    
def send_mail():

    a_tags_message = ""

    for i in range(len(previously_found_watches)):
        if previously_found_watches[i].is_sent is False:
            a_tags_message += "<br><a href=" + '"' + str(previously_found_watches[i].link) + '">' + str(previously_found_watches[i].title) + "</a><br>" 

    #Generate message
    if a_tags_message != "":
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Watch found"
        msg['From'] = get_email()
        msg['To'] = get_receiver_email()

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
                    """ + a_tags_message + """
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
            server.login(get_email(), get_password())

            #SEND EMAIL         
            server.sendmail(get_email(), get_receiver_email(), msg.as_string())
            print("Email sent")

    #SET THE SENT WATCHES TO TRUE
    for i in range(len(previously_found_watches)):
        previously_found_watches[i].is_sent = True

    return


def main_program():
    
    scrape_result = init_scrape()

    for pfw in previously_found_watches:
        for sr in scrape_result:
            if sr.title == pfw.title:
                sr.is_sent = True

    for i in range(len(scrape_result)):
            if scrape_result[i].is_sent is False:
                previously_found_watches.append(scrape_result[i])
                

    if previously_found_watches:
        for i in range(len(previously_found_watches)):
            print(str(previously_found_watches[i].title) + " : " + str(previously_found_watches[i].is_sent))

    print("Latest search was made: " + str(datetime.datetime.now()) + "\n")

    if previously_found_watches:
        send_mail()
        print("Return to main for now, waiting \n")
    else:
        print("Nothing was found, returning to main, waiting! \n")

    return
  

if __name__ == "__main__":
    #lf = input("Type name of watch you are looking for!: ")

    main_program()

    #Schedule won't let me pass any data to function...
    schedule.every(10).minutes.do(main_program)

    while True:
        schedule.run_pending()
        time.sleep(1)   

    exit(0)    



