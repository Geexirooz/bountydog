import subprocess
import argparse
import os
import sys
import smtplib
import ssl
from email.message import EmailMessage


class col:
    if sys.stdout.isatty():
        green = '\033[32m'
        blue = '\033[94m'
        red = '\033[31m'
        brown = '\033[33m'
        grey = '\033[90m'
        end = '\033[0m'
    else:   # Colours mess up redirected output, disable them
        green = ""
        blue = ""
        red = ""
        brown = ""
        grey = ""
        end = ""


# Parse arguments
parser = argparse.ArgumentParser(
    'gitcheck.py', formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=40))
parser.add_argument('-r', '--repo', help='Repo to scan',
                    dest='repo', required=True)

parser.add_argument('-b', '--branch', help='Branch to scan',
                    dest='branch', required=True)
# parser.add_argument('-c', '--count', help='Number of commits to scan (default all)', dest='count', default=sys.maxsize, type=int)
# parser.add_argument('-v', '--verbose', help='Verbose output', dest='verbose', action='store_true', default=False)
args = parser.parse_args()

# args.repo needs to be sanitized
repo_name = args.repo.rsplit("/", 1)[1]
repo_url = args.repo
branch = args.branch


# send the recent changes to an gmail:
def sendeit(msg):
    # Define email sender and receiver and subject
    email_sender = 'sender@gmail.com'
    email_password = os.environ.get("EMAIL_PASSWORD")
    email_receiver = 'receiver@gmail.com'
    subject = 'Recent changes on the repo'
    # Shape an email
    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver
    em['Subject'] = subject
    em.set_content(msg)

    # Add SSL (layer of security)
    context = ssl.create_default_context()

    # Log in and send the email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, em.as_string())


def logit(log):
    with open("/tmp/log.txt", "w") as f:
        f.write(log)


def gitscanner():
    subprocess.run("git fetch", capture_output=True,
                   text=True, shell=True, check=True)
    latest_changes = subprocess.run("git diff {:s} origin/{:s}".format(branch, branch),
                                    capture_output=True, text=True, shell=True, check=True).stdout
    if latest_changes:
        sendeit(latest_changes)
        logit(latest_changes)
        subprocess.run("git merge", capture_output=True,
                       text=True, shell=True, check=True)
    return


try:
    print("{:s}Trying to clone '{:s}' from '{:s}'{:s}".format(
        col.blue, repo_name, repo_url, col.end))
    subprocess.run("git clone -v {:s}".format(repo_url), capture_output=True,
                   text=True, shell=True, check=True)
    os.chdir(repo_name)
    gitscanner()
except subprocess.CalledProcessError as e:
    if e.returncode == 128:
        if os.path.isdir(repo_name):
            print("{:s}'{:s}' directory exists!{:s}".format(
                col.green, repo_name, col.end))
            os.chdir(repo_name)
            gitscanner()
        else:
            print("{:s}'{:s}' repository does not exist!{:s}".format(
                col.red, repo_name, col.end))
    else:
        print(e.stderr)
