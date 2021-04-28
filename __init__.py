# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
#
# Copyright 2008-2021 Neongecko.com Inc. | All Rights Reserved
#
# Notice of License - Duplicating this Notice of License near the start of any file containing
# a derivative of this software is a condition of license for this software.
# Friendly Licensing:
# No charge, open source royalty free use of the Neon AI software source and object is offered for
# educational users, noncommercial enthusiasts, Public Benefit Corporations (and LLCs) and
# Social Purpose Corporations (and LLCs). Developers can contact developers@neon.ai
# For commercial licensing, distribution of derivative works or redistribution please contact licenses@neon.ai
# Distributed on an "AS IS” basis without warranties or conditions of any kind, either express or implied.
# Trademarks of Neongecko: Neon AI(TM), Neon Assist (TM), Neon Communicator(TM), Klat(TM)
# Authors: Guy Daniels, Daniel McKnight, Regina Bloomstine, Elon Gasper, Richard Leeds
#
# Specialized conversational reconveyance options from Conversation Processing Intelligence Corp.
# US Patents 2008-2021: US7424516, US20140161250, US20140177813, US8638908, US8068604, US8553852, US10530923, US10530924
# China Patent: CN102017585  -  Europe Patent: EU2156652  -  Patents Pending
import base64
import glob
import os
import datetime

from neon_utils.message_utils import request_from_mobile

from mycroft import intent_file_handler

from neon_utils.skills.neon_skill import NeonSkill, LOG


class SupportSkill(NeonSkill):

    def __init__(self):
        super(SupportSkill, self).__init__(name="SupportHelper")

    @intent_file_handler('contact.support.intent')
    def troubleshoot(self, message):
        # flac_filename = message.context["flac_filename"]
        # Get a problem description from the user

        # if (not user_words or not any(
        #         i.strip() in user_words for i in yes_words
        # )):
        #     self.speak_dialog('cancelled')
        #     return
        self.user_config.check_for_updates()
        self.local_config.check_for_updates()
        if request_from_mobile(message):
            self.mobile_skill_intent("stop", {}, message)
            # self.socket_io_emit("support", "", flac_filename=flac_filename)
            self.speak_dialog('mobile.complete', private=True)
        elif self.server:
            LOG.warning(">>>SUPPORT INTENT<<<")
            LOG.warning(self.get_utterance_user(message))
            # self.speak_dialog('mobile.complete', private=True)
            # TODO: Report problem conversation? DM
        else:
            if self.preference_user(message)['email']:
                # try:
                # TODO: Get Description from speech and write to email body
                # description = self.get_response('ask.description', num_retries=0)
                # if description is None:
                #     self.speak_dialog('cancelled')
                #     return
                if self.check_for_signal('CORE_useHesitation', -1):
                    self.speak_dialog('one_moment', private=True)
                try:
                    self.send_diagnostic_email(message)
                    self.speak_dialog('complete', private=True)
                except Exception as e:
                    LOG.error(e)
                    self.speak_dialog("email.error", private=True)
                # except Exception as e:
                #     LOG.error(e)
            else:
                self.speak_dialog('no.email')

    def send_diagnostic_email(self, message):
        preference_user = self.preference_user(message)
        # email_path = self.configuration_available["dirVars"]["tempDir"] + '/Diagnostic Info_' + \
        #     preference_user['email'] + '_' + str(datetime.date.today()) + '.txt'

        # Define Paths for files that are to be uploaded with diagnostics
        paths = [
            self.local_config.path + '/*.yml',
            self.local_config["dirVars"]["logsDir"] + '/*.log'
            ]

        attachments = {}
        # Create Directory for Attachments
        # if not os.path.exists(self.configuration_available["dirVars"]["tempDir"] + '/attachments/'):
        #     os.mkdir(self.configuration_available["dirVars"]["tempDir"] + '/attachments/')

        # Append email to each file and copy to Attachments Directory
        for path in paths:
            for file in glob.glob(path):
                try:
                    LOG.debug(file)
                    basename = os.path.basename(os.path.splitext(file)[0])
                    file_ext = os.path.splitext(file)[1]
                    # If file is larger than 20MB, Truncate it
                    if os.path.getsize(file) > 20000000:
                        with open(file) as f:
                            log_lines = f.read().split('\n')
                            log_lines = '\n'.join(log_lines[-5000:])
                        attachments[f"{basename}.{file_ext}"] = base64.b64encode(log_lines.encode("utf-16"))\
                            .decode("utf-8")
                    else:
                        with open(file) as f:
                            attachments[f"{basename}.{file_ext}"] = base64.b64encode(f.read().encode("utf-16"))\
                                .decode("utf-8")
                except Exception as e:
                    LOG.error(e)
                    LOG.error(file)

        # Draft email here and move to ${config_dirVars_tempDir}/title_email_$(date +%Y-%m-%d).txt
        # with open(email_path, 'a') as body:
        #     body.write("\nFind attached your requested diagnostics files. You can forward this message"
        #                " to info@neongecko.com with a description of your issue for further support.\n\n"
        #                "-Neon")
        #     body.write("\nDiagnostics sent from " +
        #                str(self.configuration_available["devVars"]["devName"]) + ' on ' +
        #                str(datetime.datetime.now()))
        #
        # subprocess.Popen(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
        #                  + "/functions.sh; sendEmail"])

        # Emit message for core to send this email
        title = "Diagnostic Info"
        body = f"\nFind attached your requested diagnostics files. You can forward this message to info@neongecko.com "\
               f"with a description of your issue for further support.\n\n-Neon\nDiagnostics sent from "\
               f"{str(self.configuration_available['devVars']['devName'])} on {str(datetime.datetime.now())}"
        self.send_email(title, body, message, email_addr=preference_user["email"], attachments=attachments)
        # self.bus.emit(Message("neon.email", {"title": title, "email": preference_user['email'], "body": body}))

    def stop(self):
        pass


