# -*- coding: utf-8 -*-

from fabric.api import abort


class Deployment(object):
    required_attributes = (
        'ENVIRONMENT',
        'DEPLOYMENT_SERVER',
    )
    ENVIRONMENT = ''  # staging, production, ...

    ELB_NAME = ''

    UMASK = 'umask 0002'

    DEPLOYMENT_SERVER = 'opbeat.com'
    DEPLOYMENT_FLAGS = ''

    ROLES_CONFIG = {}

    @classmethod
    def apply(cls, env):
        # set roledefs, virtualenv and target
        for role, conf in cls.ROLES_CONFIG.iteritems():
            if 'servers' in conf:
                env.roledefs[role] = conf['servers']
            if 'virtualenv' in conf:
                setattr(env, role + '_venv', conf['virtualenv'])
            if 'target' in conf:
                setattr(env, role + '_target', conf['target'])

        # all-caps attributes are assumed to be settings, their values are
        # applied verbatim to the env, with a lower-cased attribute name
        for attr in dir(cls):
            if attr.isupper():
                setattr(env, attr.lower(), getattr(cls, attr))

    @classmethod
    def check(cls):
        missing = []
        for attr in cls.required_attributes:
            if not getattr(cls, attr):
                missing.append(attr)
        if missing:
            abort('One or more required attributes missing on {}:\n{}'.format(
                cls.__name__,
                '\n'.join(' - ' + attr for attr in missing)
            ))

