import subprocess
import argparse
import os
import sys
import smtplib
import ssl
from email.message import EmailMessage
import requests
import json


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

"""
This section parses the arguments
"""

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

"""
Global variables are defined here
"""

repo_url = "https://github.com/Osb0rn3/bugbounty-targets"
repo_name = repo_url.rsplit("/", 1)[1]
branch = "main"


def sendit(msg: str, sender: str, receiver: str) -> None:
    
    """
    This function sends the recent changes to a gmail account (specified by the user)
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

    return None


def logit(log: str) -> None:
    
    """
    Write to a log file
    """
    
    with open("/tmp/log.txt", "a") as f:
        f.write(log)

    return None


def discordit(msg: str, webhook: str) -> None:
    
    """
    This section sends a message to a channel which is specified by the user
    """
    
    # Discord does not allow sending a message containing more than 2000 chars
    if len(msg) > 2000:
        num_of_chunks = len(msg) // 1900 + 1
        lst = msg.split("\n")
        sized_msg = ""
        for i in range(num_of_chunks):
            while len(sized_msg) <= 1900 and len(lst) > 0:
                sized_msg = sized_msg + lst.pop(0) + "\n"
            if len(lst) != 0:
                sized_msg = (
                    sized_msg
                    + "```\n#########################\nTo Be Continued .......\n#########################\n"
                )
            data = {"content": sized_msg}
            requests.post(webhook, json=data)
            sized_msg = "```"
    #If it's shorter than 2000 chars -> just send it
    else:
        data = {"content": msg}
        requests.post(webhook, json=data)

    return None


def downloadit(prg_file) -> None:
    
    """
    This function downloads the associated program file from the repository which is being monitored
    """
    
    dl = "wget https://raw.githubusercontent.com/Osb0rn3/bugbounty-targets/main/programs/{:s} -O /tmp/{:s}".format(
        prg_file, prg_file
    )

    subprocess.run(
        dl,
        capture_output=True,
        text=True,
        shell=True,
        check=True,
    )

    return None


def hackerone_scope_extractor(hackerone_file_path: str):
    
    """
    This function extracts Hackerone's scopes info fields from the json file which is downloaded from the repository
    Then it returns a list of out-of-scope and in-scope programs info
    """
    
    with open(hackerone_file_path, "r") as f:
        hackerone_in_scope = set()
        hackerone_out_of_scope = set()
        hackerone_prg_list = json.loads(f.read())
        for prg_json in hackerone_prg_list:
            for key, value in prg_json.items():
                if key == "relationships":
                    targets_list = value["structured_scopes"]["data"]
                    for target_json in targets_list:
                        if (
                            " " not in target_json["attributes"]["asset_identifier"]
                            and "." in target_json["attributes"]["asset_identifier"]
                        ):
                            scope = target_json["attributes"]["asset_identifier"]

                        if (
                            scope
                            and target_json["attributes"]["eligible_for_submission"]
                        ):
                            hackerone_in_scope.add(scope)
                        elif (
                            scope
                            and not target_json["attributes"]["eligible_for_submission"]
                        ):
                            hackerone_out_of_scope.add(scope)

    return [hackerone_in_scope, hackerone_out_of_scope]


def hackerone(hackerone_file: str) -> list:
    
    """
    This function compares Hackerone's changes and returns a list of changes in both in-scope
    and out-of-scope programs
    """
    
    downloadit(hackerone_file)

    old_in_scope, old_out_of_scope = hackerone_scope_extractor(
        "programs/hackerone.json"
    )
    new_in_scope, new_out_of_scope = hackerone_scope_extractor("/tmp/hackerone.json")

    newly_added_in_scope = new_in_scope.difference(old_in_scope)
    newly_removed_in_scope = old_in_scope.difference(new_in_scope)

    newly_added_out_of_scope = new_out_of_scope.difference(old_out_of_scope)
    newly_removed_out_of_scope = old_out_of_scope.difference(new_out_of_scope)

    return [
        newly_added_in_scope,
        newly_removed_in_scope,
        newly_added_out_of_scope,
        newly_removed_out_of_scope,
    ]


def bugcrowd_scope_extractor(bugcrowd_file_path: str):
    
    """
    This function extracts Bugcrowd's scopes info fields from the json file which is downloaded from the repository
    Then it returns a list of out-of-scope and in-scope programs info
    """

    with open(bugcrowd_file_path, "r") as f:
        bugcrowd_in_scope = set()
        bugcrowd_out_of_scope = set()
        bugcrowd_prg_list = json.loads(f.read())
        for prg_json in bugcrowd_prg_list:
            for key, value in prg_json.items():
                if key == "target_groups":
                    # lst_of_target_jsons = value
                    for targets_json in value:
                        for targets_key, targets_value in targets_json.items():
                            if targets_key == "targets":
                                for each_target_json in targets_value:
                                    if (
                                        " " not in each_target_json["name"]
                                        and "." in each_target_json["name"]
                                    ):
                                        scope = each_target_json["name"]
                                    elif each_target_json["uri"]:
                                        scope = each_target_json["uri"]
                                    if targets_json["in_scope"] and scope:
                                        bugcrowd_in_scope.add(scope)
                                    elif not targets_json["in_scope"] and scope:
                                        bugcrowd_out_of_scope.add(scope)

        return [bugcrowd_in_scope, bugcrowd_out_of_scope]


def bugcrowd(bugcrowd_file: str) -> set:
    
    """
    This function compares Bugcrowd's changes and returns a list of changes in both in-scope
    and out-of-scope programs
    """
    
    downloadit(bugcrowd_file)

    old_in_scope, old_out_of_scope = bugcrowd_scope_extractor("programs/bugcrowd.json")
    new_in_scope, new_out_of_scope = bugcrowd_scope_extractor("/tmp/bugcrowd.json")

    newly_added_in_scope = new_in_scope.difference(old_in_scope)
    newly_removed_in_scope = old_in_scope.difference(new_in_scope)

    newly_added_out_of_scope = new_out_of_scope.difference(old_out_of_scope)
    newly_removed_out_of_scope = old_out_of_scope.difference(new_out_of_scope)

    return [
        newly_added_in_scope,
        newly_removed_in_scope,
        newly_added_out_of_scope,
        newly_removed_out_of_scope,
    ]


def intigriti_scope_extractor(intigriti_file_path: str):
    
    """
    This function extracts Intigriti's scopes info fields from the json file which is downloaded from the repository
    Then it returns a list of out-of-scope and in-scope programs info
    """
    
    with open(intigriti_file_path, "r") as f:
        intigriti_in_scope = set()
        intigriti_out_of_scope = set()
        intigriti_prg_list = json.loads(f.read())
        for prg_json in intigriti_prg_list:
            for key, value in prg_json.items():
                if key == "domains":
                    for target_json in value:
                        intigriti_in_scope.add(target_json["endpoint"])
    return [intigriti_in_scope, intigriti_out_of_scope]


def intigriti(intigriti_file: str) -> list:
    
    """
    This function compares Intigriti's changes and returns a list of changes in both in-scope
    and out-of-scope programs
    """

    downloadit(intigriti_file)

    old_in_scope, old_out_of_scope = intigriti_scope_extractor(
        "programs/intigriti.json"
    )
    new_in_scope, new_out_of_scope = intigriti_scope_extractor("/tmp/intigriti.json")

    newly_added_in_scope = new_in_scope.difference(old_in_scope)
    newly_removed_in_scope = old_in_scope.difference(new_in_scope)

    newly_added_out_of_scope = new_out_of_scope.difference(old_out_of_scope)
    newly_removed_out_of_scope = old_out_of_scope.difference(new_out_of_scope)

    return [
        newly_added_in_scope,
        newly_removed_in_scope,
        newly_added_out_of_scope,
        newly_removed_out_of_scope,
    ]


def yeswehack_scope_extractor(yeswehack_file_path: str):
    
    """
    This function extracts Yeswehack's scopes info fields from the json file which is downloaded from the repository
    Then it returns a list of out-of-scope and in-scope programs info
    """

    with open(yeswehack_file_path, "r") as f:
        yeswehack_in_scope = set()
        yeswehack_out_of_scope = set()
        yeswehack_prg_list = json.loads(f.read())
        for prg_json in yeswehack_prg_list:
            for key, value in prg_json.items():
                if key == "scopes":
                    for target_json in value:
                        yeswehack_in_scope.add(target_json["scope"])
    return [yeswehack_in_scope, yeswehack_out_of_scope]


def yeswehack(yeswehack_file: str) -> list:

    """
    This function compares Yeswehack's changes and returns a list of changes in both in-scope
    and out-of-scope programs
    """

    downloadit(yeswehack_file)

    old_in_scope, old_out_of_scope = yeswehack_scope_extractor(
        "programs/yeswehack.json"
    )
    new_in_scope, new_out_of_scope = yeswehack_scope_extractor("/tmp/yeswehack.json")

    newly_added_in_scope = new_in_scope.difference(old_in_scope)
    newly_removed_in_scope = old_in_scope.difference(new_in_scope)

    newly_added_out_of_scope = new_out_of_scope.difference(old_out_of_scope)
    newly_removed_out_of_scope = old_out_of_scope.difference(new_out_of_scope)

    return [
        newly_added_in_scope,
        newly_removed_in_scope,
        newly_added_out_of_scope,
        newly_removed_out_of_scope,
    ]


def bountydog() -> None:
    
    """
    This function does as follows:
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
            "ls programs",
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
            discordit(
                "Apparently new program is added to bugbounty-targets repository!"
            )
        # Create a msg for Discord or email etc.
        #    if len(latest_changes_list[0]) > 0 or len(latest_changes_list[1]) > 0:
        res = ""
        (
            newly_added_in_scope,
            newly_removed_in_scope,
            newly_added_out_of_scope,
            newly_removed_out_of_scope,
        ) = latest_changes_list

        if len(newly_added_in_scope) > 0:
            res = "#########################\nADDED in-scope TARGETS TO {:s}\n#########################\n```\n{:s}\n```\n".format(
                prg_name.capitalize(), "\n".join(newly_added_in_scope)
            )
        if len(newly_removed_in_scope) > 0:
            res = (
                res
                + "#########################\nREMOVED in-scope TARGETS FROM {:s}\n#########################\n```\n{:s}\n```\n".format(
                    prg_name.capitalize(), "\n".join(newly_removed_in_scope)
                )
            )
        if len(newly_added_out_of_scope) > 0:
            res = (
                res
                + "#########################\nADDEED out-of-scope TARGETS TO {:s}\n#########################\n```\n{:s}\n```\n".format(
                    prg_name.capitalize(), "\n".join(newly_added_out_of_scope)
                )
            )
        if len(newly_removed_out_of_scope) > 0:
            res = (
                res
                + "#########################\nREMOVED out-of-scope TARGETS FROM {:s}\n#########################\n```\n{:s}\n```\n".format(
                    prg_name.capitalize(), "\n".join(newly_removed_out_of_scope)
                )
            )

        final_res = final_res + res

    # Final message which pointing out the end of the msg by adding a trailing part
    final_res = final_res + trailing
    
    # Send the message if not empty
    if final_res != trailing:
        if args.webhook:
            discordit(final_res, args.webhook)
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

    # Merge the changes to update our local repo
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
        
        #Informing the user that no changes will be notified at this run
        print(
            "{:s}No changes will be shown now, You can extract changes from the next commit to the repo{:s}".format(
                col.grey, col.end
            )
        )
    
    # If the repo exists -> call bountydog function
    # Also poorly handles other errors
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

    return


if __name__ == "__main__":
    main()
