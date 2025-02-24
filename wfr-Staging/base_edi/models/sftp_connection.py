import socket
import paramiko

from io import BytesIO

from .ftp_connection import FTPConnection


class SFTPConnection(FTPConnection):
    def _ping(self):
        pass

    @property
    def _connected(self):
        return True

    def _connect(self):
        transport = paramiko.Transport((self._host, self._port))
        transport.connect(
            username=self._login,
            password=self._password,
            gss_host=socket.getfqdn(self._host),
            gss_auth=False,
            gss_kex=False,
            # timeout=10,
        )
        self._conn = paramiko.SFTPClient.from_transport(transport)

        if self._repin:
            self.cd(self._repin)

    def _disconnect(self):
        self._conn.close()

    def ls(self):
        return self._conn.listdir()

    def cd(self, dirname):
        self._conn.chdir(path=dirname)

    def mkd(self, dirname):
        # NOTE: A mode parameter is accepted, using posix style. By default,
        # 0777 (octal) is used
        self._conn.mkdir(path=dirname)

    def mkf(self, filename, contents, directory=None):
        self._conn.putfo(
            contents,
            '%s/%s' % (directory, filename) if directory else filename
        )

    def rename(self, old_name, new_name, add_postfix_if_exists=True):
        contents = self.download_file(old_name)
        self.mkf(new_name, BytesIO(contents))
        self.rm(old_name)

    def rm(self, filename):
        self._conn.unlink(filename)

    def download_file(self, filename):
        data = BytesIO()
        self._conn.getfo(filename, data)
        content = data.getvalue()
        data.close()
        return content
