# -*- coding: utf-8 -*-
import time

from fabric.api import run, env


def deregister_from_elb():
    if env.elb_name:
        run('elb-dance deregister {}'.format(env.elb_name))
        print "Waiting for instance to be fully deregistered"
        # No way to know when it's really out, but empirically seems to be around
        # 10 secs.
        # Update: 12 seconds was not always enough.
        time.sleep(20)


def register_with_elb():
    if env.elb_name:
        run('elb-dance register {}'.format(env.elb_name))


