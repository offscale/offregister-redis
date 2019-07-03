from offregister_fab_utils.apt import apt_depends

from offregister_redis.base import dl_install_redis_server


def dl_install0(*args, **kwargs):
    apt_depends('build-essential')
    return dl_install_redis_server(listen_port=kwargs.get('redis_port', 6379),
                                   version=kwargs.get('redis_version', '5.0.5'))
