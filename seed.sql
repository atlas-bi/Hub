/*

    Extract Management 2.0
    Copyright (C) 2020  Riverside Healthcare, Kankakee, IL

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

*/

/*

  required for app to run

*/

-------------------------------

insert into
  login_type ('name')
values
  ('login'),
  ('logout'),
  ('bad login');

-------------------------------

insert into
  task_source_type ('name')
values
  ('Database'),
  ('Network File (SMB Connection)'),
  ('File (SFTP Connection)'),
  ('File (FTP Connection)'),
  ('Python Script');

-------------------------------

insert into
  task_processing_type ('name')
values
  ('Network File (SMB Connection)'),
  ('File (SFTP Connection)'),
  ('File (FTP Connection)'),
  ('Git URL'),
  ('Other URL (no auth)'),
  ('Source Code');

-------------------------------

insert into
  task_source_query_type ('name')
values
  ('Git URL'),
  ('File Path (SMB Connection)'),
  ('Other URL (no auth)'),
  ('Source Code'),
  ('File Path (SFTP Connection)'),
  ('File Path (FTP Connection)');

-------------------------------

insert into
  connection_database_type ('name')
values
  ('Postgres'),
  ('SQL Sever'),
  ('Sqlite');

-------------------------------

insert into
  task_destination_file_type ('name', 'ext')
values
  ('CSV (.csv)','csv'),
  ('Text (.txt)','txt'),
  ('Excel (.csv)','csv'),
  ('Other (specify in filename)','');


-------------------------------

insert into
  task_status ('name')
values
  ('Running'),
  ('Errored'),
  ('Stopped'),
  ('Completed'),
  ('Starting'),
  ('Scheduler'),
  ('User'),
  ('Runner'),
  ('SFTP'),
  ('SMB'),
  ('File'),
  ('Email'),
  ('FTP'),
  ('Py Processer'),
  ('Git/Web Code'),
  ('Date Parser');

/*
  org specific and not required for app to run.
  data is for demo purposes only.
*/

-------------------------------

insert into
  user ('user_id', 'full_name')
values
  ('1234', 'Boss Man');

-------------------------------

-- https://rnacentral.org/help/public-database
insert into
  connection_database ('name', 'type_id', 'connection_string','connection_id')
values
  ('Public Database',1,'host=hh-pgsql-public.ebi.ac.uk dbname=pfmegrnargs user=reader password=NWDMCE5xdipIjRrp',1);

-------------------------------

insert into
  connection (
    'name',
    'description',
    'address',
    'primary_contact',
    'primary_contact_email',
    'primary_contact_phone'
  )
values
  (
    'Extract Organization',
    'The best place to send data.',
    'Organization Extract',
    'Boss Man',
    'boss@man.org',
    '(000)-000-0000'
  );

-------------------------------

-- http://speedtest.tele2.net
insert into
  connection_ftp (
    'connection_id',
    'name',
    'address',
    'path',
    'username',
    'Password'
  )
values
  (
    1,
    'Speed Test Tele2',
    'speedtest.tele2.net/',
    '/upload/',
    'anonymous',
    'anonymous'
  );

-------------------------------

insert into
  project (
    'name',
    'description',
    'owner_id',
    'creator_id',
    'updater_id',
    'intv',
    'intv_type',
    'intv_value'
  )
values
  ('Demo Project', 'This description must be the best', 1, 1, 1, 1,'m',15);

-------------------------------

insert into
  task (
    'name',
    'source_type_id',
    'source_code',
    'destination_ftp',
    'destination_ftp_id',
    'project_id',
    'source_query_type_id',
    'source_database_id',
    'enabled',
    'destination_file_name',
    'destination_file_type_id',
    'destination_file_delimiter'
  )
values
  (
    'Task 1',
    1,
    'select ''1''',
    1,
    1,
    1,
    4,
    1,
    1,
    'test_%d_%M',
    2,
    '|'
  );
