import ftplib

from io import StringIO, BytesIO


class FTPConnection(object):

    def __init__(cls, config=None, *args, **kwargs):
        if not config:
            raise Exception

        cls._host = config.get('host')
        cls._port = config.get('port')
        cls._login = config.get('login')
        cls._password = config.get('password')
        cls._repin = config.get('repin')
        cls._active = config.get('active')

        cls._conn = None

    def __enter__(self):
        """ Allows python 'using' construct"""
        self._connect()
        return self

    def __exit__(self, type, value, traceback):
        """ Allows python 'using' construct"""
        self._disconnect()

    def _ping(self):
        """ Pings the server to determine if we are still connected """
        self._conn.voidcmd("NOOP")

    @property
    def _connected(self):
        """ Pings the server to determine if we are still connected """
        try:
            self._ping()
            return True
        except ftplib.all_errors:
            return False

    def _connect(self):
        try:
            self._conn = ftplib.FTP(
                            host=self._host,
                            user=self._login,
                            passwd=self._password,
                            timeout=10
                        )
            if self._active:
                self._conn.set_pasv(False)
            self.cd(self._repin)
            return self._conn
        except ftplib.all_errors as e:
            raise Exception(e)

    def _disconnect(self):
        if self._connected:
            self._conn.quit()

    def ls(self):
        if hasattr(self._conn, 'mlst'):
            return self._conn.mlsd()
        else:
            return self._conn.nlst()

    def cd(self, dirname):
        if dirname:
            self._conn.cwd(dirname)

    def mkd(self, dirname):
        """ Create directory in the current working directory """
        if dirname:
            self._conn.mkd(dirname)

    def mkf(self, filename, contents, directory=None):
        """
        Create a file with filename and contents in the current or specified directory
        @param buffer contents: Buffer object like StringIO containing contents
        """
        self._conn.storbinary('STOR %s%s' % (directory and directory + '/' or '', filename), contents)

    def rename(self, old_name, new_name, add_postfix_if_exists=True):
        """ rename / move a file """
        try:
            self._conn.rename(old_name, new_name)
        except ftplib.error_perm as e:
            if 'existant' in e.message:
                new_name = new_name.split('.')
                new_name = "-new.".join(new_name)
                self.rename(old_name, new_name)
            else:
                raise

    def rm(self, filename):
        """ Delete a file """
        return self._conn.delete(filename)

    def download_file(self, filename, data=None):
        """
        Downloads data for the specified file
        @return str the contents of the file
        """
        if not data:
            data = BytesIO()
        self._conn.retrbinary('RETR %s' % filename, data.write)
        contents = data.getvalue()
        data.close()
        return contents

    def upload_file(self, filename, content='', directory=None):
        self.mkf(filename, content, directory=directory)

    def download_incoming_file(self, incoming_file):
        content = self.download_file(incoming_file)
        return content.decode('utf-8')

    def upload_outgoing_files(self, outgoing_files, directory=None, on_conflicts='replace'):
        outgoing_filenames = [out_file['x_name'] for out_file in outgoing_files]
        existing_filenames = self.ls()
        conflicts = set(existing_filenames) & set(outgoing_filenames)
        if conflicts and on_conflicts == 'raise':
            raise Exception('Some filenames already exist!')
        elif conflicts and on_conflicts == 'rename':
            for filename in conflicts:
                self.rename(filename, filename + '.bak')
        elif conflicts and on_conflicts == 'replace':
            for filename in conflicts:
                self.rm(filename)

        for outgoing_file in outgoing_files:
            self.upload_outgoing_file(outgoing_file, directory=directory)

    def upload_outgoing_file(self, outgoing_file, directory=None):
        filename = outgoing_file['x_name']
        content_type = outgoing_file['x_content_type']
        content = outgoing_file['x_content']
        self.upload_file(
            filename,
            content=StringIO(content_type == 'xls' and content.encode('utf-8', 'replace') or encodestring(content)),
            directory=directory
        )

    def delete_outgoing_files(self, outgoing_files, directory=None):
        outgoing_filenames = [out_file['x_name'] for out_file in outgoing_files]
        existing_filenames = self.ls()
        to_remove = set(existing_filenames) & set(outgoing_filenames)
        for outgoing_filename in to_remove:
            self.rm(directory and directory + '/' or '' + outgoing_filename)
