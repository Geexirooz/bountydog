import subprocess
import argparse
import os
import sys
import smtplib
import ssl
from email.message import EmailMessage
import re


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


def sendit(msg):
    """
    send the recent changes to a gmail account
    """
    # Define the email's components and build it
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
    """
    write to a log file
    """
    with open("./log.txt", "a") as f:
        f.write(log)


def run_diff(prg_file):
    """
    run git diff command on prg_file
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
    # find excluded targets 
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
    latest_changes_list = [rm_targets, new_targets]
    return latest_changes_list


def bugcrowd(bugcrowd_file):
    """
    extract bugcrowd changes
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


def hackerone(hackerone_file):
    """
    extract hackerone changes
    """
    latest_changes = run_diff(hackerone_file)

    removed_targets_regex = r"-\s*\"attributes\":\s{\n-\s*\"asset_type\":\s[^-]*-\s*\"asset_identifier\":\s\"([^\"]*)\""
    new_targets_regex = r"\+\s*\"attributes\":\s{\n\+\s*\"asset_type\":\s[^-]*\+\s*\"asset_identifier\":\s\"([^\"]*)\""

    latest_changes_list = regextractor(
        latest_changes, removed_targets_regex, new_targets_regex
    )

    return latest_changes_list


def intigriti(intigriti_file):
    """
    extract intigriti changes
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
    extract yeswehack changes
    """
    latest_changes = run_diff(yeswehack_file)
    removed_targets_regex = r"-\s*\"scope\":\s\"([^\"]*)\"[^-]*-\s*\"scope_type\""
    new_targets_regex = r"\+\s*\"scope\":\s\"([^\"]*)\"[^\+]*\+\s*\"scope_type\""
    latest_changes_list = regextractor(
        latest_changes, removed_targets_regex, new_targets_regex
    )
    return latest_changes_list


def changes_extractor(program):
    if program == "bugcrowd.json":
        latest_changes_list = bugcrowd(program)
        if latest_changes_list:
            return latest_changes_list
    elif program == "hackerone.json":
        latest_changes_list = hackerone(program)
        if latest_changes_list:
            return latest_changes_list
    elif program == "intigriti.json":
        latest_changes_list = intigriti(program)
        if latest_changes_list:
            return latest_changes_list
    elif program == "yeswehack.json":
        latest_changes_list = yeswehack(program)
        if latest_changes_list:
            return latest_changes_list


def bountydog():
    """
    1.fetch the remote repository
    2.create a msg including the changes 
    3.pass the changes to sendit and logit functions to report them
    4.merge the changes to the local repo
    """
    #fetch the remote repo
    os.chdir(repo_name)
    subprocess.run("git fetch", capture_output=True, text=True, shell=True, check=True)

    #get a list of programs
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
    trailing = "######################### THE END #########################\n\n"
    
    #find the changes to each program
    for prg_file in prg_files:
        prg_name = prg_file.split(".")[0]
        latest_changes_list = changes_extractor(prg_file)
        
        #create a msg
        if len(latest_changes_list[0]) > 0 or len(latest_changes_list[1]) > 0:
            res = ""
            removed_targets, added_targets = latest_changes_list
            res = "######################### REMOVED TARGETS FROM {:s} #########################\n\n{:s}\n\n######################### ADDED TARGETS TO {:s} #########################\n\n{:s}\n\n".format(
                prg_name,
                "\n".join(removed_targets),
                prg_name,
                "\n".join(added_targets),
            )
            final_res = final_res + res
    #final message
    final_res = final_res + trailing
    if final_res != trailing:
        logit(final_res)
        sendit(final_res)

    #merge the changes
    subprocess.run("git merge", capture_output=True, text=True, shell=True, check=True)
    return


def main():
    """
    First tries to clone the repo if it is not present.
    if present, it calls bountydog funtion to take it from there
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
        print("{:s}successfully cloned!{:s}".format(col.green, col.end))
        print(
            "{:s}No changes will be shown now, You can extract changes from the next commit to the repo{:s}".format(
                col.grey, col.end
            )
        )
    except subprocess.CalledProcessError as e:
        if e.returncode == 128:
            if os.path.isdir(repo_name):
                print(
                    "{:s}'{:s}' directory exists!{:s}".format(
                        col.green, repo_name, col.end
                    )
                )
                bountydog()
            else:
                print(
                    "{:s}'{:s}' repository does not exist!{:s}".format(
                        col.red, repo_name, col.end
                    )
                )
        else:
            print(e.stderr)


if __name__ == "__main__":
    main()
