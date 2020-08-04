# ![](https://0000.us/klatchat/app/files/neon_images/icons/neon_paw.png)Support Helper
  
# Summary  
  
Provides an option to send current logs via email.
  
# Requirements  
This skill requires a remote server be configured to receive uploads and send emails, by default this is configured for
`64.34.186.92`.
  
# Description  
  
The skill provides the functionality to truncate and upload Neon logs that are then sent to the user email configured in
`ngi_user_info.yml`.  
  
# How to Use  
  
First, make your request:  
  
Say `“Hey Neon”` if you are in the wake words mode. Make sure to follow the pattern of `"AV play artist or song name"` or `"play some artist or song name"` and add `"music"` or any combination of the following commands to your request: `“playlist, repeat, video”`.  
For example:  
  
- "create a troubleshooting package"
    
If you do not have an email address configured, Neon will respond:  
`I don't know your email address. You can tell me by saying 'Neon, my email address is...'`

  
# Location  
  

     ${skills}/support-helper.neon

# Files
<details>
<summary>Click to expand.</summary>
<br>

    ${skills}/support-helper.neon
    ${skills}/support-helper.neon/.gitignore
    ${skills}/support-helper.neon/__pycache__
    ${skills}/support-helper.neon/__pycache__/__init__.cpython-36.pyc
    ${skills}/support-helper.neon/vocab
    ${skills}/support-helper.neon/vocab/en-us
    ${skills}/support-helper.neon/vocab/en-us/contact.support.intent
    ${skills}/support-helper.neon/vocab/de-de
    ${skills}/support-helper.neon/vocab/de-de/contact.support.intent
    ${skills}/support-helper.neon/README.md
    ${skills}/support-helper.neon/README.old
    ${skills}/support-helper.neon/__init__.py
    ${skills}/support-helper.neon/test
    ${skills}/support-helper.neon/test/intent
    ${skills}/support-helper.neon/test/intent/sample2.intent.json
    ${skills}/support-helper.neon/test/intent/sample1.intent.json
    ${skills}/support-helper.neon/dialog
    ${skills}/support-helper.neon/dialog/en-us
    ${skills}/support-helper.neon/dialog/en-us/support.dialog
    ${skills}/support-helper.neon/dialog/en-us/complete.dialog
    ${skills}/support-helper.neon/dialog/en-us/support.email.template
    ${skills}/support-helper.neon/dialog/en-us/one.moment.dialog
    ${skills}/support-helper.neon/dialog/en-us/support.title.dialog
    ${skills}/support-helper.neon/dialog/en-us/no.email.dialog
    ${skills}/support-helper.neon/dialog/en-us/confirm.support.dialog
    ${skills}/support-helper.neon/dialog/en-us/cancelled.dialog
    ${skills}/support-helper.neon/dialog/en-us/yes.list
    ${skills}/support-helper.neon/dialog/en-us/ask.description.dialog
    ${skills}/support-helper.neon/dialog/de-de
    ${skills}/support-helper.neon/dialog/de-de/support.dialog
    ${skills}/support-helper.neon/dialog/de-de/complete.dialog
    ${skills}/support-helper.neon/dialog/de-de/support.email.template
    ${skills}/support-helper.neon/dialog/de-de/one.moment.dialog
    ${skills}/support-helper.neon/dialog/de-de/support.title.dialog
    ${skills}/support-helper.neon/dialog/de-de/confirm.support.dialog
    ${skills}/support-helper.neon/dialog/de-de/cancelled.dialog
    ${skills}/support-helper.neon/dialog/de-de/yes.list
    ${skills}/support-helper.neon/dialog/de-de/ask.description.dialog
    ${skills}/support-helper.neon/settings.json
    ${skills}/support-helper.neon/LICENSE

</details>
  

# Class Diagram
[Click Here](https://0000.us/klatchat/app/files/neon_images/class_diagrams/support-helper.png)
  

# Available Intents
<details>
<summary>Show list</summary>
<br>


### contact.support.intent

    create a troubleshoot request
    create a troubleshooting ticket
    troubleshoot my device
    contact support
    create a support ticket

</details>


# Examples

### Text

	    Create a support ticket    
	    >> One moment.
	    >> I've sent an email to your registered account with debugging information and instructions for contacting support.    

### Picture

### Video

  
# Troubleshooting
If you do not see your troubleshooting email, check your spam folder.

# Contact Support
Use the [link](https://neongecko.com/ContactUs) or [submit an issue on GitHub](https://help.github.com/en/articles/creating-an-issue)

# Credits
reginaneon [neongeckocom](https://neongecko.com/) Mycroft AI djmcknight358


