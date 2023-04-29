# bountydog

Let's assume that:
1. You have `foo.robot@gmail.com` account and its App Password is configured.
2. The robot's account's 16 chars password is `AVerySecretPassA`.
3. Your personal account is `mypersonalgmail@gmail.com`.

# Usage

### Command
```
EMAIL_PASSWORD=AVerySecretPassA python3 bountydog.py -r https://github.com/Osb0rn3/bugbounty-targets -b main -R mypersonalgmail@gmail.com -S foo.robot@gmail.com
```
### Crontab to run the command every 3 hours
```
0 */3 * * * cd /PATH/TO/bountydog/; EMAIL_PASSWORD=AVerySecretPassA /usr/bin/python3 ./bountydog.py -r https://github.com/Osb0rn3/bugbounty-targets -b main -R mypersonalgmail@gmail.com -S foo.robot@gmail.com
```
