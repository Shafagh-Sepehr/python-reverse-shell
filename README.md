## local client-server project written in C++ using TCP socket.  
the server can handle multiple clients simultaneously.  
the client app is a malicious calculator(the graphical interface) that after running connects to the server. and the server can run Linux commands on the victim's machine (the terminal is opened in the same directory the calculator was in) and receive the outputs of that command.  

in addition to Linux commands (bash built-in commands are not available except cd), there are two other commands for uploading and downloading files to or from the victim's system:  
**DOWNLOAD \<file path>/filename.ext \<destination path>**  
**UPLOAD \<file path>/filename.ext \<destination path>**  
the **\<file path>** can be relative or absolute. the **\<destination path>** can also be relative or absolute, other than that it can specify a new name for the file or overwrite an existing file (can be like folder1/folder2/../name_of_file.ext). if not specified the original filename will be used.  

the cd command also supports "**cd**" and "**cd ~**" variations. the absolute and relative addressing approaches are also available.

the server can terminate, sort by name, and rename clients. it can also send one single command to all clients and receive the result from them which will be shown separately in the output area. and also in each client's separate output area.  
(in case of downloading files having the same name like filename.txt, they will be renamed to filename_client1.txt, filename_client2.txt, ... (suppose client names are like client1, client2, ...))  

there's also a config file that can be used to change port and TCP data segment size(header). the last one is to disable sending the outputs of commands that have been run on all clients to each client's separate text area.
