mbdbEditor
==========


Description
-----------

These tools decode/encode a mbdb file to/from a csv file.
The decoder comes from a [Stack Overflow answer](http://stackoverflow.com/questions/3085153/how-to-parse-the-manifest-mbdb-file-in-an-ios-4-0-itunes-backup), slightly modified to export all the fields to a csv file, while the encoder was written from scratch.

Files structure
---------------

The mbdb format is explained on [The iPhone Wiki](https://www.theiphonewiki.com/wiki/ITunes_Backup#Manifest.mbdb) (little correction, the inode is an uint64).  
The csv file has the following fields:
`file type and permissions, inode, userid, groupid, file size, mtime, atime, ctime, fileID, filename, link target, domain, flag, base64(datahash), base64(encryption key)[,property1_name,base64(property1_value) ... ,propertyN_name,base64(propertyN_value)]`

Note: the `fileID` is not actually stored in the mbdb, it comes from `sha1(domain-filename)`. It is exported for your convenience.

Usage
-----

To convert a mbdb file to a csv:
```sh
./parse_manifest.py In.mbdb Out.csv
```
To convert a csv to a mbdb file:
```sh
./parse_csv.py In.csv Out.mbdb
```

Example
-------

When I upgraded my iPhone from iOS 8 to iOS 9, I wanted to start with a clean installation, only restoring my SMS.  
Since it is not possible to restore only this file, the trick consists to do a backup, upgrade, create a new backup, copy the files from the old to the new backup, and restore this modified backup.

1. Create a backup with the [libimobiledevice](http://www.libimobiledevice.org/) tools:
    ```sh
    $ mkdir iPhoneBackup
    $ idevicebackup2 backup iPhoneBackup
    ```

2. Decode the mbdb:
    ```sh
    $ cd iPhoneBackup/<UniqueDeviceID>
    $ ./parse_manifest.py Manifest.mbdb Manifest.csv
    ```

3. Now upgrade your phone/tablet, create a backup, decode it.  
   From the first backup, copy/replace the files to the new backup, e.g. `Library/SMS/sms.db` and `Library/SMS/Attachments*`  
   In Manifest.csv, add the entries of the new files, and don't forget to delete the old ones.  
   It might be a good idea to check for duplicate inodes, some entries have the same inodes by default, I don't know what could happen with regular files.

4. Now generate the new Manifest.mbdb and restore the backup:
    ```sh
    $ mv Manifest.mbdb Manifest.mbdb.backup
    $ ./parse_csv.py Manifest.csv Manifest.mbdb
    $ idevicebackup2 restore --reboot --system --settings iPhoneBackup
    ```
