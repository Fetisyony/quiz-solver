#include <windows.h>
#include <stdio.h>
#include <tchar.h>
#include <psapi.h>
#include <iostream>
using namespace std;


int char_len(TCHAR *c) {
    int i = 0;
    while (i < 10000 && c[i] != '\0')
        ++i;
    return i;
}

bool equal_char(TCHAR *c1, char *c2) {
    for (int i = 0; i < char_len(c1) && i < 10; ++i) {
        if (c1[i] != c2[i])
            return false;
    }
    return true;
}

TCHAR name[MAX_PATH];
void getProcessName(DWORD processID) {
    TCHAR szProcessName[MAX_PATH] = TEXT("<unknown>");

    // Get a handle to the process.
    HANDLE hProcess = OpenProcess(PROCESS_QUERY_INFORMATION |
                                  PROCESS_VM_READ,
                                  FALSE, processID);

    // Get the process name.

    if (NULL != hProcess) {
        HMODULE hMod;
        DWORD cbNeeded;

        if (EnumProcessModules( hProcess, &hMod, sizeof(hMod), &cbNeeded)) {
            GetModuleBaseName(hProcess, hMod, szProcessName, sizeof(szProcessName)/sizeof(TCHAR));
        }
    }
    // Release the handle to the process.
    CloseHandle(hProcess);

    int ind = 0;
    for (auto i : szProcessName) {
        if (i == '\0')
            name[ind] = '\0';

        name[ind++] = i;
    }
}

bool check_existance(char* procToFind) {
    // Get the list of process identifiers.
    DWORD aProcesses[1024], cbNeeded, cProcesses;

    if (!EnumProcesses(aProcesses, sizeof(aProcesses), &cbNeeded))
        return 1;

    // Calculate how many process identifiers were returned.
    cProcesses = cbNeeded / sizeof(DWORD);

    for (unsigned int i = 0; i < cProcesses; i++) {
        if (aProcesses[i] != 0) {
            getProcessName(aProcesses[i]);
            if (equal_char(name, procToFind)) {
                return true;
            }
        }
    }
    return false;
}

void run_again() {
    STARTUPINFO si;
    PROCESS_INFORMATION pi;
    ZeroMemory( &si, sizeof(si) );
    si.cb = sizeof(si);
    ZeroMemory( &pi, sizeof(pi) );

    CreateProcess(NULL,
                  (LPTSTR)"python.exe C:\\Users\\Admin\\Desktop\\Mine\\PROGRAMMING\\projects\\Press_immitation\\quiz\\main.py",
                  NULL,           // Process handle not inheritable
                  NULL,           // Thread handle not inheritable
                  FALSE,          // Set handle inheritance to FALSE
                  0,              // No creation flags
                  NULL,           // Use parent's environment block
                  NULL,           // Use parent's starting directory
                  &si,            // Pointer to STARTUPINFO structure
                  &pi);
}

int main() {
    char name[] = "python.exe";

    start:
    while (check_existance(name)) {
        Sleep(100);
    }

    int value = MessageBox(NULL,
                           (LPCSTR)"main.py was interrupted!",
                           (LPCSTR)"Error",
                           MB_ICONERROR | MB_RETRYCANCEL | MB_TOPMOST | MB_SYSTEMMODAL
                           );
    if (value == 4) {
        run_again();

        Sleep(5000);
        goto start;
    }
    return 0;
}