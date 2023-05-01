import subprocess
import argparse
import os
import sys
import smtplib
import ssl
from email.message import EmailMessage
import re
import requests


class col:
    """
    A class to define colors for a nice output printing
    """

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
    "bountydog.py",
    formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=40),
)

parser.add_argument(
    "-S",
    "--sender",
    help="gmail account to send the email FROM",
    dest="email_sender",
)

parser.add_argument(
    "-R",
    "--receiver",
    help="gmail account to send the email TO",
    dest="email_receiver",
)

parser.add_argument(
    "-d",
    "--discord",
    help="Discord's channel Webhook",
    dest="webhook",
    default=sys.maxsize,
    type=str,
)

args = parser.parse_args()

# Global variables
repo_url = "https://github.com/Osb0rn3/bugbounty-targets"
repo_name = repo_url.rsplit("/", 1)[1]
branch = "main"


def sendit(msg, sender, receiver):
    """
    Send the recent changes to a gmail account
    """
    # Define the email's components and build it
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
    """
    Write to a log file
    """
    with open("/tmp/log.txt", "a") as f:
        f.write(log)


def discordit(msg: str, webhook: str):
    # Discord does not allow sending a message containing more than 2000 chars
    if len(msg) > 2000:
        num_of_chunks = len(msg) // 1900 + 1
        lst = msg.split("\n")
        for i in range(num_of_chunks):
            sized_msg = ""
            while len(sized_msg) <= 1900 and len(lst) > 0:
                sized_msg = sized_msg + lst.pop(0) + "\n"
            if len(lst) != 0:
                sized_msg = (
                    sized_msg + "#########################\nTo Be Continued .......\n"
                )
            data = {"content": sized_msg}
            requests.post(webhook, json=data)
    else:
        data = {"content": msg}
        requests.post(webhook, json=data)

    return


def run_diff(prg_file):
    """
    Run git diff command on prg_file
    """
    latest_changes = subprocess.run(
        "git diff origin/main -- programs/{:s}".format(prg_file),
        capture_output=True,
        text=True,
        shell=True,
        check=True,
    ).stdout
    return latest_changes


def regextractor(latest_changes, removed_targets_regex, new_targets_regex):
    """
    Extract changed targets using regex
    """
    # Find excluded targets
    matched_removed_targets = re.findall(removed_targets_regex, latest_changes)
    rm_targets = []
    for matched_target in matched_removed_targets:
        if " " not in matched_target and "." in matched_target:
            rm_targets.append(matched_target.strip())

    # Find included matches
    matched_addeded_targets = re.findall(new_targets_regex, latest_changes)
    new_targets = []
    for matched_target in matched_addeded_targets:
        if " " not in matched_target and "." in matched_target:
            new_targets.append(matched_target.strip())

    # Return them as a list
    latest_changes_list = [rm_targets, new_targets]
    return latest_changes_list


def hackerone(hackerone_file):
    """
    Extract hackerone changes
    """
    latest_changes = run_diff(hackerone_file)

    removed_targets_regex = r"-\s*\"attributes\":\s{\n-\s*\"asset_type\":\s[^-]*-\s*\"asset_identifier\":\s\"([^\"]*)\""
    new_targets_regex = r"\+\s*\"attributes\":\s{\n\+\s*\"asset_type\":\s[^-]*\+\s*\"asset_identifier\":\s\"([^\"]*)\""

    latest_changes_list = regextractor(
        latest_changes, removed_targets_regex, new_targets_regex
    )

    return latest_changes_list


def bugcrowd(bugcrowd_file):
    """
    Extract bugcrowd changes
    """
    latest_changes = run_diff(bugcrowd_file)

    removed_targets_regex = (
        r"-\s*\"targets\":\s\[\n-[^{]*{\n-[^,]*,\n-\s*\"name\":\s\"([^\"]*)\","
    )
    new_targets_regex = (
        r"\+\s*\"targets\":\s\[\n\+[^{]*{\n\+[^,]*,\n\+\s*\"name\":\s\"([^\"]*)\","
    )
    latest_changes_list = regextractor(
        latest_changes, removed_targets_regex, new_targets_regex
    )

    return latest_changes_list


