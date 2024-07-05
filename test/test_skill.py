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

from os.path import dirname, join, isfile, getsize
from mock import Mock
from ovos_bus_client import Message
from neon_utils.user_utils import get_default_user_config
from neon_minerva.tests.skill_unit_test_base import SkillTestCase


os.environ["TEST_SKILL_ENTRYPOINT"] = "skill-support_helper.neongeckocom"


class TestSkill(SkillTestCase):
    def test_00_skill_init(self):
        # Test any parameters expected to be set in init or initialize methods
        from neon_utils.skills.neon_skill import NeonSkill

        self.assertIsInstance(self.skill, NeonSkill)
        self.assertIsInstance(self.skill.support_email, str)

    def test_handle_contact_support(self):
        real_get_support_info = self.skill._get_support_info
        real_parse_attachments = self.skill._parse_attachments
        test_attachments = {'attachment': ''}
        self.skill._get_support_info = Mock(return_value={"test": True})
        self.skill._parse_attachments = Mock(return_value=test_attachments)

        self.skill.ask_yesno = Mock(return_value="no")

        user_config = get_default_user_config()
        user_config["user"]["username"] = "test_user"
        user_config["user"]["email"] = ''
        test_message = Message("test", {"utterance": "This is a test"},
                               {"klat_data": True, "username": "test_user",
                                "user_profiles": [user_config]})
        # Contact Support No Email Declined
        self.skill.handle_contact_support(test_message)
        self.skill.speak_dialog.assert_any_call("no_email", private=True)

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
        self.skill.send_email.return_value = True
        self.skill.handle_contact_support(test_message)
        self.assertEqual(self.skill._get_support_info.call_args[0][0],
                         test_message)
        self.skill.send_email.assert_called_with("Neon AI Diagnostics",
                                                 self.skill._format_email_body(
                                                     {"test": True,
                                                      "user_description": None}
                                                 ),
                                                 test_message, "test@neon.ai",
                                                 attachments=test_attachments)
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
            test_message, "test@neon.ai", attachments=test_attachments)
        self.skill.speak_dialog.assert_called_with("complete",
                                                   {"email": "test@neon.ai"},
                                                   private=True)

        # Email failed
        self.skill.send_email.return_value = False
        self.skill.handle_contact_support(test_message)
        self.assertEqual(self.skill._get_support_info.call_args[0][0],
                         test_message)
        self.skill.get_response.assert_called_with("ask_description",
                                                   num_retries=0)
        self.skill.send_email.assert_called_with(
            "Neon AI Diagnostics", self.skill._format_email_body(
                {"test": True,
                 "user_description": "This is only a test"}),
            test_message, "test@neon.ai")
        self.skill.speak_dialog.assert_called_with("email_error",
                                                   private=True)

        self.skill._get_support_info = real_get_support_info
        self.skill._parse_attachments = real_parse_attachments

    def test_format_email_body(self):
        test_diagnostics = {"user_profile": "testing",
                            "module_status": {"module": None}}
        # No description
        body = self.skill._format_email_body(test_diagnostics)
        parts = body.split('\n\n')
        self.assertEqual(len(parts), 3)
        self.assertIn(self.skill.support_email, parts[0])
        self.assertEqual(parts[1], "No Description Provided")
        self.assertEqual(parts[2], "- Neon AI")

        # User description provided
        test_diagnostics['user_description'] = "testing diagnostics"
        body = self.skill._format_email_body(test_diagnostics)
        parts = body.split('\n\n')
        self.assertEqual(len(parts), 3)
        self.assertIn(self.skill.support_email, parts[0])
        self.assertEqual(parts[1], test_diagnostics['user_description'])
        self.assertEqual(parts[2], "- Neon AI")

    def test_get_log_files(self):
        from ovos_utils.log import LOG
        test_dir = join(dirname(__file__), "logs")
        real_path = LOG.base_path
        LOG.base_path = test_dir
        logs = self.skill._get_log_files()
        LOG.base_path = real_path
        self.assertEqual(set(logs), {join(test_dir, "audio.log"),
                                     join(test_dir, "skills.log")})
        for log in logs:
            self.assertTrue(isfile(log))
            self.assertEqual(dirname(log), test_dir)

        os.remove(join(test_dir, "neon-utils.log"))

    def test_parse_attachments(self):
        from neon_utils.file_utils import decode_base64_string_to_file
        test_dir = join(dirname(__file__), "logs")
        log_files = [join(test_dir, "audio.log"), join(test_dir, "skills.log")]
        parsed = self.skill._parse_attachments(log_files)
        self.assertEqual(set(parsed.keys()),
                         {'audio_log.txt', 'skills_log.txt'})
        for file, log in parsed.items():
            self.assertIsInstance(log, str)
            test_log_file = join(test_dir, f"test_{file}")
            decode_base64_string_to_file(log, test_log_file)
            with open(test_log_file, 'r') as f:
                test_output = f.read()
            with open(join(test_dir, file.replace('_log.txt',
                                                  '.log')), 'r') as f:
                self.assertEqual(f.read(), test_output)
            os.remove(test_log_file)

        # Test truncated log
        from uuid import uuid4
        test_file = join(test_dir, "truncate.log")
        i = 0
        with open(test_file, 'w+') as f:
            i += 1
            line = str(uuid4()) * 4
            for i in range(100000):
                f.write(f'{i} - {line}\n')
        input_size = int(getsize(test_file))
        self.assertTrue(input_size > 1000000)
        parsed = self.skill._parse_attachments([test_file])
        file = list(parsed.keys())[0]
        log = list(parsed.values())[0]
        self.assertEqual(file, "truncate_log.txt")
        self.assertIsInstance(log, str)
        test_outfile = join(test_dir, "test_truncate.log")
        decode_base64_string_to_file(log, test_outfile)
        with open(test_file, 'r') as f:
            original = f.readlines()
        with open(test_outfile, 'r') as f:
            truncated = f.readlines()
        self.assertTrue(set(truncated) <= set(original))  # truncated is subset
        self.assertIsInstance(int(truncated[0].split()[0]), int)
        self.assertEqual(truncated[0].split()[1], '-')
        self.assertEqual(truncated[-1], original[-1])
        self.assertLess(getsize(test_outfile), 1000000)
        os.remove(test_outfile)
        os.remove(test_file)

    def test_check_service_status(self):
        # TODO
        pass

    def test_get_support_info(self):
        from datetime import datetime
        from neon_utils.net_utils import get_ip_address

        user_config = get_default_user_config()
        user_config["user"]["username"] = "test_user"
        test_context = {"klat_data": True, "username": "test_user",
                        "user_profiles": [user_config]}
        test_message = Message("test", {"utterance": "This is a test"},
                               dict(test_context))
        # No modules respond
        diagnostics = self.skill._get_support_info(test_message)
        diag_time = diagnostics["generated_time_utc"]
        self.assertIsInstance(datetime.fromisoformat(diag_time), datetime)
        pip_info = diagnostics["packages"]
        context = diagnostics["message_context"]
        for key in test_context:
            self.assertEqual(test_context[key], context[key])
        self.assertIsInstance(pip_info, str)
        self.assertEqual(diagnostics, {"user_profile": user_config,
                                       "message_context": context,
                                       "module_status": {"speech": None,
                                                         "audio": None,
                                                         "voice": None,
                                                         "skills": None,
                                                         "gui": None,
                                                         "enclosure": None,
                                                         "admin": None},
                                       "loaded_skills": None,
                                       "host_device": {"ip": get_ip_address()},
                                       "generated_time_utc": diag_time,
                                       "packages": pip_info
                                       })

    def test_get_attachments(self):
        real_status = self.skill._check_service_status
        self.skill._check_service_status = Mock(return_value={'test': True})

        original_context = {"content": "something", "context": True}
        test_message = Message("test", {}, dict(original_context))
        test_profile = {"user": {"username": "test_user"},
                        "data": {"key": "val"}}

        content = self.skill._get_support_info(test_message, test_profile)
        for key in {'user_profile', 'message_context', 'module_status',
                    'loaded_skills', 'packages', 'host_device',
                    'generated_time_utc'}:
            self.assertIn(key, content, key)
        self.assertEqual(content['user_profile'], test_profile)
        self.assertEqual(content['message_context'], original_context)
        self.assertEqual(content['module_status'], {'test': True})
        self.assertIsInstance(content['packages'], str)
        self.assertIsInstance(content['host_device']['ip'], str)
        self.assertIsInstance(content['generated_time_utc'], str)

        self.skill._check_service_status = real_status


if __name__ == '__main__':
    unittest.main()
