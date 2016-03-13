
-- create device table
create table DAT_Devices (id integer primary key, name text, idDeviceType int);

-- create file table
create table DAT_Files (id integer primary key, idDevice integer, idParentDir integer, name text, bits integer, userId integer, groupId integer, size integer, aTime real, mTime real);

-- create directory table
create table DAT_Dirs (id integer, idDevice integer, idParentDir integer, name text, bits integer, userId integer, groupId integer, aTime real, mTime real);

-- create device type table
create table DAT_DeviceTypes (id integer primary key, name text);

--	create category table
create table DAT_Categories (id integer primary key, name text);

-- fill in device type table
insert into DAT_DeviceTypes (name) values ("Folder");
insert into DAT_DeviceTypes (name) values ("Floppy");
insert into DAT_DeviceTypes (name) values ("CD-Rom");
insert into DAT_DeviceTypes (name) values ("DVD");
insert into DAT_DeviceTypes (name) values ("HardDisk");
insert into DAT_DeviceTypes (name) values ("Removable Device");
