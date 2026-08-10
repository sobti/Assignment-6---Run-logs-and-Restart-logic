#ifndef _PROCESS_H_
#define _PROCESS_H_

#include "main.h"

void parse_process(Process_Info * process_info, const int * inode);
void parse_pid(int * pid, const int * inode);
void parse_pname(char pname[], const int * pid);
void parse_cmd(char cmd[], const int * pid);
void parse_opt(char opt[], const int * pid);

#endif
