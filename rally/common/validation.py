# Copyright 2017: Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import abc
import traceback

import six

from rally.common import logging
from rally.common.plugin import plugin
from rally import exceptions

configure = plugin.configure


LOG = logging.getLogger(__name__)


@plugin.base()
@six.add_metaclass(abc.ABCMeta)
class Validator(plugin.Plugin):

    def __init__(self):
        pass

    @abc.abstractmethod
    def validate(self, credentials, config, plugin_cls, plugin_cfg):
        """Method that validates something.

        :param credentials: credentials dict for all platforms
        :param config: dict, configuration of workload
        :param plugin_cls: plugin class
        :param plugin_cfg: dict, with exact configuration of the plugin
        :returns: ValidationResult instances
        """

    def fail(self, msg):
        return ValidationResult(False, msg=msg)

    @classmethod
    def _get_doc(cls):
        doc = ""
        if cls.__doc__ is not None:
            doc = cls.__doc__
        if cls.__init__.__doc__ is not None:
            if not cls.__init__.__doc__.startswith("\n"):
                doc += "\n"
            doc += cls.__init__.__doc__
        return doc


@configure(name="required_platform")
class RequiredPlatformValidator(Validator):

    def __init__(self, platform, admin=False, users=False):
        """Validates credentials for specified platform.

        This allows us to create 4 kind of benchmarks:
        1) platform independent (validator is not specified)
        2) requires platform with admin
        3) requires platform with admin + users
        4) requires platform with users

        :param platform: name of the platform
        :param admin: requires admin credential
        :param users: requires user credentials
        """
        super(RequiredPlatformValidator, self).__init__()
        self.platform = platform
        self.admin = admin
        self.users = users

    def validate(self, credentials, config, plugin_cls, plugin_cfg):
        if not (self.admin or self.users):
            return self.fail(
                "You should specify admin=True or users=True or both.")

        if credentials is None:
            credentials = {}
        credentials = credentials.get(self.platform, {})

        if self.admin and credentials.get("admin") is None:
            return self.fail("No admin credential for %s" % self.platform)
        if self.users and len(credentials.get("users", ())) == 0:
            if credentials.get("admin") is None:
                return self.fail("No user credentials for %s" % self.platform)
            else:
                # NOTE(andreykurilin): It is a case whem the plugin requires
                #   'users' for launching, but there are no specified users in
                #   deployment. Let's assume that 'users' context can create
                #   them via admin user and do not fail."
                pass


def add(name, **kwargs):
    """Add validator to the plugin class meta.

    Add validator name and arguments to validators list stored in the
    plugin meta by 'validators' key. This would be used to iterate
    and execute through all validators during execution of subtask.

    :param name: str, name of the validator plugin
    :param kwargs: dict, arguments used to initialize validator class
        instance
    """

    def wrapper(plugin):
        if issubclass(plugin, RequiredPlatformValidator):
            raise exceptions.RallyException(
                "Cannot add a validator to RequiredPlatformValidator")
        elif issubclass(plugin, Validator) and name != "required_platform":
            raise exceptions.RallyException(
                "Only RequiredPlatformValidator can be added "
                "to other validators as a validator")

        plugin._meta_setdefault("validators", [])
        plugin._meta_get("validators").append((name, (), kwargs,))
        return plugin

    return wrapper


def add_default(name, **kwargs):
    """Add validator to the plugin class default meta.

    Validator will be added to all subclasses by default

    :param name: str, name of the validator plugin
    :param kwargs: dict, arguments used to initialize validator class
        instance
    """

    def wrapper(plugin):
        if not hasattr(plugin, "DEFAULT_META"):
            plugin.DEFAULT_META = {}
        plugin.DEFAULT_META.setdefault("validators", [])
        plugin.DEFAULT_META["validators"].append((name, (), kwargs,))
        return plugin
    return wrapper


class ValidationResult(object):

    def __init__(self, is_valid, msg="", etype=None, etraceback=None):
        self.is_valid = is_valid
        self.msg = msg
        self.etype = etype
        self.etraceback = etraceback

    def __str__(self):
        if self.is_valid:
            return "validation success"
        if self.etype:
            return ("---------- Exception in validator ----------\n" +
                    self.etraceback)
        return self.msg


class ValidatablePluginMixin(object):

    @staticmethod
    def _load_validators(plugin):
        validators = plugin._meta_get("validators", default=[])
        return [(Validator.get(name), args, kwargs)
                for name, args, kwargs in validators]

    @classmethod
    def validate(cls, name, credentials, config, plugin_cfg,
                 namespace=None, allow_hidden=False, vtype=None):
        """Execute all validators stored in meta of plugin.

        Iterate during all validators stored in the meta of Validator
        and execute proper validate() method and add validation result
        to the list.

        :param name: name of the plugin to validate
        :param namespace: namespace of the plugin
        :param credentials: credentials dict for all platforms
        :param config: dict with configuration of specified workload
        :param plugin_cfg: dict, with exact configuration of the plugin
        :param allow_hidden: do not ignore hidden plugins
        :param vtype: Type of validation. Allowed types: syntax, platform,
            semantic. HINT: To specify several types use tuple or list with
            types
        :returns: list of ValidationResult(is_valid=False) instances
        """
        try:
            plugin = cls.get(name, allow_hidden=allow_hidden,
                             namespace=namespace)
        except exceptions.PluginNotFound:
            msg = "There is no %s plugin with name: '%s'" % (
                cls.__name__, name)
            return [ValidationResult(is_valid=False, msg=msg)]

        if vtype is None:
            semantic = True
            syntax = True
            platform = True
        else:
            if not isinstance(vtype, (list, tuple)):
                vtype = [vtype]
            wrong_types = set(vtype) - {"semantic", "syntax", "platform"}
            if wrong_types:
                raise ValueError("Wrong type of validation: %s" %
                                 ", ".join(wrong_types))
            semantic = "semantic" in vtype
            syntax = "syntax" in vtype
            platform = "platform" in vtype

        syntax_validators = []
        platform_validators = []
        regular_validators = []

        plugin_validators = cls._load_validators(plugin)
        for validator, args, kwargs in plugin_validators:
            if issubclass(validator, RequiredPlatformValidator):
                if platform:
                    platform_validators.append((validator, args, kwargs))
            else:
                validators_of_validators = cls._load_validators(validator)
                if validators_of_validators:
                    if semantic:
                        regular_validators.append((validator, args, kwargs))
                    if platform:
                        # Load platform validators from each validator
                        platform_validators.extend(validators_of_validators)
                else:
                    if syntax:
                        syntax_validators.append((validator, args, kwargs))

        results = []
        for validators in (syntax_validators, platform_validators,
                           regular_validators):
            for validator_cls, args, kwargs in validators:
                try:
                    validator = validator_cls(*args, **kwargs)

                    # NOTE(amaretskiy): validator is successful by default
                    result = (validator.validate(credentials=credentials,
                                                 config=config,
                                                 plugin_cls=plugin,
                                                 plugin_cfg=plugin_cfg)
                              or ValidationResult(True))
                except Exception as exc:
                    result = ValidationResult(
                        is_valid=False,
                        msg=str(exc),
                        etype=type(exc).__name__,
                        etraceback=traceback.format_exc())
                if not result.is_valid:
                    LOG.debug("Result of validator '%s' is not successful for "
                              "plugin %s.", validator_cls.get_name(), name)
                    results.append(result)

            if results:
                break

        return results
