# BountyDog

This tool monitors [this repository](https://github.com/Osb0rn3/bugbounty-targets) to find the latest scopes on HackerOne, Bugcrowd, Intigrity, Yeswehack bugbounty platforms. The deployment is explained via an example in the following.

Let's assume that:

Either:
1. You have `your.gmail.robot@gmail.com` account and its App Password is configured.
2. The robot's account's 16 chars password is `AVerySecretPassA`.
3. Your personal account is `your.personal.account@gmail.com`.

Or:
1. You have a channel on Discord with the following URL -> `https://discord.com/api/webhooks/My-Webhook`

Or:

You have all of them together (you can use `-S`, `-R` and `-d` altogether)

## Usage

### Command to receive email
```
EMAIL_PASSWORD=AVerySecretPassA python3 bountydog.py -R mypersonalgmail@gmail.com -S your.gmail.robot@gmail.com
```
### Command to receive Discord message
```
python3 bountydog.py -d https://discord.com/api/webhooks/My-Webhook
```

### Crontab to run the command every 3 hours
```
0 */3 * * * cd /PATH/TO/bountydog/; EMAIL_PASSWORD=AVerySecretPassA /usr/bin/python3 ./bountydog.py -R your.personal.account@gmail.com -S your.gmail.robot@gmail.com
```
