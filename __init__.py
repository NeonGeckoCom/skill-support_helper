# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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

        # Emit message for core to send this email
        title = "Diagnostic Info"
        body = f"\nFind attached your requested diagnostics files. You can forward this message to info@neongecko.com "\
               f"with a description of your issue for further support.\n\n-Neon\nDiagnostics sent from "\
               f"{str(self.local_config['devVars']['devName'])} on {str(datetime.datetime.now())}"
        self.send_email(title, body, message, email_addr=preference_user["email"], attachments=attachments)

    def stop(self):
        pass


def create_skill():
    return SupportSkill()
