# BountyDog

Let's assume that:
Either:
1. You have `your.gmail.robot@gmail.com` account and its App Password is configured.
2. The robot's account's 16 chars password is `AVerySecretPassA`.
3. Your personal account is `your.personal.account@gmail.com`.
Or:
1. you have a channel on Discord with the following URL -> `https://discord.com/api/webhooks/My-Webhook`
Or:
you have all of them together (you can use `-S`, `-R` and `-d` altogether)

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



### Sample email/message
when only HackerOne and Bugcrowd scope have been changed
```
######################### REMOVED TARGETS FROM bugcrowd #########################
  
1shoppingcart.com
*.1shoppingcart.com

######################### ADDED TARGETS TO bugcrowd #########################

1shoppingcart.com
*.1shoppingcart.com

######################### REMOVED TARGETS FROM hackerone #########################

go.hacker.one
b5s.hackerone-ext-content.com
com.yahoo.mobile.client.android.mail
http://*.email.vimeo.com
com.basecamp.hey
help.bitso.com
dev.bitso.com

######################### ADDED TARGETS TO hackerone #########################

go.hacker.one
b5s.hackerone-ext-content.com
com.yahoo.mobile.client.android.mail
com.basecamp.hey
help.bitso.com
dev.bitso.com
http://bitso.com/alpha
av.urbandictionary.biz
com.urbandictionary.iphone

######################### THE END #########################
```
