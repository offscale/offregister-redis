from functools import partial
from os import path

from fabric.api import run
from fabric.context_managers import shell_env, cd
from fabric.contrib.files import exists, upload_template
from fabric.operations import sudo
from offregister_fab_utils.fs import cmd_avail
from pkg_resources import resource_filename

redis_dir = partial(
    path.join,
    path.dirname(resource_filename("offregister_redis", "__init__.py")),
    "configs",
)


def dl_install_redis_server(listen_port=6379, version="6.0.9", skip_if_avail=True):
    if skip_if_avail and cmd_avail("redis-server"):
        return
    pkg = "redis-{version}.tar.gz".format(version=version)
    tmp_dir = run("mktemp -d", quiet=True)
    with cd(tmp_dir):
        run("wget http://download.redis.io/releases/{pkg}".format(pkg=pkg))
        run("tar xf {pkg}".format(pkg=pkg))
        with cd("redis-{version}".format(version=version)), shell_env(BUILD_WITH_SYSTEMD='yes', USE_SYSTEMD='yes'):
            run("make")
            sudo("make install")

            redis_executable = run("command -v redis-server", quiet=True)
            redis_data_dir = "/var/lib/redis/{listen_port}".format(
                                        listen_port=listen_port
                                    )
            with shell_env(
                REDIS_PORT=str(listen_port),
                REDIS_CONFIG_FILE="/etc/redis/{}.conf".format(listen_port),
                REDIS_LOG_FILE="/var/log/redis_{}.log".format(listen_port),
                REDIS_DATA_DIR=redis_data_dir,
                REDIS_EXECUTABLE=redis_executable,
            ):
                if version[0] >= "6" and exists("/etc/systemd/system"):
                    sudo('mkdir -p {redis_data_dir}'.format(redis_data_dir=redis_data_dir))
                    sudo('sysctl vm.overcommit_memory=1')
                    upload_template(
                        redis_dir("systemd-redis_server.service"),
                        "/etc/systemd/system/redis_{listen_port}.service".format(
                            listen_port=listen_port
                        ),
                        context={
                            "REDIS_SERVER": redis_executable,
                            "REDIS_SERVER_ARGS": " ".join(
                                (
                                    "--port {listen_port}".format(
                                        listen_port=listen_port
                                    ),
                                    "--logfile /var/log/redis_{listen_port}.log".format(
                                        listen_port=listen_port
                                    ),
                                )
                            ),
                            "WORKING_DIR": redis_data_dir
                        },
                        use_sudo=True,
                    )
                else:
                    return sudo("sh utils/install_server.sh")
