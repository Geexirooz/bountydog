import subprocess
import argparse
import os
import sys
import smtplib
import ssl
from email.message import EmailMessage
import re


class col:
    if sys.stdout.isatty():
        green = "\033[32m"
        blue = "\033[94m"
        red = "\033[31m"
        brown = "\033[33m"
        grey = "\033[90m"
        end = "\033[0m"
    else:  # Colours mess up redirected output, disable them
        green = ""
        blue = ""
        red = ""
        brown = ""
        grey = ""
        end = ""


# Parse arguments
parser = argparse.ArgumentParser(
    "gitcheck.py",
    formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=40),
)
parser.add_argument("-r", "--repo", help="Repo to scan", dest="repo", required=True)

parser.add_argument(
    "-b", "--branch", help="Branch to scan", dest="branch", required=True
)

parser.add_argument(
    "-S",
    "--sender",
    help="gmail account to send the email FROM",
    dest="email_sender",
    required=True,
)

parser.add_argument(
    "-R",
    "--receiver",
    help="gmail account to send the email TO",
    dest="email_receiver",
    required=True,
)
# parser.add_argument('-c', '--count', help='Number of commits to scan (default all)', dest='count', default=sys.maxsize, type=int)
# parser.add_argument('-v', '--verbose', help='Verbose output', dest='verbose', action='store_true', default=False)
args = parser.parse_args()

# args.repo needs to be sanitized
repo_name = args.repo.rsplit("/", 1)[1]
repo_url = args.repo
branch = args.branch


# send the recent changes to an gmail:
def sendeit(msg):
    # Define the email's components and shape it
    sender = args.email_sender
    receiver = args.email_receiver
    email_password = os.environ.get("EMAIL_PASSWORD")
    subject = "Recent changes on the repo"

    em = EmailMessage()
    em["From"] = sender
    em["To"] = receiver
    em["Subject"] = subject
    em.set_content(msg)

    # Add SSL (layer of security)
    context = ssl.create_default_context()

    # Log in and send the email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
        smtp.login(sender, email_password)
        smtp.sendmail(sender, receiver, em.as_string())


def logit(log):
    with open("/tmp/log.txt", "a") as f:
        f.write(log)


def bugcrowd(bugcrowd_file):
    # run git diff
    latest_changes = subprocess.run(
        "git diff origin/main -- programs/{:s}".format(bugcrowd_file),
        capture_output=True,
        text=True,
        shell=True,
        check=True,
    ).stdout

    # parse the diff reponse
    removed_targets_regex = (
        r"-\s*\"targets\":\s\[\n-[^{]*{\n-[^,]*,\n-\s*\"name\":\s\"([^\"]*)\","
    )
    new_targets_regex = (
        r"\+\s*\"targets\":\s\[\n\+[^{]*{\n\+[^,]*,\n\+\s*\"name\":\s\"([^\"]*)\","
    )

    # find excluded matches
    matched_removed_targets = re.findall(removed_targets_regex, latest_changes)

    rm_targets = []
    for matched_target in matched_removed_targets:
        if " " not in matched_target and "." in matched_target:
            rm_targets.append(matched_target.strip())

    # find included matches
    matched_addeded_targets = re.findall(new_targets_regex, latest_changes)

    new_targets = []
    for matched_target in matched_addeded_targets:
        if " " not in matched_target and "." in matched_target:
            new_targets.append(matched_target.strip())

    # return them as a list
    latest_changes = [rm_targets, new_targets]

    return latest_changes


def hackerone(hackerone_file):
    latest_changes = subprocess.run(
        "git diff origin/main -- programs/{:s}".format(hackerone_file),
        capture_output=True,
        text=True,
        shell=True,
        check=True,
    ).stdout

    removed_targets_regex = r"-\s*\"attributes\":\s{\n-\s*\"asset_type\":\s[^-]*-\s*\"asset_identifier\":\s\"([^\"]*)\""
    new_targets_regex = r"\+\s*\"attributes\":\s{\n\+\s*\"asset_type\":\s[^-]*\+\s*\"asset_identifier\":\s\"([^\"]*)\""

    matched_removed_targets = re.findall(removed_targets_regex, latest_changes)

    rm_targets = []
    for matched_target in matched_removed_targets:
        if " " not in matched_target and "." in matched_target:
            rm_targets.append(matched_target.strip())

    # find included matches
    matched_addeded_targets = re.findall(new_targets_regex, latest_changes)

    new_targets = []
    for matched_target in matched_addeded_targets:
        if " " not in matched_target and "." in matched_target:
            new_targets.append(matched_target.strip())

    # return them as a list
    latest_changes = [rm_targets, new_targets]

    return latest_changes


def changes_extractor(program):
    if program == "bugcrowd.json":
        latest_changes = bugcrowd(program)
        if latest_changes:
            return latest_changes
    elif program == "hackerone.json":
        latest_changes = hackerone(program)
        if latest_changes:
            return latest_changes


def gitscanner():
    os.chdir(repo_name)

    subprocess.run("git fetch", capture_output=True, text=True, shell=True, check=True)

    prg_files = (
        subprocess.run(
            "ls programs".format(branch, branch),
            capture_output=True,
            text=True,
            shell=True,
            check=True,
        )
        .stdout.strip()
        .split("\n")
    )
    final_res = ""
    for prg_file in prg_files:
        prg_name = prg_file.split(".")[0]
        latest_changes = changes_extractor(prg_file)
        if latest_changes:
            # sendeit(latest_changes)
            res = ""
            removed_targets, added_targets = latest_changes
            res = "Removed Targtes from {:s}:\n{:s}\n#########################\n#########################\nAdded Targets:\n{:s}\n".format(
                prg_name,
                "\n".join(removed_targets),
                "\n".join(added_targets),
            )
            final_res = final_res + res + "\n" * 5
    logit(final_res)

    # subprocess.run(
    #    "git merge", capture_output=True, text=True, shell=True, check=True
    # )
    return


try:
    print(
        "{:s}Trying to clone '{:s}' from '{:s}'{:s}".format(
            col.blue, repo_name, repo_url, col.end
        )
    )
    subprocess.run(
        "git clone -v {:s}".format(repo_url),
        capture_output=True,
        text=True,
        shell=True,
        check=True,
    )
    print("{:s}successfully cloned!{:s}".format(col.green, col.end))
    gitscanner()
except subprocess.CalledProcessError as e:
    if e.returncode == 128:
        if os.path.isdir(repo_name):
            print(
                "{:s}'{:s}' directory exists!{:s}".format(col.green, repo_name, col.end)
            )
            gitscanner()
        else:
            print(
                "{:s}'{:s}' repository does not exist!{:s}".format(
                    col.red, repo_name, col.end
                )
            )
    else:
        print(e.stderr)