def create_skill():
    return SupportSkill()

    #
    # log_locations = [
    #     self.configuration_available['dirVars']['rootDir'] + '/*.json',
    #     self.configuration_available['dirVars']['logsDir'] + '/*.log',
    #     self.configuration_available['dirVars']['ngiDir'] + '/*.yml',
    #     '/etc/mycroft/*.conf',
    #     join(dirname(dirname(mycroft.__file__)), 'scripts', 'logs', '*.log')
    # ]

    # Service used to temporarilly hold the debugging data (linked to
    # via email)
    # host = 'termbin.com'
    #

    # if check_for_signal('skip_wake_word', -1):
    #     self.disable_intent("contact.support.intent"),

    # def draft_message(self, log_str):
    #     # Send the various log and info files
    #     # Upload to termbin.com using the nc (netcat) util
    #     fd, path = mkstemp()
    #     with open(path, 'w') as f:
    #         f.write(log_str)
    #     os.close(fd)
    #     cmd = 'cat ' + path + ' | nc ' + self.host + ' 9999'
    #     return check_output(cmd, shell=True).decode().strip('\n\x00')
    #
    # def get_device_name(self):
    #     try:
    #         return DeviceApi().get()['name']
    #     except:
    #         self.log.exception('API Error')
    #         return ':error:'
    #
    # def upload_debug_info(self):
    #     all_lines = []
    #     threads = []
    #     for log_file in sum([glob(pattern) for pattern in self.log_locations], []):
    #         copyfile(log_file, self.upload_dir)
    #         def do_thing(log_file=log_file):
    #             with open(log_file) as f:
    #                 log_lines = f.read().split('\n')
    #             lines = ['=== ' + log_file + ' ===']
    #             # if len(log_lines) > 1000:
    #             #     log_lines = '\n'.join(log_lines[-5000:])
    #             #     print('Uploading ' + log_file + '...')
    #             #     lines.append(self.upload_and_create_url(log_lines))
    #             # else:
    #             lines.extend(log_lines)
    #             lines.append('')
    #             all_lines.extend(lines)
    #
    #         t = Thread(target=do_thing)
    #         t.daemon = True
    #         t.start()
    #         threads.append(t)
    #     for t in threads:
    #         t.join()
    #     return self.draft_message('\n'.join(all_lines))

    # "Create a support ticket"

    # Log so that the message will appear in the package of logs sent
    # self.log.debug("Troubleshooting Package Description: " +
    #                str(description))

    # # Upload the logs to the web
    # url = self.upload_debug_info()

    # Create the troubleshooting email and send to user
    # data = {'url': url, 'device_name': self.get_device_name(),
    #         'description': description}
    # email = '\n'.join(self.translate_template('support.email', data))
    # title = self.translate('support.title')
    # self.send_email(title, email)
