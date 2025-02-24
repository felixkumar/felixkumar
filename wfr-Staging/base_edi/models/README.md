# EDIS

## Table of Contents
- [Introduction](#user-content-introduction)
- [Document Synchronization ](#user-content-documentdynchronization)
  - [New Document Synchronization](#user-content-newdocumentsynchronization)
- [FTPConnection](#user-content-ftpconnection)

## Introduction
This module defines the logic needed to allow an Odoo instance to work like a synchronization server documents with third-party services and Odoo instances hosted in Odoo's Odoo,sh environment.
The module tries to provide a flexible and easy-to-use framework to develop EDI XML Document import/export modules communicating between Odoo instances and third-party services.
This enables new base technical framework, keeping this modular enough to make application by verticals.

## DocumentSynchronization

### NewDocumentSynchronization
Model `edi.config` allows setup multi-document sync with FTP credentials from different providers. User may create one EDI synchronization per FTP provider and add EDI synchronization action to be synchronized with the provider.

Model `edi.sync.action` allows document synchronization with  `sync.document.type` linked to which help decide what document to be sync and also keep track of other trivial details.

New Document Sycnhcinzaion be added by inheriting [`_inherit`](https://www.odoo.com/documentation/12.0/reference/orm.html#odoo.models.Model._inherit) the model `sync.document.type`.
After inheriting the model add document code (`doc_code`) and method to support new document code import/export operations. New `doc_code` can be added by using attribute [`selection_add`](https://www.odoo.com/documentation/12.0/reference/orm.html#basic-fields) on field  `doc_code` selection field and methods name that is will be performing the document synchronization for new document code must be named `_do_<name_of_new_code>` in order to make it work with the base application.

Exmaple code for adding new document synchronization from your application:

```python
class SyncDocumentType(models.Model):
    _inherit = 'sync.document.type'

    doc_code = fields.Selection(selection_add=[
                                      ('export_catalog', 'Export Sales Catalog (832)')
                                  ])

    def _do_export_catalog(self, conn, sync_action_id, values):
        '''
        This is dummy demo method.
        @param conn : sftp/ftp connection class.
        @param sync_action_id: recordset of type `edi.sync.action`
        @param values:dict of values that may be useful to various methods

        @return bool : return bool (True|False)
        '''
        # your code goes here...
        # below code for ftp conenection
        conn._connect()
        conn.ls()        
        conn._disconnect()
        return True

```


### FTPConnection
```python
class FTPConnection(Connection)
```
Works as a proxy around *ftplib* and *paramiko.SFTP* to be used by synchronization scripts when communicating with an FTP server. It also provides with some helpers methods to abstract common operations against an FTP server, like listing files, uploading and downloading files, etc.

- **Attributes**:
  - `_host`: Remote server host name.
    - **Type**: `str`

  - `_port`: Remote server port.
    - **Type**: `integer`

  - `_login`: User login on a remote server.
    - **Type**: `str`

  - `_password`: User password on a remote server
    - **Type**: `str`

  - `_repin`: Remote server's directory to log in.
    - **Type**: `str`

  - `_conn`: Current connection to the remote server.
    - **Type**: `ftplib.FTP`

- **Methods**:
  - `_ping()`: Method to ping the server to determine if we are still connected.

  - `_connect()`: Tries to connect to an FTP server using the related attributes.

  - `_disconnect()`: Method to close the current connection.

  - `ls()`: Method to list contents of a directory.

  - `cd(dirname)`: Method to change the CWD.

  - `mkd(dirname)`: Method to create a directory.

  - `mkf(filename, contents, directory=None)`: Method to create a file.

  - `rename(old_name, new_name, add_postfix_if_exists=True)`: Method to change a file's name.

  - `rm(filename)`: Method to delete a file.

  - `download_file(filename)`: Method to download a file.

  - `upload_file(filename, content='', directory=None)`: Method to upload a file.

