# -*- coding: utf-8 -*-
import os
import time
import ConfigParser

from boto import ec2, route53
from fabric.api import run, env, abort
from fabric.contrib.console import confirm


def _get_elbs():
    elbs = []
    if env.elb_name:
        elbs = [env.elb_name]
    elif env.elb_names:
        elbs = env.elb_names

    return elbs


def deregister_from_elb():
    elbs = _get_elbs()
    if elbs:
        for elb in elbs:
            run('elb-dance deregister {}'.format(elb))

        print "Waiting for instance to be fully deregistered"
        # No way to know when it's really out, but empirically seems to be around
        # 10 secs.
        # Update: 12 seconds was not always enough.
        time.sleep(20)


def register_with_elb():
    elbs = _get_elbs()

    for elb in elbs:
        run('elb-dance register {}'.format(elb))


def setup_instance(
        hostname,
        image_name='stage',
        instance_type='m1.small',
        iam_role='staging-server',
        security_group_name='stage',
        key_name='ron',
        credentials_file=os.path.join(os.path.expanduser('~'), '.s3cfg'),
        region='us-east-1',
    ):
    """
    Sets up a new EC2 instance. The defaults set up a new staging instance.
    """
    conn = get_connection(
        ec2.connect_to_region,
        region=region,
        credentials_file=credentials_file,
    )
    instance = get_instance_by_name(conn, hostname)
    if instance and not instance.state == 'terminated':
        abort('Instance with name {} already running, id: {}, IP: {}'.format(
            hostname,
            instance.id,
            instance.ip_address,
        ))
    image = _get_ami_by_name(conn, image_name)
    reservation = conn.run_instances(
        image.id,
        key_name=key_name,
        instance_type=instance_type,
        security_groups=[security_group_name],
        instance_profile_name=iam_role,
    )
    instance = reservation.instances[0]
    instance.add_tag('Name', hostname)
    return conn, instance


def terminate_instance(
        hostname,
        credentials_file=os.path.join(os.path.expanduser('~'), '.s3cfg'),
        region='us-east-1',
    ):
    conn = get_connection(
        ec2.connect_to_region,
        region=region,
        credentials_file=credentials_file,
    )
    instance = get_instance_by_name(conn, hostname)
    if not instance:
        abort('Instance with name {} not found'.format(hostname))
    _set_volume_autoterminate(instance)
    conn.terminate_instances([instance.id])
    return conn, instance


def setup_dns(
        hostname,
        dns_name,
        ttl=300,
        zone_name='opbeat.com',
        credentials_file=os.path.join(os.path.expanduser('~'), '.s3cfg'),
    ):
    conn = get_connection(
        route53.connect_to_region,
        region='universal',
        credentials_file=credentials_file,
    )
    zone = conn.get_zone(zone_name)
    if zone.get_cname(hostname) and not confirm(
        'CNAME for {} already exists. Shall I update it?'.format(hostname)
    ):
        return conn, None
    changes = route53.record.ResourceRecordSets(
        connection=conn,
        hosted_zone_id=zone.id
    )
    change = changes.add_change('UPSERT', hostname, 'CNAME', ttl)
    change.add_value(dns_name)
    changes.commit()
    return conn, zone


def get_instance_by_name(conn, name):
    reservations = conn.get_all_instances(filters={'tag:Name': name})
    if reservations:
        return reservations[0].instances[0]
    else:
        return None


def _get_ami_by_name(conn, name):
    images = conn.get_all_images(owners='self', filters={'name': name})
    if not images:
        abort('Image with name {} not found'.format(name))
    return images[0]


def _get_access_keys_from_config(path):
    config = ConfigParser.ConfigParser()
    config.read(path)
    return (
        config.get('default', 'access_key'),
        config.get('default', 'secret_key'),
    )


def _set_volume_autoterminate(instance):
    mapping = instance.get_attribute('blockDeviceMapping')
    devices = [key + '=1' for key in mapping['blockDeviceMapping'].keys()]
    instance.modify_attribute('blockDeviceMapping', devices)


def get_connection(
        connector=ec2.connect_to_region,
        region='us-east-1',
        credentials_file=os.path.join(os.path.expanduser('~'), '.s3cfg'),
    ):
    access_key, secret_key = _get_access_keys_from_config(credentials_file)
    return connector(
        region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )


