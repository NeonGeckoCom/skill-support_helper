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

import json

from copy import deepcopy
from datetime import datetime
from glob import glob
from os.path import join, basename

from mycroft_bus_client import Message
from neon_utils.user_utils import get_user_prefs
from neon_utils.skills.neon_skill import NeonSkill
from neon_utils.net_utils import get_ip_address
from neon_utils.file_utils import encode_file_to_base64_string
from ovos_utils import classproperty
from ovos_utils.log import LOG
from ovos_utils.process_utils import RuntimeRequirements

from mycroft.skills import intent_file_handler


class SupportSkill(NeonSkill):
    def __init__(self):
        super(SupportSkill, self).__init__(name="SupportHelper")

    @classproperty
    def runtime_requirements(self):
        return RuntimeRequirements(network_before_load=False,
                                   internet_before_load=False,
                                   gui_before_load=False,
                                   requires_internet=True,
                                   requires_network=True,
                                   requires_gui=False,
                                   no_internet_fallback=False,
                                   no_network_fallback=False,
                                   no_gui_fallback=True)

    @property
    def support_email(self) -> str:
        """
        Email to refer users to for support
        """
        return self.settings.get("support_email") or "support@neon.ai"

    @intent_file_handler('contact_support.intent')
    def handle_contact_support(self, message: Message):
        """
        Handle a user request to contact support
        :param message: Message associated with request
        """
        user_profile = get_user_prefs(message)
        if not user_profile["user"]["email"]:
            # TODO: Ask to send to support@neon.ai?
            self.speak_dialog("no_email", private=True)
            return
        if self.ask_yesno("confirm_support",
                          {"email": user_profile["user"]["email"]}) == "yes":
            if user_profile["response_mode"].get("hesitation"):
                self.speak_dialog("one_moment", private=True)
            diagnostic_info = self._get_support_info(message, user_profile)
            user_description = self.get_response("ask_description",
                                                 num_retries=0)
            diagnostic_info["user_description"] = user_description
            attachment_files = self._parse_attachments(self._get_log_files())
            if self.send_email(self.translate("email_title"),
                               self._format_email_body(diagnostic_info),
                               message, user_profile["user"]["email"],
                               attachments=attachment_files):
                self.speak_dialog("complete",
                                  {"email": user_profile["user"]["email"]},
                                  private=True)
                return
            LOG.error("Email failed to send, retry without attachments")
            if self.send_email(self.translate("email_title"),
                               self._format_email_body(diagnostic_info),
                               message, user_profile["user"]["email"]):
                self.speak_dialog("complete",
                                  {"email": user_profile["user"]["email"]},
                                  private=True)
            else:
                LOG.error(f"Email Failed to send!")
                self.speak_dialog("email_error", private=True)
        else:
            self.speak_dialog("cancelled", private=True)

    @staticmethod
    def _parse_attachments(files: list) -> dict:
        """
        Parse a list of files into a dict of filenames to B64 contents
        """
        attachments = {}
        for file in files:
            try:
                attachments[basename(file)] = encode_file_to_base64_string(file)
            except Exception as e:
                LOG.exception(e)
        return attachments

    def _format_email_body(self, diagnostics: dict) -> str:
        """
        Format the diagnostic data with email dialog and return a string body
        :param diagnostics: diagnostic data to format into the email
        :returns: email body to send
        """
        json_str = json.dumps(diagnostics, indent=4)
        return '\n\n'.join((self.translate("email_intro",
                                           {"email": self.support_email}),
                            json_str,
                            self.translate("email_signature")))

    def _check_service_status(self, message: Message = None) -> dict:
        """
        Query services on the messagebus and report back their status
        """
        message = message or Message("get_status")

        speech_module = self.bus.wait_for_response(
            message.forward("mycroft.speech.is_ready"))
        speech_status = speech_module.data.get("status") if speech_module \
            else None

        audio_module = self.bus.wait_for_response(
            message.forward("mycroft.audio.is_ready"))
        audio_status = audio_module.data.get("status") if audio_module \
            else None

        skills_module = self.bus.wait_for_response(
            message.forward("mycroft.skills.is_ready"))
        skills_status = skills_module.data.get("status") if skills_module \
            else None

        gui_module = self.bus.wait_for_response(
            message.forward("mycroft.gui_service.is_ready"))
        gui_status = gui_module.data.get("status") if gui_module \
            else None

        enclosure_module = self.bus.wait_for_response(
            message.forward("mycroft.PHAL.is_ready")
        )
        enclosure_status = enclosure_module.data.get("status") if enclosure_module \
            else None

        admin_module = self.bus.wait_for_response(
            message.forward("mycroft.PHAL.admin.is_ready")
        )
        admin_status = admin_module.data.get("status") if admin_module \
            else None

        return {"speech": speech_status,
                "audio": audio_status,
                "skills": skills_status,
                "gui": gui_status,
                "enclosure": enclosure_status,
                "admin": admin_status}

    def _get_log_files(self):
        log_path = LOG.base_path
        log_files = glob(join(log_path, "*.log"))
        LOG.info(f"Found log files: {log_files}")
        return log_files

    def _get_support_info(self, message: Message,
                          profile: dict = None) -> dict:
        """
        Collect relevant information to include in a support ticket
        :param message: Message associated with support request
        """
        user_profile = profile or get_user_prefs(message)
        message_context = deepcopy(message.context)

        loaded_skills = self.bus.wait_for_response(
            message.forward("skillmanager.list"), "mycroft.skills.list"
        )
        loaded_skills = loaded_skills.data if loaded_skills else None

        core_device_ip = get_ip_address()

        return {
            "user_profile": user_profile,
            "message_context": message_context,
            "module_status": self._check_service_status(message),
            "loaded_skills": loaded_skills,
            "host_device": {"ip": core_device_ip},
            "generated_time_utc": datetime.utcnow().isoformat()
        }

    def stop(self):
        pass


def create_skill():
    return SupportSkill()
