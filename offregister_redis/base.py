from functools import partial
from os import path

from fabric.context_managers import shell_env
from fabric.contrib.files import exists
from offregister_fab_utils.fs import cmd_avail
from pkg_resources import resource_filename

redis_dir = partial(
    path.join,
    path.dirname(resource_filename("offregister_redis", "__init__.py")),
    "configs",
)


def dl_install_redis_server(c, listen_port=6379, version="6.0.9", skip_if_avail=True):
    if skip_if_avail and cmd_avail(c, "redis-server"):
        return
    pkg = "redis-{version}.tar.gz".format(version=version)
    tmp_dir = c.run("mktemp -d", hide=True).stdout
    with c.cd(tmp_dir):
        c.run("wget http://download.redis.io/releases/{pkg}".format(pkg=pkg))
        c.run("tar xf {pkg}".format(pkg=pkg))
        with c.cd("redis-{version}".format(version=version)), shell_env(
            BUILD_WITH_SYSTEMD="yes", USE_SYSTEMD="yes"
        ):
            c.run("make")
            c.sudo("make install")

            redis_executable = c.run("command -v redis-server", hide=True).stdout
            redis_data_dir = "/var/lib/redis/{listen_port}".format(
                listen_port=listen_port
            )
            env = dict(
                REDIS_PORT=str(listen_port),
                REDIS_CONFIG_FILE="/etc/redis/{}.conf".format(listen_port),
                REDIS_LOG_FILE="/var/log/redis_{}.log".format(listen_port),
                REDIS_DATA_DIR=redis_data_dir,
                REDIS_EXECUTABLE=redis_executable,
            )
            if version[0] >= "6" and exists(
                c, runner=c.run, path="/etc/systemd/system"
            ):
                c.sudo(
                    "mkdir -p {redis_data_dir}".format(redis_data_dir=redis_data_dir),
                    env=env,
                )
                c.sudo("sysctl vm.overcommit_memory=1", env=env)
                upload_template_fmt(
                    c,
                    redis_dir("systemd-redis_server.service"),
                    "/etc/systemd/system/redis_{listen_port}.service".format(
                        listen_port=listen_port
                    ),
                    context={
                        "REDIS_SERVER": redis_executable,
                        "REDIS_SERVER_ARGS": " ".join(
                            (
                                "--port {listen_port}".format(listen_port=listen_port),
                                "--logfile /var/log/redis_{listen_port}.log".format(
                                    listen_port=listen_port
                                ),
                            )
                        ),
                        "WORKING_DIR": redis_data_dir,
                    },
                    use_sudo=True,
                )
            else:
                return c.sudo("sh utils/install_server.sh", env=env)

__all__ = ["dl_install_redis_server"]
