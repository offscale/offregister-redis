from offregister_fab_utils.apt import apt_depends
from offregister_fab_utils.ubuntu.systemd import restart_systemd

from offregister_redis.base import dl_install_redis_server


def dl_install0(c, *args, **kwargs):
    apt_depends(c, "build-essential", "pkg-config", "libsystemd-dev")
    return dl_install_redis_server(
        c,
        listen_port=kwargs.get("redis_port", 6379),
        skip_if_avail=kwargs.get("skip_if_avail", True),
        **dict(version=kwargs["redis_version"]) if "redis_version" in kwargs else {},
    )


def ensure_service_is_started1(c, *args, **kwargs):
    listen_port = kwargs.get("redis_port", 6379)
    return restart_systemd(c, "redis_{listen_port}".format(listen_port=listen_port))


__all__ = ["dl_install0", "ensure_service_is_started1"]
