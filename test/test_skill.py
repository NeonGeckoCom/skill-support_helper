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

import unittest
import os

from os import mkdir
from os.path import dirname, join, exists
from mock import Mock
from ovos_utils.messagebus import FakeBus
from mycroft_bus_client import Message
from neon_utils.user_utils import get_default_user_config
from mycroft.skills.skill_loader import SkillLoader


class TestSkill(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        bus = FakeBus()
        bus.run_in_thread()
        skill_loader = SkillLoader(bus, dirname(dirname(__file__)))
        skill_loader.load()
        cls.skill = skill_loader.instance

        # Define a directory to use for testing
        cls.test_fs = join(dirname(__file__), "skill_fs")
        if not exists(cls.test_fs):
            mkdir(cls.test_fs)
        os.environ["NEON_CONFIG_PATH"] = cls.test_fs

        # Override the configuration and fs paths to use the test directory
        cls.skill.settings_write_path = cls.test_fs
        cls.skill.file_system.path = cls.test_fs
        cls.skill._init_settings()
        cls.skill.initialize()

        # Override speak and speak_dialog to test passed arguments
        cls.skill.speak = Mock()
        cls.skill.speak_dialog = Mock()

    def test_00_skill_init(self):
        # Test any parameters expected to be set in init or initialize methods
        from neon_utils.skills.neon_skill import NeonSkill

        self.assertIsInstance(self.skill, NeonSkill)
        self.assertIsInstance(self.skill.support_email, str)

    def test_handle_contact_support(self):
        real_get_support_info = self.skill._get_support_info
        self.skill._get_support_info = Mock(return_value={"test": True})

        self.skill.ask_yesno = Mock(return_value="no")

        user_config = get_default_user_config()
        user_config["user"]["username"] = "test_user"
        user_config["user"]["email"] = ''
        test_message = Message("test", {"utterance": "This is a test"},
                               {"klat_data": True, "username": "test_user",
                                "user_profiles": [user_config]})
        # Contact Support No Email
        self.skill.handle_contact_support(test_message)
        self.skill.speak_dialog.assert_called_with("no_email", private=True)
        # Contact Support Declined
        test_message.context["user_profiles"][0]["user"]["email"] = \
            "test@neon.ai"
        self.skill.handle_contact_support(test_message)
        self.skill.ask_yesno.assert_called_with("confirm_support",
                                                {"email": "test@neon.ai"})
        self.skill.speak_dialog.assert_called_with("cancelled", private=True)
        # Contact Support Approved No Details
        self.skill.ask_yesno = Mock(return_value="yes")
        self.skill.send_email = Mock()
        self.skill.handle_contact_support(test_message)
        self.assertEqual(self.skill._get_support_info.call_args[0][0],
                         test_message)
        self.skill.send_email.assert_called_with("Neon AI Diagnostics",
                                                 self.skill._format_email_body(
                                                     {"test": True,
                                                      "user_description": None}
                                                 ),
                                                 test_message, "test@neon.ai")
        self.skill.speak_dialog.assert_called_with("complete",
                                                   {"email": "test@neon.ai"},
                                                   private=True)
        # Contact Support Approved With Details
        self.skill.get_response = Mock(return_value="This is only a test")
        self.skill.handle_contact_support(test_message)
        self.assertEqual(self.skill._get_support_info.call_args[0][0],
                         test_message)
        self.skill.get_response.assert_called_once_with("ask_description",
                                                        num_retries=0)
        self.skill.send_email.assert_called_with(
            "Neon AI Diagnostics", self.skill._format_email_body(
                {"test": True,
                 "user_description": "This is only a test"}),
            test_message, "test@neon.ai")
        self.skill.speak_dialog.assert_called_with("complete",
                                                   {"email": "test@neon.ai"},
                                                   private=True)

        self.skill._get_support_info = real_get_support_info

    def test_format_email_body(self):
        import json

        test_diagnostics = {"user_profile": "testing",
                            "module_status": {"module": None}}
        body = self.skill._format_email_body(test_diagnostics)
        parts = body.split('\n\n')
        self.assertEqual(len(parts), 3)
        self.assertIn(self.skill.support_email, parts[0])
        self.assertEqual(json.loads(parts[1]), test_diagnostics)
        self.assertEqual(parts[2], "- Neon AI")

    def test_get_support_info(self):
        from datetime import datetime
        from neon_utils.net_utils import get_ip_address

        user_config = get_default_user_config()
        user_config["user"]["username"] = "test_user"
        test_message = Message("test", {"utterance": "This is a test"},
                               {"klat_data": True, "username": "test_user",
                                "user_profiles": [user_config]})
        # No modules respond
        diagnostics = self.skill._get_support_info(test_message)
        diag_time = diagnostics["generated_time_utc"]
        self.assertIsInstance(datetime.fromisoformat(diag_time), datetime)
        self.assertEqual(diagnostics, {"user_profile": user_config,
                                       "message_context": test_message.context,
                                       "module_status": {"speech": None,
                                                         "audio": None,
                                                         "skills": None},
                                       "loaded_skills": None,
                                       "host_device": {"ip": get_ip_address()},
                                       "generated_time_utc": diag_time
                                       })


if __name__ == '__main__':
    unittest.main()