def intigriti(intigriti_file):
    """
    Extract intigriti changes
    """
    latest_changes = run_diff(intigriti_file)

    removed_targets_regex = (
        r"-\s*\"id\"[^\+]*-\s*\"type\"[^-]*-\s*\"endpoint\":\s\"([^\"]*)\""
    )
    new_targets_regex = (
        r"\+\s*\"id\"[^\+]*\+\s*\"type\"[^\+]*\+\s*\"endpoint\":\s\"([^\"]*)\""
    )

    latest_changes_list = regextractor(
        latest_changes, removed_targets_regex, new_targets_regex
    )

    return latest_changes_list


def yeswehack(yeswehack_file):
    """
    Extract yeswehack changes
    """
    latest_changes = run_diff(yeswehack_file)
    removed_targets_regex = r"-\s*\"scope\":\s\"([^\"]*)\"[^-]*-\s*\"scope_type\""
    new_targets_regex = r"\+\s*\"scope\":\s\"([^\"]*)\"[^\+]*\+\s*\"scope_type\""
    latest_changes_list = regextractor(
        latest_changes, removed_targets_regex, new_targets_regex
    )
    return latest_changes_list


def bountydog():
    """
    1.Fetch the remote repository
    2.Create a msg including the changes
    3.Pass the changes to sendit and logit functions to report them
    4.Merge the changes to the local repo
    """
    # Fetch the remote repo
    os.chdir(repo_name)
    subprocess.run("git fetch", capture_output=True, text=True, shell=True, check=True)

    # Get a list of programs
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
    trailing = "#########################\nTHE END\n#########################\n\n"

    # Find the changes to each program
    for prg_file in prg_files:
        prg_name = prg_file.split(".")[0]
        # Python older than 3.10
        if prg_file == "bugcrowd.json":
            latest_changes_list = bugcrowd(prg_file)
        elif prg_file == "hackerone.json":
            latest_changes_list = hackerone(prg_file)
        elif prg_file == "intigriti.json":
            latest_changes_list = intigriti(prg_file)
        elif prg_file == "yeswehack.json":
            latest_changes_list = yeswehack(prg_file)
        else:
            sendit("Apparently new program is added to bugbounty-targets repository!")

        # Create a msg
        if len(latest_changes_list[0]) > 0 or len(latest_changes_list[1]) > 0:
            res = ""
            removed_targets, added_targets = latest_changes_list
            res = "#########################\nREMOVED TARGETS FROM {:s}\n#########################\n\n{:s}\n\n#########################\nADDED TARGETS TO {:s}\n#########################\n\n{:s}\n\n".format(
                prg_name,
                "\n".join(removed_targets),
                prg_name,
                "\n".join(added_targets),
            )
            final_res = final_res + res
    # Final message
    final_res = final_res + trailing
    if final_res != trailing:
        logit(final_res)
        if args.email_sender and args.email_receiver:
            try:
                sendit(final_res, args.email_sender, args.email_receiver)
            except Exception:
                print(
                    "You have either not set {:s}EMAIL_PASSWORD environment{:s} variable OR hit your {:s}daily quota{:s}!".format(
                        col.red, col.end, col.red, col.end
                    )
                )
        if args.webhook:
            discordit(final_res, args.webhook)

    # Merge the changes
    subprocess.run("git merge", capture_output=True, text=True, shell=True, check=True)
    return


def main():
    """
    First tries to clone the repo if it is not present.
    If present, it calls bountydog funtion to take it from there
    """
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
        print("{:s}Successfully cloned!{:s}".format(col.green, col.end))
        print(
            "{:s}No changes will be shown now, You can extract changes from the next commit to the repo{:s}".format(
                col.grey, col.end
            )
        )
    except subprocess.CalledProcessError as e:
        if e.returncode == 128:
            if os.path.isdir(repo_name):
                print(
                    "{:s}'{:s}' Directory exists!{:s}".format(
                        col.green, repo_name, col.end
                    )
                )
                bountydog()
            else:
                print(
                    "{:s}'{:s}' Repository does not exist!{:s}".format(
                        col.red, repo_name, col.end
                    )
                )
        else:
            print(e.stderr)


if __name__ == "__main__":
    main()
